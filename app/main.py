
from pathlib import Path
from fastapi import FastAPI, HTTPException
from app.system_monitor import get_latest_reading
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.persistence import get_measurements
from fastapi import HTTPException, Response, status

from app.auth import require_sensor_api_key
from app.persistence import insert_measurement
from app.schemas import MeasurementCreate, MeasurementResponse

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

@app.get(
    "/api/garden/measurements",
    tags=["Garden"],
    summary="Retrieve sensor measurements",
)
def read_measurements(
    sensor_id: Annotated[str, Query(min_length=1)],
    session: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    measurements = get_measurements(
        session=session,
        sensor_external_id=sensor_id,
        limit=limit,
    )

    return [
        {
            "measurement_id": m.measurement_id,
            "sensor_id": sensor_id,
            "metric": m.metric,
            "value": m.value,
            "unit": m.unit,
            "recorded_at": m.recorded_at,
        }
        for m in measurements
    ]

@app.post(
    "/api/garden/measurements",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Garden"],
    summary="Submit sensor measurement",
)
def create_measurement(
    payload: MeasurementCreate,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_sensor_api_key)],
):
    try:
        measurement, created = insert_measurement(
            session=session,
            measurement_id=payload.measurement_id,
            device_external_id=payload.device_id,
            sensor_external_id=payload.sensor_id,
            metric=payload.metric,
            value=payload.value,
            unit=payload.unit,
        )

        result = MeasurementResponse(
            id=measurement.id,
            status="created" if created else "existing",
            recorded_at=measurement.recorded_at.isoformat(),
        )

        session.commit()

    except ValueError as exc:
        session.rollback()

        if str(exc) == "Conflicting duplicate measurement":
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        session.rollback()

        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable",
        ) from exc

    if not created:
        response.status_code = status.HTTP_200_OK

    return result