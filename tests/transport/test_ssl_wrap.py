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

import os
import ssl
import threading
from os.path import dirname
from socketserver import TCPServer, BaseRequestHandler
from unittest import TestCase

import pytest

import squeezealexa.transport.base
from squeezealexa.transport.ssl_wrap import SslSocketTransport
from squeezealexa.utils import print_d

TEST_DATA = os.path.join(dirname(__file__), '..', 'data')


class CertFiles:
    CERT_AND_KEY = os.path.join(TEST_DATA, 'cert-and-key.pem')
    BAD_HOSTNAME = os.path.join(TEST_DATA, 'bad-hostname.pem')
    CERT_ONLY = os.path.join(TEST_DATA, 'cert-only.pem')


def response_for(request):
    return "%s, or something!\n" % request.strip()


class FakeRequestHandler(BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(1024).decode('utf-8')
        except UnicodeDecodeError:
            data = "(invalid)"
        response = response_for(data)
        print_d("> \"%s\"\n%s" % (data.strip(), response))
        self.request.sendall(response.encode('utf-8'))


class TestSslWrap(TestCase):

    def test_with_real_server(self):
        with ServerResource() as server:
            sslw = SslSocketTransport('', port=server.port,
                                      cert_file=CertFiles.CERT_AND_KEY,
                                      ca_file=CertFiles.CERT_AND_KEY)
            assert sslw.is_connected
            response = sslw.communicate('HELLO\n')
            assert response == response_for("HELLO")

    def test_no_ca(self):
        with ServerResource() as server:
            with pytest.raises(squeezealexa.transport.base.Error) as exc:
                SslSocketTransport('', port=server.port,
                                   cert_file=CertFiles.CERT_AND_KEY)
            assert 'cert not trusted' in exc.value.message.lower()

    def test_cert_no_key(self):
        with pytest.raises(squeezealexa.transport.base.Error) as exc:
            SslSocketTransport('', port=0, cert_file=CertFiles.CERT_ONLY)
        assert 'include the private key' in exc.value.message.lower()

    def test_missing_cert(self):
        with pytest.raises(squeezealexa.transport.base.Error) as exc:
            SslSocketTransport('', port=0, cert_file="not.there",
                               ca_file='ca.not.there')
        assert "can't find 'ca.not.there'" in exc.value.message.lower()

    def test_bad_hostname(self):
        with pytest.raises(squeezealexa.transport.base.Error) as exc:
            SslSocketTransport('zzz.qqq', port=0)
        msg = exc.value.message.lower()
        assert "unknown host" in msg
        assert "zzz.qqq" in msg

    def test_cert_bad_hostname(self):
        with ServerResource() as server:
            with pytest.raises(squeezealexa.transport.base.Error) as exc:
                SslSocketTransport('', port=server.port,
                                   cert_file=CertFiles.BAD_HOSTNAME)
            assert 'right hostname' in exc.value.message.lower()

    def test_wrong_port(self):
        with ServerResource(tls=False) as server:
            with pytest.raises(squeezealexa.transport.base.Error) as exc:
                SslSocketTransport('', port=server.port)
            msg = exc.value.message.lower()
            assert ('not tls on port %d' % server.port) in msg

    def test_bad_port(self):
        with pytest.raises(squeezealexa.transport.base.Error) as exc:
            SslSocketTransport('localhost', port=12345,
                               cert_file=CertFiles.CERT_AND_KEY)
        message = exc.value.message.lower()
        assert 'nothing listening on localhost:12345.' in message

    def test_timeout(self):
        with TimeoutServer() as server:
            with pytest.raises(squeezealexa.transport.base.Error) as exc:
                SslSocketTransport('', port=server.port,
                                   cert_file=CertFiles.CERT_AND_KEY,
                                   ca_file=CertFiles.CERT_AND_KEY,
                                   timeout=1)
            assert "check the server setup and the firewall" in str(exc)


class ServerResource(TCPServer, object):

    def __init__(self, tls=True):
        super(ServerResource, self).__init__(('', 0), FakeRequestHandler)
        if tls:
            self.socket = ssl.wrap_socket(self.socket,
                                          cert_reqs=ssl.CERT_REQUIRED,
                                          certfile=CertFiles.CERT_AND_KEY,
                                          ca_certs=CertFiles.CERT_AND_KEY,
                                          server_side=True)
        self.socket.settimeout(5)

    @property
    def port(self):
        return self.socket.getsockname()[1]

    def __enter__(self):
        self.socket.settimeout(3)
        print_d("Creating test TCP server")
        self.thread = threading.Thread(target=self.serve_forever)

        print_d("Starting test server")
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        print_d("Destroyed test server")
        self.thread.join(1)


class TimeoutServer(ServerResource):

    def __init__(self):
        super(TimeoutServer, self).__init__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
