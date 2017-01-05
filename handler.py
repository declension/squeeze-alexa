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

from squeezealexa.alexa.requests import Request
from squeezealexa.main import SqueezeAlexa, APPLICATION_ID


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """

    request = event['request']
    req_type = request['type']
    if req_type.startswith('AudioPlayer'):
        print("Ignoring %s callback" % (request['type'],))
        return

    session = _verified_app_session(event)

    sqa = SqueezeAlexa()
    if session['new']:
        sqa.on_session_started(request, session)

    if req_type == Request.LAUNCH:
        return sqa.on_launch(request, session)
    elif req_type == Request.INTENT:
        return sqa.on_intent(request, session)
    elif req_type == Request.SESSION_ENDED:
        return sqa.on_session_ended(request, session)
    else:
        raise ValueError("Unknown request type %s" % req_type)


def _verified_app_session(event):
    if 'session' not in event:
        raise ValueError("Can't process event: %r" % (event,))
    session = event['session']
    if (APPLICATION_ID and
            session['application']['applicationId'] != APPLICATION_ID):
        raise ValueError("Invalid application (%s)" % session['application'])
    return session
