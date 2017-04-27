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
from squeezealexa.utils import print_w


class AlexaHandler(object):

    def __init__(self, app_id=None):
        self.app_id = app_id

    def on_session_ended(self, session_ended_request, session):
        """ Called when the user ends the session.
        Is not called when the skill returns should_end_session=true
        """

    def on_session_started(self, request, session):
        """Called when the session starts """

    def on_launch(self, launch_request, session):
        """Called when the user launches the skill
        without specifying what they want"""

    def on_intent(self, intent_request, session):
        """Called when the user specifies an intent for this skill"""

    def handle(self, event, context=None):
        """The main entry point for Alexa requests"""
        request = event['request']
        req_type = request['type']
        session = self._verified_app_session(event)

        if session and session['new']:
            self.on_session_started(request, session)

        if req_type == Request.LAUNCH:
            return self.on_launch(request, session)
        elif req_type == Request.INTENT:
            return self.on_intent(request, session)
        elif req_type == Request.SESSION_ENDED:
            return self.on_session_ended(request, session)
        elif req_type == Request.EXCEPTION:
            print_w("ERROR callback received (\"%s\"). Full event: %s"
                    % (request['error'].get('message', "?"), event))
        else:
            raise ValueError("Unknown request type %s" % req_type)

    def _verified_app_session(self, event):
        if 'session' not in event:
            # Probably an exception message
            return None
        session = event['session']
        app = session['application']
        if self.app_id and app['applicationId'] != self.app_id:
            raise ValueError("Invalid application (%s)" % app)
        return session


class IntentHandler(object):

    def __init__(self):
        self._handlers = {}

    def for_name(self, name):
        """Returns the handler for the given intent, or `None`"""
        return self._handlers.get(name, None)

    def handle(cls, name):
        """Registers a handler function for the given intent"""

        def _handler(func):
            cls._handlers[name] = func
            return func

        return _handler
