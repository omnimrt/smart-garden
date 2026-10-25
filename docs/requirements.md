# FR-001

## User story

As the garden owner, I want to monitor each pot's soil-moisture status on a dashboard so that I can identify plants requiring watering.

## Acceptance criteria

1. Each monitored pot has its own configurable soil-moisture threshold.
2. The dashboard displays the latest available measurement for each monitored pot.
3. When a valid measurement falls below that pot's threshold, the dashboard indicates that watering is required.
4. Missing or outdated measurements are displayed as unavailable or stale, not as healthy.

## Out of Scope

- Push notifications
- Automatic watering
- Predictive recommendations

## Open Questions

- Moisture threshold: What measurement scale and threshold values will we use? To be determined after sensor calibration.

- Stale measurement: Validate the provisional 90-minute threshold during sensor integration.

## Measurement Policy

- Each monitored pot shall have an individual soil-moisture sensor.
- The system shall collect soil-moisture measurements every 60 minutes.
- Measurements older than 90 minutes shall be classified as stale.
- Sampling and stale-data intervals are provisional and subject to validation.

# NFR-001 — Sensor Fault Isolation

Failure of an individual soil-moisture sensor shall not prevent
other functioning sensors from reporting measurements.

## Acceptance Criteria

1. Given nine functioning sensors, when one sensor stops reporting, measurements from the other eight continue to be collected.
2. Failure of one sensor does not cause the entire measurement collection process to terminate.
3. The affected sensor is identified separately from functioning sensors.

# NFR-002 — Measurement and Failure Logging

The system shall record detected measurement timeouts,
sensor read errors and communication failures to support
troubleshooting and incident investigation.

## Acceptance Criteria

1. Each detected error generates a log entry.
2. Each entry contains a timestamp, sensor identifier,
   event type and available diagnostic information.
3. Logs remain accessible after the monitoring process
   restarts.
4. Log entries describe observed conditions without
   asserting an unverified root cause.
