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

import random
import re
import unicodedata
import sys
from time import time, sleep
from typing import Dict, Iterable, Union

from squeezealexa.i18n import _


def print_d(template, *args, **kwargs):
    if args and not kwargs:
        raise ValueError("Use only named parameters please")
    text = template.format(*args, **kwargs)
    print(text)
    return text


print_w = print_d


def human_join(items: Iterable, final: str =_("and")) -> str:
    """Like join, but in English (no Oxford commas...)
       Kinda works in some other languages (French, German)"""
    items = list(filter(None, items or []))
    most = ", ".join(items[0:-1])
    sep = " %s " % final.strip()
    return sep.join(filter(None, [most] + items[-1:]))


_SPACIFIES = {i: u' ' for i in range(sys.maxunicode)
              if unicodedata.category(chr(i)).startswith('P')}

_REMOVALS = {ord(i): None for i in ['\'', '!']}

_SANITISE = {'&': ' N ',
             '+': ' N ',
             '$': 's'}


def remove_punctuation(text):
    return text.translate(_REMOVALS).translate(_SPACIFIES)


def sanitise_text(text):
    """Makes a genre / playlist / artist name safer for Alexa output"""
    if not text:
        return ""
    safer = text
    for (bad, good) in _SANITISE.items():
        safer = safer.replace(bad, good)
    no_punc = remove_punctuation(safer)
    return re.sub(r'\s{2,}', ' ', no_punc)


def with_example(template: str, collection) -> str:
    """Takes a template string with `{num}` in it and gives a length
    and an example, if possible."""
    if "{num}" not in template:
        raise ValueError("Need {num} in the template")
    total = len(collection)
    msg = template.format(num=total)
    if collection:
        extra = ' ({eg}"{item}")'.format(eg='e.g. ' if total > 1 else '',
                                         item=random.choice(list(collection)))
        msg += extra
    return msg


def stronger(k, v, extra_bools=None):
    """Return a stronger-typed version of a value if possible"""
    prefixes = set(extra_bools or [])
    prefixes.update({'has', 'is', 'can'})
    try:
        for prefix in prefixes:
            if k.startswith(prefix):
                return bool(int(v))
        try:
            return int(v)
        except ValueError:
            return float(v)
    except ValueError:
        return None if not v else v


def wait_for(func, timeout=3, what=None, context=None):
    nt = t = time()
    while not func(context):
        sleep(0.1)
        nt = time()
        if nt - t > timeout:
            msg = "Failed \"{task}\" in {context}, after {secs:.2f}s".format(
                task=what, context=str(context), secs=nt - t)
            raise Exception(msg)
    print_d("Stats: \"{task}\" took < {duration:.2f} seconds", task=what,
            duration=nt - t)


def first_of(details: Dict, tags: Iterable[str]) -> Union[str, None]:
    """Gets the first non-null value from the list of tags"""
    for tag in tags:
        if tag in details:
            return details[tag]
    return None
