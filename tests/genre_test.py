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

from os.path import dirname
from unittest import TestCase
from os import path

from squeezealexa.main import SqueezeAlexa

ROOT = dirname(dirname(__file__))
GENRES = open(path.join(ROOT, 'metadata/slots/genres.txt')).read().splitlines()


class GenreTest(TestCase):

    def setUp(self):
        self.alexa = SqueezeAlexa(server=None)

    def get_results(self, *args):
        return self.alexa._genres_from_slots(args, GENRES)

    def test_difficult_ands(self):
        results = self.get_results(['R', 'B'])
        assert 'R and B' in results

    def test_dnb(self):
        results = self.get_results('Drum', 'Base')
        assert 'Drum n Bass' in results

    def test_complete_answer(self):
        results = self.get_results('blues', 'bluegrass')
        assert results == {'Blues', 'Bluegrass'}

    def test_complete_answer_overlapping_words(self):
        results = self.get_results('funk rock')
        assert results == {'Funk', 'Rock'}

    def test_hyphenation(self):
        results = self.get_results('hip-hop')
        assert results == {'Hip Hop'}

    def test_exact(self):
        results = self.get_results('dub')
        assert results == {'Dub'}
        results = self.get_results('House')
        assert results == {'House'}
