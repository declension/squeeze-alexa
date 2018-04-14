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

from traceback import format_exc

from squeezealexa import settings
from squeezealexa.alexa.response import speech_response
from squeezealexa.main import SqueezeAlexa
from squeezealexa.settings import APPLICATION_ID
from squeezealexa.utils import print_w

try:
    from squeezealexa.i18n import _
except ImportError:
    def _(s):
        return s


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    sqa = SqueezeAlexa(app_id=APPLICATION_ID)
    try:
        return sqa.handle(event, context)
    except Exception as e:
        if not settings.USE_SPOKEN_ERRORS:
            raise e
        # Work with AWS stack-trace log magic
        print_w(format_exc().replace('\n', '\r'))
        error = str(e.msg if hasattr(e, "msg") else e)
        return speech_response(title=_("All went wrong"),
                               text=_("Oh dear: {type}. {message}").format(
                                   type=type(e).__name__, message=error))
