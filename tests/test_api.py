
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_system_status_success(tmp_path, monkeypatch):
    csv_file = tmp_path / "readings.csv"

    csv_file.write_text(
        "timestamp,cpu_temperature_c\n"
        "2026-11-02T19:00:00+01:00,30.8\n"
        "2026-11-02T19:05:00+01:00,31.2\n"
    )

    monkeypatch.setattr("app.main.READINGS_FILE", csv_file)

    response = client.get("/api/system")

    assert response.status_code == 200
    assert response.json() == {
        "timestamp": "2026-11-02T19:05:00+01:00",
        "cpu": {
            "temperature_c": 31.2
        }
    }


def test_system_status_missing_data(tmp_path, monkeypatch):
    csv_file = tmp_path / "missing.csv"

    monkeypatch.setattr("app.main.READINGS_FILE", csv_file)

    response = client.get("/api/system")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No system monitoring data available"
    }


def test_system_status_invalid_data(tmp_path, monkeypatch):
    csv_file = tmp_path / "readings.csv"

    csv_file.write_text(
        "timestamp,cpu_temperature_c\n"
        "2026-11-02T19:05:00+01:00,invalid\n"
    )

    monkeypatch.setattr("app.main.READINGS_FILE", csv_file)

    response = client.get("/api/system")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Invalid system monitoring data"
    }
