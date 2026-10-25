# FR-001

## User story

As the garden owner, I want to monitor each pot's soil-moisture status on a dashboard so that I can identify plants requiring watering.

## Acceptance criteria

1. Each monitored pot has its own configurable soil-moisture threshold.
2. The dashboard displays the latest available measurement for each monitored pot.
3. When a valid measurement falls below that pot's threshold, the dashboard indicates that watering is required.
4. Missing or outdated measurements are displayed as unavailable or stale, not as healthy.
   Out of scope for now: Push notifications, automatic watering and predictive recommendations.

## Out of Scope

- Push notifications
- Automatic watering
- Predictive recommendations

## Open Questions

- Moisture threshold: What measurement scale and threshold values will we use? To be determined after sensor calibration.

- Stale measurement: How old must a measurement be before the dashboard considers it outdated?
