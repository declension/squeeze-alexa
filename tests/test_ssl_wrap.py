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

import pytest

from squeezealexa import ssl_wrap
from squeezealexa.ssl_wrap import SslSocketWrapper
from squeezealexa.utils import print_d, PY2
if PY2:
    from SocketServer import TCPServer, BaseRequestHandler
else:
    from socketserver import TCPServer, BaseRequestHandler


TEST_DATA = os.path.join(dirname(__file__), 'data')


class CertFiles:
    CERT_AND_KEY = os.path.join(TEST_DATA, 'cert-and-key.pem')
    BAD_HOSTNAME = os.path.join(TEST_DATA, 'bad-hostname.pem')
    CERT_ONLY = os.path.join(TEST_DATA, 'cert-only.pem')


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
        with ServerResource() as server:
            sslw = SslSocketWrapper('', port=server.port,
                                    cert_file=CertFiles.CERT_AND_KEY,
                                    ca_file=CertFiles.CERT_AND_KEY)
            assert sslw.is_connected
            response = sslw.communicate('HELLO\n')
            assert response == response_for("HELLO")

    def test_cert_no_key(self):
        with pytest.raises(ssl_wrap.Error) as exc:
            SslSocketWrapper('', port=0, cert_file=CertFiles.CERT_ONLY)
        assert 'include the private key' in exc.value.message.lower()

    def test_cert_bad_hostname(self):
        with ServerResource() as server:
            with pytest.raises(ssl_wrap.Error) as exc:
                SslSocketWrapper('', port=server.port,
                                 cert_file=CertFiles.BAD_HOSTNAME)
            assert 'right hostname' in exc.value.message.lower()

    def test_bad_port(self):
        with pytest.raises(ssl_wrap.Error) as exc:
            SslSocketWrapper('', port=12345,
                             cert_file=CertFiles.CERT_AND_KEY)
        message = exc.value.message.lower()
        assert 'nothing listening' in message
        assert '12345' in message


class ServerResource(TCPServer, object):

    def __init__(self):
        super(ServerResource, self).__init__(('', 0), FakeRequestHandler)
        self.socket = ssl.wrap_socket(self.socket,
                                      certfile=CertFiles.CERT_AND_KEY,
                                      server_side=True)
        self.socket.settimeout(1)

    @property
    def port(self):
        return self.socket.getsockname()[1]

    def __enter__(self):
        self.socket = ssl.wrap_socket(
            self.socket, certfile=CertFiles.CERT_AND_KEY,
            server_side=True)
        self.socket.settimeout(1)
        print_d("Creating test TCP server")
        self.thread = threading.Thread(target=self.serve_forever)

        print_d("Starting test server")
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        print_d("Destroyed test server")
        self.thread.join(1)
