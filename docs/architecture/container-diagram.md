# C4 Level 2 — Container Architecture

**Status:** To-Be / Planned

## Container Diagram

```mermaid
flowchart TB
    Owner["Garden Owner (Person)"]

    subgraph SG["Smart Garden — Planned Software System"]
        API["FastAPI Application<br/>REST API + Web Dashboard"]
        DB[("PostgreSQL Database")]
        ESP["ESP32 Firmware<br/>Sensor Acquisition"]
    end

    Owner -->|"Views dashboard and configures thresholds via HTTP"| API
    ESP -->|"Sends measurements via HTTP POST / JSON"| API
    API -->|"Reads and writes measurements and settings"| DB
```

## Design Decisions

- HTTP REST is the initial communication protocol between ESP32 and FastAPI.
- ESP32 uses bounded retries with temporary in-memory buffering.
- Measurements may be lost if the ESP32 restarts before successful delivery.
- Durable store-and-forward delivery is deferred.
- PostgreSQL is the primary relational database (ADR-0002).
- MQTT and store-and-forward delivery are deferred improvements.
- The MVP dashboard will be served by FastAPI. A separate frontend application is deferred.
