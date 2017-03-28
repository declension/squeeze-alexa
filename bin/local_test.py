#!/usr/bin/env python2
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

import sys
from _socket import gaierror
from os.path import dirname
from traceback import print_exc

sys.path.append(dirname(dirname(__file__)))

import ssl
from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server
from squeezealexa.ssl_wrap import SslSocketWrapper

TEST_GENRES = ["Rock", "Latin", "Blues"]


def run_diagnostics(sslw):
    server = Server(debug=False,
                    ssl_wrap=sslw,
                    cur_player_id=DEFAULT_PLAYER,
                    user=SERVER_USERNAME,
                    password=SERVER_PASSWORD)
    print("Found %d LMS genres!" % len(server.genres))
    print("Currently playing: %s" %
          " >> ".join(server.get_track_details().values()))

    status = server.get_status()
    print("Up next: %s >> %s >> %s" % (status.get('genre', "Unknown genre"),
                                       status.get('title', 'Unknown track'),
                                       status.get('artist', 'Unknown artist')))


def die(help="No idea, sorry."):
    print_exc()
    print("\n>>>> Failed with %s - %s <<<<" % (type(e).__name__, help))
    sys.exit(2)


if __name__ == '__main__':
    try:
        sslw = SslSocketWrapper(hostname=SERVER_HOSTNAME, port=SERVER_PORT,
                                ca_file=CA_FILE_PATH, cert_file=CERT_FILE_PATH,
                                verify_hostname=VERIFY_SERVER_HOSTNAME)
        run_diagnostics(sslw)
        print("\n>>>> Looks good! <<<<")
        sys.exit(0)
    except ssl.SSLError as e:
        if 'WRONG_VERSION_NUMBER' in e.strerror:
            die('probably not SSL - wrong SERVER_PORT maybe?')
        die("could be mismatched certificate files, or wrong hostname in cert."
            "Check CERT_FILE and certs on server too.")
    except gaierror as e:
        if "Name or service not know" in e.strerror:
            die("unknown host (%s) - check SERVER_HOSTNAME" % SERVER_HOSTNAME)
        die()
    except IOError as e:
        if 'Connection refused' in e.strerror:
            die("nothing listening on port %s:%s. Check settings."
                % (SERVER_HOSTNAME, SERVER_PORT))
        die('wrong path to certificate in settings?')
    except Exception as e:
        die()