from squeezealexa.settings import *
from squeezealexa.squeezebox.server import Server
from squeezealexa.ssl_wrap import SslSocketWrapper

if __name__ == '__main__':
    sslw = SslSocketWrapper(hostname=SERVER_HOSTNAME, port=SERVER_PORT,
                            ca_file=CA_FILE_PATH, cert_file=CERT_FILE_PATH,
                            verify_hostname=VERIFY_SERVER_HOSTNAME)
    server = Server(debug=True,
                    ssl_wrap=sslw,
                    cur_player_id=DEFAULT_PLAYER,
                    user=SERVER_USERNAME,
                    password=SERVER_PASSWORD)
    print(server.get_status())
    # print(server.genres)
    print(" >> ".join(server.get_track_details().values()))
    server.play_genres(["Rock Ballad", "Latin", "Blues"])
