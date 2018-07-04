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

from squeezealexa.transport.base import Error, Transport
from squeezealexa.utils import print_d, print_w


class SslSocketTransport(Transport):
    _MAX_FAILURES = 3

    def __init__(self, hostname, port=9090,
                 ca_file=None, cert_file=None,
                 verify_hostname=False,
                 timeout=5):

        self.hostname = hostname
        self.port = port
        self.timeout = timeout
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

        sock = socket.socket()
        sock.settimeout(self.timeout)
        self._ssl_sock = context.wrap_socket(sock,
                                             server_hostname=hostname)
        print_d("Connecting to port {port} on {hostname}",
                port=port, hostname=hostname or '(localhost)')
        try:
            self._ssl_sock.connect((hostname, port))
        except socket.gaierror as e:
            if "Name or service not know" in e.strerror:
                self._die("unknown host ({}) - check SERVER_HOSTNAME"
                          .format(hostname), e)
            self._die("Couldn't connect to %s with TLS" % (self,), e)
        except IOError as e:
            err_str = e.strerror or str(e)
            if 'Connection refused' in err_str:
                self._die("nothing listening on {}. "
                          "Check settings, or (re)start server.".format(self))
            elif 'WRONG_VERSION_NUMBER' in err_str:
                self._die('probably not TLS on port {} - '
                          'wrong SERVER_PORT maybe?'.format(port),
                          e)
            elif 'Connection reset by peer' in err_str:
                self._die("server killed the connection - handshake error? "
                          "Check the SSL tunnel logs")
            elif 'CERTIFICATE_VERIFY_FAILED' in err_str:
                self._die("Cert not trusted by / from server. "
                          "Is your CA correct? Is the cert expired? "
                          "Is the cert for the right hostname ({})?"
                          .format(hostname), e)
            elif 'timed out' in err_str:
                msg = ("Couldn't connect to port {port} on {host} - "
                       "check the server setup and the firewall."
                       ).format(host=self.hostname, port=self.port)
                self._die(msg)
            self._die("Connection problem ({}: {})".format(type(e).__name__,
                                                           err_str))

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
            if 'read operation timed out' in str(e):
                raise Error("Timed out waiting for CLI response. "
                            "Perhaps the tunnel endpoint is incorrect, "
                            "or the LMS CLI is down?")
            else:
                print_d("Couldn't communicate with Squeezebox ({!r})", e)
            self.failures += 1
            if self.failures >= self._MAX_FAILURES:
                print_w("Too many Squeezebox failures. Disconnecting")
                self.is_connected = False
            return None

    def details(self):
        return "{hostname}:{port} over SSL".format(**self.__dict__)

    def __del__(self):
        print_d("Closing {}", self)
        if hasattr(self, '_ssl_sock'):
            self._ssl_sock.close()
