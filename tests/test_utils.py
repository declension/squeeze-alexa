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

from unittest import TestCase

from squeezealexa.utils import english_join

LOTS = ['foo', 'bar', 'baz', 'quux']


class TestEnglish_join(TestCase):
    def test_basics(self):
        assert english_join([]) == ''
        assert english_join(['foo']) == 'foo'
        assert english_join(['foo', 'bar']) == 'foo and bar'
        assert english_join(LOTS[:-1]) == 'foo, bar and baz'
        assert english_join(LOTS) == 'foo, bar, baz and quux'

    def test_alternate_join_works(self):
        assert english_join(['foo', 'bar'], 'or') == 'foo or bar'

    def test_tuples_ok(self):
        assert english_join(('foo', 'bar'), 'or') == 'foo or bar'

    def test_skips_falsey(self):
        assert english_join(['foo', None, 'bar', '']) == 'foo and bar'
