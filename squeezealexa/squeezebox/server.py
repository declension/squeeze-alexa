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

import time

from typing import List
from squeezealexa.utils import with_example, print_d, stronger, print_w

import urllib.request as urllib
import re


class SqueezeboxException(Exception):
    """Errors communicating with the Squeezebox"""


class SqueezeboxPlayerSettings(dict):
    """Encapsulates player settings"""

    def __init__(self, data: dict):
        super().__init__(data)
        if 'playerid' not in data:
            raise SqueezeboxException(
                "Couldn't find a playerid in {data}".format(data=data))

    @property
    def id(self) -> str:
        return self['playerid']

    def __getattr__(self, key):
        return self.get(key, None)

    def __str__(self):
        return "{name} [{short}]".format(short=self['playerid'][-5:], **self)


class Server(object):
    """Encapsulates access to a Squeezebox player via a Squeezecenter server"""

    _TIMEOUT = 10
    _MAX_FAILURES = 3
    _MAX_CACHE_SECS = 600
    _INSTANCE = None
    _CREATION_TIME = None

    def __new__(cls, *args, **kwargs):
        if not cls._INSTANCE:
            print_d("Creating new server instance")
            cls._INSTANCE = super().__new__(cls)
            cls._CREATION_TIME = time.time()
            return cls._INSTANCE
        if time.time() - cls._CREATION_TIME > cls._MAX_CACHE_SECS:
            print_d("Recreating stale server instance")
            del cls._INSTANCE
            cls._CREATION_TIME = time.time()
            cls._INSTANCE = super().__new__(cls)
        return cls._INSTANCE

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
        players = list(self.players.values())
        if not players:
            raise SqueezeboxException("Uh-oh. No players found.")
        if not cur_player_id:
            self.cur_player_id = players[0].id
        elif cur_player_id not in self.players:
            print_w("Couldn't find player {id} (found: {all}). "
                    "Check your DEFAULT_PLAYER config.",
                    id=cur_player_id, all=", ".join(list(self.players.keys())))
            self.cur_player_id = players[0].id
        else:
            self.cur_player_id = cur_player_id
        print_d("Current player is now: {player}",
                player=self.players[self.cur_player_id])
        self.__genres = []
        self.__playlists = []
        self.__favorites = []

    @property
    def player_names(self):
        return {p.get("name", "unknown") for p in self.players.values()}

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

    def _request(self, lines, raw=False, wait=True) -> List[str]:
        """
        Send multiple pipelined requests to the server, if connected,
        and return their responses,
        assuming order is maintained (which seems safe).
        """
        if not (lines and len(lines)):
            return []
        lines = [l.rstrip() for l in lines]

        first_word = lines[0].split()[0]
        if not (self.transport.is_connected or first_word == 'login'):
            raise SqueezeboxException(
                "Can't do '{cmd}', {transport} is not connected".format(
                    cmd=first_word, transport=self.transport))

        if self._debug:
            print_d("<<<< " + "\n..<< ".join(lines))
        request = "\n".join(lines)
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
        """Returns a series of dicts from `response`.
        If `start` is specified, items prior to this will be discarded,
        and each dict will be grouped starting with this key.
        `extra_bools` allows custom keys to be booleaned"""
        groups = []
        for k, v in self.__pairs_from(response):
            if k == start:
                if groups:
                    yield dict(groups)
                # New group starts here
                groups = [(k, stronger(k, v, extra_bools))]
            else:
                if groups or not start:
                    groups.append((k, stronger(k, v, extra_bools)))
        if groups:
            yield dict(groups)

    def refresh_status(self):
        """ Updates the list of the Squeezebox players available and other
        server metadata."""
        print_d("Refreshing server and player statuses...")
        response = self.__a_request("serverstatus 0 99", raw=True)
        self.players = {}
        for data in self._groups(response, 'playerid',
                                 extra_bools=['power', 'connected']):
            self.players[data['playerid']] = SqueezeboxPlayerSettings(data)
        print_d("Found {total} player(s): {players}",
                total=len(self.players),
                players=[p['name'] for p in self.players.values()])
        if self._debug:
            print_d("Player(s): {players}", players=self.players.values())

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

    def play_artist(self, artist, player_id=None):
        """Adds then plays the albums of the specified artist"""
        commands = (["playlist clear"] +
                    ["playlist addalbum * %s *"
                     % urllib.quote(artist)] +
                    ["play 2"])
        pid = player_id or self.cur_player_id
        return self._request(["%s %s" % (pid, com) for com in commands])

    def play_album(self, album, player_id=None):
        """Adds then plays the specified album"""
        commands = (["playlist clear", "playlist shuffle 0"] +
                    ["playlist addalbum * * %s"
                     % urllib.quote(album)] +
                    ["play 2"])
        pid = player_id or self.cur_player_id
        return self._request(["%s %s" % (pid, com) for com in commands])

    def get_track_details(self, player_id=None):
        keys = ["genre", "artist", "current_title"]
        pid = player_id or self.cur_player_id
        responses = self._request(["%s %s ?" % (pid, s)
                                   for s in keys])
        return dict(zip(keys, responses))

    def search_for_album(self, term=None):
        resp = self.__a_request("search 0 10 term:%s" % term, raw=True)
        albums = [v for k, v in self.__pairs_from(resp)
                  if k == 'album' and re.search(term, v, re.IGNORECASE)]
        return albums

    def search_for_artist(self, term=None):
        resp = self.__a_request("search 0 10 term:%s" % term, raw=True)
        artist = [v for k, v in self.__pairs_from(resp)
                  if k == 'contributor' and v.lower() == term.lower()]
        return artist

    @property
    def genres(self):
        if not self.__genres:
            resp = self.__a_request("genres 0 255", raw=True)
            self.__genres = [v for k, v in self.__pairs_from(resp)
                             if k == 'genre']
            print_d(with_example("Loaded {num} LMS genres", self.__genres))
        return self.__genres

    @property
    def playlists(self):
        if not self.__playlists:
            resp = self.__a_request("playlists 0 255", raw=True)
            self.__playlists = [v for k, v in self.__pairs_from(resp)
                                if k == 'playlist']
            print_d(with_example("Loaded {num} LMS playlists",
                                 self.__playlists))
        return self.__playlists

    @property
    def favorites(self):
        if not self.__favorites:
            resp = self.__a_request("favorites items 0 255 want_url:1",
                                    raw=True)
            self.__favorites = {d['name']: d
                                for d in self._groups(resp, 'name')
                                if d['isaudio']}
            print_d(with_example("Loaded {num} LMS faves", self.__favorites))
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
        return "Squeezebox server over {transport}".format(**self.__dict__)

    def __del__(self):
        print_d("Goodbye from {what}", what=self)
        del self.transport
