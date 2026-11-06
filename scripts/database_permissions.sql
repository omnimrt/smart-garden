-- SG-18: PostgreSQL application role permissions
-- Run as the database owner or an authorized administrator.
-- Prerequisite: garden_app exists and Alembic migrations are complete.

BEGIN;

GRANT USAGE ON SCHEMA public TO garden_app;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public
FROM garden_app;

GRANT SELECT, INSERT, UPDATE
ON TABLE devices, pots, sensors
TO garden_app;

GRANT SELECT, INSERT
ON TABLE measurements
TO garden_app;

REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public
FROM garden_app;

GRANT USAGE
ON ALL SEQUENCES IN SCHEMA public
TO garden_app;

COMMIT;