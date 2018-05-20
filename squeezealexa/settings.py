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

from os.path import join

from squeezealexa import ROOT_DIR, Settings

"""
This file contains settings with everything set to the defaults
At the very least you need to set SERVER_HOSTNAME, SERVER_SSL_PORT.
"""


# --------------------------- Amazon / Alexa Config ---------------------------

APPLICATION_ID = None
"""The Skill's Amazon application ID (e.g. amznl.ask.skill.xyz...) as a string
A value of None means verification of the request's Skill will be disabled.
"""

LOCALE = 'en_US'
"""The locale (language & region) to use for your app,
e.g. en_GB.UTF-8, or de_DE"""

RESPONSE_AUDIO_FILE_URL = \
    "https://s3.amazonaws.com/declension-alexa-media/silence.mp3"
"""Change this to your own HTTPS MP3 file, which must be accessible to Alexa"""

# ----------------------------- Squeezebox Config -----------------------------

SERVER_HOSTNAME = 'my-squeezebox-cli-proxy.example.com'
"""The public hostname / IP of your Squeezebox server CLI proxy"""

SERVER_SSL_PORT = 19090
"""The above proxy server's listening port (that accepts TLS connections).
For stunnel, this will be the same as `accept = ...`"""

SERVER_USERNAME = None
"""A string containing the Squeezebox CLI username, or None if not required."""

SERVER_PASSWORD = None
"""A string containing the Squeezebox CLI password, or None if not required."""

DEFAULT_PLAYER = None
"""The default Squeezebox player ID (long MAC-like string) to use"""

DEBUG_LMS = False
"""Dump LMS CLI communication to log if True"""

USE_SPOKEN_ERRORS = True
"""If True, Alexa will response with squeeze-alexa error information.
Sometimes this is useful, sometimes it's definitely not what you want"""


# ------------------------- TLS (SSL) Configuration ---------------------------

CERT_FILE = 'squeeze-alexa.pem'
"""The PEM-format certificate filename for TLS verification,
or None to disable"""

CERT_DIR = join(ROOT_DIR, "etc", "certs")
"""The directory that certs can be found in"""

CERT_FILE_PATH = join(CERT_DIR, CERT_FILE) if CERT_FILE else None
"""The full path to the certificate file, usually under etc/"""

CA_FILE_PATH = CERT_FILE_PATH
"""The certificate authority file, in .pem.
This can be the same as the CERT_FILE_PATH if you're self-certifying."""

VERIFY_SERVER_HOSTNAME = bool(CERT_FILE_PATH)
"""Whether to verify the server's TLS certificate hostname.
Override to False if your certificate is for a different domain from your
SERVER_HOSTNAME."""


# ------------------------------- MQTT Settings -------------------------------


class MqttSettings(Settings):
    hostname = 'aorobo3koaq53.iot.eu-west-1.amazonaws.com'
    """The hostname for the Internet MQTT server (for MQTT mode)
    e.g. "xxxxxxxxxxxxx.iot.eu-west-1.amazonaws.com
    Leaving this blank will disable MQTT mode"""

    port = 8883
    """The (TLS) port the above server is listening on. 8883 is default"""

    cert_dir = CERT_DIR
    """Where the AWS IoT certificate / key files are kept"""

    internal_server_hostname = "192.168.1.9"
    """The LAN-side hostname for your Squeezeserver
    e.g. my-nas or 192.168.1.100"""

    internal_cli_port = 9090
    """The LAN-side port for your Squeezserver CLI, defaults to 9090"""

    topic_req = 'squeeze-req'
    """The MQTT topic for incoming messages (from squeeze-alexa Lambda)"""

    topic_resp = 'squeeze-resp'
    """The MQTT topic for outgoing messages (back to squeeze-alexa Lambda)"""

    @classmethod
    @property
    def configured(cls) -> bool:
        """Whether the settings are configured"""
        return bool(cls.hostname and cls.port and
                    cls.topic_req and cls.topic_resp)


MQTT_SETTINGS = MqttSettings()
