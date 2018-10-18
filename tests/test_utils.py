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
from time import sleep
from unittest import TestCase

from pytest import raises

from squeezealexa import Settings
from squeezealexa.utils import human_join, sanitise_text, with_example, \
    stronger, print_d, print_w, wait_for

LOTS = ['foo', 'bar', 'baz', 'quux']


class TestEnglishJoin(TestCase):
    def test_basics(self):
        assert human_join([]) == ''
        assert human_join(['foo']) == 'foo'
        assert human_join(['foo', 'bar']) == 'foo and bar'
        assert human_join(LOTS[:-1]) == 'foo, bar and baz'
        assert human_join(LOTS) == 'foo, bar, baz and quux'

    def test_alternate_join_works(self):
        assert human_join(['foo', 'bar'], 'or') == 'foo or bar'

    def test_tuples_ok(self):
        assert human_join(('foo', 'bar'), 'or') == 'foo or bar'

    def test_skips_falsey(self):
        assert human_join(['foo', None, 'bar', '']) == 'foo and bar'

    def test_nothing(self):
        assert human_join(None) == ''


class TestSanitise(TestCase):
    def test_nothing(self):
        assert sanitise_text("") == ""

    def test_ands(self):
        assert sanitise_text('Drum & Bass') == 'Drum N Bass'
        assert sanitise_text('Drum&Bass') == 'Drum N Bass'
        assert sanitise_text('R&B') == 'R N B'
        assert sanitise_text('Jazz+Funk') == 'Jazz N Funk'

    def test_punctuation(self):
        assert sanitise_text('Alt. Rock') == 'Alt Rock'
        assert sanitise_text('Alt.Rock') == 'Alt Rock'
        assert sanitise_text('Trip-hop') == 'Trip hop'
        assert sanitise_text('Pop/Funk') == 'Pop Funk'

    def test_apostrophes(self):
        assert sanitise_text("10's pop") == '10s pop'

    def test_playlists(self):
        assert sanitise_text("My bad-a$$ playlist") == 'My bad ass playlist'


class TestWithExample(TestCase):
    def test_with_example_zero(self):
        assert with_example("{num} words", []) == "0 words"

    def test_with_example(self):
        output = with_example("{num} words", ['one', 'two'])
        assert output.startswith('2 words (e.g. "')

    def test_with_example_dict(self):
        assert with_example("{num} words", {1: 'one'}) == '1 words ("1")'

    def test_missing_num_raises(self):
        with raises(ValueError):
            with_example("Nothing {there}", [2])


class TestStrong(TestCase):
    def test_full(self):
        for (k, v), exp in [(('canpoweroff', '1'), True),
                            (('hasitems', '0'), False),
                            (('duration', '0.0'), 0.0),
                            (('foo', 'bar'), 'bar')]:
            assert stronger(k, v) == exp


class TestLogging(TestCase):
    def test_print_d(self):
        actual = print_d("{foo} - {num:.1f}", foo="bar", num=3.1415)
        assert actual == "bar - 3.1"

    def test_print_d_rejects_positional(self):
        with raises(ValueError):
            print_d("This is not cool: {}", "bar")

    def test_print_w(self):
        assert "Exception" in print_w("{ex!r}", ex=Exception("bar"))


class FakeSettings(Settings):
    foo = "bar"
    _private = 1234


class TestSettings:
    def test_str(self):
        s = FakeSettings()
        assert "_private" not in str(s)
        assert str(s) == "{'foo': 'bar'}"

    def test_configured(self):
        assert FakeSettings().configured
        assert Settings().configured


class TestWaitFor:

    def test_timeout_raises_nicely(self):
        context = FakeSettings()
        with raises(Exception) as e:
            wait_for(lambda x: sleep(1.1), 1, "Doing things", context)
        assert "Failed \"Doing things\"" in str(e)
        assert str(context) in str(e)
        assert "after 1.20s" in str(e)
