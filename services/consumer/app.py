import logging
import os
import signal
import sys

import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", "mqtt-broker")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "sandbox/events")
QOS = int(os.getenv("MQTT_QOS", "1"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logging.info("Connected to %s:%s, subscribing to %s", BROKER_HOST, BROKER_PORT, TOPIC)
        client.subscribe(TOPIC, qos=QOS)
    else:
        logging.error("Connection failed: rc=%s", reason_code)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    logging.info("Received on %s: %s", msg.topic, msg.payload.decode("utf-8"))


def create_client() -> mqtt.Client:
    client_id = os.getenv("MQTT_CLIENT_ID", "consumer-service")
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_message = on_message
    return client


def main():
    client = create_client()
    client.connect(BROKER_HOST, BROKER_PORT)

    def handle_stop(signum, frame):
        logging.info("Signal %s received, shutting down", signum)
        client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    client.loop_forever()


if __name__ == "__main__":
    main()
