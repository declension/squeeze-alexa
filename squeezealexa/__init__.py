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

import gettext

from os import path

from os.path import dirname

LOCALE_DIR = path.join(dirname(dirname(__file__)), 'locale')
t = gettext.translation('squeeze-alexa', localedir=LOCALE_DIR)
_ = t.gettext

# Canary translation
_("favorites")
