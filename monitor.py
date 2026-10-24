
import csv
import subprocess
from datetime import datetime
from pathlib import Path

# Read the Raspberry Pi CPU temperature
result = subprocess.check_output(
    ["vcgencmd", "measure_temp"],
    text=True
).strip()

temperature = float(result.split("=")[1].replace("'C", ""))

# Prepare our CSV file
file_path = Path("readings.csv")
new_file = not file_path.exists()

# Save the measurement
with file_path.open("a", newline="") as file:
    writer = csv.writer(file)

    if new_file:
        writer.writerow(["timestamp", "cpu_temperature_c"])

    writer.writerow([
        datetime.now().astimezone().isoformat(timespec="seconds"),
        temperature
    ])

print(f"Recorded CPU temperature: {temperature:.1f}°C")
