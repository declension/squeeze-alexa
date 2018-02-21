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

from os.path import dirname, join

"""
This file contains settings with everything set to the defaults
At the very least you need to set SERVER_HOSTNAME, SERVER_SSL_PORT.
"""


# --------------------------- Amazon / Alexa Config ---------------------------

APPLICATION_ID = None
"""The Skill's Amazon application ID (e.g. amznl.ask.skill.xyz...) as a string
A value of None means verification of the request's Skill will be disabled.
"""

RESPONSE_AUDIO_FILE_URL = "https://www.dropbox.com/s/9o4urpbittfqmg9/silence.mp3?dl=1"
"""https://s3.amazonaws.com/declension-alexa-media/silence.mp3"""
"""Change this to your own HTTPS MP3 file, which must be accessible to Alexa"""

# ----------------------------- Squeezebox Config -----------------------------

SERVER_HOSTNAME = 'alldayflat.mywire.org'
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

# ------------------------- TLS (SSL) Configuration ---------------------------

CERT_FILE = 'squeeze-alexa.pem'
"""The PEM-format certificate filename for TLS verification,
or None to disable"""

CERT_FILE_PATH = (join(dirname(dirname(__file__)), CERT_FILE)
                  if CERT_FILE else None)
"""The full path to the certificate file"""

CA_FILE_PATH = CERT_FILE_PATH
"""The certificate authority file, in .pem.
This can be the same as the CERT_FILE_PATH if you're self-certifying."""

VERIFY_SERVER_HOSTNAME = bool(CERT_FILE_PATH)
"""Whether to verify the server's TLS certificate hostname.
Override to False if your certificate is for a different domain than your
SERVER_HOSTNAME."""

# ------------------------- Squeezealexa Configuration ---------------------------
LANGUAGE = "EN"
"""Possible Values:
   - EN: english
"""
