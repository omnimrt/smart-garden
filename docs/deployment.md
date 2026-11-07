# Smart Garden — Raspberry Pi Deployment

## Environment

- Host: `gardenpi`
- OS: Raspberry Pi OS 64-bit (Debian 13)
- Application directory: `/home/omnimrt/gardenpi`
- Python: 3.13
- PostgreSQL: 17
- Backend: FastAPI / Uvicorn / SQLAlchemy
- Database migrations: Alembic
- Service: `garden-api.service`
- API address: `127.0.0.1:8000`

## 1. Application installation

Deploy a reviewed Git revision or branch. Do not automatically pull `main` when deploying an unmerged feature branch.

```bash
cd ~/gardenpi

git fetch origin
git switch feature/SG-18-postgresql-foundation
git pull --ff-only

python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

For future deployments, replace the feature branch with the approved release branch or revision.

## 2. PostgreSQL installation

```bash
sudo apt update
sudo apt install -y postgresql postgresql-client

pg_lsclusters
systemctl is-active postgresql
```

The database server runs locally on port 5432.

## 3. Database provisioning

Connect as the PostgreSQL administrator:

```bash
sudo -u postgres psql
```

Create separate migration and application roles:

```sql
CREATE ROLE garden_owner LOGIN;
CREATE ROLE garden_app LOGIN;

CREATE DATABASE smart_garden OWNER garden_owner;
```

Connect to the application database using `\connect smart_garden` on a separate line.

```sql
REVOKE ALL ON DATABASE smart_garden FROM PUBLIC;
GRANT CONNECT ON DATABASE smart_garden TO garden_app;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO garden_app;
```

Set passwords interactively:

```text
\password garden_owner
\password garden_app
```

Use distinct, strong passwords. Do not store them in Git.

The database owner runs schema migrations. FastAPI uses the restricted application role.

## 4. Environment configuration

Create `/home/omnimrt/gardenpi/.env` containing:

```dotenv
DATABASE_URL=postgresql+psycopg://garden_app:ENCODED_PASSWORD@127.0.0.1:5432/smart_garden
MIGRATION_DATABASE_URL=postgresql+psycopg://garden_owner:ENCODED_PASSWORD@127.0.0.1:5432/smart_garden
SENSOR_API_KEY=GENERATED_RANDOM_SECRET
```

Percent-encode passwords when placing them in connection URLs.

Protect the file:

```bash
chmod 600 .env
git check-ignore -v .env
```

The `.env` file is excluded from version control.

## 5. Migrations and permissions

Apply migrations using the privileged migration connection:

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic current
```

Provision application permissions:

```bash
sudo -u postgres psql \
  -X -v ON_ERROR_STOP=1 \
  -d smart_garden \
  -f scripts/database_permissions.sql
```

Expected policy:

| Table        | SELECT | INSERT | UPDATE | DELETE |
| ------------ | ------ | ------ | ------ | ------ |
| devices      | Yes    | Yes    | Yes    | No     |
| pots         | Yes    | Yes    | Yes    | No     |
| sensors      | Yes    | Yes    | Yes    | No     |
| measurements | Yes    | Yes    | No     | No     |

Application access requires the appropriate sequence `USAGE` permissions.

Reapply and verify the permissions script when provisioning a fresh database.

## 6. API service

The tracked service file is `deploy/garden-api.service`.

It uses:

- The application Python virtual environment
- `/home/omnimrt/gardenpi/.env`
- Localhost binding on port 8000
- Automatic restart on failure

Install or update:

```bash
sudo install -m 644 deploy/garden-api.service \
  /etc/systemd/system/garden-api.service

sudo systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/garden-api.service
sudo systemctl enable garden-api.service
sudo systemctl restart garden-api.service
```

Verify:

```bash
systemctl is-active garden-api.service
curl -fsS http://127.0.0.1:8000/health
```

## 7. API verification

