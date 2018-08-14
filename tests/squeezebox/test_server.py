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

from pytest import raises

from squeezealexa.squeezebox.server import Server, SqueezeboxPlayerSettings, \
    SqueezeboxException, ServerFactory
from squeezealexa.transport.base import Transport
from squeezealexa.transport.factory import TransportFactory
from squeezealexa.utils import print_d
from tests.transport.fake_transport import FakeTransport, FAKE_LENGTH, \
    A_REAL_STATUS


class TestSqueezeboxPlayerSettings:
    def test_raises_if_no_playerid_found(self):
        with raises(SqueezeboxException) as e:
            SqueezeboxPlayerSettings({})
        assert "couldn't find a playerid" in str(e).lower()


class FixedTransportFactory(TransportFactory):

    def __init__(self, instance: Transport = None):
        super().__init__()
        self.instance = instance
        self.count = 0

    def create(self, mqtt_client=None):
        self.count += 1
        print_d("Creating instance #{count}", count=self.count)
        return self.instance


class NoRefreshServer(Server):
    """A normal server, that has no transport never returns any players"""

    def __init__(self, user=None, password=None, cur_player_id=None):
        super().__init__(FixedTransportFactory(FakeTransport()),
                         user, password, cur_player_id, False)

    def refresh_status(self):
        self.players = {}


class TestServerNoTransport:
    def test_no_players_raises(self):
        with raises(SqueezeboxException) as e:
            Server._INSTANCE = None
            NoRefreshServer()
        assert "no players" in str(e).lower()


class TestServerFactory(TestCase):
    def setUp(self):
        transport = FakeTransport().start()
        self.factory = ServerFactory(FixedTransportFactory(transport))

    def test_singleton(self):
        first = self.factory.create()
        second = self.factory.create()
        assert first is second

    def test_staleness_creates_new_instance(self):
        first = self.factory.create()
        ServerFactory._CREATION_TIME = (time.time() -
                                        ServerFactory._MAX_CACHE_SECS - 1)
        second = self.factory.create()
        assert first is not second


class TestServerWithTransport(TestCase):

    def setUp(self):
        self.transport = FakeTransport().start()
        self.server = Server(transport=self.transport)

    def test_debug(self):
        Server(self.transport, debug=True)

    def test_unknown_default_player(self):
        transport = FakeTransport(fake_id="foo").start()
        self.server = Server(transport=transport, cur_player_id="GONE")
        assert self.server.cur_player_id == "foo"

    def test_get_current(self):
        assert self.server.get_status()['genre']

    def test_status(self):
        assert self.server.get_milliseconds() == FAKE_LENGTH * 1000

    def test_str(self):
        assert 'localhost:0' in str(self.server)

    def test_login(self):
        self.server = Server(transport=self.transport,
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

    def test_groups_multiple(self):
        raw = """BLAH
        playerindex%3A0 playerid%3A00%3A04%3A20%3A17%3A6f%3Ad1
        uuid%3A968b401ba4791d3fadd152bbac2f1dab ip%3A192.168.1.35%3A23238
        name%3AUpstairs%20Music seq_no%3A0 model%3Areceiver
        modelname%3ASqueezebox%20Receiver power%3A0 isplaying%3A0
        displaytype%3Anone isplayer%3A1 canpoweroff%3A1 connected%3A1
        firmware%3A77
        playerindex%3A2 playerid%3A40%3A16%3A7e%3Aad%3A87%3A07 uuid%3A
        ip%3A192.168.1.37%3A54652 name%3AStudy seq_no%3A0 model%3Asqueezelite
        modelname%3ASqueezeLite power%3A0 isplaying%3A0
        displaytype%3Anone isplayer%3A1 canpoweroff%3A1 connected%3A1
        firmware%3Av1.8 sn%20player%20count%3A0 other%20player%20count%3A0
""".replace('\n', '')
        groups = self.server._groups(raw, 'playerid')
        players = list(groups)
        assert len(players) == 2
        first = players[0]
        assert first['playerid'] == "00:04:20:17:6f:d1"
        assert players[1]['name'] == "Study"
        for data in groups:
            assert 'playerid' in data

    def test_groups_dodgy(self):
        raw = "blah bar%3Abaz"
        groups = list(self.server._groups(raw, start="id"))
        assert not groups

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
