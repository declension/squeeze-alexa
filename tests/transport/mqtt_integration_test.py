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

from _ssl import PROTOCOL_TLSv1_2
from datetime import datetime
from time import time

import pytest
from paho.mqtt.client import MQTT_ERR_INVAL, MQTTMessage, Client

from squeezealexa.settings import MqttSettings
from squeezealexa.transport.factory import TransportFactory
from squeezealexa.transport.mqtt import CustomClient
from squeezealexa.utils import wait_for
from tests.utils import TEST_DATA_DIR


class CustomTlsCustomClient(CustomClient):

    def __init__(self, settings: MqttSettings):
        super().__init__(settings)
        self.connections = 0

    def _configure_tls(self):
        self.tls_set(ca_certs=self._conf_file_of("mosquitto.org*.crt"),
                     tls_version=PROTOCOL_TLSv1_2)

    def connect(self, host=None, port=None, keepalive=30, bind_address=""):
        self.connections += 1
        return super().connect(host, port, keepalive, bind_address)


@pytest.mark.skip("test.mosquitto.org via TLS is broken")
class TestLiveMqttTransport:
    """Actually tests against test.mosquitto.org
    which is semi-guaranteed to be alive.
    TODO: set up a test broker instead (but this is easier)"""

    def test_real_publishing(self):
        test_mqtt_settings = self.mqtt_settings()
        self.published = []
        self.subscribed = False

        def on_message(client: Client, userdata, msg: MQTTMessage):
            msg = msg.payload.decode('utf-8').strip()
            client.publish(test_mqtt_settings.topic_resp,
                           "GOT: {msg}".format(msg=msg).encode('utf-8'))

        def on_subscribe(client, data, mid, granted_qos):
            self.subscribed = True

        replier = CustomTlsCustomClient(test_mqtt_settings)
        replier.on_message = on_message
        replier.connect()
        replier.on_subscribe = on_subscribe

        def on_publish(client, userdata, mid):
            self.published.append(mid)

        client = CustomTlsCustomClient(test_mqtt_settings)
        client.on_publish = on_publish

        msg = "TEST MESSAGE at %s" % datetime.now()
        factory = TransportFactory(ssl_config=None,
                                   mqtt_settings=test_mqtt_settings)
        transport = factory.create(mqtt_client=client)
        transport.start()
        try:
            replier.subscribe(test_mqtt_settings.topic_req)
            assert replier.loop_start() != MQTT_ERR_INVAL
            wait_for(lambda x: self.subscribed,
                     what="confirming subscription", timeout=3)
            reply = transport.communicate(msg, timeout=3)
            wait_for(lambda x: self.published,
                     what="confirming publish", timeout=3)
        finally:
            transport.stop()
            del transport
            replier.loop_stop()
            del replier
        assert len(self.published) == 1
        assert reply == "GOT: {msg}".format(**locals())

    def test_over_connect(self):
        settings = self.mqtt_settings()
        client = CustomTlsCustomClient(settings)
        factory = TransportFactory(ssl_config=None, mqtt_settings=settings)
        transport = factory.create(mqtt_client=client)
        transport.start()
        wait_for(lambda t: t.is_connected, context=transport)
        transport.start()
        transport.start()
        assert client.connections == 1, "Over connected to MQTT"

        del transport

    def mqtt_settings(self) -> MqttSettings:
        uid = time()
        return MqttSettings(
            hostname='test.mosquitto.org', port=8883,
            cert_dir=TEST_DATA_DIR,
            topic_req="squeeze-req-%s" % uid,
            topic_resp="squeeze-resp-%s" % uid)
