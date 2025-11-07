import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", "broker")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_PREFIX = os.getenv("BROADCAST_TOPIC_PREFIX", "sandbox")
MESSAGE_TEMPLATE = os.getenv("PUBLISH_MESSAGE", "Hello from broadcaster")
INTERVAL_SECONDS = float(
    os.getenv(
        "BROADCAST_INTERVAL",
        os.getenv("PUBLISH_INTERVAL", os.getenv("PUBLISH_INTERVAL_SECONDS", "5")),
    )
)
QOS = int(os.getenv("MQTT_QOS", "1"))
NUM_CLIENTS = int(os.getenv("BROADCAST_CLIENTS", "3"))
CLIENT_ID_PREFIX = os.getenv("MQTT_CLIENT_PREFIX", "broadcaster")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


@dataclass
class SourceClient:
    source_id: str
    topic: str
    client: mqtt.Client


def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logging.info("Connected to %s:%s", BROKER_HOST, BROKER_PORT)
    else:
        logging.error("Connection failed: rc=%s", reason_code)


def create_source_client(index: int) -> SourceClient:
    source_id = str(uuid.uuid4())
    topic = f"{TOPIC_PREFIX}/{source_id}"
    client_id = f"{CLIENT_ID_PREFIX}-{index+1}-{source_id[:8]}"
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    return SourceClient(source_id=source_id, topic=topic, client=client)


def main():
    sources = [create_source_client(i) for i in range(NUM_CLIENTS)]
    for source in sources:
        source.client.connect(BROKER_HOST, BROKER_PORT)
        source.client.loop_start()
        logging.info("Source %s broadcasting on %s", source.source_id, source.topic)

    try:
        while True:
            for source in sources:
                payload = (
                    f"{MESSAGE_TEMPLATE} from {source.source_id} @ "
                    f"{datetime.now(timezone.utc).isoformat()}"
                )
                info = source.client.publish(source.topic, payload=payload, qos=QOS, retain=False)
                status = info.rc
                if status == mqtt.MQTT_ERR_SUCCESS:
                    logging.info("Published to %s: %s", source.topic, payload)
                else:
                    logging.warning("Failed to publish message for %s (rc=%s)", source.source_id, status)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logging.info("Publisher interrupted, shutting down")
    finally:
        for source in sources:
            source.client.loop_stop()
            source.client.disconnect()


if __name__ == "__main__":
    main()
