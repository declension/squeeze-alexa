# -*- coding: utf-8 -*-
#
#   Copyright 2017-2018 Nick Boultbee
#   This file is part of squeeze-alexa.
#
#   squeeze-alexa is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   See LICENSE for full license

import socket

import ssl
import _ssl

from squeezealexa.utils import print_d, print_w


class Error(Exception):

    def __init__(self, msg, e):
        super(Error, self).__init__(msg)
        self.message = msg
        self.__cause__ = e


class SslSocketWrapper(object):
    _MAX_FAILURES = 3

    def __init__(self, hostname, port=9090,
                 ca_file=None, cert_file=None,
                 verify_hostname=False):

        self.hostname = hostname
        self.port = port
        self.failures = 0
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        self.__harden_context(context)
        try:
            if ca_file:
                context.load_verify_locations(ca_file)
            if cert_file:
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = verify_hostname
                context.load_cert_chain(cert_file)
        except ssl.SSLError as e:
            raise Error("Problem with Cert / CA (+key) files ({} / {}). "
                        "Does it include the private key?"
                        .format(cert_file, ca_file), e)
        except IOError as e:
            if 'No such file or directory' in e.strerror:
                self._die("Can't find '{ca_file}'. "
                          "Check CERT_NAME / CERT_PATH in settings"
                          .format(ca_file=ca_file))
            self._die("could be mismatched certificate files, "
                      "or wrong hostname in cert."
                      "Check CERT_FILE and certs on server too.", e)

        self._ssl_sock = context.wrap_socket(socket.socket(),
                                             server_hostname=hostname)
        print_d("Connecting to {port}", port=port)
        try:
            self._ssl_sock.connect((hostname, port))
        except socket.gaierror as e:
            if "Name or service not know" in e.strerror:
                self._die("unknown host ({}) - check SERVER_HOSTNAME"
                          .format(hostname), e)
            self._die("Couldn't connect to %s with TLS" % (self,), e)
        except IOError as e:
            if 'Connection refused' in e.strerror:
                self._die("nothing listening on {}"
                          "Check settings, or (re)start server.".format(self))
            elif 'WRONG_VERSION_NUMBER' in e.strerror:
                self._die('probably not TLS on port {} - '
                          'wrong SERVER_PORT maybe?'.format(port),
                          e)
            elif 'Connection reset by peer' in e.strerror:
                self._die("server killed the connection - handshake error? "
                          "Check the SSL tunnel logs")
            elif 'CERTIFICATE_VERIFY_FAILED' in e.strerror:
                self._die("Cert not trusted by / from server. "
                          "Is your CA correct? Is the cert expired? "
                          "Is the cert for the right hostname ({})?"
                          .format(hostname), e)
            self._die("Connection problem ({})".format(e.strerror))

        peer_cert = self._ssl_sock.getpeercert()
        if peer_cert is None:
            self._die("No certificate configured at {}".format(self))
        elif not peer_cert:
            print_w("Unvalidated server cert at {}", self)
        else:
            subject_data = peer_cert['subject']
            try:
                data = {k: v for d in subject_data for k, v in d}
            except Exception:
                data = subject_data
            print_d("Validated cert for {}", data)
        self.is_connected = True

    def _die(self, msg, e=None):
        raise Error(msg, e)

    @staticmethod
    def __harden_context(context):
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
            self._ssl_sock.sendall(data.encode('utf-8'))
            if not wait:
                return None
            while not eof:
                response += self._ssl_sock.recv().decode('utf-8')
                eof = response.count("\n") == num_lines or not response
            return response
        except socket.error as e:
            print_d("Couldn't communicate with Squeezebox ({!r})", e)
            self.failures += 1
            if self.failures >= self._MAX_FAILURES:
                print_w("Too many Squeezebox failures. Disconnecting")
                self.is_connected = False
            return None

    def __str__(self):
        return "{hostname}:{port}".format(**self.__dict__)
