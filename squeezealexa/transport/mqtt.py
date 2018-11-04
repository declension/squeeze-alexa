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
import ssl
from _ssl import PROTOCOL_TLSv1_2
from glob import glob
from os.path import dirname, realpath, join
from typing import Union

from paho.mqtt.client import Client, MQTT_ERR_SUCCESS, error_string, \
    MQTT_ERR_INVAL

from squeezealexa.settings import MqttSettings
from squeezealexa.transport.base import Transport, Error, check_listening
from squeezealexa.utils import print_d, wait_for

BASE = realpath(join(dirname(__file__), "..", ".."))


class CustomClient(Client):
    """Opinionated Client subclass that configures from passed settings,
    and also does some safety checks"""

    def __init__(self, settings: MqttSettings):
        super().__init__()
        self.settings = settings
        self._host = settings.hostname
        self._port = settings.port
        self._configure_tls()
        self.connected = False

    def _configure_tls(self):
        self.tls_set(certfile=self._conf_file_of("*-certificate.pem.crt"),
                     keyfile=self._conf_file_of("*-private.pem.key"),
                     tls_version=PROTOCOL_TLSv1_2)

    def connect(self, host=None, port=None, keepalive=30, bind_address=""):
        host = host or self._host
        port = port or self._port

        check_listening(host, port, msg="check your MQTT settings")
        try:
            ret = super().connect(host=self._host,
                                  port=self._port,
                                  keepalive=keepalive,
                                  bind_address=bind_address)
        except ssl.SSLError as e:
            if 'SSLV3_ALERT_CERTIFICATE_UNKNOWN' in str(e):
                raise Error("Certificate problem with MQTT. "
                            "Is the certificate enabled in AWS?")
        else:
            if MQTT_ERR_SUCCESS == ret:
                print_d("Connecting to {settings}", settings=self.settings)
                self.connected = True
                return ret
        raise Error("Couldn't connect to {settings}".format(
            settings=self.settings))

    def disconnect(self):
        ret = super().disconnect()
        self.connected = False
        return ret

    def _conf_file_of(self, rel_glob: str) -> str:
        full_glob = os.path.join(self.settings.cert_dir, rel_glob)
        results = glob(full_glob)
        try:
            return results[0]
        except IndexError:
            raise Error("Can't find {glob} within dir {base}".format(
                base=self.settings.cert_dir, glob=rel_glob))

    def __del__(self):
        print_d("Disconnecting {what}", what=self)
        self.disconnect()
        self.loop_stop()

    def __str__(self) -> str:
        return "client to {host}:{port}".format(host=self._host,
                                                port=self._port)


class MqttTransport(Transport):
    """Transport over TLS-encrypted MQTT"""

    def __init__(self, client: CustomClient, req_topic: str, resp_topic: str):
        def subscribed(client, userdata, mind, granted_qos):
            self.is_connected = True
            print_d("MQTT/TLS transport to {client} initialised. (@QoS {qos})",
                    client=client, qos=granted_qos)

        super().__init__()
        self.client = client
        self.req_topic = req_topic
        self.resp_topic = resp_topic
        self.client.on_subscribe = subscribed
        self.client.on_message = self._on_message
        self.message = []
        print_d("Created transport: {self!r}", self=self)

    def start(self):
        def connected(client, userdata, flags, rc):
            print_d("Connected to {client}. Subscribing to {topic}",
                    client=self.client, topic=self.resp_topic)
            result, mid = self.client.subscribe(self.resp_topic, qos=1)
            if result != MQTT_ERR_SUCCESS:
                raise Error("Couldn't subscribe to '{topic}'", self.resp_topic)

        def disconnected(client, userdata, rc):
            print_d("Disconnected from {client}", client=self.client)
            self.is_connected = False

        self.is_connected = self.client.connected
        if self.is_connected:
            print_d("Already connected, great!")
            return
        self.client.on_connect = connected
        self.client.on_disconnect = disconnected
        assert self.client.loop_start() != MQTT_ERR_INVAL
        self.client.connect()
        wait_for(lambda s: s.is_connected, what="connection", context=self)
        return self

    def _on_message(self, client, userdata, message):
        self.response_lines += message.payload.splitlines()

    @property
    def details(self):
        return "MQTT to {client}".format(client=self.client)

    def communicate(self, raw: str, wait=True, timeout=5) -> Union[str, None]:
        data = raw.strip() + '\n'
        num_lines = data.count('\n')
        self._clear()
        ret = self.client.publish(self.req_topic, data.encode('utf-8'),
                                  qos=1 if wait else 0)
        if not wait:
            return None
        ret.wait_for_publish()
        if ret.rc != MQTT_ERR_SUCCESS:
            msg = "Error publishing message: {err}".format(
                err=error_string(ret.rc))
            raise Error(msg)
        print_d("Published to {topic} OK. Waiting for {num} line(s)...",
                topic=self.req_topic, num=num_lines)

        wait_for(lambda s: len(s.response_lines) >= num_lines, context=self,
                 what="response from mqtt-squeeze", timeout=timeout,
                 exc_cls=Error)
        return "\n".join(m.decode('utf-8') for m in self.response_lines)

    def _clear(self):
        self.response_lines = []

    def stop(self):
        print_d("Killing {what}...", what=self)
        print_d("Unsubscribing from '{topic}'", topic=self.resp_topic)
        self.client.on_message = None
        self.client.on_subscribe = None
        self.client.unsubscribe(self.resp_topic)
        self.client.disconnect()
        return super().stop()

    def __del__(self):
        self.stop()
