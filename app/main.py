
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.system_monitor import get_latest_reading


app = FastAPI()

READINGS_FILE = Path("readings.csv")


@app.get("/health")
def health_check():
    return {"status": "ok"}




@app.get(
    "/api/system",
    summary="Get system monitoring data",
    description=(
        "Returns the latest recorded Raspberry Pi system metrics "
        "from CSV storage. Currently includes CPU temperature "
        "and the measurement timestamp."
    ),
    tags=["System Monitoring"],
    responses={
        200: {
            "description": "Latest system monitoring data",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2026-11-02T19:05:00+01:00",
                        "cpu": {
                            "temperature_c": 31.2
                        }
                    }
                }
            }
        },
        404: {"description": "No monitoring data available"},
        500: {"description": "Invalid monitoring data"}
    }
)

def get_system_status():
    try:
        reading = get_latest_reading(READINGS_FILE)
    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=500,
            detail="Invalid system monitoring data"
        ) from None

    if reading is None:
        raise HTTPException(
            status_code=404,
            detail="No system monitoring data available"
        )

    return {
        "timestamp": reading["timestamp"],
        "cpu": {
            "temperature_c": reading["temperature_c"]
        }
    }
