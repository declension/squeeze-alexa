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


# --------------------------- App (Skill) Settings ----------------------------

class SkillSettings(Settings):
    APPLICATION_ID = None
    """The Skill's Amazon application ID (e.g. "amznl.ask.skill.xyz")
    A value of None means verification of the request's Skill will be disabled.
    """

    LOCALE = 'en_US'
    """The locale (language & region) to use for your app,
    e.g. en_GB.UTF-8, or de_DE"""

    RESPONSE_AUDIO_FILE_URL = \
        'https://s3.amazonaws.com/declension-alexa-media/silence.mp3'
    """Change this to your own HTTPS MP3, which must be accessible to Alexa"""

    USE_SPOKEN_ERRORS = True
    """If True, Alexa will response with squeeze-alexa error information.
    Sometimes this is useful, sometimes it's definitely not what you want"""

    CERT_DIR = join(ROOT_DIR, "etc", "certs")
    """The directory that certs can be found in"""


# ----------------------- LMS (SqueezeServer) Settings ------------------------

class LmsSettings(Settings):
    CLI_PORT = 9090
    """The LAN-side port for your Squeezeserver CLI, defaults to 9090"""

    USERNAME = None
    """A string containing the CLI username, or None if not required."""

    PASSWORD = None
    """A string containing the CLI password, or None if not required."""

    DEFAULT_PLAYER = None
    """The default player ID (long MAC-like string) to use"""

    DEBUG = False
    """Dump LMS CLI communication to log if True"""


# -------------------------- SSL Transport Settings ---------------------------

class SslSettings(Settings):

    SERVER_HOSTNAME = 'my-squeezebox-cli-proxy.example.com'
    """The public hostname / IP of your Squeezebox server CLI proxy"""

    PORT = 19090
    """The above proxy server's listening port (that accepts TLS connections).
    For stunnel, this will be the same as `accept = ...`"""

    CERT_FILE = 'squeeze-alexa.pem'
    """The PEM-format certificate filename for TLS verification,
    or None to disable"""

    CERT_FILE_PATH = (join(SkillSettings.CERT_DIR, CERT_FILE)
                      if CERT_FILE else None)
    """The full path to the certificate file, usually under etc/"""

    CA_FILE_PATH = CERT_FILE_PATH
    """The certificate authority file, in .pem.
    This can be the same as the CERT_FILE_PATH if you're self-certifying."""

    VERIFY_SERVER_HOSTNAME = bool(CERT_FILE_PATH)
    """Whether to verify the server's TLS certificate hostname.
    Override to False if your certificate is for a different domain from your
    SERVER_HOSTNAME."""


# -------------------------- MQTT Transport Settings --------------------------

class MqttSettings(Settings):

    HOSTNAME = ''
    """The hostname for the Internet MQTT server (for MQTT mode)
    e.g. "xxxxxxxxxxxxx.iot.eu-west-1.amazonaws.com
    Leaving this blank will disable MQTT mode"""

    PORT = 8883
    """The (TLS) port the above server is listening on. 8883 is default"""

    CERT_DIR = SkillSettings.CERT_DIR
    """Where the AWS IoT certificate / key files are kept"""

    INTERNAL_SERVER_HOSTNAME = '192.168.1.9'
    """The LAN-side hostname for your Squeezeserver
    e.g. my-nas or 192.168.1.100"""

    TOPIC_REQ = 'squeeze-req'
    """The MQTT topic for incoming messages (from squeeze-alexa Lambda)"""

    TOPIC_RESP = 'squeeze-resp'
    """The MQTT topic for outgoing messages (back to squeeze-alexa Lambda)"""

    def __init__(self, hostname=HOSTNAME, port=PORT, cert_dir=CERT_DIR,
                 internal_server_hostname=INTERNAL_SERVER_HOSTNAME,
                 topic_req=TOPIC_REQ, topic_resp=TOPIC_RESP):
        # Do these explicitly to allow us to override by name
        self.hostname = hostname
        self.cert_dir = cert_dir
        self.port = port
        self.internal_server_hostname = internal_server_hostname
        self.topic_req = topic_req
        self.topic_resp = topic_resp


    @property
    def configured(self):
        """Whether the settings are configured"""
        return bool(self.hostname and self.port and
                    self.topic_req and self.topic_resp)


# Singletons for lazy^W easy importing

SSL_SETTINGS = SslSettings()

SKILL_SETTINGS = SkillSettings()

LMS_SETTINGS = LmsSettings()

MQTT_SETTINGS = MqttSettings()
