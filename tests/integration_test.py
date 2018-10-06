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

from pprint import pprint
from typing import Any, Dict
from unittest import TestCase

from squeezealexa.main import SqueezeAlexa
from squeezealexa.squeezebox.server import Server
from tests.transport.fake_transport import FakeTransport
from tests.utils import GENRES

MULTI_ARTIST_STATUS = """ tags%3AAlG player_name%3AStudy player_connected%3A1 
player_ip%3A192.168.1.40%3A50556 power%3A1 signalstrength%3A0 mode%3Aplay 
time%3A13.8465571918488 rate%3A1 duration%3A281.566 can_seek%3A1 
sync_master%3A40%3A16%3A7e%3Aad%3A87%3A07 sync_slaves%3A00%3A04%3A20%3A17%3A6f
%3Ad1%2C00%3A04%3A20%3A17%3Ade%3Aa0%2C00%3A04%3A20%3A17%3A5c%3A94 
mixer%20volume%3A86 playlist%20repeat%3A0 playlist%20shuffle%3A2 
playlist%20mode%3Aoff seq_no%3A0 playlist_cur_index%3A0 
playlist_timestamp%3A1538824028.72799 playlist_tracks%3A1 
digital_volume_control%3A1 playlist%20index%3A0 id%3A12919 
title%3AShut%20'Em%20Down artist%3APublic%20Enemy%2C%20Pete%20Rock 
album%3ASingles%20N'%20Remixes%201987-1992 
genres%3AHip-Hop""".replace('\n', '')

CLASSICAL_STATUS = """tags%3AAlG player_name%3AStudy player_connected%3A1 
player_ip%3A192.168.1.40%3A51878 power%3A1 signalstrength%3A0 mode%3Aplay 
time%3A19.720863161087 rate%3A1 duration%3A548 can_seek%3A1 
sync_master%3A40%3A16%3A7e%3Aad%3A87%3A07 
sync_slaves%3A00%3A04%3A20%3A17%3A6f%3Ad1%2C00%3A04%3A20%3A17%3Ade%3Aa0%2C00
%3A04%3A20%3A17%3A5c%3A94 mixer%20volume%3A86 playlist%20repeat%3A0 
playlist%20shuffle%3A2 playlist%20mode%3Aoff seq_no%3A0 
playlist_cur_index%3A0 playlist_timestamp%3A1538824933.95403 
playlist_tracks%3A27 digital_volume_control%3A1 playlist%20index%3A0 
id%3A10083 title%3AKyrie%20Eleison artist%3ANo%20Artist 
composer%3AJohann%20Sebastian%20Bach conductor%3ADiego%20Fasolis 
album%3AMass%20in%20B%20minor%20BWV%20232 genres%3AClassical
""".replace('\n', '')

SOME_PID = "zz:zz:zz"
FAKE_ID = "ab:cd:ef:gh"
A_PLAYLIST = 'Moody Bluez'


def resp(text: str, pid: str = FAKE_ID) -> str:
    return ' '.join([pid, text])


class FakeSqueeze(Server):

    def __init__(self):
        self.lines = []
        self.players = {}
        self._debug = False
        self.cur_player_id = FAKE_ID
        self._genres = []
        self._playlists = []
        self.transport = FakeTransport()

    @property
    def genres(self):
        return self._genres

    @property
    def playlists(self):
        return self._playlists

    def _request(self, lines, raw=False, wait=True):
        if self._debug:
            pprint(lines)
        self.lines += lines
        return lines


def one_slot_intent(slot: str, value: Any) -> Dict[str, Any]:
    return {'slots': {slot: {'name': slot,
                             'value': str(value),
                             'confirmationStatus': 'NONE'}}}


def speech_in(response):
    return response['response']['outputSpeech']['text']


class IntegrationTests(TestCase):

    def setUp(self):
        super(IntegrationTests, self).setUp()
        self.stub = FakeSqueeze()
        self.alexa = SqueezeAlexa(server=self.stub)

    def test_on_pause_resume(self):
        intent = {}
        self.alexa.on_pause(intent, None)
        self.alexa.on_resume(intent, None)
        assert self.stub.lines == [resp('pause 1'), resp('pause 0 1')]

    def test_on_pause_resume_player_id(self):
        intent = {}
        self.alexa.on_pause(intent, None, pid=SOME_PID)
        self.alexa.on_resume(intent, None, pid=SOME_PID)
        assert self.stub.lines == [resp('pause 1', pid=SOME_PID),
                                   resp('pause 0 1', pid=SOME_PID)]

    def test_on_random_mix_trickier(self):
        self.stub._genres = GENRES
        intent = {'slots': {'primaryGenre': {'value': 'Jungle band Blues'},
                            'secondaryGenre': {'value': 'House'}}}

        response = self.alexa.on_play_random_mix(intent, None)
        assert self.stub.lines[-1] == resp('play 2')
        content = response['response']['card']['content']
        assert content.startswith('Playing mix of')
        assert 'Jungle' in content
        assert 'House' in content
        # 3 = reset genres, clear, play. 4 = 2 + 2
        assert len(self.stub.lines) <= 4 + 3

    def test_on_playlist_play_without_playlists(self):
        intent = one_slot_intent('Playlist', 'Moody Blues')
        response = self.alexa.on_play_playlist(intent, FAKE_ID)
        speech = speech_in(response)
        assert "No Squeezebox playlists" in speech

    def test_on_playlist_play(self):
        self.stub._playlists = ['Black Friday', A_PLAYLIST, 'Happy Mondays']
        intent = one_slot_intent('Playlist', 'Mood Blues')

        response = self.alexa.on_play_playlist(intent, FAKE_ID)
        last_cmd = self.stub.lines[-1]
        assert last_cmd.startswith(resp('playlist resume %s'
                                   % A_PLAYLIST.replace(' ', '%20')))
        content = response['response']['card']['content']
        assert content.startswith('Playing "%s" playlist' % A_PLAYLIST)
        assert len(self.stub.lines) <= 4 + 3

    def test_set_invalid_volume(self):
        intent = one_slot_intent('Volume', 11)
        response = self.alexa.on_set_vol(intent, FAKE_ID)
        speech = speech_in(response)
        assert " between 0 and 10" in speech.lower()

    def test_set_invalid_percent_volume(self):
        intent = one_slot_intent('Volume', 999)
        response = self.alexa.on_set_vol_percent(intent, FAKE_ID)
        speech = speech_in(response)
        assert " between 0 and 100" in speech.lower()


class TestNowPlaying(TestCase):
    def test_commas_in_title(self):
        fake_output = FakeTransport().start()
        server = Server(transport=fake_output)
        alexa = SqueezeAlexa(server=server)
        resp = alexa.now_playing([], None)
        speech = speech_in(resp)
        assert "I Think, I Love" in speech
        assert "by Jamie Cullum" in speech

    def test_multiple_artists(self):
        fake_output = FakeTransport(fake_status=MULTI_ARTIST_STATUS).start()
        server = Server(transport=fake_output)
        alexa = SqueezeAlexa(server=server)
        resp = alexa.now_playing([], None)
        speech = speech_in(resp)
        assert '"Shut \'Em Down"' in speech
        assert "by Public Enemy and Pete Rock" in speech

    def test_classical(self):
        fake_output = FakeTransport(fake_status=CLASSICAL_STATUS).start()
        server = Server(transport=fake_output)
        alexa = SqueezeAlexa(server=server)
        resp = alexa.now_playing([], None)
        speech = speech_in(resp)
        assert '"Kyrie Eleison"' in speech
        assert "by Johann Sebastian Bach" in speech
