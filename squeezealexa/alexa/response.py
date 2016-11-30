# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation


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


def audio_response(text):
    output = {
        "directives": [
            {
                "type": "AudioPlayer.Play",
                "playBehavior": "REPLACE_ALL",
                "audioItem": {
                    "stream": {
                        "token": "beep-50",
                        "url": "https://s3.amazonaws.com/declension-alexa-media/computerbeep_50.mp3",
                        "offsetInMilliseconds": 0
                    }
                }
            }
        ],
        'shouldEndSession': True
    }
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
