# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

from os.path import dirname, join

"""
This file contains settings with everything set to the defaults
At the very least you need to set SERVER_HOSTNAME, SERVER_PORT and CERT_FILE.
"""


############################# Amazon / Alexa Config ###########################

APPLICATION_ID = None
"""The Skill's Amazon application ID (e.g. amznl.ask.skill.xyz...) as a string
A value of None means verification of the request's Skill will be disabled.
"""


############################## Squeezebox Config ##############################

SERVER_HOSTNAME = 'my-squeezebox-cli-proxy.example.com'
"""The public hostname / IP of your Squeezebox server CLI proxy"""

SERVER_PORT = 9090
"""The above server's port"""

SERVER_USERNAME = None
"""A string containing the Squeezebox CLI username, or None if not required."""

SERVER_PASSWORD = None
"""A string containing the Squeezebox CLI password, or None if not required."""

DEFAULT_PLAYER = None
"""The default Squeezebox player ID (long MAC-like string) to use"""



########################### TLS (SSL) Configuration ###########################

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
