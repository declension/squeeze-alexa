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

from _ssl import PROTOCOL_TLSv1_2
from datetime import datetime
from time import time

from paho.mqtt.client import MQTT_ERR_INVAL, MQTTMessage, Client

from squeezealexa.settings import MqttSettings
from squeezealexa.transport.configured import create_transport
from squeezealexa.transport.mqtt import CustomClient
from squeezealexa.utils import wait_for
from tests.utils import TEST_DATA_DIR


class CustomTlsCustomClient(CustomClient):

    def _configure_tls(self):
        self.tls_set(ca_certs=self._conf_file_of("mosquitto.org*.crt"),
                     tls_version=PROTOCOL_TLSv1_2)


class TestLiveMqttTransport:
    """Actually tests against test.mosquitto.org
    which is semi-guaranteed to be alive.
    TODO: set up a test broker instead (but this is easier)"""

    def test_real_publishing(self):
        test_mqtt_settings = self.mqtt_settings()
        self.published = []

        def on_message(client: Client, userdata, msg: MQTTMessage):
            msg = msg.payload.decode('utf-8').strip()
            client.publish(test_mqtt_settings.topic_resp,
                           "GOT: {msg}".format(msg=msg).encode('utf-8'))
        replier = CustomTlsCustomClient(test_mqtt_settings)
        replier.on_message = on_message
        replier.connect()

        def on_publish(client, userdata, mid):
            self.published.append(mid)
        client = CustomTlsCustomClient(test_mqtt_settings)
        client.on_publish = on_publish

        msg = "TEST MESSAGE at %s" % datetime.now()
        transport = create_transport(ssl_config=None,
                                     mqtt_settings=test_mqtt_settings,
                                     mqtt_client=client)
        try:
            replier.subscribe(test_mqtt_settings.topic_req)
            assert replier.loop_start() != MQTT_ERR_INVAL
            reply = transport.communicate(msg)
            wait_for(lambda x: self.published,
                     what="confirming publish", timeout=5)
        finally:
            del transport
            replier.loop_stop()
            del replier
        assert len(self.published) == 1
        assert reply == "GOT: {msg}".format(**locals())

    def mqtt_settings(self) -> MqttSettings:
        uid = time()
        test_mqtt_settings = MqttSettings(
            hostname='test.mosquitto.org', port=8883, cert_dir=TEST_DATA_DIR,
            topic_req="squeeze-req-%s" % uid,
            topic_resp="squeeze-resp-%s" % uid)
        return test_mqtt_settings
