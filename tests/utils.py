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

from os.path import dirname, join, realpath

ROOT = dirname(dirname(__file__))
EN_GENRES = join(ROOT, 'metadata/intents/v0/locale/en_GB/slots/genres.txt')
GENRES = open(EN_GENRES).read().splitlines()
TEST_DATA_DIR = realpath(join(dirname(__file__), 'data'))
