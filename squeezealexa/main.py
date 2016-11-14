# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation


"""
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function

from squeezealexa.alexa.intents import Audio, General, Custom
from squeezealexa.alexa.response \
    import speechlet_fragment, build_response, build_audio_response
from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server

print_d = print_w = print


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


class SqueezeAlexa(AlexaHandler):
    _server = None
    """The server instance
    :type Server"""

    def on_session_started(self, request, session):
        print_d("Starting new session sessionId=%s for requestId=%s" %
                (session['sessionId'], request['requestId']))

    def on_launch(self, launch_request, session):

        print_d("Entering interactive mode for sessionId=%s"
                % session['sessionId'])
        return self.get_welcome_response()

    def get_welcome_response(self):
        """ If we wanted to initialize the session to have some attributes
        we could add those here
        """
        card_title = "Welcome"
        speech_output = "Squeezebox is online. Please try some commands."
        reprompt_text = "Try resume, pause, next, previous " \
                        "or ask Squeezebox to turn it up or down"
        return build_response(speechlet_fragment(
            card_title, speech_output, reprompt_text))

    @classmethod
    def get_server(cls):
        """
        :return a Server instance
        :rtype Server
        """
        if not cls._server:
            cls._server = Server(SERVER_HOSTNAME, SERVER_PORT,
                                 cur_player_id=DEFAULT_PLAYER,
                                 debug=True,
                                 ca_file=CA_FILE_PATH,
                                 cert_file=CERT_FILE_PATH)
        return cls._server

    def on_intent(self, intent_request, session):

        intent = intent_request['intent']
        intent_name = intent['name']
        print_d("Received %s: %s" % (intent_name, intent))

        if intent_name == Audio.RESUME:
            self.get_server().resume()
            return build_audio_response("Resumed")

        elif intent_name == Audio.PAUSE:
            self.get_server().pause()
            return build_audio_response("Paused")

        elif intent_name == Audio.PREVIOUS:
            self.get_server().previous()
            return build_response(
                speechlet_fragment("Previous", "Rewind! Selectah!"))

        elif intent_name == Audio.NEXT:
            self.get_server().next()
            return build_response(
                speechlet_fragment("Next", "Yep, pretty lame."))

        elif intent_name == Custom.INC_VOL:
            self.get_server().change_volume(+12.5)
            return build_response(
                speechlet_fragment("Increase Volume", "Pumped it up."))

        elif intent_name == Custom.DEC_VOL:
            self.get_server().change_volume(-12.5)
            return build_response(
                speechlet_fragment("Decrease Volume", "OK, it's quieter now."))

        elif intent_name == General.HELP:
            return self.get_welcome_response()

        elif intent_name in [General.CANCEL, General.STOP]:
            return self.on_session_ended(intent_request, session)

        else:
            return build_response(speechlet_fragment(
                "Confused",
                "Sorry, I don't know how to process \"%s\"" % intent_name))

    def on_session_ended(self, session_ended_request, session):
        print_d("on_session_ended requestId=%s, sessionId=%s" %
                (session_ended_request['requestId'], session['sessionId']))
        # add cleanup logic here
        speech_output = "Thank you for trying the Squeezebox Skill"
        return build_response(speechlet_fragment(
            "Session Ended", speech_output, should_end_session=True))
