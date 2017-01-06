# -*- coding: utf-8 -*-
#
#   Copyright 2017 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

from __future__ import print_function

import urllib

from squeezealexa.settings import *
from squeezealexa.ssl_wrap import SslSocketWrapper

print_d = print_w = print


def _(s):
    return s


class SqueezeboxException(Exception):
    """Errors communicating with the Squeezebox"""


class SqueezeboxPlayerSettings(dict):
    """Encapsulates player settings"""

    def __init__(self, player_id=None):
        super(SqueezeboxPlayerSettings, self).__init__()
        if player_id:
            self['playerid'] = player_id

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
            return _("unidentified Squeezebox player: %r" % self)


class Server(object):
    """Encapsulates access to a Squeezebox player via a Squeezecenter server"""

    _TIMEOUT = 10
    _MAX_FAILURES = 3

    def __init__(self, ssl_wrap, user=None, password=None,
                 cur_player_id=None, debug=False):

        self.ssl_wrap = ssl_wrap
        self._debug = debug
        self.user = user
        self.password = password
        if user and password:
            self.log_in()
        print_d("Connected to %s!" % self)
        self.players = {}
        self.player_names = set()
        self.refresh_status()
        self.cur_player_id = cur_player_id or self.players.keys()[0]
        print_d("Default player is now %s " % self.cur_player_id[-5:])
        self.__genres = []

    def log_in(self):
        result = self.__a_request("login %s %s" % (self.user, self.password))
        if result != "%s ******" % self.user:
            raise SqueezeboxException(
                "Couldn't log in to squeezebox: response was '%s'" % result)

    def __a_request(self, line, raw=False, wait=True):
        reply = self._request([line], raw=raw, wait=wait)[0]
        if reply:
            return reply
        if self.user and self.password:
            print_d("Command failed. Trying to re-log in.")
            self.log_in()
            reply = self._request([line], raw=raw, wait=wait)[0]
            if reply:
                return reply
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
        if not self.ssl_wrap.is_connected:
            return []
        if not (lines and len(lines)):
            return []
        lines = map(str.rstrip, lines)

        first_word = lines[0].split()[0]
        if not (self.ssl_wrap.is_connected or first_word == 'login'):
            print_d("Can't do '%s' - not connected" % first_word, self)
            return

        if self._debug:
            print_d(">>>> \"%s\"" % "\n".join(lines))
        request = "\n".join(lines) + "\n"
        raw_response = self.ssl_wrap.communicate(request, wait=wait)
        if not wait:
            return []
        if not raw_response:
            raise SqueezeboxException(
                "No further response from %s. Login problem?" % self)
        raw_response = raw_response.rstrip("\n")
        response = raw_response if raw else self._unquote(raw_response)
        if self._debug:
            print_d("<<<< \"%s\"" % (response,))

        def start_point(text):
            if first_word == 'login':
                return 6
            delta = -1 if text.endswith('?') else 1
            return len(self._unquote(text) if raw else text) + delta

        if len(lines) != len(response.splitlines()):
            raise ValueError("%s != %s" % (lines, response))
        return [resp_line[start_point(line):]
                for line, resp_line in zip(lines, response.splitlines())]

    def __pairs_from(self, response):
        """Split and unescape a response"""
        def demunge(string):
            s = urllib.unquote(string)
            return tuple(s.split(':', 1))
        return filter(lambda t: len(t) == 2,
                      map(demunge, response.split(' ')))

    def refresh_status(self):
        """ Updates the list of the Squeezebox players available and other
        server metadata."""
        print_d("Refreshing server and player statuses...")
        pairs = self.__pairs_from(
            self.__a_request("serverstatus 0 99", raw=True))
        self.players = {}
        self.player_names.clear()
        player_id = None
        for key, val in pairs:
            if key == "playerid":
                player_id = val
                self.players[player_id] = SqueezeboxPlayerSettings(player_id)
            elif player_id:
                # Don't worry, playerid is *always* the first entry...
                self.players[player_id][key] = val
                if key == "name":
                    self.player_names.add(val)
        if self._debug:
            print_d("Found %d player(s): %s" %
                    (len(self.players), self.players))
        assert (int(dict(pairs)['player count']) == len(self.players))

    def player_request(self, line, player_id=None, raw=False, wait=True):
        """Makes a single request to a particular player (or the current)"""
        try:
            player_id = (player_id
                         or self.cur_player_id
                         or list(self.players.values())[0]["playerid"])
            return self._request(["%s %s" % (player_id, line)],
                                 raw=raw, wait=wait)[0]
        except IndexError:
            return None

    def play(self, player_id=None):
        """Plays the current song"""
        self.player_request("play", player_id=player_id)

    def play_random_mix(self, genre_list, player_id=None):
        gs = genre_list or []
        commands = ["randomplaygenreselectall 0"]
        commands += ["randomplaychoosegenre %s 1" % urllib.quote(g)
                     for g in gs]
        commands += ["playlist clear", "randomplay tracks"]
        pid = player_id or self.cur_player_id
        return self._request(["%s %s" % (pid, com) for com in commands])

    def is_stopped(self, player_id=None):
        """Returns whether the player is in any sort of non-playing mode"""
        response = self.player_request("mode ?", player_id=player_id)
        return "play" != response

    def get_current(self, player_id=None):
        # return self.player_request("current_title ?", player_id=player_id)
        return self.get_status(player_id)

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
            print_d("Loaded %d LMS genres" % len(self.__genres))
        return self.__genres

    def get_server_status(self, player_id=None):
        return self.player_request("serverstatus 0 99", player_id=player_id)

    def get_status(self, player_id=None):
        response = self.player_request("status - 2", player_id=player_id,
                                       raw=True)
        return self.__pairs_from(response)

    def next(self, player_id=None):
        self.player_request("playlist jump +1", player_id=player_id)

    def previous(self, player_id=None):
        self.player_request("playlist jump -1", player_id=player_id)

    def playlist_play(self, path):
        """Play song immediately"""
        self.player_request("playlist play %s" % (urllib.quote(path)))

    def playlist_clear(self):
        self.player_request("playlist clear", wait=False)

    def playlist_resume(self, name, resume, wipe=False):
        cmd = ("playlist resume %s noplay:%d wipePlaylist:%d"
               % (urllib.quote(name), int(not resume), int(wipe)))
        self.player_request(cmd, wait=False)

    def change_song(self, path):
        """Queue up a song"""
        self.player_request("playlist clear")
        self.player_request("playlist insert %s" % (urllib.quote(path)))

    def change_volume(self, delta, player_id=None):
        if not delta:
            return
        cmd = "mixer volume %s%.1f" % ('+' if delta > 0 else '', float(delta))
        self.player_request(cmd, player_id=player_id)

    def get_milliseconds(self):
        secs = self.player_request("time ?") or 0
        return float(secs) * 1000.0

    def pause(self, player_id=None):
        self.player_request("pause 1", player_id=player_id)

    def resume(self, player_id=None, fade_in_secs=1):
        self.player_request("pause 0 %d" % fade_in_secs, player_id=player_id)

    def stop(self, player_id=None):
        self.player_request("stop", player_id=player_id)

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
        return "Squeezebox server at %s" % self.ssl_wrap


if __name__ == '__main__':
    sslw = SslSocketWrapper(hostname=SERVER_HOSTNAME, port=SERVER_PORT,
                            ca_file=CA_FILE_PATH, cert_file=CERT_FILE_PATH,
                            verify_hostname=VERIFY_SERVER_HOSTNAME)
    server = Server(debug=True,
                    ssl_wrap=sslw,
                    cur_player_id=DEFAULT_PLAYER,
                    user=SERVER_USERNAME,
                    password=SERVER_PASSWORD)
    print(server.get_current())
    # print(server.get_status())
    print(server.genres)
    print(" >> ".join(server.get_track_details().values()))
    print(server.players[server.cur_player_id].id)
    server.play_random_mix(["Rock Ballad", "Latin", "Blues"])
