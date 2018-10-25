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

from traceback import format_exc

from squeezealexa.alexa.response import speech_response
from squeezealexa.main import SqueezeAlexa
from squeezealexa.settings import SKILL_SETTINGS, LMS_SETTINGS
from squeezealexa.squeezebox.server import ServerFactory
from squeezealexa.transport.factory import TransportFactory

try:
    from squeezealexa.i18n import _
except ImportError:
    def _(s):
        return s

ERROR_SPEECH = _("<speak><say-as interpret-as='interjection'>d'oh</say-as>: "
                 "{type} - {message}.</speak>")

factory = ServerFactory(TransportFactory())


def get_server():
    return factory.create(user=LMS_SETTINGS.username,
                          password=LMS_SETTINGS.password,
                          cur_player_id=LMS_SETTINGS.default_player,
                          debug=LMS_SETTINGS.debug)


def lambda_handler(event, context, server=None):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    try:
        sqa = SqueezeAlexa(server=server or get_server(),
                           app_id=SKILL_SETTINGS.application_id)
        return sqa.handle(event, context)
    except Exception as e:
        if not SKILL_SETTINGS.use_spoken_errors:
            raise e
        # Work with AWS stack-trace log magic
        print(format_exc().replace('\n', '\r'))
        error = str(e.msg if hasattr(e, "msg") else e)
        speech = ERROR_SPEECH.format(type=type(e).__name__, message=error)
        return speech_response(title=_("All went wrong"), speech=speech,
                               text=error, use_ssml="SSML")
