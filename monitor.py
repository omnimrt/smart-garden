
import csv
import subprocess
from datetime import datetime
from pathlib import Path

def parse_temperature(output):
    return float(output.split("=")[1].replace("'C", ""))


def read_cpu_temperature():
    result = subprocess.check_output(
        ["vcgencmd", "measure_temp"],
        text=True
    ).strip()

    return parse_temperature(result)

def save_reading(temperature, file_path=Path("readings.csv")):
    new_file = not file_path.exists()

    with file_path.open("a", newline="") as file:
        writer = csv.writer(file)

        if new_file:
            writer.writerow(["timestamp", "cpu_temperature_c"])

        writer.writerow([
            datetime.now().astimezone().isoformat(timespec="seconds"),
            temperature
        ])

def main():
    temperature = read_cpu_temperature()
    save_reading(temperature)
    print(f"Recorded CPU temperature: {temperature:.1f}°C")


if __name__ == "__main__":
    main()