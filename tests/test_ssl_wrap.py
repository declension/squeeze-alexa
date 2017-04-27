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

import os
import ssl
import threading
from os.path import dirname
from unittest import TestCase

from squeezealexa.ssl_wrap import SslSocketWrapper
from squeezealexa.utils import print_d, PY2
if PY2:
    from SocketServer import TCPServer, BaseRequestHandler
else:
    from socketserver import TCPServer, BaseRequestHandler


CERT_AND_KEY_FILE = os.path.join(dirname(__file__), 'data', 'cert-and-key.pem')


def response_for(request):
    return "%s, or something!\n" % request.strip()


class FakeRequestHandler(BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).decode('utf-8')
        response = response_for(data)
        print_d("> \"%s\"\n%s" % (data.strip(), response))
        self.request.sendall(response.encode('utf-8'))


class TestSslWrap(TestCase):
    def test_with_real_server(self):
        server = TCPServer(('', 0), FakeRequestHandler)
        server.socket = ssl.wrap_socket(server.socket,
                                        certfile=CERT_AND_KEY_FILE,
                                        server_side=True)
        server.socket.settimeout(1)
        print_d("Creating test HTTPS server")
        thread = threading.Thread(target=server.serve_forever)
        try:
            print_d("Starting test server")
            thread.start()
            sslw = SslSocketWrapper('', port=server.socket.getsockname()[1],
                                    cert_file=CERT_AND_KEY_FILE,
                                    ca_file=CERT_AND_KEY_FILE)
            assert sslw.is_connected
            print_d("Set up SSL wrapper")
            response = sslw.communicate('HELLO\n')
            assert response == response_for("HELLO")
        finally:
            server.shutdown()
            thread.join(1)
