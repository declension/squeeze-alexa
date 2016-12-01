# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation


from __future__ import print_function

from fuzzywuzzy import process

from squeezealexa.alexa.handlers import AlexaHandler
from squeezealexa.alexa.intents import Audio, General, Custom, Power, \
    CustomAudio
from squeezealexa.alexa.response import audio_response, speech_response
from squeezealexa.alexa.utterances import Utterances
from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server

MIN_CONFIDENCE = 75

print_d = print_w = print


class SqueezeAlexa(AlexaHandler):
    _server = None
    """The server instance
    :type Server"""

    def on_session_started(self, request, session):
        print_d("Starting new session %s for request %s" %
                (session['sessionId'], request['requestId']))

    def on_launch(self, launch_request, session):

        print_d("Entering interactive mode for sessionId=%s"
                % session['sessionId'])
        speech_output = "Squeezebox is online. Please try some commands."
        reprompt_text = "Try resume, pause, next, previous " \
                        "or ask Squeezebox to turn it up or down"
        return speech_response("Welcome", speech_output, reprompt_text,
                               end=False)

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
            print_d("Created %r" % cls._server)
        else:
            print_d("Reusing cached %r" % cls._server)
        return cls._server

    def on_intent(self, intent_request, session):

        intent = intent_request['intent']
        intent_name = intent['name']
        print_d("Received %s: %s" % (intent_name, intent))
        pid = self.player_id_from(intent)

        if intent_name == Audio.RESUME:
            self.get_server().resume(player_id=pid)
            return audio_response("Resumed")

        elif intent_name == Audio.PAUSE:
            self.get_server().pause(player_id=pid)
            return audio_response("Paused")

        elif intent_name == Audio.PREVIOUS:
            self.get_server().previous(player_id=pid)
            return speech_response("Previous", "Rewind! Selectah!")

        elif intent_name == Audio.NEXT:
            self.get_server().next(player_id=pid)
            return speech_response("Next", "Yep, pretty lame.")

        elif intent_name == Custom.CURRENT:
            details = self.get_server().get_track_details()
            title = details['current_title']
            artist = details['artist']
            desc = "Currently playing: \"%s\", by %s" % (title, artist)
            heading = "Now playing: \"%s\"" % title
            return speech_response(heading, desc)

        elif intent_name == Custom.INC_VOL:
            self.get_server().change_volume(+12.5, player_id=pid)
            return speech_response("Increase Volume", "Pumped it up.")

        elif intent_name == Custom.DEC_VOL:
            self.get_server().change_volume(-12.5, player_id=pid)
            return speech_response("Decrease Volume", "OK, it's quieter now.")

        elif intent_name == Custom.SELECT_PLAYER:
            srv = self.get_server()
            srv.refresh_status()

            # Do it again, yes, but not defaulting this time.
            pid = self.player_id_from(intent, defaulting=False)
            if pid:
                player = srv.players[pid]
                srv.cur_player_id = player
                return speech_response(
                    "Selected player %s" % player,
                    "Selected %s" % player.name,
                    store={"player_id": pid})
            else:
                speech = ("I only found these players: %s. "
                          "Could you try again?"
                          % ", ".join(srv.player_names))
                reprompt = ("You can select a player by saying "
                            "\"%s\" and then the player name."
                            % Utterances.SELECT_PLAYER)
                try:
                    title = ("No player called \"%s\""
                             % intent['slots']['Player']['value'])
                except KeyError:
                    title = "Didn't recognise a player name"
                return speech_response(title, speech, reprompt_text=reprompt,
                                       end=False)

        elif intent_name in [Audio.SHUFFLE_ON, CustomAudio.SHUFFLE_ON]:
            self.get_server().set_shuffle(True, player_id=pid)
            return audio_response("Shuffle on")

        elif intent_name in [Audio.SHUFFLE_OFF, CustomAudio.SHUFFLE_OFF]:
            self.get_server().set_shuffle(False, player_id=pid)
            return audio_response("Shuffle off")

        elif intent_name in [Audio.LOOP_ON, CustomAudio.LOOP_ON]:
            self.get_server().set_repeat(True, player_id=pid)
            return audio_response("Repeat on")

        elif intent_name in [Audio.LOOP_OFF, CustomAudio.LOOP_OFF]:
            self.get_server().set_repeat(False, player_id=pid)
            return audio_response("Repeat off")

        elif intent_name == Power.PLAYER_OFF:
            self.get_server().set_power(on=False, player_id=pid)
            return speech_response("Switched %s off" % pid)

        elif intent_name == Power.PLAYER_ON:
            player = self.player_id_from(intent)
            self.get_server().set_power(on=True, player_id=player.id)
            return speech_response("Switched %s on" % pid)

        elif intent_name == Power.ALL_OFF:
            self.get_server().set_all_power(on=False)
            return speech_response("Players all off", "Silence.")

        elif intent_name == Power.ALL_ON:
            self.get_server().set_all_power(on=True)
            return speech_response("Players all on", "All On.")

        elif intent_name == General.HELP:
            return self.on_launch(intent_request, session)

        elif intent_name in [General.CANCEL, General.STOP]:
            return self.on_session_ended(intent_request, session)

        else:
            return speech_response(
                "Confused",
                "Sorry, I don't know how to process \"%s\"" % intent_name)

    def player_id_from(self, intent, defaulting=True):
        srv = self.get_server()
        try:
            player_name = intent['slots']['Player']['value']
        except KeyError:
            pass
        else:
            by_name = {s.name: s for s in srv.players.values()}
            result = process.extractOne(player_name, by_name.keys())
            print_d("%s was the best guess for '%s' from %s"
                    % (result, player_name, by_name.keys()))
            if result and int(result[1]) >= MIN_CONFIDENCE:
                return by_name.get(result[0]).id
        return srv.cur_player_id if defaulting else None

    def on_session_ended(self, session_ended_request, session):
        print_d("on_session_ended requestId=%s, sessionId=%s" %
                (session_ended_request['requestId'], session['sessionId']))
        # add cleanup logic here
        speech_output = "Thank you for trying the Squeezebox Skill"
        return speech_response("Session Ended", speech_output, end=True)
