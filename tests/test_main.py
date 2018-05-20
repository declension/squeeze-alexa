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

from squeezealexa.main import SqueezeAlexa, MqttSettings
from squeezealexa.transport.base import Error


class TestSqueezeAlexa:
    def test_ssl_setup(self):
        s = MqttSettings()
        s.hostname = None
        configured = s.configured
        assert not configured
        with raises(Error) as e:
            SqueezeAlexa.create_transport(mqtt_settings=s)
        assert "Check CERT_NAME" in str(e)
