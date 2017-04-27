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

from squeezealexa.main import handler, SqueezeAlexa
from squeezealexa.squeezebox.server import Server
from squeezealexa.utils import print_d
from tests.fake_ssl import FakeSsl


class AllIntentHandlingTest(TestCase):
    """Makes sure all registered handlers are behaving at least vaguely well"""

    def test_all_handler(self):
        fake_output = FakeSsl()
        server = Server(ssl_wrap=fake_output)
        alexa = SqueezeAlexa(server=server)
        for name, func in handler._handlers.items():
            print_d(">>> Testing %s() <<<" % func.__name__)
            session = {'sessionId': None}
            intent = {'requestId': 'abcd', 'slots': {}}
            raw = func(alexa, intent, session, None)
            response = raw['response']
            assert 'directives' in response or 'outputSpeech' in response
            assert 'shouldEndSession' in response
