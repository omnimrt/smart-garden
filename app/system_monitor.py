
import csv
from pathlib import Path
from datetime import datetime

def get_latest_reading(file_path: Path):
    if not file_path.exists():
        return None

    with file_path.open("r", newline="") as file:
        reader = csv.DictReader(file)
        latest = None

        for row in reader:
            latest = row

    if latest is None:
        return None

    
    timestamp = datetime.fromisoformat(latest["timestamp"])

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Timestamp must include timezone information")


 
    return {
        "timestamp": timestamp.isoformat(),
        "temperature_c": float(latest["cpu_temperature_c"])
    }

