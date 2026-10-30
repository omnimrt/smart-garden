import csv
from unittest.mock import patch
from monitor import read_cpu_temperature

from monitor import parse_temperature, save_reading
import subprocess
import pytest

def test_parse_temperature():
    result = parse_temperature("temp=30.1'C")
    assert result == 30.1


def test_save_reading(tmp_path):
    file_path = tmp_path / "test_readings.csv"

    save_reading(30.1, file_path)
    save_reading(31.5, file_path)

    with file_path.open("r", newline="") as file:
        rows = list(csv.reader(file))

    assert rows[0] == ["timestamp", "cpu_temperature_c"]
    assert len(rows) == 3
    assert float(rows[1][1]) == 30.1
    assert float(rows[2][1]) == 31.5

def test_read_cpu_temperature():
    with patch("monitor.subprocess.check_output") as mock_command:
        mock_command.return_value = "temp=32.5'C\n"

        temperature = read_cpu_temperature()

        assert temperature == 32.5

        mock_command.assert_called_once_with(
            ["vcgencmd", "measure_temp"],
            text=True
        )

def test_read_cpu_temperature_command_failure():
    with patch("monitor.subprocess.check_output") as mock_command:
        mock_command.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["vcgencmd", "measure_temp"]
        )

        with pytest.raises(subprocess.CalledProcessError):
            read_cpu_temperature()

        mock_command.assert_called_once()