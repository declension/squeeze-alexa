# -*- coding: utf-8 -*-
# Copyright 2016 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

from __future__ import print_function
import socket

import ssl
import _ssl

print_d = print_w = print


class Error(Exception):
    pass


class SslSocketWrapper(object):
    _MAX_FAILURES = 3

    def __init__(self, hostname, port=9090,
                 ca_file=None, cert_file=None,
                 verify_hostname=False):

        self.hostname = hostname
        self.port = port
        self.failures = 0
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        self.harden_context(context)
        try:
            if ca_file:
                context.load_verify_locations(ca_file)
            if cert_file:
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = verify_hostname
                context.load_cert_chain(cert_file)
        except ssl.SSLError as e:
            print_d("Problem with Cert/CA (+key) files (%s). "
                    "Does it include the private key?" % e)
            raise e
        except IOError as e:
            print_d("Problem loading Cert/CA files at %s or %s (%s)" %
                    (ca_file, cert_file, e))
            raise e

        self._ssl_sock = context.wrap_socket(socket.socket(),
                                             server_hostname=hostname)
        try:
            self._ssl_sock.connect((hostname, port))
        except (ssl.SSLError, socket.gaierror):
            print_w("Couldn't connect to %s with TLS" % (self,))
            raise
        peer_cert = self._ssl_sock.getpeercert()
        if peer_cert is None:
            raise Error("No certificate configured at %s" % self)
        elif not peer_cert:
            print_w("Unvalidated server cert at %s" % self)
        else:
            print_d("Validated cert for %s" % (peer_cert['subject'],))
        self.is_connected = True

    @staticmethod
    def harden_context(context):
        # disallow ciphers with known vulnerabilities
        context.set_ciphers(ssl._RESTRICTED_SERVER_CIPHERS)
        # Prefer the server's ciphers by default so that we get stronger
        # encryption
        context.options |= getattr(_ssl, "OP_CIPHER_SERVER_PREFERENCE", 0)
        # Use single use keys in order to improve forward secrecy
        context.options |= getattr(_ssl, "OP_SINGLE_DH_USE", 0)
        context.options |= getattr(_ssl, "OP_SINGLE_ECDH_USE", 0)

    def communicate(self, data, wait=True):
        eof = False
        response = ''
        num_lines = data.count("\n")
        try:
            self._ssl_sock.sendall(data)
            if not wait:
                return None
            while not eof:
                response += self._ssl_sock.recv()
                eof = response.count("\n") == num_lines or not response
            return response
        except socket.error as e:
            print_d("Couldn't communicate with Squeezebox (%s)" % e)
            self.failures += 1
            if self.failures >= self._MAX_FAILURES:
                print_w("Too many Squeezebox failures. Disconnecting")
                self.is_connected = False
            return None

    def __str__(self):
        return "{hostname}:{port}".format(**self.__dict__)
