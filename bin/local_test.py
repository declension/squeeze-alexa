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
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))

from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server
from squeezealexa.ssl_wrap import SslSocketWrapper
from squeezealexa.utils import english_join

TEST_GENRES = ["Rock", "Latin", "Blues"]

if __name__ == '__main__':
    sslw = SslSocketWrapper(hostname=SERVER_HOSTNAME, port=SERVER_PORT,
                            ca_file=CA_FILE_PATH, cert_file=CERT_FILE_PATH,
                            verify_hostname=VERIFY_SERVER_HOSTNAME)
    server = Server(debug=False,
                    ssl_wrap=sslw,
                    cur_player_id=DEFAULT_PLAYER,
                    user=SERVER_USERNAME,
                    password=SERVER_PASSWORD)
    print("Found %d LMS genres!" % len(server.genres))

    # print("Playing a genre mix of %s..." % english_join(TEST_GENRES))
    # server.play_genres(TEST_GENRES)

    print("Currently playing: %s" %
          " >> ".join(server.get_track_details().values()))

    status = server.get_status()
    print("Up next: %s >> %s >> %s" % (status.get('genre', "Unknown genre"),
                                       status.get('title', 'Unknown track'),
                                       status.get('artist', 'Unknown artist')))
