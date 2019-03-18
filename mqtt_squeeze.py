#!/usr/bin/env python3
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


import socket
import sys
import telnetlib
from logging import getLogger, basicConfig, DEBUG, INFO
from os.path import dirname, abspath
import paho
import paho.mqtt.client as mqtt

# Sort out running directly
path = dirname(dirname(abspath(__file__)))
sys.path.append(path)

basicConfig(level=INFO, format="[{levelname:7s}] {message}", style="{")
logger = getLogger(__name__)
logger.setLevel(DEBUG)

from squeezealexa.settings import MQTT_SETTINGS, LMS_SETTINGS
from squeezealexa.transport.mqtt import CustomClient

telnet = None


def on_connect(client, data, flags, rc):
    logger.info("Connection status: %s", mqtt.error_string(rc))
    client.subscribe(MQTT_SETTINGS.topic_req, qos=1)


def on_subscribe(client, data, mid, granted_qos):
    logger.info("Subscribed to %s @ QOS %s. Ready to go!",
                MQTT_SETTINGS.topic_req, granted_qos[0])


def on_message(client, userdata, message):
    num_lines = message.payload.count(b'\n')
    msg = message.payload.decode('utf-8')
    if MQTT_SETTINGS.debug:
        logger.debug(">>> %s (@QoS %s)", msg.strip(), message.qos)
    telnet.write(message.payload.strip() + b'\n')
    resp_lines = []
    while len(resp_lines) < num_lines:
        resp_lines.append(telnet.read_until(b'\n').strip())

    rsp = b'\n'.join(resp_lines)
    if rsp:
        if MQTT_SETTINGS.debug:
            logger.debug("<<< %s", rsp.decode('utf-8'))
        client.publish(MQTT_SETTINGS.topic_resp, rsp, qos=1)
    else:
        logger.warning("No reply")


def connect_cli():
    global telnet
    telnet = telnetlib.Telnet(host=MQTT_SETTINGS.internal_server_hostname,
                              port=LMS_SETTINGS.cli_port, timeout=5)
    logger.info("Connected to the LMS CLI.")
    return telnet


if __name__ == "__main__":
    logger.debug("paho-mqtt %s", paho.mqtt.__version__)
    logger.debug("Checking MQTT configuration")
    if not MQTT_SETTINGS.configured:
        logger.error("MQTT transport not configured. Check your settings")
        exit(1)
    try:
        telnet = connect_cli()
    except socket.timeout as e:
        logger.error("Couldn't connect to LMS CLI using %s (%s)",
                     MQTT_SETTINGS, e)
        exit(3)
    else:
        client = CustomClient(MQTT_SETTINGS)
        client.enable_logger()
        client.on_connect = on_connect
        client.on_subscribe = on_subscribe
        client.on_message = on_message
        logger.debug("Connecting to MQTT endpoint")
        client.connect()
        logger.debug("Starting MQTT client loop")
        # Continue the network loop
        client.loop_forever(retry_first_connection=False)
    finally:
        if telnet:
            telnet.close()
        logger.info("Exiting")
