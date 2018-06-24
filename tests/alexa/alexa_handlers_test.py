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

import traceback
import uuid
from collections import defaultdict
from unittest import TestCase

import pytest

from squeezealexa.alexa.handlers import AlexaHandler
from squeezealexa.alexa.requests import Request
from squeezealexa.main import SqueezeAlexa, handler
from squeezealexa.squeezebox.server import Server
from tests.intents_test import FakeTransport

SOME_SESSION = {'new': False,
                'sessionId': uuid.uuid4(),
                'application': 'my-app-id'}

NO_SESSION = {'new': True,
              'sessionId': uuid.uuid4(),
              'application': 'abc-123'}


class SpyAlexaHandler(AlexaHandler):
    """Spy on AlexaHandler base class"""

    def __init__(self):
        super(SpyAlexaHandler, self).__init__()
        self.called = defaultdict(int)
        self.delegate = AlexaHandler()

    def on_session_ended(self, session_ended_request, session):
        return self.__record('on_session_ended')

    def on_session_started(self, request, session):
        return self.__record('on_session_started')

    def on_intent(self, intent_request, session):
        return self.__record('on_intent')

    def on_launch(self, launch_request, session):
        return self.__record('on_launch')

    def __record(self, name, *args, **kwargs):
        call = traceback.extract_stack(limit=5)[3]
        # 4-tuple (filename, line number, function name, text)
        self.called[call[2]] += 1
        return getattr(self.delegate, name)(args, kwargs)


class AlexaHandlerTest(TestCase):

    def test_throws_for_unknown_type(self):
        ah = AlexaHandler()
        with pytest.raises(ValueError) as excinfo:
            ah.handle(self.request_of('InvalidType'))
        assert 'unknown request type' in str(excinfo.value).lower()

    def test_launch(self):
        tah = SpyAlexaHandler()
        tah.handle(self.request_of(Request.LAUNCH))
        assert tah.called['on_launch'], tah.called

    def test_end(self):
        tah = SpyAlexaHandler()
        tah.handle(self.request_of(Request.SESSION_ENDED))
        assert tah.called['on_session_ended'], tah.called

    def request_of(self, type):
        return {'request': {'requestId': '1234',
                            'type': type}}


class SqueezeAlexaTest(TestCase):

    def test_ignores_audio_callbacks(self):
        sqa = SqueezeAlexa(server=None)
        sqa.handle({'request': {'requestId': '1234',
                                'type': 'AudioPlayerStarted'}})

    def test_handling_all_intents(self):
        fake_output = FakeTransport()
        server = Server(transport=fake_output)
        alexa = SqueezeAlexa(server=server)
        for name, func in handler._handlers.items():
            intent = {'name': name,
                      'slots': {'Player': {'name': 'Player', 'value': 'fake'},
                                'Volume': {'name': 'Volume', 'value': '5'}}}
            output = alexa.handle(self.request_for(intent, SOME_SESSION))
            self.validate_response(name, output)

    def test_handling_all_intents_without_session_or_slots(self):
        alexa = SqueezeAlexa(server=(Server(transport=(FakeTransport()))))
        for name, func in handler._handlers.items():
            request = self.request_for({'name': name, 'slots': {}}, NO_SESSION)
            output = alexa.handle(request, None)
            self.validate_response(name, output)

    def validate_response(self, name, output):
        response = output['response']
        assert 'directives' in response or 'outputSpeech' in response, \
            "%s handling failed (%s)" % (name, output)

    def request_for(self, intent, session):
        return {'request': {'requestId': uuid.uuid4(),
                            'type': Request.INTENT,
                            'intent': intent},
                'session': session}
