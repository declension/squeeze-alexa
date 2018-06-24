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

import pytest
from pytest import raises

from squeezealexa.settings import MqttSettings, SslSettings
from squeezealexa.transport.base import check_listening, Error
from squeezealexa.transport.configured import create_transport
from tests.transport.base import TimeoutServer


def test_check_listening():
    with TimeoutServer() as server:
        check_listening("localhost", server.port, timeout=1)

        wrong_port = server.port + 1
        with pytest.raises(Error) as e:
            check_listening("localhost", wrong_port, timeout=1,
                            msg="OHNOES")
        s = str(e)
        assert ("on localhost:%d" % wrong_port) in s
        assert "OHNOES" in s


def test_create_transport_uses_full_ca_path():
    ssls = SslSettings()
    ssls.ca_file_path = "/foo/bar"
    with raises(Error) as e:
        create_transport(ssls, MqttSettings())
    assert ("CA '%s'" % ssls.ca_file_path) in str(e)


def test_create_transport_uses_cert_path():
    ssls = SslSettings()
    ssls.cert_file_path = "/foo/bar"
    with raises(Error) as e:
        create_transport(ssls, MqttSettings())
    assert ("cert '%s'" % ssls.cert_file_path) in str(e)
