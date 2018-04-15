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

from os import path
from os.path import dirname

from squeezealexa import settings

LOCALE_DIR = path.join(dirname(dirname(__file__)), 'locale')
# Realistically this will have to be the default, sigh.
CODE_LOCALE = "en_US"


def set_up_gettext(user_locale):
    t = gettext.translation('squeeze-alexa', localedir=LOCALE_DIR,
                            languages=[user_locale], fallback=True)
    if not isinstance(t, GNUTranslations) and user_locale != CODE_LOCALE:
        print("No translation file found for requested locale '%s', "
              "using default (en_US) instead." % user_locale)
    return t.gettext


_ = set_up_gettext(settings.LOCALE)

# Canary translation
_("favorites")
