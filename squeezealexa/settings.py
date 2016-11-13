# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import os
from os.path import dirname

SERVER_HOSTNAME = 'my-vera-server.example.com'
"""The public hostname / IP of your Vera CLI server"""

SERVER_PORT = 9090
"""The above Vera server's CLI port (default: 9090)"""

CERT_FILE = 'my-cert-file.pem'
"""The .pem certification file for TLS signing"""

CERT_FILE_PATH = os.path.join(dirname(dirname(__file__)), CERT_FILE)
"""The certificate file, in .pem format."""

CA_FILE_PATH = CERT_FILE_PATH
"""The certificate authority file, in .pem.
This can be the same as the CERT_FILE_PATH if you're self-certifying."""

APPLICATION_ID = None
"""The Amazon application ID (e.g. amznl.ask.skill.xyz...)"""

DEFAULT_PLAYER = None
"""The default Squeezebox player ID (string) to use"""
