# ADR-0001 — HTTP REST for Sensor Data Ingestion

**Status:** Accepted
**Date:** 2026-10-28

## Context

Smart Garden will collect soil-moisture measurements from nine sensors using ESP32 firmware.

The measurements will be transmitted approximately once per hour to a FastAPI backend running on Raspberry Pi.

We need to select a communication protocol for the initial implementation.

## Decision

Use HTTP REST with JSON payloads for ESP32-to-FastAPI communication.

Sensor measurements will be submitted to a backend ingestion endpoint.

## Alternatives Considered

**MQTT:** Publish-subscribe messaging through an MQTT broker.

MQTT offers efficient messaging and supports multiple consumers, but introduces additional infrastructure and operational complexity for our small initial deployment.

## Consequences

**Benefits**

- Simple architecture with fewer services.
- Direct integration with FastAPI.
- Practical experience with HTTP, REST APIs and JSON.

**Limitations**

- HTTP REST requires the backend to be reachable when a request is made.
- Unlike MQTT, HTTP does not provide a built-in publish-subscribe messaging model.
- Reliable delivery during outages requires additional application-level mechanisms, such as buffering and retries.

## Future Considerations

Evaluate MQTT if event-driven communication or multiple consumers become necessary.

Evaluate store-and-forward buffering if measurement loss becomes unacceptable.
