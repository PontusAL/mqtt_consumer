import logging
import os
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", "mqtt-broker")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "sandbox/events")
MESSAGE_TEMPLATE = os.getenv(
    "PUBLISH_MESSAGE", "Hello from publisher"
)
INTERVAL_SECONDS = float(os.getenv("PUBLISH_INTERVAL_SECONDS", "5"))
QOS = int(os.getenv("MQTT_QOS", "1"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logging.info("Connected to %s:%s", BROKER_HOST, BROKER_PORT)
    else:
        logging.error("Connection failed: rc=%s", reason_code)


def create_client() -> mqtt.Client:
    client_id = os.getenv("MQTT_CLIENT_ID", "publisher-service")
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    return client


def main():
    client = create_client()
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    try:
        while True:
            payload = f"{MESSAGE_TEMPLATE} @ {datetime.now(timezone.utc).isoformat()}"
            info = client.publish(TOPIC, payload=payload, qos=QOS, retain=False)
            status = info.rc
            if status == mqtt.MQTT_ERR_SUCCESS:
                logging.info("Published to %s: %s", TOPIC, payload)
            else:
                logging.warning("Failed to publish message (rc=%s)", status)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logging.info("Publisher interrupted, shutting down")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
