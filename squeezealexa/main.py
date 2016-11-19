# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation


from __future__ import print_function

from squeezealexa.alexa.handlers import AlexaHandler
from squeezealexa.alexa.intents import Audio, General, Custom, Power, \
    CustomAudio
from squeezealexa.alexa.response \
    import speechlet_fragment, build_response, build_audio_response
from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server

print_d = print_w = print


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
        speech_output = "Squeezebox is online. Please try some commands."
        reprompt_text = "Try resume, pause, next, previous " \
                        "or ask Squeezebox to turn it up or down"
        return build_response(speechlet_fragment(
            "Welcome", speech_output, reprompt_text))

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
        else:
            print_d("Reusing cached %r" % cls._server)
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

        elif intent_name == Custom.CURRENT:
            details = self.get_server().get_track_details()
            title = details['current_title']
            artist = details['artist']
            desc = "Currently playing: \"%s\", by %s" % (title, artist)
            heading = "Now playing: \"%s\"" % title
            return build_response(speechlet_fragment(heading, desc))

        elif intent_name == Custom.INC_VOL:
            self.get_server().change_volume(+12.5)
            return build_response(
                speechlet_fragment("Increase Volume", "Pumped it up."))

        elif intent_name == Custom.DEC_VOL:
            self.get_server().change_volume(-12.5)
            return build_response(
                speechlet_fragment("Decrease Volume", "OK, it's quieter now."))

        elif intent_name in [Audio.SHUFFLE_ON, CustomAudio.SHUFFLE_ON]:
            self.get_server().set_shuffle(True)
            return build_audio_response("Shuffle on")

        elif intent_name in [Audio.SHUFFLE_OFF, CustomAudio.SHUFFLE_OFF]:
            self.get_server().set_shuffle(False)
            return build_audio_response("Shuffle off")

        elif intent_name in [Audio.LOOP_ON, CustomAudio.LOOP_ON]:
            self.get_server().set_repeat(True)
            return build_audio_response("Repeat on")

        elif intent_name in [Audio.LOOP_OFF, CustomAudio.LOOP_OFF]:
            self.get_server().set_repeat(False)
            return build_audio_response("Repeat off")

        elif intent_name == Power.ALL_OFF:
            self.get_server().set_power(False)
            return build_response(
                speechlet_fragment("Players all off", "Silence."))

        elif intent_name == Power.ALL_ON:
            self.get_server().set_power(True)
            return build_response(
                speechlet_fragment("Players all on", "Ready."))

        elif intent_name == General.HELP:
            return self.on_launch(intent_request, session)

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
