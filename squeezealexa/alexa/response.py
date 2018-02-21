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

from squeezealexa.settings import RESPONSE_AUDIO_FILE_URL


def speech_fragment(speech=None, text=None, title=None,
                    reprompt_text=None, end=True):
    text = text or speech
    speech = speech or text
    output = {'shouldEndSession': end}

    if speech:
        output['outputSpeech'] = {
            'type': 'PlainText',
            'text': speech
        }

    if text:
        card = {
            'type': 'Simple',
            'content': text
        }
        if title:
            card['title'] = title
        output['card'] = card

    if reprompt_text:
        output['reprompt'] = {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        }
    return output


def audio_response(speech=None, text=None, title=None,
                   reprompt_text=None, end=True, store=None):
    speechlet_response = speech_fragment(speech=speech, text=text, title=title,
                                         reprompt_text=reprompt_text, end=end)
    speechlet_response['directives'] = [
        {
            'type': 'AudioPlayer.Play',
            'playBehavior': 'REPLACE_ALL',
            'audioItem': {
                'stream': {
                    'token': 'beep',
                    'url': RESPONSE_AUDIO_FILE_URL,
                    'offsetInMilliseconds': 0
                }
            }
        }
    ]

    return _build_response(speechlet_response, store=store)


def speech_response(speech=None, title=None, text=None,
                    reprompt_text=None, end=True, store=None):
    speechlet_response = speech_fragment(speech=speech, text=text, title=title,
                                         reprompt_text=reprompt_text, end=end)
    return _build_response(speechlet_response, store=store)


def _build_response(speechlet_response, store=None):
    return {
        'version': '1.0',
        'sessionAttributes': store or {},
        'response': speechlet_response
    }
