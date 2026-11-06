import os
from unittest.mock import patch
from unittest.mock import MagicMock
from sqlalchemy.exc import OperationalError

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Device, Pot, Sensor, Measurement
from app.persistence import get_measurements
from sqlalchemy.exc import IntegrityError
from app.persistence import insert_measurement
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, func
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db

load_dotenv()

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

if not TEST_DATABASE_URL.rsplit("/", 1)[-1] == "smart_garden_test":
    raise RuntimeError("Refusing to run tests against a non-test database")


@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL)

    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
    bind=connection,
    join_transaction_mode="create_savepoint",
)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def test_get_measurements(db_session):
    device = Device(
        device_id="test-esp32-01",
        name="Test ESP32",
    )

    pot = Pot(
        pot_id="test-pot-01",
        plant_name="Basil",
    )

    db_session.add_all([device, pot])
    db_session.flush()

    sensor = Sensor(
        sensor_id="test-soil-01",
        device_id=device.id,
        pot_id=pot.id,
        metric="soil_moisture",
    )

    db_session.add(sensor)
    db_session.flush()

    measurement = Measurement(
        measurement_id="test-reading-001",
        device_id=device.id,
        sensor_id=sensor.id,
        metric="soil_moisture",
        pot_id=pot.id,
        value=2450,
        unit="adc_raw",
    )   

    db_session.add(measurement)
    db_session.flush()

    readings = get_measurements(
        db_session,
        sensor_external_id="test-soil-01",
    )

    assert len(readings) == 1
    assert readings[0].value == 2450
    assert readings[0].measurement_id == "test-reading-001"

