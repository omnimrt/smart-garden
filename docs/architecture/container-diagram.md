# C4 Level 2 — Container Architecture

**Status:** To-Be / Planned

## Container Diagram

```mermaid
flowchart TB
    Owner["Garden Owner (Person)"]

    subgraph SG["Smart Garden — Planned Software System"]
        API["FastAPI Application<br/>REST API + Web Dashboard"]
        DB[("SQLite Database")]
        ESP["ESP32 Firmware<br/>Sensor Acquisition"]
    end

    Owner -->|"Views dashboard and configures thresholds via HTTP"| API
    ESP -->|"Sends measurements via HTTP POST / JSON"| API
    API -->|"Reads and writes measurements and settings"| DB
```

## Design Decisions

- HTTP REST is the initial communication protocol between ESP32 and FastAPI.
- Sensor measurements use best-effort delivery without persistent buffering.
- SQLite is the initial database.
- MQTT and store-and-forward delivery are deferred improvements.
- The MVP dashboard will be served by FastAPI. A separate frontend application is deferred.
