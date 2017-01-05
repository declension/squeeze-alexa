# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation


from __future__ import print_function

from fuzzywuzzy import process

from squeezealexa.alexa.handlers import AlexaHandler, IntentHandler
from squeezealexa.alexa.intents import Audio, General, Custom, Power, \
    CustomAudio, RandomMix
from squeezealexa.alexa.response import audio_response, speech_response
from squeezealexa.alexa.utterances import Utterances
from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server
from squeezealexa.ssl_wrap import SslSocketWrapper

MIN_CONFIDENCE = 75

print_d = print_w = print

handler = IntentHandler()


class SqueezeAlexa(AlexaHandler):
    _server = None
    """The server instance
    :type Server"""

    def __init__(self):
        super(SqueezeAlexa, self).__init__()

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
            sslw = SslSocketWrapper(hostname=SERVER_HOSTNAME, port=SERVER_PORT,
                                    ca_file=CA_FILE_PATH,
                                    cert_file=CERT_FILE_PATH,
                                    verify_hostname=VERIFY_SERVER_HOSTNAME)
            cls._server = Server(sslw,
                                 user=SERVER_USERNAME,
                                 password=SERVER_PASSWORD,
                                 cur_player_id=DEFAULT_PLAYER,
                                 debug=True)
            print_d("Created %r" % cls._server)
        else:
            print_d("Reusing cached %r" % cls._server)
        return cls._server

    def on_intent(self, intent_request, session):
        intent = intent_request['intent']
        intent_name = intent['name']
        print_d("Received %s: %s" % (intent_name, intent))
        pid = self.player_id_from(intent)

        intent_handler = handler.for_name(intent_name)
        if intent_handler:
            return intent_handler(self, intent, session, pid=pid)
        return speech_response(
            "Confused",
            "Sorry, I don't know how to process \"%s\"" % intent_name)

    @handler.handle(Audio.RESUME)
    def on_resume(self, intent, session, pid=None):
        self.get_server().resume(player_id=pid)
        return audio_response("Resumed")

    @handler.handle(Audio.PAUSE)
    def on_pause(self, intent, session, pid=None):
        self.get_server().pause(player_id=pid)
        return audio_response("Paused")

    @handler.handle(Audio.PREVIOUS)
    def on_previous(self, intent, session, pid=None):
        self.get_server().previous(player_id=pid)
        return speech_response("Previous", "Rewind!")

    @handler.handle(Audio.NEXT)
    def on_next(self, intent, session, pid=None):
        self.get_server().next(player_id=pid)
        return speech_response("Next", "Yep, pretty lame.")

    @handler.handle(Custom.CURRENT)
    def on_current(self, intent, session, pid=None):
        details = self.get_server().get_track_details()
        title = details['current_title']
        artist = details['artist']
        desc = "Currently playing: \"%s\", by %s" % (title, artist)
        heading = "Now playing: \"%s\"" % title
        return speech_response(heading, desc)

    @handler.handle(Custom.INC_VOL)
    def on_inc_vol(self, intent, session, pid=None):
        self.get_server().change_volume(+12.5, player_id=pid)
        return speech_response("Increase Volume", "Pumped it up.")

    @handler.handle(Custom.DEC_VOL)
    def on_dec_vol(self, intent, session, pid=None):
        self.get_server().change_volume(-12.5, player_id=pid)
        return speech_response("Decrease Volume", "OK, it's quieter now.")

    @handler.handle(Custom.SELECT_PLAYER)
    def on_select_player(self, intent, session, pid=None):
        srv = self.get_server()
        srv.refresh_status()

        # Do it again, yes, but not defaulting this time.
        pid = self.player_id_from(intent, defaulting=False)
        if pid:
            player = srv.players[pid]
            srv.cur_player_id = player.id
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

    @handler.handle(Audio.SHUFFLE_ON)
    @handler.handle(CustomAudio.SHUFFLE_ON)
    def on_shuffle_on(self, intent, session, pid=None):
        self.get_server().set_shuffle(True, player_id=pid)
        return audio_response("Shuffle on")

    @handler.handle(Audio.SHUFFLE_OFF)
    @handler.handle(CustomAudio.SHUFFLE_OFF)
    def on_shuffle_off(self, intent, session, pid=None):
        self.get_server().set_shuffle(False, player_id=pid)
        return audio_response("Shuffle off")

    @handler.handle(Audio.LOOP_ON)
    @handler.handle(CustomAudio.LOOP_ON)
    def on_loop_on(self, intent, session, pid=None):
        self.get_server().set_repeat(True, player_id=pid)
        return audio_response("Repeat on")

    @handler.handle(Audio.LOOP_OFF)
    @handler.handle(CustomAudio.LOOP_OFF)
    def on_loop_off(self, intent, session, pid=None):
        self.get_server().set_repeat(False, player_id=pid)
        return audio_response("Repeat off")

    @handler.handle(Power.PLAYER_OFF)
    def on_player_off(self, intent, session, pid=None):
        server = self.get_server()
        server.set_power(on=False, player_id=pid)
        player = server.players[pid]
        return speech_response("Switched %s off" % (player),
                               "%s is now off" % player.name)

    @handler.handle(Power.PLAYER_ON)
    def on_player_off(self, intent, session, pid=None):
        server = self.get_server()
        server.set_power(on=True, player_id=pid)
        player = server.players[pid]
        return speech_response("Switched %s on" % player,
                               "%s is now on" % player.name)

    @handler.handle(Power.ALL_OFF)
    def on_all_off(self, intent, session, pid=None):
        self.get_server().set_all_power(on=False)
        return speech_response("Players all off", "Silence.")

    @handler.handle(Power.ALL_ON)
    def on_all_on(self, intent, session, pid=None):
        self.get_server().set_all_power(on=True)
        return speech_response("Players all on", "All On.")

    @handler.handle(RandomMix.PLAY)
    def on_random_mix(self, intent, session, pid=None):
        server = self.get_server()
        try:
            genres = [v.get('value') for k, v in intent['slots'].items()
                      if k.endswith('Genre')]
            print_d("Extracted genres: %s" % genres)
        except KeyError:
            print_d("Couldn't process Random Intent: %s" % intent)
            pass
        else:
            def safe(g):
                if not g:
                    return
                res = process.extractOne(g, server.genres)
                if res and int(res[1]) >= MIN_CONFIDENCE:
                    return res[0]

            lms_genres = filter(None, map(safe, genres))
            if genres:
                server.play_random_mix(lms_genres)
                gs = " and ".join(lms_genres)
                return speech_response(
                    "Playing random mix of %s" % gs,
                    "Random mix of %s" % gs)
            else:
                return speech_response(
                    "Don't understand genre '%s'" % genres,
                    "Can't find genre %s" % genres)

    @handler.handle(General.HELP)
    def on_help(self, intent, session, pid=None):
        return self.on_launch(intent, session)

    @handler.handle(General.CANCEL)
    @handler.handle(General.STOP)
    def on_stop(self, intent, session, pid=None):
        return self.on_session_ended(intent, session)

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
