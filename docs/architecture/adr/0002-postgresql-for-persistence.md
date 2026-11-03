# ADR-0002: PostgreSQL for Persistent Data Storage

**Status:** Accepted
**Jira:** SG-16
**Milestone:** Smart Garden v0.3

## Context

Smart Garden v0.3 introduces persistent storage for
environmental sensor measurements and metadata.

The initial architecture proposed SQLite.

Although SQLite is sufficient for the expected workload,
the project also serves as a practical engineering lab.

## Decision

Use PostgreSQL as the primary relational database.

PostgreSQL will run on GardenPi alongside FastAPI.

## Rationale

- Practice relational database design and SQL.
- Learn database administration and service management.
- Implement migrations, permissions and backups.
- Support structured historical sensor measurements.
- Gain experience integrating FastAPI with a database server.

## Consequences

Positive:

- Strong relational integrity and transaction support.
- Experience with database operations.
- Extensible persistence architecture.

Negative:

- Additional memory and CPU consumption on Raspberry Pi.
- More complex installation and maintenance than SQLite.
- Database availability becomes an operational dependency.

## Alternatives Considered

### SQLite

Simpler and sufficient for the current sensor workload,
but provides fewer opportunities to practice database
server administration.

## Scope

Database installation, schema implementation, migrations
and backup procedures belong to subsequent v0.3 tasks.

This ADR records the architectural decision only.
