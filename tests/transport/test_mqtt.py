from datetime import datetime

import pytest
from paho.mqtt.client import MQTT_ERR_SUCCESS, MQTTMessage, MQTTMessageInfo

from squeezealexa.settings import MqttSettings
from squeezealexa.transport.mqtt import MqttTransport, CustomClient


# def test_real_publish():
#     client = CustomClient(MQTT_SETTINGS)
#     t = MqttTransport(client,
#                       req_topic=MQTT_SETTINGS.topic_req,
#                       resp_topic=MQTT_SETTINGS.topic_resp)
#     msg = "TEST MESSAGE at %s\n" % datetime.now()
#     ret = t.communicate(msg)
#     assert ret
#


class EchoingFakeClient(CustomClient):
    PREFIX = "OK: "

    def __init__(self, settings: MqttSettings):
        super().__init__(settings)

    def _configure_tls(self):
        pass

    def connect(self, host=None, port=None, keepalive=30, bind_address=""):
        if self.on_connect:
            self.on_connect(self, None, None, 1)
        return MQTT_ERR_SUCCESS

    def subscribe(self, topic, qos=0):
        if self.on_subscribe:
            self.on_subscribe(self, None, 123, (qos,))
        return MQTT_ERR_SUCCESS

    def publish(self, topic, payload=None, qos=0, retain=False):
        if self.on_publish:
            self.on_publish(self, None, 123)
        self.react_to_msg(payload)
        info = MQTTMessageInfo(123)
        info._published = True
        return info

    def react_to_msg(self, payload):
        """Fake the round trip entirely"""
        msg = MQTTMessage(topic=self.settings.topic_resp)
        msg.payload = b"%s%s" % (self.PREFIX.encode('utf-8'), payload)
        self.on_message(self, None, msg)

    def __str__(self) -> str:
        return "<Fake MQTT>"

    def reconnect(self):
        # if self.on_connect:
        #     self.on_connect(self, None, None, 123)
        return MQTT_ERR_SUCCESS


class FakeSettings(MqttSettings):
    pass

@pytest.fixture
def fake_client():
    c = EchoingFakeClient(FakeSettings())
    c.connect()
    yield c
    c.disconnect()
    del c


def test_communicate(fake_client):
    """Ensure that the communication we get back is the echo server's"""
    t = MqttTransport(fake_client, req_topic="foo", resp_topic="bar")
    t.start()
    msg = "TEST MESSAGE at %s" % datetime.now()
    ret = t.communicate(msg)
    assert ret == fake_client.PREFIX + msg


def test_multiline_communicate(fake_client):
    """Ensure that the communication we get back is the echo server's"""
    t = MqttTransport(fake_client, req_topic="foo", resp_topic="bar")
    t.start()
    msg = "TEST MESSAGE at %s\nAND ANOTHER\nLAST" % datetime.now()
    ret = t.communicate(msg)
    assert ret == fake_client.PREFIX + msg
