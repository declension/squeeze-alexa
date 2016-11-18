from __future__ import print_function

import urllib

from squeezealexa.settings import CERT_FILE_PATH, SERVER_PORT, CA_FILE_PATH, \
    SERVER_HOSTNAME, DEFAULT_PLAYER
from squeezealexa.ssl_wrap import SslCommsMixin

print_d = print_w = print


def _(s):
    return s


class SqueezeboxException(Exception):
    """Errors communicating with the Squeezebox"""


class SqueezeboxServerSettings(dict):
    """Encapsulates Server settings"""
    def __str__(self):
        try:
            return _("Squeezebox server at {hostname}:{port}").format(**self)
        except KeyError:
            return _("unidentified Squeezebox server")


class SqueezeboxPlayerSettings(dict):
    """Encapsulates player settings"""
    def __str__(self):
        try:
            return "{name} [{playerid}]".format(**self)
        except KeyError:
            return _("unidentified Squeezebox player: %r" % self)


class Server(SslCommsMixin):
    """Encapsulates access to a Squeezebox player via a squeezecenter server"""

    _TIMEOUT = 10
    _MAX_FAILURES = 3

    def __init__(self, hostname="localhost", port=9090, user="", password="",
                 cur_player_id=None, debug=False,
                 ca_file=None, cert_file=None):
        super(Server, self).__init__(hostname=hostname, port=port,
                                     ca_file=ca_file, cert_file=cert_file)
        self._debug = debug
        self.failures = 0
        self.config = SqueezeboxServerSettings(locals())
        if user:
            result = self.__a_request("login %s %s" % (user, password))
            if result != (6 * '*'):
                raise SqueezeboxException(
                    "Couldn't log in to squeezebox: response was '%s'"
                    % result)
        self.is_connected = True
        self.failures = 0
        self.cur_player_id = cur_player_id
        print_d("Connected to %s! (Player: %s)" % (self, self.cur_player_id))
        self.players = {}
        self.get_players_full(refresh=True)

    def get_library_dir(self):
        return self.config['library_dir']

    def __a_request(self, line, raw=False, wait=True):
        return self._request([line], raw=raw, wait=wait)[0]

    def _unquote(self, response):
        return ' '.join(urllib.unquote(s) for s in response.split(' '))

    def _request(self, lines, raw=False, wait=True):
        """
        Send multiple pipelined requests to the server, if connected,
        and return their responses,
        assuming order is maintained (which seems safe).

        :type lines list[str]
        :rtype list[str]
        """
        if not (lines and len(lines)):
            return
        lines = map(str.rstrip, lines)

        first_word = lines[0].split()[0]
        if not (self.is_connected or first_word == 'login'):
            print_d("Can't do '%s' - not connected" % first_word, self)
            return

        if self._debug:
            print_d(">>>> \"%s\"" % "\n".join(lines))
        request = "\n".join(lines) + "\n"
        raw_response = self.communicate(request, wait=wait).rstrip("\n")
        if not wait or not raw_response:
            return
        response = raw_response if raw else self._unquote(raw_response)
        if self._debug:
            print_d("<<<< \"%s\"" % (response,))

        def start_point(text):
            delta = -1 if text.endswith('?') else 1
            return len(self._unquote(text) if raw else text) + delta

        if len(lines) != len(response.splitlines()):
            raise ValueError("%s != %s" % (lines, response))
        return [resp_line[start_point(line):]
                for line, resp_line in zip(lines, response.splitlines())]

    def get_players(self, refresh=False):
        """ Returns (and caches) a list of the Squeezebox players available"""
        if self.players and not refresh:
            return self.players
        pairs = self.__pairs_from(self.__a_request("players 0 99", True))
        # First element is always count
        count = int(pairs.pop(0)[1])
        self.players = []
        for key, val in pairs:
            if key == "playerindex":
                player_index = int(val)
                self.players.append(SqueezeboxPlayerSettings())
            else:
                # Don't worry, playerindex is *always* the first entry...
                self.players[player_index][key] = val
        if self._debug:
            print_d("Found %d player(s): %s" %
                    (len(self.players), self.players))
        assert (count == len(self.players))
        return self.players

    def __pairs_from(self, response):
        """Split and unescape a response"""
        def demunge(string):
            s = urllib.unquote(string)
            return tuple(s.split(':', 1))
        return filter(lambda t: len(t) == 2,
                      map(demunge, response.split(' ')))

    def get_players_full(self, refresh=False):
        """ Returns (and caches) a list of the Squeezebox players available"""
        if self.players and not refresh:
            return self.players
        pairs = self.__pairs_from(
            self.__a_request("serverstatus 0 99", raw=True))

        self.players = {}
        player_id = None
        for key, val in pairs:
            if key == "playerid":
                player_id = val
                self.players[player_id] = SqueezeboxPlayerSettings()
            elif player_id:
                # Don't worry, playerid is *always* the first entry...
                self.players[player_id][key] = val
        if self._debug:
            print_d("Found %d player(s): %s" %
                    (len(self.players), self.players))
        assert (int(dict(pairs)['player count']) == len(self.players))
        return self.players

    def player_request(self, line, player_id=None, raw=False, wait=True):
        if not self.is_connected:
            return
        try:
            player_id = (player_id
                         or self.cur_player_id
                         or list(self.players.values())[0]["playerid"])
            return self._request(["%s %s" % (player_id, line)],
                                 raw=raw, wait=wait)[0]
        except IndexError:
            return None

    def play(self, player_id=None):
        """Plays the current song"""
        self.player_request("play", player_id=player_id)

    def is_stopped(self, player_id=None):
        """Returns whether the player is in any sort of non-playing mode"""
        response = self.player_request("mode ?", player_id=player_id)
        return "play" != response

    def get_current(self, player_id=None):
        # return self.player_request("current_title ?", player_id=player_id)
        return self.get_status(player_id)

    def get_track_details(self, player_id=None):
        keys = ["genre", "artist", "current_title"]
        pid = player_id or self.cur_player_id
        responses = self._request(["%s %s ?" % (pid, s)
                                   for s in keys])
        return dict(zip(keys, responses))

    def get_server_status(self, player_id=None):
        return self.player_request("serverstatus 0 99", player_id=player_id)

    def get_status(self, player_id=None):
        response = self.player_request("status - 2", player_id=player_id,
                                       raw=True)
        return self.__pairs_from(response)

    def next(self, player_id=None):
        self.player_request("playlist jump +1", player_id=player_id)

    def previous(self, player_id=None):
        self.player_request("playlist jump -1", player_id=player_id)

    def playlist_play(self, path):
        """Play song immediately"""
        self.player_request("playlist play %s" % (urllib.quote(path)))

    def playlist_clear(self):
        self.player_request("playlist clear", wait=False)

    def playlist_resume(self, name, resume, wipe=False):
        cmd = ("playlist resume %s noplay:%d wipePlaylist:%d"
               % (urllib.quote(name), int(not resume), int(wipe)))
        self.player_request(cmd, wait=False)

    def change_song(self, path):
        """Queue up a song"""
        self.player_request("playlist clear")
        self.player_request("playlist insert %s" % (urllib.quote(path)))

    def change_volume(self, delta, player_id=None):
        if not delta:
            return
        cmd = "mixer volume %s%.1f" % ('+' if delta > 0 else '', float(delta))
        self.player_request(cmd, player_id=player_id)

    def get_milliseconds(self):
        secs = self.player_request("time ?") or 0
        return float(secs) * 1000.0

    def pause(self, player_id=None):
        self.player_request("pause 1", player_id=player_id)

    def resume(self, player_id=None, fade_in_secs=1):
        self.player_request("pause 0 %d" % fade_in_secs, player_id=player_id)

    def stop(self, player_id=None):
        self.player_request("stop", player_id=player_id)

    def set_shuffle(self, on=True, player_id=None):
        self.player_request("playlist shuffle %d" % int(bool(on) * 2),
                            player_id=player_id)

    def set_repeat(self, on=True, player_id=None):
        self.player_request("playlist repeat %d" % int(bool(on)),
                            player_id=player_id)

    def set_power(self, on=True, player_id=None):
        self.player_request("power %d" % int(bool(on)), player_id=player_id)

    def __str__(self):
        return str(self.config)


if __name__ == '__main__':
    server = Server(hostname=SERVER_HOSTNAME, port=SERVER_PORT, debug=True,
                    cur_player_id=DEFAULT_PLAYER,
                    ca_file=CA_FILE_PATH, cert_file=CERT_FILE_PATH)
    print(server.get_current())
    print(server.get_status())
    server.get_server_status()
    print(" >> ".join(server.get_track_details().values()))
    server.set_repeat(False)
    server.set_shuffle(True)
