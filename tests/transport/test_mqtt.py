# -*- coding: utf-8 -*-
#
#   Copyright 2018-19 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license
from datetime import datetime

import pytest
from paho.mqtt.client import MQTT_ERR_SUCCESS, MQTTMessage, MQTTMessageInfo

from squeezealexa.settings import MqttSettings
from squeezealexa.transport.base import Error
from squeezealexa.transport.mqtt import MqttTransport, CustomClient


class NoTlsCustomClient(CustomClient):
    def _configure_tls(self):
        pass


class EchoingFakeClient(NoTlsCustomClient):
    PREFIX = "OK: "

    def __init__(self, settings: MqttSettings):
        super().__init__(settings)
        self.subscribed = []
        self.unsubscribed = []

    def connect(self, host=None, port=None, keepalive=30, bind_address=""):
        if self.on_connect:
            self.on_connect(self, None, None, 1)
        return MQTT_ERR_SUCCESS, 1

    def subscribe(self, topic, qos=0):
        self.subscribed.append(topic)
        if self.on_subscribe:
            self.on_subscribe(self, None, 123, (qos,))
        return MQTT_ERR_SUCCESS, 2

    def publish(self, topic, payload=None, qos=0, retain=False):
        if self.on_publish:
            self.on_publish(self, None, 123)
        self.react_to_msg(payload)
        info = MQTTMessageInfo(123)
        info._published = True
        return info

    def unsubscribe(self, topic):
        self.unsubscribed.append(topic)
        return super().unsubscribe(topic)

    def react_to_msg(self, payload):
        """Fake the round trip entirely"""
        msg = MQTTMessage(topic=self.settings.topic_resp)
        msg.payload = b"%s%s" % (self.PREFIX.encode('utf-8'), payload)
        self.on_message(self, None, msg)

    def __str__(self) -> str:
        return "<Fake MQTT>"

    def reconnect(self):
        return MQTT_ERR_SUCCESS


@pytest.fixture
def fake_client():
    c = EchoingFakeClient(MqttSettings())
    c.connect()
    yield c
    c.disconnect()
    del c


class TestMqttTransport:
    def test_communicate(self, fake_client):
        """Ensure that the communication we get back is the echo server's"""
        t = MqttTransport(fake_client, req_topic="foo", resp_topic="bar")
        t.start()
        assert fake_client.subscribed == ["bar"]
        msg = "TEST MESSAGE at %s" % datetime.now()
        ret = t.communicate(msg)
        assert ret == fake_client.PREFIX + msg
        del t

    def test_lazy_communicate(self, fake_client):
        t = MqttTransport(fake_client, req_topic="foo", resp_topic="bar")
        t.start()
        assert not t.communicate("FIRE AND FORGET", wait=False)

    def test_multiline_communicate(self, fake_client):
        """Ensure that the communication we get back is the echo server's"""
        t = MqttTransport(fake_client, req_topic="foo", resp_topic="bar")
        t.start()
        msg = "TEST MESSAGE at %s\nAND ANOTHER\nLAST" % datetime.now()
        ret = t.communicate(msg)
        assert ret == fake_client.PREFIX + msg

    def test_details(self, fake_client):
        """Ensure that the communication we get back is the echo server's"""
        t = MqttTransport(fake_client, req_topic="foo", resp_topic="bar")
        s = str(t)
        assert "MQTT " in s
        assert str(fake_client) in s

    def test_stop(self, fake_client):
        t = MqttTransport(fake_client, req_topic="foo", resp_topic="bar")
        t.stop()
        # We no longer unsubscribe on stop
        # assert fake_client.unsubscribed == ['bar'
        assert not t.is_connected


class TestCustomClient:
    def test_get_conf_file(self):
        c = NoTlsCustomClient(MqttSettings())
        assert c._conf_file_of("*.md")

    def test_get_conf_file_raises(self):
        c = NoTlsCustomClient(MqttSettings())
        with pytest.raises(Error) as e:
            c._conf_file_of("*.py")
        assert "Can't find" in str(e)


class TestMqttSettings:
    def test_configured(self):
        m = MqttSettings()
        m.hostname = None
        c = m.configured
        assert not c
