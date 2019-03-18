#!/usr/bin/env python3
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

import sys
from os.path import dirname, realpath
from traceback import print_exc

sys.path.append(dirname(dirname(realpath(__file__))))

from squeezealexa.settings import *
from squeezealexa.transport.factory import TransportFactory
from squeezealexa.squeezebox.server import Server, people_from
from squeezealexa.transport.base import Transport

TEST_GENRES = ["Rock", "Latin", "Blues"]


def run_diagnostics(transport: Transport):
    server = Server(transport=transport,
                    debug=LMS_SETTINGS.DEBUG,
                    cur_player_id=LMS_SETTINGS.DEFAULT_PLAYER,
                    user=LMS_SETTINGS.USERNAME,
                    password=LMS_SETTINGS.PASSWORD)
    assert server.genres
    assert server.playlists
    cur_play_details = server.get_track_details()
    if cur_play_details:
        print("Currently playing: \n >> %s" %
              "\n >> ".join("%s: %s" % (k, ", ".join(v))
                            for k, v in cur_play_details.items()))
    else:
        print("Nothing currently in playlist")

    d = server.get_track_details(offset=+1)
    print("Up next: %s >> %s >> %s" % (d.get('genre', ["Unknown genre"])[0],
                                       people_from(d, ["Unknown people"])[0],
                                       d.get('title', ['Unknown track'])[0]))
    del server


def die(e):
    print_exc()
    print("\n>>>> Failed with %s: %s <<<<" % (type(e).__name__, e))
    sys.exit(2)


if __name__ == '__main__':
    try:
        transport = TransportFactory().create().start()
        run_diagnostics(transport)
        print("\n>>>> Looks good! <<<<")
        sys.exit(0)
    except Exception as e:
        die(e)
