from squeezealexa.settings import MQTT_SETTINGS, SSL_SETTINGS
from squeezealexa.transport.mqtt import CustomClient, MqttTransport
from squeezealexa.transport.ssl_wrap import SslSocketTransport
from squeezealexa.utils import print_d


class TransportFactory:
    """Create Transports on demand. Helps with caching"""

    def __init__(self, ssl_config=SSL_SETTINGS, mqtt_settings=MQTT_SETTINGS):
        self.ssl_config = ssl_config
        self.mqtt_settings = mqtt_settings

    def create(self, mqtt_client=None):
        if self.mqtt_settings.configured:
            s = self.mqtt_settings
            print_d("Found MQTT config, so setting up MQTT transport.")
            client = mqtt_client or CustomClient(s)
            return MqttTransport(client,
                                 req_topic=s.topic_req,
                                 resp_topic=s.topic_resp)

        print_d("Defaulting to SSL transport")
        s = self.ssl_config
        return SslSocketTransport(hostname=s.server_hostname,
                                  port=s.port,
                                  ca_file=s.ca_file_path,
                                  cert_file=s.cert_file_path,
                                  verify_hostname=s.verify_server_hostname)