Available endpoints:

- `GET /health`
- `GET /api/system`
- `GET /api/garden/measurements`
- `POST /api/garden/measurements`

POST measurement ingestion requires the `X-API-Key` header.

Expected POST behavior:

| Scenario                               | HTTP status |
| -------------------------------------- | ----------- |
| New valid measurement                  | 201         |
| Identical retry                        | 200         |
| Conflicting duplicate                  | 409         |
| Invalid or missing API key             | 401         |
| Invalid payload                        | 422         |
| Unsupported measurement or association | 400         |
| SQLAlchemy database failure            | 503         |

For new measurements, the configured metric/unit combination is `soil_moisture` / `adc_raw`.

The API must use `garden_app`, not `garden_owner`.

The `/health` endpoint verifies API responsiveness, not database connectivity. Database-backed endpoints require separate verification.

## 8. Backup

Backups are currently manual.

Create a private directory:

```bash
mkdir -p ~/garden-backups
chmod 700 ~/garden-backups
```

Create a custom-format backup:

```bash
sudo -u postgres pg_dump \
  -Fc -d smart_garden \
  -f /tmp/smart_garden.dump

sudo install -o omnimrt -g omnimrt -m 600 \
  /tmp/smart_garden.dump \
  ~/garden-backups/smart_garden.dump

sudo rm /tmp/smart_garden.dump
```

Inspect the backup:

```bash
pg_restore -l ~/garden-backups/smart_garden.dump
```

Keep backup files outside the Git repository. A backup must be tested through restoration before being considered recoverable.

## 9. Restoration verification

Never perform a recovery drill against the live `smart_garden` database.

Create an isolated database:

```bash
sudo -u postgres createdb \
  -O garden_owner smart_garden_restore_test
```

Make the backup accessible to the PostgreSQL system user without exposing it publicly:

```bash
sudo install -o postgres -g postgres -m 600 \
  ~/garden-backups/smart_garden.dump \
  /var/lib/postgresql/smart_garden_restore_test.dump
```

Restore:

```bash
sudo -u postgres pg_restore \
  --exit-on-error \
  --no-owner \
  --role=garden_owner \
  -d smart_garden_restore_test \
  /var/lib/postgresql/smart_garden_restore_test.dump
```

Verify restored tables, measurement records, and Alembic revision. Reapply and verify the permissions policy:

```bash
sudo -u postgres psql \
  -X -v ON_ERROR_STOP=1 \
  -d smart_garden_restore_test \
  -f scripts/database_permissions.sql
```

After successful verification, remove the isolated recovery database and temporary backup copy:

```bash
sudo -u postgres dropdb smart_garden_restore_test
sudo rm /var/lib/postgresql/smart_garden_restore_test.dump
```

The original backup and live database must remain untouched.

## 10. Monitoring and troubleshooting

The existing `garden-monitor.timer` continues to collect CPU temperature readings approximately every five minutes.

Its CSV data is stored at:

`/home/omnimrt/gardenpi/readings.csv`

The monitoring system remains independent of PostgreSQL sensor-measurement ingestion.

Inspect service logs:

```bash
journalctl -u garden-api.service -n 50 --no-pager
```

Inspect service status:

```bash
systemctl status garden-api.service
systemctl status postgresql
systemctl status garden-monitor.timer
```

Preserve database contents, `.env`, and `readings.csv` during application updates or rollback.

Schema downgrades and database restores must be planned separately from Git rollback.

## 11. Security and operational limitations

- FastAPI binds to `127.0.0.1`.
- PostgreSQL is intended for local connections.
- API ingestion requires a secret API key.
- The application database role does not own the tables.
- Historical measurements cannot be updated or deleted by `garden_app`.
- Database backups are manual; scheduled backups and off-device retention are not yet configured.
- Database permissions must be rechecked after restoration or role changes.
- A successful `/health` response alone does not guarantee PostgreSQL availability.
