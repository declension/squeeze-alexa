# -*- coding: utf-8 -*-
#
#   Copyright 2018 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

from unittest.mock import MagicMock

import pytest

from squeezealexa.main import SqueezeAlexa
from squeezealexa.squeezebox.server import Server
from tests.integration_test import speech_in


@pytest.fixture(scope="module")
def mock_server():
    return MagicMock(Server)


@pytest.fixture(scope="module")
def alexa(mock_server):
    return SqueezeAlexa(server=mock_server)


class TestWithStubbedServer:

    def test_no_artist(self, mock_server, alexa):
        details = {"title": ["BBC Radio 4"]}
        mock_server.get_track_details = MagicMock(return_value=details)

        resp = alexa.now_playing([], None)
        speech = speech_in(resp)
        assert "Currently playing: \"BBC Radio 4\"" in speech

    def test_no_title(self, mock_server, alexa):
        details = {"artist": ["Someone"]}
        mock_server.get_track_details = MagicMock(return_value=details)
        resp = alexa.now_playing([], None)
        speech = speech_in(resp)
        assert "Nothing playing." == speech

    def test_multi_artist(self, mock_server, alexa):
        details = {"artist": ["Someone", "Someone Else"],
                   "title": ["Something"]}
        mock_server.get_track_details = MagicMock(return_value=details)
        resp = alexa.now_playing([], None)
        speech = speech_in(resp)
        assert "Currently playing: \"Something\", " \
               "by Someone and Someone Else." == speech
