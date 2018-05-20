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
from os.path import dirname
from traceback import print_exc

from squeezealexa.main import SqueezeAlexa
from squeezealexa.transport.base import Transport

sys.path.append(dirname(dirname(__file__)))

from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server

TEST_GENRES = ["Rock", "Latin", "Blues"]


def run_diagnostics(transport: Transport):
    server = Server(debug=DEBUG_LMS,
                    transport=transport,
                    cur_player_id=DEFAULT_PLAYER,
                    user=SERVER_USERNAME,
                    password=SERVER_PASSWORD)
    assert server.genres
    assert server.playlists
    assert server.favorites
    cur_play_details = server.get_track_details().values()
    if cur_play_details:
        print("Currently playing: %s" %
              " >> ".join(cur_play_details))
    else:
        print("Nothing currently in playlist")

    status = server.get_status()
    print("Up next: %s >> %s >> %s" % (status.get('genre', "Unknown genre"),
                                       status.get('title', 'Unknown track'),
                                       status.get('artist', 'Unknown artist')))
    del server


def die(e):
    print_exc()
    print("\n>>>> Failed with %s: %s <<<<" % (type(e).__name__, e))
    sys.exit(2)


if __name__ == '__main__':
    try:
        transport = SqueezeAlexa.create_transport()
        run_diagnostics(transport)
        print("\n>>>> Looks good! <<<<")
        sys.exit(0)
    except Exception as e:
        die(e)
