# Smart Garden — Raspberry Pi Deployment

## Environment

- Host: gardenpi
- OS: Raspberry Pi OS (64-bit)
- Application directory: `/home/omnimrt/gardenpi`
- Python: 3.13
- API: FastAPI / Uvicorn
- Service: `garden-api.service`
- Bind address: `127.0.0.1:8000`

## Installation

From the Raspberry Pi:

```bash
cd /home/omnimrt/gardenpi
git pull --ff-only origin main
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -v
```

Install the systemd unit:

```bash
sudo cp deploy/garden-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now garden-api.service
```

## Service management

```bash
sudo systemctl restart garden-api.service
sudo systemctl stop garden-api.service
sudo systemctl start garden-api.service
systemctl status garden-api.service
```

## Verification

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/system
```

/health returns HTTP 200 when the API is responding. /api/system returns HTTP 200 when valid monitoring data is available, HTTP 404 when no data exists, and HTTP 500 when the stored data is invalid.

## Logs

```bash
journalctl -u garden-api.service -n 50 --no-pager
journalctl -u garden-api.service -f
```

## Monitoring integration

The existing `garden-monitor.timer` runs the CPU monitoring script approximately every five minutes.

Both services use:

`/home/omnimrt/gardenpi/readings.csv`

The monitoring service writes measurements; the API reads the latest measurement.

## Troubleshooting and recovery

If the API is unavailable:

1. Check `systemctl status garden-api.service`.
2. Inspect `journalctl -u garden-api.service -n 50`.
3. Verify that `.venv` and the installed dependencies exist.
4. Verify that `readings.csv` exists and is readable.
5. Restart the API service and repeat the health check.

If a deployment introduces a regression, stop the API, restore the last known working application revision and matching dependencies, then restart and verify the service. Preserve `readings.csv` and do not modify the monitoring timer during API recovery.

## Network security

Uvicorn binds to `127.0.0.1`. The API is accessible only from GardenPi itself.

Remote access and authentication are outside the scope of SG-13.
