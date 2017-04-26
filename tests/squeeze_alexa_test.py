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

import pytest

from squeezealexa.main import SqueezeAlexa


class SqueezeAlexaTest(TestCase):

    def test_ignores_audio_callbacks(self):
        sqa = SqueezeAlexa()
        sqa.handle({'request': {'requestId': '1234',
                                'type': 'AudioPlayerStarted'}}, {})

    def test_throws_for_unknown_type(self):
        sqa = SqueezeAlexa()
        with pytest.raises(ValueError) as excinfo:
            sqa.handle({'request': {'requestId': '1234',
                                    'type': 'CrazyThing'}}, {})
        assert 'unknown request type' in str(excinfo.value).lower()
