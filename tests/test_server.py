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

from unittest import TestCase

from squeezealexa.squeezebox.server import Server
from tests.fake_ssl import FakeSsl, FAKE_LENGTH


class TestServer(TestCase):
    def setUp(self):
        self.server = Server(ssl_wrap=FakeSsl())

    def test_get_current(self):
        assert self.server.get_status()['genre']

    def test_status(self):
        assert self.server.get_milliseconds() == FAKE_LENGTH * 1000

    def test_str(self):
        assert 'localhost:0' in str(self.server)

    def test_login(self):
        self.server = Server(ssl_wrap=FakeSsl(), user='admin', password='pass')
        assert self.server.user == 'admin'
