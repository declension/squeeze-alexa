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
from unittest import TestCase

from squeezealexa.squeezebox.server import Server, SqueezeboxPlayerSettings
from tests.transport.fake_transport import *


def test_settings():
    sps = SqueezeboxPlayerSettings({})
    assert "Unidentified Squeezebox player" in str(sps)


class TestServer(TestCase):

    def setUp(self):
        self.transport = FakeTransport()
        self.server = Server(transport=self.transport)

    def test_singleton(self):
        second = Server(transport=self.transport)
        assert second is self.server

    def test_staleness_creates_new_instance(self):
        Server._CREATION_TIME = time.time() - Server._MAX_CACHE_SECS - 1
        second = Server(transport=self.transport)
        assert second is not self.server

    def test_debug(self):
        Server(self.transport, debug=True)

    def test_get_current(self):
        assert self.server.get_status()['genre']

    def test_status(self):
        assert self.server.get_milliseconds() == FAKE_LENGTH * 1000

    def test_str(self):
        assert 'localhost:0' in str(self.server)

    def test_login(self):
        self.server = Server(transport=FakeTransport(),
                             user='admin', password='pass')
        assert self.server.user == 'admin'

    def test_groups(self):
        raw = """"something%3Afoobar playerid%3Aecho6fd1 uuid%3A
            ip%3A127.0.0.1%3A39365
            name%3ALavf%20from%20echo6fd1 seq_no%3A0 model%3Ahttp power%3A1
            isplaying%3A0 canpoweroff%3A0 connected%3A0 isplayer%3A1
            sn%20player%20count%3A0
            other%20player%20count%3A0""".replace('\n', '')
        groups = self.server._groups(raw, 'playerid', ['connected'])
        expected = {'playerid': 'echo6fd1', 'uuid': None,
                    'ip': '127.0.0.1:39365', 'name': 'Lavf from echo6fd1',
                    'seq_no': 0, 'model': 'http', 'power': True,
                    'isplaying': False, 'canpoweroff': False,
                    'connected': False, 'isplayer': True,
                    'sn player count': 0, 'other player count': 0}
        assert next(groups) == expected

    def test_groups_status(self):
        data = next(self.server._groups(A_REAL_STATUS))
        assert data['player_name'] == 'Study'
        assert data['playlist_cur_index'] == 20
        assert data['artist'] == 'Jamie Cullum'
        assert isinstance(data['can_seek'], bool)

    def test_faves(self):
        assert len(self.server.favorites) == 2

    def test_playlists(self):
        assert len(self.server.playlists) == 0

    def test_genres(self):
        assert len(self.server.genres) == 0

    def test_change_volume(self):
        self.server.change_volume(3)
        assert "mixer volume +3" in self.transport.all_input

    def test_change_volume_zero(self):
        self.server.change_volume(0)
        assert "mixer volume" not in self.transport.all_input
