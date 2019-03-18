# -*- coding: utf-8 -*-
#
#   Copyright 2017-18 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

from squeezealexa.settings import SkillSettings
from squeezealexa.utils import print_d


def speech_fragment(speech, title=None, reprompt_text=None, end=True,
                    text=None, use_ssml=False):
    text_type = 'SSML' if use_ssml else 'PlainText'
    text_key = 'ssml' if use_ssml else 'text'
    output = {
        'outputSpeech': {
            'type': text_type,
            text_key: speech
        },
        'shouldEndSession': end
    }
    if title:
        output['card'] = {
            'type': 'Simple',
            'title': title,
            'content': text or speech
        }
    if reprompt_text:
        output['reprompt'] = {
            'outputSpeech': {
                'type': text_type,
                text_key: reprompt_text
            }
        }
    return output


def audio_response(speech=None, text=None, title=None):
    output = {
        'directives': [
            {
                'type': 'AudioPlayer.Play',
                'playBehavior': 'REPLACE_ALL',
                'audioItem': {
                    'stream': {
                        'token': 'beep',
                        'url': SkillSettings.RESPONSE_AUDIO_FILE_URL,
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
        card = {'type': 'Simple', 'content': text}
        if title:
            card['title'] = title
        output['card'] = card

    return _build_response(output)


def speech_response(title=None, speech=None, reprompt_text=None, end=True,
                    store=None, text=None, use_ssml=False):
    speechlet_response = speech_fragment(speech=speech or title, title=title,
                                         reprompt_text=reprompt_text,
                                         text=text, end=end,
                                         use_ssml=use_ssml)
    print_d("Returning {response}", response=speechlet_response)
    return _build_response(speechlet_response, store=store)


def _build_response(speechlet_response, store=None):
    return {
        'version': '1.0',
        'sessionAttributes': store or {},
        'response': speechlet_response
    }
