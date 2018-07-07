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
from tests.utils import GENRES

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
        self.transport = None

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
