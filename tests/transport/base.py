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

import ssl
import threading
from os.path import join
from socketserver import TCPServer, BaseRequestHandler

from squeezealexa.utils import print_d
from tests.utils import TEST_DATA_DIR


class CertFiles:
    CERT_AND_KEY = join(TEST_DATA_DIR, 'cert-and-key.pem')
    LOCALHOST_CERT_AND_KEY = join(TEST_DATA_DIR, 'broker-certificate.pem.crt')
    BAD_HOSTNAME = join(TEST_DATA_DIR, 'bad-hostname.pem')
    CERT_ONLY = join(TEST_DATA_DIR, 'cert-only.pem')


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
