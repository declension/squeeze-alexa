# -*- coding: utf-8 -*-
#
#   Copyright 2018 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

import gettext
from gettext import GNUTranslations
from glob import glob

from os import path
from os.path import dirname

from squeezealexa.settings import SKILL_SETTINGS

LOCALE_DIR = path.abspath(path.join(dirname(dirname(__file__)), 'locale'))
DOMAIN = 'squeeze-alexa'
# Realistically this will have to be the default, sigh.
CODE_LOCALE = "en_US"


def set_up_gettext(user_locale):
    t = gettext.translation(DOMAIN, localedir=LOCALE_DIR,
                            languages=[user_locale], fallback=True)
    if not isinstance(t, GNUTranslations) and user_locale != CODE_LOCALE:
        # Can't import print_d here...
        print("No translation file found for requested locale '{locale}', "
              "using default ({default}) instead.".format(locale=user_locale,
                                                          default=CODE_LOCALE))
    return t.gettext


def available_translations():
    files = glob(path.join(LOCALE_DIR, '*', 'LC_MESSAGES', '%s.mo' % DOMAIN))
    return [file.split(path.sep)[-3] for file in files]


_ = set_up_gettext(SKILL_SETTINGS.LOCALE)

# Canary translation
_("favorites")
