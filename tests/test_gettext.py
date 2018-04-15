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
import os

from squeezealexa.i18n import _, LOCALE_DIR, set_up_gettext

AN_UNTRANSLATED_STRING = "foobar baz"


def test_gettext_basic():
    assert _(AN_UNTRANSLATED_STRING) == AN_UNTRANSLATED_STRING


def test_gettext_finds_mo():
    with NewLocale("en_GB.UTF-8"):
        mo_file = gettext.find('squeeze-alexa', localedir=LOCALE_DIR)
        assert mo_file, "Can't find British .mo"


def test_binding_uses_settings_locale():
    with NewLocale("fr_FR"):
        _ = set_up_gettext("en_GB.UTF-8")
        assert _("favorites") == "favourites"


class NewLocale(object):

    def __init__(self, loc):
        self.loc = loc
        self.old = None

    def __enter__(self):
        self.old = os.environ["LANG"]
        os.environ["LANG"] = self.loc
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.environ["LANG"] = self.old
