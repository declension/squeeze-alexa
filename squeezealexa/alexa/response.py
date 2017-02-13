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


def speech_fragment(title, text, reprompt_text=None,
                    end=True):
    output = {
        'outputSpeech': {
            'type': 'PlainText',
            'text': text
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': text
        },
        'shouldEndSession': end
    }
    if reprompt_text:
        output['reprompt'] = {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        }
    return output


def audio_response(speech=None, text=None):
    output = {
        'directives': [
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
        ],
        'shouldEndSession': True
    }
    if speech:
        output['outputSpeech'] = {'type': 'PlainText',
                                  'text': speech}
    if text:
        output['card'] = {'type': 'Simple', 'content': text}
    return _build_response(output)


def speech_response(title, text=None, reprompt_text=None, end=True,
                    store=None):
    return _build_response(
        speech_fragment(title=title, text=text, reprompt_text=reprompt_text,
                        end=end), store=store)


def _build_response(speechlet_response, store=None):
    return {
        'version': '1.0',
        'sessionAttributes': store or {},
        'response': speechlet_response
    }
