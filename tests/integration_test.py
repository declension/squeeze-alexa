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

from os.path import dirname, join
from pprint import pprint
from unittest import TestCase

import time

from squeezealexa.squeezebox.server import Server
from squeezealexa.main import SqueezeAlexa

SOME_PID = "zz:zz:zz"
FAKE_ID = "ab:cd:ef:gh"
ROOT = dirname(dirname(__file__))
GENRES = open(join(ROOT, 'metadata/slots/genres.txt')).read().splitlines()
A_PLAYLIST = 'Moody Bluez'


def resp(text, pid=FAKE_ID):
    return "%s %s" % (pid, text)


class FakeSqueeze(Server):

    def __init__(self):
        self.lines = []
        self.players = {}
        self._debug = False
        self.cur_player_id = FAKE_ID
        self._genres = []
        self._playlists = []
        self._created_time = time.time()
        self.ssl_wrap = None

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
        intent = {'slots': {'Playlist': {'name': 'Playlist',
                                         'value': 'Moody Blues'}}}
        response = self.alexa.on_play_playlist(intent, FAKE_ID)
        speech = response['response']['outputSpeech']['text']
        assert "No Squeezebox playlists" in speech

    def test_on_playlist_play(self):
        self.stub._playlists = ['Black Friday', A_PLAYLIST, 'Happy Mondays']
        intent = {'slots': {'Playlist': {'name': 'Playlist',
                                         'value': 'Mood Blues'}}}

        response = self.alexa.on_play_playlist(intent, FAKE_ID)
        last_cmd = self.stub.lines[-1]
        assert last_cmd.startswith(resp('playlist resume %s'
                                   % A_PLAYLIST.replace(' ', '%20')))
        content = response['response']['card']['content']
        assert content.startswith('Playing "%s" playlist' % A_PLAYLIST)
        assert len(self.stub.lines) <= 4 + 3
