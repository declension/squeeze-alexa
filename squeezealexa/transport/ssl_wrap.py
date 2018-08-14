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

    def __init__(self, hostname, port=9090, ca_file=None, cert_file=None,
                 verify_hostname=False, timeout=5):

        super().__init__()
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.failures = 0
        context = ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
        self.__harden_context(context)
        try:
            if ca_file:
                context.load_verify_locations(ca_file)
            if cert_file:
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = verify_hostname
                context.load_cert_chain(cert_file)
        except ssl.SSLError as e:
            self._die("Problem with Cert / CA (+key) files ({cert} / {ca}). "
                      "Does it include the private key? ({reason})",
                      cert=cert_file, ca=ca_file, reason=e.reason, err=e)
        except IOError as e:
            if 'No such file or directory' in e.strerror:
                self._die("Can't find cert '{cert_file}' or CA '{ca_file}'. "
                          "Check CERT_FILE / CA_FILE_PATH in settings",
                          ca_file=ca_file, cert_file=cert_file)
            self._die("could be mismatched certificate files, "
                      "or wrong hostname in cert."
                      "Check CERT_FILE and certs on server too.", e)

        sock = socket.socket()
        sock.settimeout(self.timeout)
        self._ssl_sock = context.wrap_socket(sock,
                                             server_hostname=hostname)

    def start(self):
        print_d("Connecting to port {port} on {hostname}",
                port=self.port, hostname=self.hostname or '(localhost)')
        try:
            self._ssl_sock.connect((self.hostname, self.port))
        except socket.gaierror as e:
            if "Name or service not know" in e.strerror:
                self._die("unknown host ({host}) - check SERVER_HOSTNAME",
                          host=self.hostname, err=e)
            self._die("Couldn't connect to {host} with TLS", host=self, err=e)
        except IOError as e:
            err_str = e.strerror or str(e)
            if 'Connection refused' in err_str:
                self._die("nothing listening on {this}. "
                          "Check settings, or (re)start server.", this=self)
            elif ('WRONG_VERSION_NUMBER' in err_str or
                  'unknown_protocol' in err_str):
                self._die('probably not TLS on port {port} - '
                          'wrong SERVER_PORT maybe?', port=self.port, err=e)
            elif 'Connection reset by peer' in err_str:
                self._die("server killed the connection - handshake error "
                          "(e.g. unsupported TLS protocol)? "
                          "Check the SSL tunnel logs")
            elif 'CERTIFICATE_VERIFY_FAILED' in err_str:
                self._die("Cert not trusted by / from server. "
                          "Is your CA correct? Is the cert expired? "
                          "Is the cert for the right hostname ({host})?",
                          host=self.hostname, err=e)
            elif 'timed out' in err_str:
                self._die("Couldn't connect to port {port} on {host} - "
                          "check the server setup and the firewall.",
                          host=self.hostname, port=self.port)
            self._die("Connection problem ({type}: {text})",
                      type=type(e).__name__, text=err_str)

        peer_cert = self._ssl_sock.getpeercert()
        if peer_cert is None:
            self._die("No certificate configured at {details}", details=self)
        elif not peer_cert:
            print_w("Unvalidated server cert at {details}", details=self)
        else:
            subject_data = peer_cert['subject']
            try:
                data = {k: v for d in subject_data for k, v in d}
            except Exception:
                data = subject_data
            print_d("Validated cert for {data}", data=data)
        self.is_connected = True
        return self

    def _die(self, msg, err=None, **kwargs):
        raise Error(msg.format(**kwargs), err)

    @staticmethod
    def __harden_context(context):
        # disallow ciphers with known vulnerabilities
        context.set_ciphers(ssl._RESTRICTED_SERVER_CIPHERS)
        # Prefer the server's ciphers by default so that we get stronger
        # encryption
        context.options |= _ssl.OP_CIPHER_SERVER_PREFERENCE
        # Use single use keys in order to improve forward secrecy
        context.options |= _ssl.OP_SINGLE_DH_USE
        context.options |= _ssl.OP_SINGLE_ECDH_USE
        # Deny outdated protocols
        context.options |= _ssl.OP_NO_SSLv2
        context.options |= _ssl.OP_NO_SSLv3
        context.options |= _ssl.OP_NO_TLSv1

    def communicate(self, raw: str, wait=True) -> str:
        eof = False
        response = ''
        data = raw.strip() + '\n'
        num_lines = data.count('\n')
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
                print_d("Couldn't communicate with Squeezebox ({error!r})",
                        error=e)
            self.failures += 1
            if self.failures >= self._MAX_FAILURES:
                self.is_connected = False
                self._ssl_sock.close()
                raise Error("Too many Squeezebox failures. Disconnecting")
            return None

    @property
    def details(self):
        return "{hostname}:{port} over SSL".format(**self.__dict__)

    def stop(self):
        print_d("Closing {who}", who=self)
        if hasattr(self, '_ssl_sock'):
            self._ssl_sock.close()

    def __del__(self):
        self.stop()
