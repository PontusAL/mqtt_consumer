import logging
import os
import signal
import sys
from typing import Any

import paho.mqtt.client as mqtt
import requests

BROKER_HOST = os.getenv("MQTT_HOST", "broker")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
BROADCAST_TOPIC = os.getenv("BROADCAST_TOPIC", os.getenv("MQTT_TOPIC", "sandbox/events"))
FORWARD_TOPIC = os.getenv("FORWARD_TOPIC", "sandbox/processed")
QOS = int(os.getenv("MQTT_QOS", "1"))
TRANSFORMER_URL = os.getenv("TRANSFORMER_URL", "http://transformer:8000/transform")
HTTP_TIMEOUT = float(os.getenv("TRANSFORMER_TIMEOUT", "5"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logging.info(
            "Connected to %s:%s, subscribing to %s",
            BROKER_HOST,
            BROKER_PORT,
            BROADCAST_TOPIC,
        )
        client.subscribe(BROADCAST_TOPIC, qos=QOS)
    else:
        logging.error("Connection failed: rc=%s", reason_code)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    payload = msg.payload.decode("utf-8")
    logging.info("Received on %s: %s", msg.topic, payload)
    transformed = transform_payload(payload)
    publish_result = client.publish(FORWARD_TOPIC, payload=transformed, qos=QOS, retain=False)
    if publish_result.rc == mqtt.MQTT_ERR_SUCCESS:
        logging.info("Forwarded transformed payload to %s", FORWARD_TOPIC)
    else:
        logging.warning("Failed to forward payload (rc=%s)", publish_result.rc)


def transform_payload(payload: str) -> str:
    try:
        response = requests.post(
            TRANSFORMER_URL,
            json={"payload": payload},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        data: Any = response.json()
        return str(data.get("payload", payload))
    except requests.RequestException:
        logging.exception("Transformer request failed, forwarding original payload")
        return payload


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
