# MQTT Sandbox Stack

This repository provides a minimal Docker Compose setup to experiment with an MQTT broker, a Python-based publisher, and a Python-based consumer. The stack is intended as a starting point for iterating on more advanced messaging flows.

## Stack overview

- **mqtt-broker** – Eclipse Mosquitto with a permissive development config.
- **publisher** – Python service that emits timestamped messages on a configurable topic.
- **consumer** – Python service that subscribes to the same topic and logs incoming payloads.

## Usage

```bash
docker compose up --build
```

The consumer logs messages to stdout as they arrive, while the publisher emits new payloads every five seconds by default. Use environment variables in `docker-compose.yml` to tweak topics, QoS, intervals, or default messages.

## Next steps

- Point the publisher or consumer services at your own Python modules for richer business logic.
- Harden Mosquitto by introducing authentication/authorization once the sandbox phase is complete.
