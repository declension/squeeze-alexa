from squeezealexa.settings import MQTT_SETTINGS, SSL_SETTINGS
from squeezealexa.transport.mqtt import CustomClient, MqttTransport
from squeezealexa.transport.ssl_wrap import SslSocketTransport
from squeezealexa.utils import print_d


def create_transport(ssl_config=SSL_SETTINGS, mqtt_settings=MQTT_SETTINGS,
                     mqtt_client=None):
    if mqtt_settings.configured:
        s = mqtt_settings
        print_d("Found MQTT config, so setting up MQTT transport.")
        client = mqtt_client or CustomClient(s)
        transport = MqttTransport(client,
                                  req_topic=s.topic_req,
                                  resp_topic=s.topic_resp)
        transport.start()
        return transport

    print_d("Defaulting to SSL transport")
    s = ssl_config
    return SslSocketTransport(hostname=s.server_hostname,
                              port=s.port,
                              ca_file=s.ca_file_path,
                              cert_file=s.cert_file_path,
                              verify_hostname=s.verify_server_hostname)
