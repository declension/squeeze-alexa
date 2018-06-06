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

from os.path import dirname

ROOT_DIR = dirname(dirname(__file__))
"""The squeeze-alexa root directory"""


class Settings:
    """Class-level settings base.
    It's in here to avoid circular imports"""

    def __str__(self) -> str:
        return str(self.dict())

    def dict(self):
        return {k: v for k, v in type(self).__dict__.items()
                if not k.startswith('_') and k not in Settings.__dict__}

    def __init__(self):
        # Set the instance-level things:
        for k, v in self.dict().items():
            setattr(self, k.lower(), v)

    def configured(self):
        return True
