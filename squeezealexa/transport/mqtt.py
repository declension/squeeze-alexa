import os
from _ssl import PROTOCOL_TLSv1_2
from glob import glob
from os.path import dirname, realpath, join

from paho.mqtt.client import Client, MQTT_ERR_SUCCESS, error_string, \
    MQTT_ERR_INVAL

from squeezealexa.settings import MqttSettings
from squeezealexa.transport.base import Transport, Error, check_listening
from squeezealexa.utils import print_d, wait_for


BASE = realpath(join(dirname(__file__), "..", ".."))


class CustomClient(Client):
    """Opinionated Client subclass that configures from passed settings,
    and also does some safety checks"""

    def __init__(self, settings: MqttSettings):
        super().__init__()
        self.settings = settings
        self._configure_tls()

    def _configure_tls(self):
        self.tls_set(certfile=self._conf_file_of("*-certificate.pem.crt"),
                     keyfile=self._conf_file_of("*-private.pem.key"),
                     tls_version=PROTOCOL_TLSv1_2)

    def connect(self, host=None, port=None, keepalive=30, bind_address=""):
        host = host or self.settings.hostname
        port = port or self.settings.port

        check_listening(host, port, msg="check your MQTT settings")
        ret = super().connect(host=host,
                              port=port,
                              keepalive=keepalive, bind_address=bind_address)
        if MQTT_ERR_SUCCESS == ret:
            print_d("Connecting to {}", self.settings)
            return ret
        raise Error("Couldn't connect to {}".format(self.settings))

    def _conf_file_of(self, rel_glob: str) -> str:
        full_glob = os.path.join(self.settings.cert_dir, rel_glob)
        results = glob(full_glob)
        try:
            return results[0]
        except IndexError:
            raise Error("Can't find {glob} within dir {base}".format(
                base=self.settings.cert_dir, glob=rel_glob))

    def __del__(self):
        print_d("Disconnecting {}", self)
        self.disconnect()
        self.loop_stop()

    def __str__(self) -> str:
        s = self.settings
        return "< #{req_topic} / #{resp_topic} on {host}:{port} >".format(
            req_topic=s.topic_req, resp_topic=s.topic_resp, host=self._host,
            port=self._port)


class MqttTransport(Transport):
    """Transport over TLS-encrypted MQTT"""

    def __init__(self, client: Client, req_topic: str, resp_topic: str):
        def subscribed(client, userdata, mind, granted_qos):
            self.is_connected = True
            print_d("MQTT/TLS transport to {} initialised. (@QoS {})",
                    client, granted_qos)

        super().__init__()
        self.client = client
        self.req_topic = req_topic
        self.resp_topic = resp_topic
        self.client.on_subscribe = subscribed
        self.client.on_message = self._on_message
        self.message = []

    def start(self):
        def connected(client, userdata, flags, rc):
            print_d("Connected to {}", self.client)
            print_d("Subscribing to '{}'", self.resp_topic)
            self.client.subscribe(self.resp_topic, qos=1)

        self.client.on_connect = connected
        assert self.client.loop_start() != MQTT_ERR_INVAL
        self.client.connect()
        wait_for(lambda s: s.is_connected, what="connection", context=self)

    def _on_message(self, client, userdata, message):
        self.response_lines += message.payload.splitlines()

    @property
    def details(self):
        return "MQTT on {}".format(self.client)

    def communicate(self, raw: str, wait=True) -> str:
        data = raw.strip() + '\n'
        num_lines = data.count('\n')
        self._clear()
        ret = self.client.publish(self.req_topic, data.encode('utf-8'),
                                  qos=1 if wait else 0)
        if not wait:
            return None
        ret.wait_for_publish()
        if ret.rc != MQTT_ERR_SUCCESS:
            raise Error("Error publishing message: {}", error_string(ret.rc))
        print_d("Published to {topic} OK. Waiting for {num} line(s)...",
                topic=self.req_topic, num=num_lines)

        wait_for(lambda s: len(s.response_lines) >= num_lines, context=self,
                 what="response from Squeezebox")
        return "\n".join(m.decode('utf-8') for m in self.response_lines)

    def _clear(self):
        self.response_lines = []

    def __del__(self):
        super().__del__()
        print_d("Killing {}", self)
        del self.client
