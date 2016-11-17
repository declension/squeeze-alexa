import socket
from pprint import pprint

import ssl

print_d = print_w = pprint


class SslCommsMixin(object):
    _MAX_FAILURES = 3

    def __init__(self, hostname, port=9090,
                 ca_file=None,
                 cert_file=None):

        super(SslCommsMixin, self).__init__()
        self.failures = 0
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.check_hostname = False
        try:
            if ca_file:
                context.load_verify_locations(ca_file)
            if cert_file:
                context.verify_mode = ssl.CERT_REQUIRED
                context.load_cert_chain(cert_file)
        except IOError as e:
            print_d("Problem loading Cert/CA files at %s or %s (%s)" %
                    (ca_file, cert_file, e))
            raise e

        self._ssl_sock = context.wrap_socket(socket.socket(),
                                             server_hostname=hostname)
        self._ssl_sock.connect((hostname, port))
        self.is_connected = True

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
                eof = response.count("\n") == num_lines
            return response
        except socket.error as e:
            print_d("Couldn't communicate with Squeezebox (%s)" % e)
            self.failures += 1
            if self.failures >= self._MAX_FAILURES:
                print_w("Too many Squeezebox failures. Disconnecting")
                self.is_connected = False
            return None
