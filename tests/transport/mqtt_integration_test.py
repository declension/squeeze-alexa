# -*- coding: utf-8 -*-
#
#   Copyright 2017-19 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

import asyncio
from _ssl import PROTOCOL_TLSv1_2
from asyncio import ensure_future, IncompleteReadError
from datetime import datetime
from logging import getLogger
from threading import Thread
from time import time

import pytest
from hbmqtt.broker import Broker
from paho.mqtt.client import MQTT_ERR_INVAL, MQTTMessage, Client

from squeezealexa.settings import MqttSettings
from squeezealexa.transport.factory import TransportFactory
from squeezealexa.transport.mqtt import CustomClient
from squeezealexa.utils import wait_for
from tests.transport.base import CertFiles
from tests.utils import TEST_DATA_DIR

TEST_MSG = "TEST MESSAGE at %s" % datetime.now()
MQTT_LISTEN_PORT = 8883
BROKER_CONFIG = {
    'listeners': {
        'default': {
            'type': 'tcp',
            'ssl': 'on',
            'capath': CertFiles.LOCALHOST_CERT_AND_KEY,
            'certfile': CertFiles.LOCALHOST_CERT_AND_KEY,
            'keyfile': CertFiles.LOCALHOST_CERT_AND_KEY,
            'bind': '0.0.0.0:%d' % MQTT_LISTEN_PORT,
        }
    }
}

log = getLogger("tests")


class CustomTlsCustomClient(CustomClient):

    def __init__(self, settings: MqttSettings,
                 on_publish=None, on_connect=None, on_subscribe=None,
                 on_message=None):
        super().__init__(settings)
        self.on_connect = on_connect
        self.on_subscribe = on_subscribe
        self.on_publish = on_publish
        self.on_message = on_message
        self.connections = 0

    def _configure_tls(self):
        self.tls_set(ca_certs=CertFiles.LOCALHOST_CERT_AND_KEY,
                     tls_version=PROTOCOL_TLSv1_2)

    def connect(self, host=None, port=None, keepalive=30, bind_address=""):
        self.connections += 1
        return super().connect(host, port, keepalive, bind_address)


class QuietBroker(Broker):
    @asyncio.coroutine
    def stream_connected(self, reader, writer, listener_name):
        try:
            yield from super().stream_connected(reader, writer, listener_name)
        except IncompleteReadError as e:
            log.warning("Broker says: %s" % e)
            # It's annoying. https://github.com/beerfactory/hbmqtt/issues/119


class BrokerThread(Thread):
    """Thread to manage the asyncio-based HBMQTT MQTT Broker"""
    def __init__(self, broker, loop):
        super().__init__()
        self.loop = loop
        self.broker = broker

    async def run_loop(self):
        await self.broker.start()
        log.info("Started broker: %s", self.broker.config)

    def run(self):
        """Switch to new event loop and run forever"""
        log.info("Starting threaded event loop")
        asyncio.set_event_loop(self.loop)
        future = ensure_future(self.run_loop(), loop=self.loop)
        self.loop.create_task(future)
        self.loop.run_forever()

    def stop(self):
        self.loop.stop()

    def join(self, timeout=None):
        log.info("Stopping thread...")
        self.broker.shutdown()
        self.loop.stop()
        super().join(timeout)


@pytest.fixture
def mqtt_settings() -> MqttSettings:
    uid = time()
    return MqttSettings(
        hostname='localhost', port=MQTT_LISTEN_PORT,
        cert_dir=TEST_DATA_DIR,
        topic_req="squeeze-req-%s" % uid,
        topic_resp="squeeze-resp-%s" % uid)


@pytest.fixture
def client(mqtt_settings):
    client = CustomTlsCustomClient(mqtt_settings)
    yield client
    client.loop_stop()


@pytest.fixture
def transport(mqtt_settings, client):
    log.info("Creating transport for %s", client)
    factory = TransportFactory(ssl_config=None, mqtt_settings=mqtt_settings)
    transport = factory.create(mqtt_client=client)
    yield transport
    transport.stop()


@pytest.fixture(scope="module")
def broker():
    worker_loop = asyncio.new_event_loop()
    broker = QuietBroker(BROKER_CONFIG, plugin_namespace='tests',
                         loop=worker_loop)
    worker = BrokerThread(broker, worker_loop)
    worker.start()
    yield broker
    worker.stop()
    worker.join()


class TestLiveMqttTransport:

    def test_real_publishing(self, mqtt_settings, client, broker, transport):
        log.info("Broker running: %s", broker)
        self.published = []
        self.subscribed = False

        def on_message(client: Client, userdata, msg: MQTTMessage):
            msg = msg.payload.decode('utf-8').strip()
            client.publish(mqtt_settings.topic_resp,
                           "GOT: {m}".format(m=msg).encode('utf-8'))

        def on_subscribe(client, data, mid, granted_qos):
            self.subscribed = True

        def on_publish(client, userdata, mid):
            self.published.append(mid)

        client.on_publish = on_publish
        replier = CustomTlsCustomClient(mqtt_settings,
                                        on_subscribe=on_subscribe,
                                        on_message=on_message)
        replier.connect()
        transport.start()
        replier.subscribe(mqtt_settings.topic_req)
        assert replier.loop_start() != MQTT_ERR_INVAL
        wait_for(lambda x: self.subscribed,
                 what="confirming subscription", timeout=3)
        reply = transport.communicate(TEST_MSG, timeout=3)
        wait_for(lambda x: self.published,
                 what="confirming publish", timeout=3)
        assert len(self.published) == 1
        log.debug("Received reply: %s", reply)
        assert reply == "GOT: {msg}".format(msg=TEST_MSG)

    def test_over_connect(self, broker, client, transport):
        transport.start()
        wait_for(lambda t: t.is_connected, context=transport)
        transport.start()
        transport.start()
        assert client.connections == 1, "Over connected to MQTT"
