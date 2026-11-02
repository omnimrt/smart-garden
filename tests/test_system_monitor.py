
from pathlib import Path
from app.system_monitor import get_latest_reading
import pytest


def test_get_latest_reading(tmp_path: Path):
    csv_file = tmp_path / "readings.csv"

    csv_file.write_text(
        "timestamp,cpu_temperature_c\n"
        "2026-11-02T19:00:00+01:00,30.8\n"
        "2026-11-02T19:05:00+01:00,31.2\n"
    )

    result = get_latest_reading(csv_file)

    assert result == {
        "timestamp": "2026-11-02T19:05:00+01:00",
        "temperature_c": 31.2
    }


def test_missing_csv_file(tmp_path: Path):
    csv_file = tmp_path / "missing.csv"

    assert get_latest_reading(csv_file) is None


def test_empty_csv_file(tmp_path: Path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("timestamp,cpu_temperature_c\n")

    assert get_latest_reading(csv_file) is None

def test_invalid_temperature(tmp_path):
    csv_file = tmp_path / "readings.csv"

    csv_file.write_text(
        "timestamp,cpu_temperature_c\n"
        "2026-11-02T19:05:00+01:00,invalid\n"
    )

    with pytest.raises(ValueError):
        get_latest_reading(csv_file)


def test_invalid_timestamp(tmp_path):
    csv_file = tmp_path / "readings.csv"

    csv_file.write_text(
        "timestamp,cpu_temperature_c\n"
        "yesterday,31.2\n"
    )

    with pytest.raises(ValueError):
        get_latest_reading(csv_file)
