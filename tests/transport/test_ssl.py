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

from _socket import socket
from socket import error as SocketError
from unittest import TestCase

import pytest

from squeezealexa.transport.base import Error as TransportError
from squeezealexa.transport.ssl_wrap import SslSocketTransport
from tests.transport.base import ServerResource, TimeoutServer, CertFiles, \
    response_for


class FailingSocket(socket):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = False

    def sendall(self, data, flags=None):
        raise SocketError()

    def close(self):
        super().close()
        self.closed = True


class TestSslWrap(TestCase):

    def _working_transport(self, server):
        return SslSocketTransport('', port=server.port,
                                  cert_file=CertFiles.CERT_AND_KEY,
                                  ca_file=CertFiles.CERT_AND_KEY)

    def test_with_real_server(self):
        with ServerResource() as server:
            sslw = self._working_transport(server)
            assert sslw.is_connected
            response = sslw.communicate('HELLO')
            assert response == response_for("HELLO")

    def test_with_real_server_no_wait(self):
        with ServerResource() as server:
            sslw = self._working_transport(server)
            assert sslw.communicate('HELLO', wait=False) is None

    def test_with_real_server_failing_socket(self):
        with ServerResource() as server:
            transport = self._working_transport(server)
            transport._ssl_sock = FailingSocket()
            assert transport.is_connected
            assert not transport.communicate('HELLO')

    def test_failing_socket_raises_eventually(self):
        with ServerResource() as server:
            transport = self._working_transport(server)
            transport._ssl_sock = FailingSocket()
            assert transport.is_connected
            assert transport._MAX_FAILURES == 3
            assert not transport.communicate('HELLO')
            assert not transport.communicate('HELLO?')
            with pytest.raises(TransportError) as e:
                transport.communicate('HELLO??')
            assert "Too many Squeezebox failures" in str(e)
            assert transport._ssl_sock.closed

    def test_no_ca(self):
        with ServerResource() as server:
            with pytest.raises(TransportError) as exc:
                SslSocketTransport('', port=server.port,
                                   cert_file=CertFiles.CERT_AND_KEY)
            assert 'cert not trusted' in exc.value.message.lower()

    def test_cert_no_key(self):
        with pytest.raises(TransportError) as exc:
            SslSocketTransport('', port=0, cert_file=CertFiles.CERT_ONLY)
        assert 'include the private key' in exc.value.message.lower()

    def test_missing_cert(self):
        with pytest.raises(TransportError) as exc:
            SslSocketTransport('', port=0, cert_file="not.there",
                               ca_file='ca.not.there')
        assert "ca 'ca.not.there'" in exc.value.message.lower()

    def test_bad_hostname(self):
        with pytest.raises(TransportError) as exc:
            SslSocketTransport('zzz.qqq', port=0)
        msg = exc.value.message.lower()
        assert "unknown host" in msg
        assert "zzz.qqq" in msg

    def test_cert_bad_hostname(self):
        with ServerResource() as server:
            with pytest.raises(TransportError) as exc:
                SslSocketTransport('', port=server.port,
                                   cert_file=CertFiles.BAD_HOSTNAME)
            assert 'right hostname' in exc.value.message.lower()

    def test_wrong_port(self):
        with ServerResource(tls=False) as server:
            with pytest.raises(TransportError) as exc:
                SslSocketTransport('', port=server.port)
            msg = exc.value.message.lower()
            assert ('not tls on port %d' % server.port) in msg

    def test_bad_port(self):
        with pytest.raises(TransportError) as exc:
            SslSocketTransport('localhost', port=12345,
                               cert_file=CertFiles.CERT_AND_KEY)
        message = exc.value.message.lower()
        assert 'nothing listening on localhost:12345' in message

    def test_timeout(self):
        with TimeoutServer() as server:
            with pytest.raises(TransportError) as exc:
                SslSocketTransport('', port=server.port,
                                   cert_file=CertFiles.CERT_AND_KEY,
                                   ca_file=CertFiles.CERT_AND_KEY,
                                   timeout=1)
            assert "check the server setup and the firewall" in str(exc)
