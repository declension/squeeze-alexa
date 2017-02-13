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

import sys
from os.path import dirname, realpath, join
from pprint import pprint
from unittest import TestCase

import time

from squeezealexa.squeezebox.server import Server

SOME_PID = "zz:zz:zz"
FAKE_ID = "ab:cd:ef:gh"
ROOT = dirname(dirname(__file__))
GENRES = open(join(ROOT, 'metadata/slots/genres.txt')).read().splitlines()

sys.path.append(realpath(dirname(dirname(__file__))))
from squeezealexa.main import SqueezeAlexa


def resp(text, pid=FAKE_ID):
    return "%s %s" % (pid, text)


class FakeSqueeze(Server):

    def __init__(self):
        self.lines = []
        self.cur_player_id = FAKE_ID
        self._genres = GENRES
        self._created_time = time.time()

    @property
    def genres(self):
        return self._genres

    def _request(self, lines, raw=False, wait=True):
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
        intent = {'slots': {'primaryGenre': {'value': 'Jungle band Blues'},
                            'secondaryGenre': {'value': 'House'}}}

        response = self.alexa.on_random_mix(intent, None)
        assert self.stub.lines[-1] == resp('randomplay tracks')
        content = response['response']['card']['content']
        assert content.startswith('Random mix of')
        assert 'Jungle' in content
        assert 'House' in content
        # 3 = reset genres, clear, play. 4 = 2 + 2
        assert len(self.stub.lines) <= 4 + 3



