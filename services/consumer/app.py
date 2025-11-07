import json
import logging
import os
import signal
import sys
from typing import Any

import paho.mqtt.client as mqtt
import requests

BROKER_HOST = os.getenv("MQTT_HOST", "broker")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
BROADCAST_TOPIC_PREFIX = os.getenv("BROADCAST_TOPIC_PREFIX", "sandbox")
BROADCAST_TOPIC_FILTER = os.getenv("BROADCAST_TOPIC_FILTER", f"{BROADCAST_TOPIC_PREFIX}/#")
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
            BROADCAST_TOPIC_FILTER,
        )
        client.subscribe(BROADCAST_TOPIC_FILTER, qos=QOS)
    else:
        logging.error("Connection failed: rc=%s", reason_code)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    payload_text = msg.payload.decode("utf-8")
    logging.info("Received on %s: %s", msg.topic, payload_text)
    source_id = extract_source_id(msg.topic)
    raw_message = extract_message_body(payload_text)
    transformed_msg = transform_payload(raw_message)
    outbound_payload = json.dumps({"source_id": source_id, "msg": transformed_msg})
    publish_result = client.publish(FORWARD_TOPIC, payload=outbound_payload, qos=QOS, retain=False)
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


def extract_source_id(topic: str) -> str:
    parts = topic.split("/")
    return parts[-1] if parts else "unknown"


def extract_message_body(payload_text: str) -> str:
    try:
        data = json.loads(payload_text)
        if isinstance(data, dict) and "msg" in data:
            return str(data["msg"])
    except json.JSONDecodeError:
        logging.warning("Payload not JSON, using raw text")
    return payload_text


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
