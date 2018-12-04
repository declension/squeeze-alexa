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

from typing import List, Dict, Union

from squeezealexa.transport.base import Error
from squeezealexa.utils import with_example, print_d, stronger, print_w, \
    first_of
from squeezealexa.i18n import _
import urllib.request as urllib


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


class ServerFactory:
    _MAX_CACHE_SECS = 600
    _INSTANCE = None
    _CREATION_TIME = None

    def __init__(self, transport_factory):
        self.transport_factory = transport_factory

    @classmethod
    def _too_old(cls):
        assert cls._INSTANCE
        age = time.time() - cls._CREATION_TIME
        print_d("Age of instance: {age:0.1f}s", age=age)
        return age > cls._MAX_CACHE_SECS

    def create(self, *args, **kwargs):
        instance = type(self)._INSTANCE
        if instance and self._too_old():
            print_d("Killing stale server instance.")
            instance.disconnect()
            instance = self._INSTANCE = None
            # Fall through

        if not instance or not instance.connected:
            print_d("Creating new server instance")
            transport = self.transport_factory.create()
            transport.start()
            inst = type(self)._INSTANCE = Server(transport, *args, **kwargs)
            type(self)._CREATION_TIME = time.time()
            return inst
        print_d("Reusing cached instance {object}", object=instance)
        return instance


class Server(object):
    """Encapsulates access to a Squeezebox player via a Squeezecenter server"""

    _TIMEOUT = 10
    _MAX_FAILURES = 3

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
            raise SqueezeboxException(_("Uh-oh. No connected players found."))
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
    def connected(self):
        return self.transport.is_connected

    def disconnect(self):
        print_d("Goodbye from {what!r}", what=self)
        self.transport.stop()

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
            print_d("Got mismatched response: {lines} vs {resp_lines}",
                    lines=lines, resp_lines=resp_lines)
            raise Error("Transport response problem: got %d lines, not %d"
                        % (len(resp_lines), len(lines)))
        return [resp_line[start_point(line):]
                for line, resp_line in zip(lines, resp_lines)]

    def __pairs_from(self, response):
        """Split and unescape a response"""

        def demunge(string):
            s = urllib.unquote(string)
            return tuple(s.split(':', 1))

        demunged = map(demunge, response.split(' '))
        return [d for d in demunged if len(d) == 2]

    def _groups(self, response: str, start_key: str =None, extra_bools=None):
        """Generator to yield a series of dicts from `response`.
        If `start` is specified, items prior to this will be discarded,
        and each dict will be grouped starting with this key.
        `extra_bools` allows custom keys to be booleaned"""
        groups = []
        started = False
        for k, v in self.__pairs_from(response):
            if k == start_key or " count" in k:
                if groups:
                    yield dict(groups)
                    groups = []
                started = True
                # New group starts here
                if " count" not in k:
                    groups = [(k, stronger(k, v, extra_bools))]
            else:
                if started or not start_key:
                    groups.append((k, stronger(k, v, extra_bools)))
        if groups:
            yield dict(groups)

    def refresh_status(self):
        """ Updates the list of the Squeezebox players available and other
        server metadata."""
        print_d("Refreshing server and player statuses.")
        response = self.__a_request("serverstatus 0 99", raw=True)
        self.players = {}
        for data in self._groups(response, 'playerid',
                                 extra_bools=['power', 'connected']):
            if data.get('connected', False):
                self.players[data['playerid']] = SqueezeboxPlayerSettings(data)
        print_d("Found {total} connected player(s): {players}",
                total=len(self.players),
                players=[p.get('name', _("Unknown player"))
                         for p in self.players.values()])
        if self._debug:
            print_d("Player(s): {players}", players=self.players.values())

    def player_request(self, line, player_id=None,
                       raw=False, wait=True) -> Union[str, None]:
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

    def get_track_details(self, player_id=None) -> Dict[str, List]:
        """Returns a dict of details"""
        pid = player_id or self.cur_player_id
        # We need to support servers with and without multi-valued tags...
        responses = self.player_request("status - 1 tags:aAlgG", pid, raw=True)
        print_d("Got track details: {details}", details=responses)
        items = next(self._groups(responses)).items()

        def values_for(tag: str, value: str) -> List[str]:
            return ([value] if tag in ('title', 'album')
                    else [v.strip() for v in value.split(',')])

        TAGS = {'title', 'genre', 'genres', 'album', 'trackartist', 'artist',
                'albumartist', 'composer'}
        details = {k: values_for(k, v)
                   for k, v in items
                   if v and k in TAGS}
        if 'genres' in details:
            details['genre'] = details['genres']
            del details['genres']
        print_d("Processed details: {d}", d=details)
        return details

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
        self.disconnect()


def people_from(details: Dict) -> Union[str, None]:
    genres = {g.lower() for g in details.get('genre', [])}
    tags = ['trackartist', 'artist', 'albumartist', 'composer']
    if genres.intersection({'classical', 'baroque', 'neoclassical'}):
        # Having it twice is fine
        tags = ['composer'] + tags
    return first_of(details, tags)
