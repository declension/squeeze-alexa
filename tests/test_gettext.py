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

import os
from squeezealexa.i18n import _, set_up_gettext, available_translations

UNSUPPORTED_LOCALE = "ku.UTF-8"
AN_UNTRANSLATED_STRING = 'foobar baz'
REQUIRED_TRANSLATIONS = ['favorites',
                         'Currently playing: "{title}"',
                         'Playing mix of {genres}',
                         'Shuffle is now off']


def test_gettext_basic():
    assert _(AN_UNTRANSLATED_STRING) == AN_UNTRANSLATED_STRING


def test_binding_respects_language():
    _ = set_up_gettext("en_US.UTF-8")
    assert _("favorites") == "favorites"


def test_gettext_uses_fallback():
    _ = set_up_gettext(UNSUPPORTED_LOCALE)
    assert _("favorites") == "favorites"


def test_binding_uses_settings_locale():
    with NewLocale("fr_FR"):
        _ = set_up_gettext("en_GB.UTF-8")
        assert _("favorites") == "favourites"


def test_some_german_works():
    _ = set_up_gettext("de_DE.UTF-8")
    assert _("favorites") == "Favoriten"
    assert _("Playing mix of {genres}") == "Spiele eine Mischung aus {genres}"


def test_some_french_works():
    _ = set_up_gettext("fr.UTF-8")
    assert _("favorites") == "favoris"
    french = "La lecture aléatoire est maintenant désactivée"
    assert _("Shuffle is now off") == french


class TestTranslations:
    def test_all_langs(self):
        langs = available_translations()
        assert 'en_GB' in langs
        assert len(langs) >= 2

    def test_each_lang(self):
        langs = set(available_translations()) - {'en_GB'}
        for lang in langs:
            translate = set_up_gettext(lang)
            for text in REQUIRED_TRANSLATIONS:
                translated = translate(text)
                assert translated
                msg = "'{text}' is untranslated for {lang}".format(**locals())
                assert translated != text, msg


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
