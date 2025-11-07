# MQTT Sandbox Stack

This repository provides a Docker Compose stack to experiment with MQTT-centric message flows. It includes a Mosquitto broker, a general broadcaster to simulate upstream data, a consumer that also republishes processed messages, and an asynchronous transformer API.

## Stack overview

- **mqtt-broker** – Eclipse Mosquitto with a permissive development config.
- **broadcaster** – Python service that spins up three simulated source clients. Each one publishes JSON objects shaped as `{ "msg": "..." }` to its own `BROADCAST_TOPIC_PREFIX/<source_id>` topic (default `sandbox/raw/<uuid>`), standing in for upstream emitters.
- **consumer** – Python client that subscribes to `BROADCAST_TOPIC_PREFIX/#`, offloads each inbound `msg` to the HTTP transformer, and republishes a JSON object `{ "source_id": "...", "msg": "..." }` to `FORWARD_TOPIC`.
- **transformer** – Async FastAPI app that exposes `/transform`; currently it simply echoes the payload but serves as a placeholder for data processing logic.

## Usage

```bash
docker compose up --build
```

- The broadcaster emits JSON payloads every `BROADCAST_INTERVAL` seconds (default 5) from three UUID-tagged clients.
- The consumer logs the incoming payload, calls the transformer via HTTP with the `msg` field, and republishes the response on `FORWARD_TOPIC` as `{source_id, msg}`.
- Inspect consumer logs to see both inbound and outbound traffic, and query `http://localhost:8000/health` to confirm the transformer is running.

Tune MQTT host/port, topic prefix, QoS, transformer endpoint, or broadcast interval via the `.env` file (Compose automatically loads it) or by exporting environment variables before running Compose.

### Listening to the broker from a terminal

Use `mosquitto_sub` (ships with Mosquitto) to watch topics directly:

```bash
# From the host that's running docker compose (localhost maps to the broker port 1883)
mosquitto_sub -h localhost -p 1883 -t 'sandbox/raw/#' -v   # raw broadcaster topics
mosquitto_sub -h localhost -p 1883 -t 'sandbox/processed' -v # consumer output
```

- `-h` specifies the broker hostname/IP. Use `localhost` when subscribing from the same machine that exposes the `1883:1883` port mapping, or replace it with another reachable host/IP if you're on a different machine.
- `-t 'sandbox/raw/#'` subscribes to the entire raw topic tree that the broadcaster uses (`BROADCAST_TOPIC_PREFIX` + client UUID). Adjust the prefix if you change it in `.env`.

## Next steps

- Point the publisher or consumer services at your own Python modules for richer business logic.
- Harden Mosquitto by introducing authentication/authorization once the sandbox phase is complete.
