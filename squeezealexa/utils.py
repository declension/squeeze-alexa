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


def english_join(items, final="and"):
    """Like join, but in English (no Oxford commas...)"""
    items = list(filter(None, items))
    most = ", ".join(items[0:-1])
    sep = " %s " % final.strip()
    return sep.join(filter(None, [most] + items[-1:]))
