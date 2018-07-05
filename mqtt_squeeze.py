#!/usr/bin/env python3
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


import socket
import sys
import telnetlib
from os.path import dirname, abspath

import paho.mqtt.client as mqtt

# Sort out running directly
path = dirname(dirname(abspath(__file__)))
sys.path.append(path)

from squeezealexa.settings import MQTT_SETTINGS, LMS_SETTINGS
from squeezealexa.transport.mqtt import CustomClient
from squeezealexa.utils import print_d, print_w

telnet = None
DEBUG = True


def on_connect(client, data, flags, rc):
    print_d("Connect: {msg}", msg=mqtt.error_string(rc))
    client.subscribe(MQTT_SETTINGS.topic_req, qos=1)


def on_subscribe(client, data, mid, granted_qos):
    print_d("Subscribed to {topic} @ QOS {granted_qos})",
            topic=MQTT_SETTINGS.topic_req, **locals())


def on_message(client, userdata, message):
    num_lines = message.payload.count(b'\n')
    msg = message.payload.decode('utf-8')
    if DEBUG:
        print_d(">>> {msg} (@QoS {qos})", msg=msg.strip(), qos=message.qos)
    telnet.write(message.payload.strip() + b'\n')
    resp_lines = []
    while len(resp_lines) < num_lines:
        resp_lines.append(telnet.read_until(b'\n').strip())

    rsp = b'\n'.join(resp_lines)
    if rsp:
        if DEBUG:
            print_d("<<< {}", rsp.decode('utf-8'))
        client.publish(MQTT_SETTINGS.topic_resp, rsp, qos=1)
    else:
        print_d("No reply")


def connect_cli():
    global telnet
    telnet = telnetlib.Telnet(host=MQTT_SETTINGS.internal_server_hostname,
                              port=LMS_SETTINGS.cli_port, timeout=5)
    print_d("Connected to Squeezeserver CLI")
    return telnet


if __name__ == "__main__":

    if not MQTT_SETTINGS.configured:
        print("MQTT transport not configured. Check your settings")
        exit(1)
    try:
        telnet = connect_cli()
    except socket.timeout as e:
        print_w("Couldn't connect to Squeeze CLI using {} ({})",
                MQTT_SETTINGS, e)
        exit(3)
    else:
        client = CustomClient(MQTT_SETTINGS)
        client.on_connect = on_connect
        client.on_subscribe = on_subscribe
        client.on_message = on_message
        client.connect()

        # Continue the network loop
        client.loop_forever(retry_first_connection=True)
    finally:
        if telnet:
            telnet.close()
