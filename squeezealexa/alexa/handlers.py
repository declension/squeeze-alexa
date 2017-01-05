# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation


class AlexaHandler(object):

    def on_session_ended(self, session_ended_request, session):
        """ Called when the user ends the session.
        Is not called when the skill returns should_end_session=true
        """
        pass

    def on_session_started(self, request, session):
        """Called when the session starts """
        pass

    def on_launch(self, launch_request, session):
        """Called when the user launches the skill
        without specifying what they want"""

    def on_intent(self, intent_request, session):
        """Called when the user specifies an intent for this skill"""
        pass


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
