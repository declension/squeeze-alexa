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

from squeezealexa.alexa.handlers import AlexaHandler, IntentHandler
from squeezealexa.alexa.intents import *
from squeezealexa.alexa.response import audio_response, speech_response, \
    _build_response
from squeezealexa.alexa.utterances import Utterances
from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server, print_d
from squeezealexa.ssl_wrap import SslSocketWrapper
from squeezealexa.utils import english_join, sanitise_text, substitute
from squeezealexa.speechout import *


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
            print_d("Overriding class server for testing")
            SqueezeAlexa._server = server

    def handle(self, event, context=None):
        request = event['request']
        req_type = request['type']
        if req_type.startswith('AudioPlayer'):
            print_d("Ignoring %s callback %s"
                    % (request['type'], request['requestId']))
            self.touch_audio()
            return _build_response({})
        return super(SqueezeAlexa, self).handle(event, context)

    def on_session_started(self, request, session):
        print_d("Starting new session %s for request %s" %
                (session['sessionId'], request['requestId']))

    def on_launch(self, launch_request, session):

        print_d("Entering interactive mode for sessionId=%s"
                % session['sessionId'])
        return self.language_response('launch', end=False)

    @classmethod
    def get_server(cls):
        """
        :return a Server instance
        :rtype Server
        """
        if not cls._server or cls._server.is_stale():
            sslw = SslSocketWrapper(hostname=SERVER_HOSTNAME,
                                    port=SERVER_SSL_PORT,
                                    ca_file=CA_FILE_PATH,
                                    cert_file=CERT_FILE_PATH,
                                    verify_hostname=VERIFY_SERVER_HOSTNAME)
            cls._server = Server(sslw,
                                 user=SERVER_USERNAME,
                                 password=SERVER_PASSWORD,
                                 cur_player_id=DEFAULT_PLAYER,
                                 debug=DEBUG_LMS)
            print_d("Created %r" % cls._server)
        else:
            print_d("Reusing cached %r" % cls._server)
        return cls._server

    def on_intent(self, intent_request, session):
        intent = intent_request['intent']
        intent_name = intent['name']
        pid = self.player_id_from(intent)
        print_d("Received %s: %s (for player %s)" % (intent_name, intent, pid))

        intent_handler = handler.for_name(intent_name)
        if intent_handler:
            return intent_handler(self, intent, session, pid=pid)
        return self.language_response('unknown_intent', [intent_name])

    @handler.handle(Audio.RESUME)
    def on_resume(self, intent, session, pid=None):
        self.get_server().resume(player_id=pid)
        return self.language_response('resume')

    @handler.handle(Audio.PAUSE)
    def on_pause(self, intent, session, pid=None):
        self.get_server().pause(player_id=pid)
        return self.language_response('pause')

    @handler.handle(Audio.PREVIOUS)
    def on_previous(self, intent, session, pid=None):
        self.get_server().previous(player_id=pid)
        return self.language_response('previous')

    @handler.handle(Audio.NEXT)
    def on_next(self, intent, session, pid=None):
        self.get_server().next(player_id=pid)
        return self.language_response('next')

    @handler.handle(Custom.CURRENT)
    def on_current(self, intent, session, pid=None):
        details = self.get_server().get_track_details(player_id=pid)
        title = details['current_title']
        artist = details['artist']
        if title:
            desc = substitute(
                speechoutput[LANGUAGE].get('current', None), [title]
            )
            if artist:
                desc += substitute(
                    speechoutput[LANGUAGE].get('current_by', None), [artist]
                )
            heading = substitute(
                textoutput[LANGUAGE].get('current', None), [title]
            )
        else:
            desc = speechoutput[LANGUAGE]['current_none']
            heading = None
        return self.smart_response(text=heading, speech=desc)

    @handler.handle(Custom.SET_VOL)
    def on_set_vol(self, intent, session, pid=None):
        srv = self.get_server()
        srv.refresh_status()
        try:
            vol = float(intent['slots']['Volume']['value'])
            print_d("Extracted playlist slot: %s" % vol)
        except KeyError:
            print_d("Couldn't process volume from: %s" % intent)
            return self.language_response('set_vol_nf')
        if (vol > 10) or (vol < 0):
            print_d("Volume value out of range: %f" % vol)
            return self.language_response('set_vol_nf')
        self.get_server().set_volume(vol * 10, pid)
        return self.language_response('set_vol', [int(vol)])

    @handler.handle(Custom.INC_VOL)
    def on_inc_vol(self, intent, session, pid=None):
        self.get_server().change_volume(+12.5, player_id=pid)
        return self.language_response('inc_vol')

    @handler.handle(Custom.DEC_VOL)
    def on_dec_vol(self, intent, session, pid=None):
        self.get_server().change_volume(-12.5, player_id=pid)
        return self.language_response('dec_vol')

    @handler.handle(Custom.SELECT_PLAYER)
    def on_select_player(self, intent, session, pid=None):
        srv = self.get_server()
        srv.refresh_status()

        # Do it again, yes, but not defaulting this time.
        pid = self.player_id_from(intent, defaulting=False)
        if pid:
            player = srv.players[pid]
            srv.cur_player_id = player.id
            return self.language_response(
                'select_player', [player, player.name],
                store={"player_id": pid}
            )
        else:
            speech = substitute(
                speechoutput[LANGUAGE].get('select_player_nf', None),
                [english_join(srv.player_names)]
            )
            reprompt = substitute(
                repromptoutput[LANGUAGE].get('select_player_nf', None),
                [Utterances.SELECT_PLAYER]
            )
            try:
                title = substitute(
                    titleoutput[LANGUAGE].get('select_player_nf', None),
                    [intent['slots']['Player']['value']]
                )
            except KeyError:
                title = titleoutput[LANGUAGE].get('select_player_nk', None)
            return self.smart_response(
                speech=speech, title=title, reprompt_text=reprompt, end=False
            )

    @handler.handle(Audio.SHUFFLE_ON)
    @handler.handle(CustomAudio.SHUFFLE_ON)
    def on_shuffle_on(self, intent, session, pid=None):
        self.get_server().set_shuffle(True, player_id=pid)
        return self.language_response('shuffle_on')

    @handler.handle(Audio.SHUFFLE_OFF)
    @handler.handle(CustomAudio.SHUFFLE_OFF)
    def on_shuffle_off(self, intent, session, pid=None):
        self.get_server().set_shuffle(False, player_id=pid)
        return self.language_response('shuffle_off')

    @handler.handle(Audio.LOOP_ON)
    @handler.handle(CustomAudio.LOOP_ON)
    def on_loop_on(self, intent, session, pid=None):
        self.get_server().set_repeat(True, player_id=pid)
        return self.language_response('loop_on')

    @handler.handle(Audio.LOOP_OFF)
    @handler.handle(CustomAudio.LOOP_OFF)
    def on_loop_off(self, intent, session, pid=None):
        self.get_server().set_repeat(False, player_id=pid)
        return self.language_response('loop_off')

    @handler.handle(Power.PLAYER_OFF)
    def on_player_off(self, intent, session, pid=None):
        if not pid:
            return self.on_all_off(intent, session)
        server = self.get_server()
        server.set_power(on=False, player_id=pid)
        player = server.players[pid]
        return self.language_response('player_off', [player.name, player])

    @handler.handle(Power.PLAYER_ON)
    def on_player_on(self, intent, session, pid=None):
        if not pid:
            return self.on_all_on(intent, session)
        server = self.get_server()
        server.set_power(on=True, player_id=pid)
        player = server.players[pid]
        speech = substitute(speechoutput[LANGUAGE]['player_on'], [player.name])
        if server.cur_player_id != pid:
            speech += speechoutput[LANGUAGE]['player_on_select']
        text = substitute(textoutput[LANGUAGE]['player_on'], [player])
        title = substitute(titleoutput[LANGUAGE]['player_on'], [player.name])
        server.cur_player_id = pid
        return self.smart_response(title=title,
                                   text=text,
                                   speech=speech)

    @handler.handle(Power.ALL_OFF)
    def on_all_off(self, intent, session, pid=None):
        self.get_server().set_all_power(on=False)
        return self.language_response('all_off')

    @handler.handle(Power.ALL_ON)
    def on_all_on(self, intent, session, pid=None):
        self.get_server().set_all_power(on=True)
        return self.language_response('all_on')

    @handler.handle(Play.PLAYLIST)
    def on_play_playlist(self, intent, session, pid=None):
        server = self.get_server()
        try:
            slot = intent['slots']['Playlist']['value']
            print_d("Extracted playlist slot: %s" % slot)
        except KeyError:
            print_d("Couldn't process playlist from: %s" % intent)
            if not server.playlists:
                return self.language_response('play_playlist_nh_none')
            return self.language_response(
                'play_playlist_nh', [random.choice(server.playlists)]
            )
        else:
            if not server.playlists:
                return self.language_response('play_playlist_none')
            result = process.extractOne(slot, server.playlists)
            print_d("%s was the best guess for '%s' from %s"
                    % (result, slot, server.playlists))
            if result and int(result[1]) >= MinConfidences.PLAYLIST:
                pl = result[0]
                server.playlist_resume(pl, player_id=pid)
                name = sanitise_text(pl)
                return self.language_response('play_playlist', [name])
            return self.language_response(
                'play_playlist_nf', [slot, random.choice(server.playlists)]
            )

    @handler.handle(Play.RANDOM_MIX)
    def on_play_random_mix(self, intent, session, pid=None):
        server = self.get_server()
        try:
            slots = [v.get('value') for k, v in intent['slots'].items()
                     if k.endswith('Genre')]
            print_d("Extracted genre slots: %s" % slots)
        except KeyError:
            print_d("Couldn't process genres from: %s" % intent)
            pass
        else:
            lms_genres = self._genres_from_slots(slots, server.genres)
            if lms_genres:
                server.play_genres(lms_genres, player_id=pid)
                gs = english_join(sanitise_text(g) for g in lms_genres)
                return self.language_response('play_random_mix', [gs])
            else:
                genres_text = english_join(slots, "or")
                return self.language_response(
                    'play_random_mix_nf', [genres_text]
                )
        raise ValueError("Don't understand intent '%s'" % intent)

    def _genres_from_slots(self, slots, genres):
        def genres_from(g):
            if not g:
                return set()
            res = process.extract(g, genres)[:MAX_GUESSES_PER_SLOT]
            print_d("Raw genre results: %s" % res)
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
            print_d("%s was the best guess for '%s' from %s"
                    % (result, player_name, by_name.keys()))
            if result and int(result[1]) >= MinConfidences.PLAYER:
                return by_name.get(result[0]).id
        return srv.cur_player_id if defaulting else None

    def on_session_ended(self, intent, session):
        print_d("Session %s ended" % session['sessionId'])
        return self.language_response('session_ended')

    @classmethod
    def touch_audio(cls, ts=None):
        cls._audio_touched = ts or time.time()

    @property
    def audio_enabled(self):
        return (time.time() - self._audio_touched) < AUDIO_TIMEOUT_SECS

    def language_response(self, resId, subs=[], end=True, store=None):
        speech = substitute(speechoutput[LANGUAGE].get(resId, None), subs)
        text = substitute(textoutput[LANGUAGE].get(resId, None), subs)
        title = substitute(titleoutput[LANGUAGE].get(resId, None), subs)
        reprompt = substitute(repromptoutput[LANGUAGE].get(resId, None), subs)
        return self.smart_response(
            speech=speech, title=title, text=text,
            reprompt_text=reprompt, end=end, store=store
        )

    def smart_response(
            self, speech=None, title=None, text=None,
            reprompt_text=None, end=True, store=None
    ):
        if (self.audio_enabled) and (speech):
            return speech_response(
                speech=speech, title=title, text=text,
                reprompt_text=reprompt_text, end=end, store=store
            )
        return audio_response(
            speech=speech, title=title, text=text,
            reprompt_text=reprompt_text, end=end, store=store
        )
