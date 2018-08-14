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

from unittest import TestCase

import os

import json

from squeezealexa.alexa.intents import Audio, Power
from squeezealexa.main import handler, SqueezeAlexa
from squeezealexa.squeezebox.server import Server
from squeezealexa.utils import print_d
from tests.transport.fake_transport import FakeTransport
from tests.utils import ROOT

INTENTS_V0_PATH = os.path.join(ROOT,
                               'metadata/intents/v0/intents.json')

INTENTS_V1_EN_GB_PATH = os.path.join(ROOT,
                                     'metadata/intents/v1/locale'
                                     '/en_GB/intents.json')

INTENTS_V1_EN_US_PATH = os.path.join(ROOT,
                                     'metadata/intents/v1/locale'
                                     '/en_US/intents.json')


def intents_from(j):
    lang_model = j["interactionModel"]["languageModel"]
    return {i["name"]: i for i in lang_model["intents"]}


def enum_values_from(cls):
    for k, v in cls.__dict__.items():
        if not k.startswith("_"):
            yield v

class AllIntentHandlingTest(TestCase):
    """Makes sure all registered handlers are behaving at least vaguely well"""

    def test_all_handler(self):
        fake_output = FakeTransport().start()
        server = Server(transport=fake_output)
        alexa = SqueezeAlexa(server=server)
        for name, func in handler._handlers.items():
            print_d(">>> Testing function() <<<", function=func.__name__)
            session = {'sessionId': None}
            intent = {'requestId': 'abcd', 'slots': {}}
            raw = func(alexa, intent, session, None)
            response = raw['response']
            assert 'directives' in response or 'outputSpeech' in response
            assert 'shouldEndSession' in response

    def test_intents_v0_json(self):
        with open(INTENTS_V0_PATH) as f:
            j = json.load(f)
            assert j["intents"]

    def test_intents_v1_en_gb_json(self):
        with open(INTENTS_V1_EN_GB_PATH) as f:
            j = json.load(f)
            intents = intents_from(j)
            assert intents, "No intents found"
            for i in enum_values_from(Power):
                assert intents[i]
            for i in enum_values_from(Audio):
                assert intents[i]

    def test_intents_v1_en_us_json(self):
        with open(INTENTS_V1_EN_US_PATH) as f:
            j = json.load(f)
            intents = intents_from(j)
            for i in enum_values_from(Power):
                assert intents[i]
            for i in enum_values_from(Audio):
                assert intents[i]
