
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import Device, Sensor, Measurement


def get_measurements(
    session: Session,
    sensor_external_id: str,
    limit: int = 10,
) -> list[Measurement]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    statement = (
        select(Measurement)
        .join(Sensor, Measurement.sensor_id == Sensor.id)
        .where(Sensor.sensor_id == sensor_external_id)
        .order_by(
            Measurement.recorded_at.desc(),
            Measurement.id.desc(),
        )
        .limit(limit)
    )

    return list(session.scalars(statement).all())


def insert_measurement(
    session: Session,
    measurement_id: str,
    device_external_id: str,
    sensor_external_id: str,
    metric: str,
    value: float,
    unit: str,
) -> tuple[Measurement, bool]:

    def matches_existing(existing: Measurement) -> bool:
        original_device = session.get(Device, existing.device_id)
        original_sensor = session.get(Sensor, existing.sensor_id)


        return (
            original_device is not None
            and original_sensor is not None
            and original_device.device_id == device_external_id
            and original_sensor.sensor_id == sensor_external_id
            and existing.value == value
            and existing.unit == unit
            and existing.metric == metric
        )

    # First check whether this measurement already exists
    existing = session.scalar(
        select(Measurement).where(
            Measurement.measurement_id == measurement_id
        )
    )

    if existing is not None:
        if matches_existing(existing):
            return existing, False

        raise ValueError("Conflicting duplicate measurement")

    # Only validate supported combinations for NEW measurements
    if (metric, unit) != ("soil_moisture", "adc_raw"):
        raise ValueError("Unsupported metric/unit combination")

    # New measurements require a current device-sensor association
    sensor = session.scalar(
        select(Sensor)
        .join(Device, Sensor.device_id == Device.id)
        .where(
            Sensor.sensor_id == sensor_external_id,
            Device.device_id == device_external_id,
        )
    )

    if sensor is None:
        raise ValueError("Unknown sensor or device association")

    if sensor.metric != metric:
        raise ValueError("Sensor metric mismatch")

    statement = (
        pg_insert(Measurement)
        .values(
            measurement_id=measurement_id,
            device_id=sensor.device_id,
            sensor_id=sensor.id,
            pot_id=sensor.pot_id,
            value=value,
            unit=unit,
            metric=metric,
        )
        .on_conflict_do_nothing(
            index_elements=["measurement_id"]
        )
        .returning(Measurement.id)
    )

    new_id = session.scalar(statement)

    if new_id is not None:
        return session.get(Measurement, new_id), True

    # Handles a concurrent request that inserted the same ID
    existing = session.scalar(
        select(Measurement).where(
            Measurement.measurement_id == measurement_id
        )
    )

    if existing is not None and matches_existing(existing):
        return existing, False

    raise ValueError("Conflicting duplicate measurement")
