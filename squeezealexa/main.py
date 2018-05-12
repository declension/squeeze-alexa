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


from __future__ import print_function

import random
import time
from fuzzywuzzy import process

from squeezealexa.i18n import _
from squeezealexa.alexa.handlers import AlexaHandler, IntentHandler
from squeezealexa.alexa.intents import *
from squeezealexa.alexa.response import audio_response, speech_response, \
    _build_response
from squeezealexa.alexa.utterances import Utterances
from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server, print_d
from squeezealexa.transport.ssl_wrap import SslSocketTransport
from squeezealexa.utils import english_join, sanitise_text


class MinConfidences(object):
    PLAYER = 85
    GENRE = 85
    MULTI_GENRE = 90
    PLAYLIST = 60
    SINGLE_GENRE = 98


MAX_GUESSES_PER_SLOT = 2
AUDIO_TIMEOUT_SECS = 60 * 15

handler = IntentHandler()


class SqueezeAlexa(AlexaHandler):
    _audio_touched = 0
    _server = None
    """The server instance
    :type Server"""

    def __init__(self, server=None, app_id=None):
        super(SqueezeAlexa, self).__init__(app_id)
        if server:
            print_d("Overriding server for testing with {}", server)
            SqueezeAlexa._server = server

    def handle(self, event, context=None):
        request = event['request']
        req_type = request['type']
        if req_type.startswith('AudioPlayer'):
            print_d("Ignoring {} callback {}",
                    request['type'], request['requestId'])
            self.touch_audio()
            return _build_response({})
        return super(SqueezeAlexa, self).handle(event, context)

    def on_session_started(self, request, session):
        print_d("Starting new session {} for request {}",
                session['sessionId'], request['requestId'])

    def on_launch(self, launch_request, session):

        print_d("Entering interactive mode for sessionId={}",
                session['sessionId'])
        speech_output = _("Squeezebox is online. Please try some commands.")
        reprompt_text = _("Try resume, pause, next, previous, play some jazz, "
                          "or ask Squeezebox to turn it up or down")
        return speech_response("Welcome", speech_output, reprompt_text,
                               end=False)

    @classmethod
    def get_server(cls):
        """
        :return a Server instance
        :rtype Server
        """
        if not cls._server or cls._server.is_stale():
            sslw = SslSocketTransport(hostname=SERVER_HOSTNAME,
                                      port=SERVER_SSL_PORT,
                                      ca_file=CA_FILE_PATH,
                                      cert_file=CERT_FILE_PATH,
                                      verify_hostname=VERIFY_SERVER_HOSTNAME)
            cls._server = Server(sslw,
                                 user=SERVER_USERNAME,
                                 password=SERVER_PASSWORD,
                                 cur_player_id=DEFAULT_PLAYER,
                                 debug=DEBUG_LMS)
            print_d("Created {!r}", cls._server)
        else:
            print_d("Reusing cached {!r}", cls._server)
        return cls._server

    def on_intent(self, intent_request, session):
        intent = intent_request['intent']
        intent_name = intent['name']
        pid = self.player_id_from(intent)
        print_d("Received {intent_name}: {intent} (for player {pid})",
                **locals())

        intent_handler = handler.for_name(intent_name)
        if intent_handler:
            return intent_handler(self, intent, session, pid=pid)
        return self.smart_response(
            speech=_("Sorry, I don't know how to process a \"{intent}\"")
                   .format(intent=intent_name),
            text=_("Unknown intent: '{intent}'").format(intent=intent_name))

    @handler.handle(Audio.RESUME)
    def on_resume(self, intent, session, pid=None):
        self.get_server().resume(player_id=pid)
        return audio_response()

    @handler.handle(Audio.PAUSE)
    def on_pause(self, intent, session, pid=None):
        self.get_server().pause(player_id=pid)
        return audio_response()

    @handler.handle(Audio.PREVIOUS)
    def on_previous(self, intent, session, pid=None):
        self.get_server().previous(player_id=pid)
        return self.smart_response(speech=_("Rewind!"))

    @handler.handle(Audio.NEXT)
    def on_next(self, intent, session, pid=None):
        self.get_server().next(player_id=pid)
        return self.smart_response(speech=_("Yep, pretty lame."))

    @handler.handle(Custom.CURRENT)
    def on_current(self, intent, session, pid=None):
        details = self.get_server().get_track_details(player_id=pid)
        title = details['current_title']
        artist = details['artist']
        if title:
            desc = _("Currently playing: \"{}\"").format(title)
            if artist:
                desc += (", by {}".format(artist))
            heading = _("Now playing: \"{}\"").format(title)
        else:
            desc = _("Nothing playing.")
            heading = None
        return self.smart_response(text=heading, speech=desc)

    @handler.handle(Custom.SET_VOL)
    def on_set_vol(self, intent, session, pid=None):
        try:
            vol = float(intent['slots']['Volume']['value'])
            print_d("Extracted volume slot: {:1f}", vol)
        except KeyError:
            print_d("Couldn't process volume from: {!s}", intent)
            desc = _("Select a volume value between 0 and 10")
            heading = _("Invalid volume value")
            return self.smart_response(text=heading, speech=desc)
        if (vol > 10) or (vol < 0):
            desc = _("Select a volume value between 0 and 10")
            heading = _("Volume value out of range: {volume}").format(vol)
            return self.smart_response(text=heading,
                                       speech=desc)
        self.get_server().set_volume(vol * 10, pid)
        desc = "OK"
        vol_out = vol if (vol != int(vol)) else int(vol)
        heading = _("Set volume to {}").format(vol_out)
        return self.smart_response(text=heading,
                                   speech=desc)

    @handler.handle(Custom.SET_VOL_PERCENT)
    def on_set_vol_percent(self, intent, session, pid=None):
        try:
            vol = int(float(intent['slots']['Volume']['value']))
            print_d("Extracted volume slot: %d".format(vol))
        except KeyError:
            print_d("Couldn't process volume from: {}", intent)
            desc = _("Select a volume value between 0 and 100 percent")
            heading = _("Invalid volume value")
            return self.smart_response(text=heading, speech=desc)
        if (vol > 100) or (vol < 0):
            desc = _("Select a volume value between 0 and 100 percent")
            heading = _("Volume value out of range: %d percent").format(vol)
            return self.smart_response(text=heading, speech=desc)
        self.get_server().set_volume(vol, pid)
        desc = _("OK")
        heading = _("Set Volume to %d percent").format(vol)
        return self.smart_response(text=heading, speech=desc)

    @handler.handle(Custom.INC_VOL)
    def on_inc_vol(self, intent, session, pid=None):
        self.get_server().change_volume(+12.5, player_id=pid)
        return self.smart_response(text=_("Increase Volume"),
                                   speech=_("Pumped it up."))

    @handler.handle(Custom.DEC_VOL)
    def on_dec_vol(self, intent, session, pid=None):
        self.get_server().change_volume(-12.5, player_id=pid)
        return self.smart_response(text=_("Decrease Volume"),
                                   speech=_("OK, quieter now."))

    @handler.handle(Custom.SELECT_PLAYER)
    def on_select_player(self, intent, session, pid=None):
        srv = self.get_server()
        srv.refresh_status()

        # Do it again, yes, but not defaulting this time.
        pid = self.player_id_from(intent, defaulting=False)
        if pid:
            player = srv.players[pid]
            srv.cur_player_id = player.id
            text = _("Selected {player}").format(player=player.name)
            title = _("Selected player {}").format(player)
            return speech_response(title=title, text=text,
                                   store={"player_id": pid})
        speech = (_("I only found these players: {}. Could you try again?")
                  .format(english_join(srv.player_names)))
        reprompt = (_("You can select a player by saying \"{utterance}\" "
                      "and then the player name.")
                    .format(utterance=Utterances.SELECT_PLAYER))
        try:
            player = intent['slots']['Player']['value']
            title = (_("No player called \"{}\"").format(player))
        except KeyError:
            title = "Didn't recognise a player name"
        return speech_response(title, speech, reprompt_text=reprompt,
                               end=False)

    @handler.handle(Audio.SHUFFLE_ON)
    @handler.handle(CustomAudio.SHUFFLE_ON)
    def on_shuffle_on(self, intent, session, pid=None):
        self.get_server().set_shuffle(True, player_id=pid)
        return self.smart_response(text=_("Shuffle on"),
                                   speech=_("Shuffle is now on"))

    @handler.handle(Audio.SHUFFLE_OFF)
    @handler.handle(CustomAudio.SHUFFLE_OFF)
    def on_shuffle_off(self, intent, session, pid=None):
        self.get_server().set_shuffle(False, player_id=pid)
        return self.smart_response(text=_("Shuffle off"),
                                   speech=_("Shuffle is now off"))

    @handler.handle(Audio.LOOP_ON)
    @handler.handle(CustomAudio.LOOP_ON)
    def on_loop_on(self, intent, session, pid=None):
        self.get_server().set_repeat(True, player_id=pid)
        return self.smart_response(text=_("Repeat on"),
                                   speech=_("Repeat is now on"))

    @handler.handle(Audio.LOOP_OFF)
    @handler.handle(CustomAudio.LOOP_OFF)
    def on_loop_off(self, intent, session, pid=None):
        self.get_server().set_repeat(False, player_id=pid)
        return self.smart_response(text=_("Repeat Off"),
                                   speech=_("Repeat is now off"))

    @handler.handle(Power.PLAYER_OFF)
    def on_player_off(self, intent, session, pid=None):
        if not pid:
            return self.on_all_off(intent, session)
        server = self.get_server()
        server.set_power(on=False, player_id=pid)
        player = server.players[pid]
        text = _("Switched {} off").format(player.name)
        speech = _("{player} is now off").format(player=player.name)
        return self.smart_response(title=text, text=text, speech=speech)

    @handler.handle(Power.PLAYER_ON)
    def on_player_on(self, intent, session, pid=None):
        if not pid:
            return self.on_all_on(intent, session)
        server = self.get_server()
        server.set_power(on=True, player_id=pid)
        player = server.players[pid]
        speech = "{player} is now on".format(player=player.name)
        if server.cur_player_id != pid:
            speech += ", and is selected."
        server.cur_player_id = pid
        text = _("Switched {player} on").format(player=player.name)
        return self.smart_response(title=text, text=text, speech=speech)

    @handler.handle(Power.ALL_OFF)
    def on_all_off(self, intent, session, pid=None):
        self.get_server().set_all_power(on=False)
        return self.smart_response(text=_("Players all off"),
                                   speech=_("Silence."))

    @handler.handle(Power.ALL_ON)
    def on_all_on(self, intent, session, pid=None):
        self.get_server().set_all_power(on=True)
        return self.smart_response(text=_("All On."),
                                   speech=_("Ready to rock"))

    @handler.handle(Play.PLAYLIST)
    def on_play_playlist(self, intent, session, pid=None):
        server = self.get_server()
        try:
            slot = intent['slots']['Playlist']['value']
            print_d("Extracted playlist slot: {}".format(slot))
        except KeyError:
            print_d("Couldn't process playlist from: {}", intent)
            if not server.playlists:
                return speech_response(text=_("There are no playlists"))
            pl = random.choice(server.playlists)
            return speech_response(
                text=_("Didn't hear a playlist there. "
                       "You could try the \"{}\" playlist?").format(pl))
        else:
            if not server.playlists:
                return speech_response(text=_("No Squeezebox playlists found"))
            result = process.extractOne(slot, server.playlists)
            print_d("{} was the best guess for '{}' from {}",
                    str(result), slot, server.playlists)
            if result and int(result[1]) >= MinConfidences.PLAYLIST:
                pl = result[0]
                server.playlist_resume(pl, player_id=pid)
                name = sanitise_text(pl)
                return self.smart_response(
                    speech=_("Playing \"{name}\" playlist").format(name=name),
                    text=_("Playing \"{name}\" playlist").format(name=name))
            pl = random.choice(server.playlists)
            template = _("Couldn't find a playlist matching \"{name}\"."
                         "How about the \"{suggestion}\" playlist?")
            return speech_response(template.format(name=slot, suggestion=pl))

    @handler.handle(Play.RANDOM_MIX)
    def on_play_random_mix(self, intent, session, pid=None):
        server = self.get_server()
        try:
            slots = [v.get('value') for k, v in intent['slots'].items()
                     if k.endswith('Genre')]
            print_d("Extracted genre slots: {}".format(slots))
        except KeyError:
            print_d("Couldn't process genres from: {}".format(intent))
            pass
        else:
            lms_genres = self._genres_from_slots(slots, server.genres)
            if lms_genres:
                server.play_genres(lms_genres, player_id=pid)
                gs = english_join(sanitise_text(g) for g in lms_genres)
                text = _("Playing mix of {genres}").format(genres=gs)
                return self.smart_response(text=text, speech=text)
            else:
                genres_text = english_join(slots, _("or"))
                text = _("Don't understand requested genres {}").format(
                    genres_text)
                speech = _("Can't find genres: {}").format(genres_text)
                return self.smart_response(text=text, speech=speech)
        raise ValueError("Don't understand intent '{}'".format(intent))

    def _genres_from_slots(self, slots, genres):
        def genres_from(g):
            if not g:
                return set()
            res = process.extract(g, genres)[:MAX_GUESSES_PER_SLOT]
            print_d("Raw genre results: {}", res)
            for g, c in res:
                # Exact(ish) matches shouldn't allow other genres
                if c > MinConfidences.SINGLE_GENRE:
                    return {g}
            return {g for g, c in res
                    if g and int(c) >= MinConfidences.MULTI_GENRE}
        # Grr where's my foldl
        results = set()
        for slot in slots:
            results |= genres_from(slot)
        return results

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
            print_d("{} was the best guess for '{}' from {}",
                    result, player_name, by_name.keys())
            if result and int(result[1]) >= MinConfidences.PLAYER:
                return by_name.get(result[0]).id
        return srv.cur_player_id if defaulting else None

    def on_session_ended(self, intent, session):
        print_d("Session {} ended", session['sessionId'])
        speech_output = _("Hasta la vista. Baby.")
        return speech_response("Session Ended", speech_output, end=True)

    @classmethod
    def touch_audio(cls, ts=None):
        cls._audio_touched = ts or time.time()

    @property
    def audio_enabled(self):
        return (time.time() - self._audio_touched) < AUDIO_TIMEOUT_SECS

    def smart_response(self, title=None, text=None, speech=None):
        if self.audio_enabled:
            return speech_response(title=title or text, text=speech)
        return audio_response(speech=speech, text=text, title=title)
