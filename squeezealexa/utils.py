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

import re
import unicodedata
import sys


def english_join(items, final="and"):
    """Like join, but in English (no Oxford commas...)"""
    items = list(filter(None, items))
    most = ", ".join(items[0:-1])
    sep = " %s " % final.strip()
    return sep.join(filter(None, [most] + items[-1:]))


_spacifies = {i: u' ' for i in range(sys.maxunicode)
              if unicodedata.category(unichr(i)).startswith('P')}

_removals = {ord(i): None for i in ['\'', '!']}


def remove_punctuation(text):
    if not isinstance(text, unicode):
        text = text.decode('utf-8')
    return text.translate(_removals).translate(_spacifies)


def sanitise_genre(genre):
    if not genre:
        return ""
    no_amps = genre.replace('&', ' N ').replace('+', ' N ')
    no_punc = remove_punctuation(no_amps)
    return re.sub(r'\s{2,}', ' ', no_punc)
