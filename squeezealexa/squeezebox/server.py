# -*- coding: utf-8 -*-
#
#   Copyright 2017-18 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

from __future__ import print_function

import time

from squeezealexa.utils import with_example, PY2, print_d, stronger

if PY2:
    import urllib
else:
    import urllib.request as urllib


class SqueezeboxException(Exception):
    """Errors communicating with the Squeezebox"""


class SqueezeboxPlayerSettings(dict):
    """Encapsulates player settings"""

    @property
    def id(self):
        return self['playerid']

    def __getattr__(self, key):
        return self.get(key, None)

    def __str__(self):
        try:
            return "{name} [{short}]".format(short=self['playerid'][-5:],
                                             **self)
        except KeyError:
            return "Unidentified Squeezebox player: %r" % self


class Server(object):
    """Encapsulates access to a Squeezebox player via a Squeezecenter server"""

    _TIMEOUT = 10
    _MAX_FAILURES = 3
    _MAX_CACHE_SECS = 600

    def __init__(self, transport, user=None, password=None,
                 cur_player_id=None, debug=False):

        self.transport = transport
        self._debug = debug
        self.user = user
        self.password = password
        if user and password:
            self.log_in()
            print_d("Authenticated with %s!" % self)
        self.players = {}
        self.refresh_status()
        self.cur_player_id = pid = cur_player_id or list(self.players)[0]
        print_d("Default player is now %s" % (self.players[pid],))
        self.__genres = []
        self.__playlists = []
        self.__favorites = []
        self._created_time = time.time()

    @property
    def player_names(self):
        return {p.get("name", "unknown") for p in self.players.values()}

    def is_stale(self):
        return (time.time() - self._created_time) > self._MAX_CACHE_SECS

    def log_in(self):
        result = self.__a_request("login %s %s" % (self.user, self.password))
        if result != "%s ******" % self.user:
            raise SqueezeboxException(
                "Couldn't log in to squeezebox: response was '%s'" % result)

    def __a_request(self, line, raw=False, wait=True):
        reply = self._request([line], raw=raw, wait=wait)
        if reply and len(reply):
            return reply[0]
        if self.user and self.password:
            print_d("Command failed. Trying to re-log in.")
            self.log_in()
            reply = self._request([line], raw=raw, wait=wait)
            if reply and len(reply):
                return reply[0]
        raise SqueezeboxException("Unprocessable command or login error")

    def _unquote(self, response):
        return ' '.join(urllib.unquote(s) for s in response.split(' '))

    def _request(self, lines, raw=False, wait=True):
        """
        Send multiple pipelined requests to the server, if connected,
        and return their responses,
        assuming order is maintained (which seems safe).

        :type lines list[str]
        :rtype list[str]
        """
        if not self.transport.is_connected:
            return []
        if not (lines and len(lines)):
            return []
        lines = [l.rstrip() for l in lines]

        first_word = lines[0].split()[0]
        if not (self.transport.is_connected or first_word == 'login'):
            print_d("Can't do '%s' - not connected" % first_word, self)
            return

        if self._debug:
            print_d("<<<< " + "\n..<< ".join(lines))
        request = "\n".join(lines) + "\n"
        raw_response = self.transport.communicate(request, wait=wait)
        if not wait:
            return []
        if not raw_response:
            raise SqueezeboxException(
                "No further response from %s. Login problem?" % self)
        raw_response = raw_response.rstrip("\n")
        response = raw_response if raw else self._unquote(raw_response)
        if self._debug:
            print_d(">>>> " + "\n..>> ".join(response.splitlines()))

        def start_point(text):
            if first_word == 'login':
                return 6
            delta = -1 if text.endswith('?') else 1
            return len(self._unquote(text) if raw else text) + delta

        resp_lines = response.splitlines()
        if len(lines) != len(resp_lines):
            raise ValueError("Response problem: %s != %s"
                             % (lines, resp_lines))
        return [resp_line[start_point(line):]
                for line, resp_line in zip(lines, resp_lines)]

    def __pairs_from(self, response):
        """Split and unescape a response"""
        def demunge(string):
            s = urllib.unquote(string)
            return tuple(s.split(':', 1))
        demunged = map(demunge, response.split(' '))
        return [d for d in demunged if len(d) == 2]

    def _groups(self, response, start=None, extra_bools=None):
        """Returns a group of dicts from `response`.
        If `start` is specified, items prior to this will be discarded,
        and each group will be starting with this.
        `extra_bools` allows custom keys to be booleaned"""
        group = []
        for k, v in self.__pairs_from(response):
            if k == start:
                if group:
                    yield dict(group)
                group = [(k, stronger(k, v, extra_bools))]
            else:
                if group or not start:
                    group.append((k, stronger(k, v, extra_bools)))
        yield dict(group)

    def refresh_status(self):
        """ Updates the list of the Squeezebox players available and other
        server metadata."""
        print_d("Refreshing server and player statuses...")
        response = self.__a_request("serverstatus 0 99", raw=True)
        self.players = {}
        for data in self._groups(response, 'playerid',
                                 extra_bools=['power', 'connected']):
            self.players[data['playerid']] = SqueezeboxPlayerSettings(data)
        print_d("Found %d player(s): %s"
                % (len(self.players),
                   [p['name'] for p in self.players.values()]))
        if self._debug:
            print_d("Player(s): %s" % (self.players.values(),))

    def player_request(self, line, player_id=None, raw=False, wait=True):
        """Makes a single request to a particular player (or the current)"""
        try:
            player_id = (player_id or
                         self.cur_player_id or
                         list(self.players.values())[0]["playerid"])
            return self._request(["%s %s" % (player_id, line)],
                                 raw=raw, wait=wait)[0]
        except IndexError:
            return None

    def play_genres(self, genre_list, player_id=None):
        """Adds then plays a random mix of albums of specified genres"""
        gs = genre_list or []
        commands = (["playlist clear", "playlist shuffle 1"] +
                    ["playlist addalbum %s * *" % urllib.quote(genre)
                     for genre in gs if genre] +
                    ["play 2"])
        pid = player_id or self.cur_player_id
        return self._request(["%s %s" % (pid, com) for com in commands])

    def get_track_details(self, player_id=None):
        keys = ["genre", "artist", "current_title"]
        pid = player_id or self.cur_player_id
        responses = self._request(["%s %s ?" % (pid, s)
                                   for s in keys])
        return dict(zip(keys, responses))

    @property
    def genres(self):
        if not self.__genres:
            resp = self.__a_request("genres 0 255", raw=True)
            self.__genres = [v for k, v in self.__pairs_from(resp)
                             if k == 'genre']
            print_d(with_example("Loaded %d LMS genres", self.__genres))
        return self.__genres

    @property
    def playlists(self):
        if not self.__playlists:
            resp = self.__a_request("playlists 0 255", raw=True)
            self.__playlists = [v for k, v in self.__pairs_from(resp)
                                if k == 'playlist']
            print_d(with_example("Loaded %d LMS playlists", self.__playlists))
        return self.__playlists

    @property
    def favorites(self):
        if not self.__favorites:
            resp = self.__a_request("favorites items 0 255 want_url:1",
                                    raw=True)
            self.__favorites = {d['name']: d
                                for d in self._groups(resp, 'name')
                                if d['isaudio']}
            print_d(with_example("Loaded %d LMS faves", self.__favorites))
        return self.__favorites

    def get_status(self, player_id=None):
        response = self.player_request("status - 2", player_id=player_id,
                                       raw=True)
        return dict(self.__pairs_from(response))

    def next(self, player_id=None):
        self.player_request("playlist jump +1", player_id=player_id)

    def previous(self, player_id=None):
        self.player_request("playlist jump -1", player_id=player_id)

    def playlist_play(self, path, player_id=None):
        """Play song / playlist immediately"""
        self.player_request("playlist play %s" % (urllib.quote(path)),
                            player_id=player_id)

    def playlist_resume(self, name, resume=True, wipe=False, player_id=None):
        cmd = ("playlist resume %s noplay:%d wipePlaylist:%d"
               % (urllib.quote(name), int(not resume), int(wipe)))
        self.player_request(cmd, wait=False, player_id=player_id)

    def change_volume(self, delta, player_id=None):
        if not delta:
            return
        cmd = "mixer volume %s%.1f" % ('+' if delta > 0 else '', float(delta))
        self.player_request(cmd, player_id=player_id)

    def set_volume(self, value, player_id=None):
        if not value:
            return
        cmd = "mixer volume %.1f" % float(value)
        self.player_request(cmd, player_id=player_id)

    def get_milliseconds(self):
        secs = self.player_request("time ?") or 0
        return float(secs) * 1000.0

    def pause(self, player_id=None):
        self.player_request("pause 1", player_id=player_id)

    def resume(self, player_id=None, fade_in_secs=1):
        self.player_request("pause 0 %d" % fade_in_secs, player_id=player_id)

    def set_shuffle(self, on=True, player_id=None):
        self.player_request("playlist shuffle %d" % int(bool(on) * 2),
                            player_id=player_id)

    def set_repeat(self, on=True, player_id=None):
        self.player_request("playlist repeat %d" % int(bool(on)),
                            player_id=player_id)

    def set_power(self, on=True, player_id=None):
        self.player_request("power %d" % int(bool(on)), player_id=player_id)

    def set_all_power(self, on=True):
        value = int(bool(on))
        self._request(["%s power %d" % (p, value)
                       for p in self.players.keys()])

    def __str__(self):
        return "Squeezebox server at {}".format(str(self.transport))
