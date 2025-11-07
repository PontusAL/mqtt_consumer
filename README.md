# MQTT Sandbox Stack

This repository provides a Docker Compose stack to experiment with MQTT-centric message flows. It includes a Mosquitto broker, a general broadcaster to simulate upstream data, a consumer that also republishes processed messages, and an asynchronous transformer API.

## Stack overview

- **mqtt-broker** – Eclipse Mosquitto with a permissive development config.
- **broadcaster** – Python service that emits timestamped messages on `BROADCAST_TOPIC`, standing in for an external data source.
- **consumer** – Python client that subscribes to `BROADCAST_TOPIC`, offloads transformation requests to the HTTP transformer, and republishes the transformed payload to `FORWARD_TOPIC`.
- **transformer** – Async FastAPI app that exposes `/transform`; currently it simply echoes the payload but serves as a placeholder for data processing logic.

## Usage

```bash
docker compose up --build
```

- The broadcaster emits payloads every `BROADCAST_INTERVAL` seconds (default 5).
- The consumer logs the incoming payload, calls the transformer via HTTP, and republishes the response on `FORWARD_TOPIC`.
- Inspect consumer logs to see both inbound and outbound traffic, and query `http://localhost:8000/health` to confirm the transformer is running.

Tune MQTT host/port, topics, QoS, transformer endpoint, or broadcast interval via the `.env` file (Compose automatically loads it) or by exporting environment variables before running Compose.

## Next steps

- Point the publisher or consumer services at your own Python modules for richer business logic.
- Harden Mosquitto by introducing authentication/authorization once the sandbox phase is complete.
