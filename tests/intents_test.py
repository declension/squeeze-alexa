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

from squeezealexa.squeezebox.server import Server
from squeezealexa.ssl_wrap import SslSocketWrapper
from squeezealexa.main import handler, SqueezeAlexa


class FakeSsl(SslSocketWrapper):

    def __init__(self, fake_name='fake', fake_id='1234'):
        self.hostname = 'localhost'
        self.port = 0
        self.failures = 0
        self.is_connected = True
        self.player_name = fake_name
        self.player_id = fake_id

    def communicate(self, data, wait=True):
        #return "\n".join([s + " OK" for s in data.splitlines()]) + "\n"
        if data.startswith('serverstatus'):
            fake_status = (' player%20count:1 playerid:{pid} name:{name}\n'
                           .format(name=self.player_name, pid=self.player_id))
            return data.rstrip("\n") + fake_status
        return data.rstrip('\n') + ' OK\n'


class AllIntentHandlingTest(TestCase):
    """Makes sure all registered handlers are behaving at least vaguely well"""

    def test_all_handler(self):
        fake_output = FakeSsl()
        server = Server(ssl_wrap=fake_output)
        alexa = SqueezeAlexa(server)
        for name, func in handler._handlers.items():
            session = {'sessionId': None}
            intent = {'requestId': 'abcd', 'slots': {}}
            raw = func(alexa, intent, session, None)
            response = raw['response']
            assert 'directives' in response or 'outputSpeech' in response
            assert 'shouldEndSession' in response