def test_duplicate_measurement_rejected(db_session):
    device = Device(
        device_id="duplicate-test-device",
        name="Test ESP32",
    )
    db_session.add(device)
    db_session.flush()

    sensor = Sensor(
        sensor_id="duplicate-test-sensor",
        device_id=device.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    first = Measurement(
        measurement_id="duplicate-reading-001",
        device_id=device.id,
        sensor_id=sensor.id,
        metric="soil_moisture",
        value=2450,
        unit="adc_raw",
    )

    db_session.add(first)
    db_session.flush()

    second = Measurement(
        measurement_id="duplicate-reading-001",
        device_id=device.id,
        sensor_id=sensor.id,
        metric="soil_moisture",
        value=2300,
        unit="adc_raw",
    )

    db_session.add(second)

    with pytest.raises(IntegrityError):
        db_session.flush()

def test_measurement_invalid_sensor_rejected(db_session):
    measurement = Measurement(
        measurement_id="invalid-sensor-reading-001",
        sensor_id=999999,
        value=2450,
        unit="adc_raw",
    )

    db_session.add(measurement)

    with pytest.raises(IntegrityError):
        db_session.flush()

def test_insert_measurement_preserves_pot(db_session):
    device = Device(
        device_id="pot-test-device",
        name="Test ESP32",
    )
    pot = Pot(
        pot_id="pot-test-basil",
        plant_name="Basil",
    )

    db_session.add_all([device, pot])
    db_session.flush()

    sensor = Sensor(
        sensor_id="pot-test-sensor",
        device_id=device.id,
        pot_id=pot.id,
        metric="soil_moisture",
    )

    db_session.add(sensor)
    db_session.flush()

    measurement, created = insert_measurement(
        session=db_session,
        measurement_id="pot-test-reading-001",
        device_external_id="pot-test-device",
        sensor_external_id="pot-test-sensor",
        metric="soil_moisture",
        value=2450,
        unit="adc_raw",
    )
    assert created is True
    assert measurement.sensor_id == sensor.id
    assert measurement.pot_id == pot.id
    assert measurement.value == 2450

def test_measurements_preserve_historical_pot(db_session):
    device = Device(
        device_id="history-test-device",
        name="Test ESP32",
    )

    basil = Pot(
        pot_id="history-basil",
        plant_name="Basil",
    )

    thyme = Pot(
        pot_id="history-thyme",
        plant_name="Thyme",
    )

    db_session.add_all([device, basil, thyme])
    db_session.flush()

    sensor = Sensor(
        sensor_id="history-test-sensor",
        device_id=device.id,
        pot_id=basil.id,
        metric="soil_moisture",
    )

    db_session.add(sensor)
    db_session.flush()

    first, created = insert_measurement(
        db_session,
        "history-reading-001",
        "history-test-device",
        "history-test-sensor",
        "soil_moisture",
        2450,
        "adc_raw",
    )

    assert created is True
    assert first.pot_id == basil.id

    # Move sensor to thyme
    sensor.pot_id = thyme.id
    db_session.flush()

    second, created = insert_measurement(
        db_session,
        "history-reading-002",
        "history-test-device",
        "history-test-sensor",
        "soil_moisture",
        2200,
        "adc_raw",
    )
    assert created is True
    assert second.pot_id == thyme.id

    # Historical measurement remains associated with basil
    db_session.refresh(first)

    assert first.pot_id == basil.id

def test_identical_measurement_retry(db_session):
    device = Device(
        device_id="retry-device",
        name="Test ESP32",
    )
    db_session.add(device)
    db_session.flush()

    sensor = Sensor(
        sensor_id="retry-sensor",
        device_id=device.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    payload = {
        "measurement_id": "retry-reading-001",
        "device_external_id": "retry-device",
        "sensor_external_id": "retry-sensor",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    first, first_created = insert_measurement(
        db_session, **payload
    )

    second, second_created = insert_measurement(
        db_session, **payload
    )

    assert first_created is True
    assert second_created is False
    assert first.id == second.id

    count = db_session.scalar(
        select(func.count())
        .select_from(Measurement)
        .where(Measurement.measurement_id == "retry-reading-001")
    )

    assert count == 1

def test_conflicting_measurement_retry(db_session):
    device = Device(
        device_id="conflict-device",
        name="Test ESP32",
    )
    db_session.add(device)
    db_session.flush()

    sensor = Sensor(
        sensor_id="conflict-sensor",
        device_id=device.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    payload = {
        "measurement_id": "conflict-reading-001",
        "device_external_id": "conflict-device",
        "sensor_external_id": "conflict-sensor",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    first, created = insert_measurement(
        db_session, **payload
    )
    assert created is True

    with pytest.raises(
        ValueError,
        match="Conflicting duplicate measurement"
    ):
        insert_measurement(
            db_session,
            **{**payload, "value": 2300}
        )

    db_session.refresh(first)
    assert first.value == 2450

def test_identical_retry_after_pot_reassignment(db_session):
    device = Device(
        device_id="reassign-device",
        name="Test ESP32",
    )

    basil = Pot(
        pot_id="reassign-basil",
        plant_name="Basil",
    )
    thyme = Pot(
        pot_id="reassign-thyme",
        plant_name="Thyme",
    )

    db_session.add_all([device, basil, thyme])
    db_session.flush()

    sensor = Sensor(
        sensor_id="reassign-sensor",
        device_id=device.id,
        pot_id=basil.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    payload = {
        "measurement_id": "reassign-reading-001",
        "device_external_id": "reassign-device",
        "sensor_external_id": "reassign-sensor",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    first, created = insert_measurement(db_session, **payload)
    assert created is True
    assert first.pot_id == basil.id

    # Sensor is moved to another pot
    sensor.pot_id = thyme.id
    db_session.flush()

    # Original measurement is delivered again
    second, created = insert_measurement(db_session, **payload)

    assert created is False
    assert second.id == first.id
    assert second.pot_id == basil.id

def test_identical_retry_after_device_reassignment(db_session):
    device_a = Device(
        device_id="device-a",
        name="ESP32 A",
    )
    device_b = Device(
        device_id="device-b",
        name="ESP32 B",
    )

    db_session.add_all([device_a, device_b])
    db_session.flush()

    sensor = Sensor(
        sensor_id="device-reassign-sensor",
        device_id=device_a.id,
        metric="soil_moisture",
    )

    db_session.add(sensor)
    db_session.flush()

    payload = {
        "measurement_id": "device-reassign-reading",
        "device_external_id": "device-a",
        "sensor_external_id": "device-reassign-sensor",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    first, created = insert_measurement(db_session, **payload)
    assert created is True

    sensor.device_id = device_b.id
    db_session.flush()

    second, created = insert_measurement(db_session, **payload)

    assert created is False
    assert second.id == first.id

def test_retry_after_sensor_metric_change(db_session):
    device = Device(
        device_id="metric-change-device",
        name="Test ESP32",
    )
    db_session.add(device)
    db_session.flush()

    sensor = Sensor(
        sensor_id="metric-change-sensor",
        device_id=device.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    payload = {
        "measurement_id": "metric-change-reading-001",
        "device_external_id": "metric-change-device",
        "sensor_external_id": "metric-change-sensor",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    first, created = insert_measurement(db_session, **payload)
    assert created is True

    # Simulate a change to the sensor's metric
    sensor.metric = "temperature"
    db_session.flush()

    # Retry the original measurement
    second, created = insert_measurement(db_session, **payload)

    assert created is False
    assert second.id == first.id

    # Different metric with the same ID must be rejected
    with pytest.raises(
        ValueError,
        match="Conflicting duplicate measurement",
    ):
        insert_measurement(
            db_session,
            **{**payload, "metric": "temperature"},
        )

def test_get_measurements_api(db_session):
    device = Device(
    device_id="api-test-device",
     name="Test ESP32",
    )
    db_session.add(device)
    db_session.flush()

    sensor = Sensor(
        sensor_id="api-test-sensor",
        device_id=device.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    insert_measurement(
        db_session,
        measurement_id="api-test-reading-001",
        device_external_id="api-test-device",
        sensor_external_id="api-test-sensor",
        metric="soil_moisture",
        value=2450,
        unit="adc_raw",
    )

    # Replace the application's normal database dependency
    # with our isolated test session.
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/garden/measurements",
                params={
                    "sensor_id": "api-test-sensor",
                    "limit": 10,
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["measurement_id"] == "api-test-reading-001"
        assert data[0]["value"] == 2450
        assert data[0]["metric"] == "soil_moisture"

    finally:
        app.dependency_overrides.clear()

def test_post_measurement_without_api_key():
    payload = {
        "measurement_id": "auth-test-001",
        "device_id": "esp32-01",
        "sensor_id": "soil-01",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/garden/measurements",
            json=payload,
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"

def test_post_measurement_authenticated(db_session):
    device = Device(
        device_id="post-test-device",
        name="Test ESP32",
    )
    db_session.add(device)
    db_session.flush()

    sensor = Sensor(
        sensor_id="post-test-sensor",
        device_id=device.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    payload = {
        "measurement_id": "post-test-reading-001",
        "device_id": "post-test-device",
        "sensor_id": "post-test-sensor",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with patch.dict(os.environ, {"SENSOR_API_KEY": "test-api-key"}):
            with TestClient(app) as client:
                response = client.post(
                    "/api/garden/measurements",
                    json=payload,
                    headers={"X-API-Key": "test-api-key"},
                )

        assert response.status_code == 201

        data = response.json()

        assert data["status"] == "created"
        assert isinstance(data["id"], int)
        assert data["recorded_at"]

        stored = db_session.scalar(
            select(Measurement).where(
                Measurement.measurement_id == "post-test-reading-001"
            )
        )

        assert stored is not None
        assert stored.value == 2450
        assert stored.metric == "soil_moisture"

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_post_measurement_identical_retry(db_session):
    device = Device(
        device_id="retry-api-device",
        name="Test ESP32",
    )
    db_session.add(device)
    db_session.flush()

    sensor = Sensor(
        sensor_id="retry-api-sensor",
        device_id=device.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    payload = {
        "measurement_id": "retry-api-reading-001",
        "device_id": "retry-api-device",
        "sensor_id": "retry-api-sensor",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with patch.dict(os.environ, {"SENSOR_API_KEY": "test-api-key"}):
            with TestClient(app) as client:
                first = client.post(
                    "/api/garden/measurements",
                    json=payload,
                    headers={"X-API-Key": "test-api-key"},
                )

                second = client.post(
                    "/api/garden/measurements",
                    json=payload,
                    headers={"X-API-Key": "test-api-key"},
                )

        assert first.status_code == 201
        assert second.status_code == 200

        assert first.json()["status"] == "created"
        assert second.json()["status"] == "existing"
        assert first.json()["id"] == second.json()["id"]

        count = db_session.scalar(
            select(func.count())
            .select_from(Measurement)
            .where(
                Measurement.measurement_id == "retry-api-reading-001"
            )
        )

        assert count == 1

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_post_measurement_conflicting_retry(db_session):
    device = Device(
        device_id="conflict-api-device",
        name="Test ESP32",
    )
    db_session.add(device)
    db_session.flush()

    sensor = Sensor(
        sensor_id="conflict-api-sensor",
        device_id=device.id,
        metric="soil_moisture",
    )
    db_session.add(sensor)
    db_session.flush()

    payload = {
        "measurement_id": "conflict-api-reading-001",
        "device_id": "conflict-api-device",
        "sensor_id": "conflict-api-sensor",
        "metric": "soil_moisture",
        "value": 2450,
        "unit": "adc_raw",
    }

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with patch.dict(os.environ, {"SENSOR_API_KEY": "test-api-key"}):
            with TestClient(app) as client:
                first = client.post(
                    "/api/garden/measurements",
                    json=payload,
                    headers={"X-API-Key": "test-api-key"},
                )

                conflicting = client.post(
                    "/api/garden/measurements",
                    json={**payload, "value": 3000},
                    headers={"X-API-Key": "test-api-key"},
                )

        assert first.status_code == 201
        assert conflicting.status_code == 409
        assert conflicting.json()["detail"] == (
            "Conflicting duplicate measurement"
        )

        stored = db_session.scalar(
            select(Measurement).where(
                Measurement.measurement_id == payload["measurement_id"]
            )
        )

        assert stored is not None
        assert stored.value == 2450

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_post_measurement_database_failure(db_session):
    fake_session = MagicMock()

    fake_session.commit.side_effect = OperationalError(
        "COMMIT",
        {},
        Exception("Simulated database failure"),
    )

    app.dependency_overrides[get_db] = lambda: fake_session

    try:
        with patch.dict(os.environ, {"SENSOR_API_KEY": "test-api-key"}):
            with patch("app.main.insert_measurement") as mock_insert:
                mock_measurement = MagicMock()
                mock_measurement.id = 123
                mock_measurement.recorded_at.isoformat.return_value = (
                    "2026-11-06T00:00:00+00:00"
                )

                mock_insert.return_value = (mock_measurement, True)

                with TestClient(app) as client:
                    response = client.post(
                        "/api/garden/measurements",
                        json={
                            "measurement_id": "db-failure-001",
                            "device_id": "esp32-01",
                            "sensor_id": "soil-01",
                            "metric": "soil_moisture",
                            "value": 2450,
                            "unit": "adc_raw",
                        },
                        headers={"X-API-Key": "test-api-key"},
                    )

        assert response.status_code == 503
        assert response.json()["detail"] == "Database temporarily unavailable"
        fake_session.rollback.assert_called_once()

    finally:
        app.dependency_overrides.pop(get_db, None)