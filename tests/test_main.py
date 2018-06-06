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

from pytest import raises

from squeezealexa import settings
from squeezealexa.settings import MqttSettings

from squeezealexa.transport.base import Error
from squeezealexa.transport.configured import create_transport


class TestSqueezeAlexa:

    def test_ssl_setup(self):
        s = MqttSettings()
        s.hostname = None
        configured = s.configured
        assert not configured
        settings.CERT_DIR = "/dev/null"
        with raises(Error) as e:
            create_transport(mqtt_settings=s)
        assert "Check CERT_NAME" in str(e)
