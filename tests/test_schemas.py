import math

import pytest
from pydantic import ValidationError

from app.schemas import MeasurementCreate
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch


VALID_PAYLOAD = {
    "measurement_id": "reading-001",
    "device_id": "esp32-01",
    "sensor_id": "soil-01",
    "metric": "soil_moisture",
    "value": 2450,
    "unit": "adc_raw",
}


@pytest.mark.parametrize(
    "value",
    [math.nan, math.inf, -math.inf],
)
def test_reject_non_finite_values(value):
    with pytest.raises(ValidationError):
        MeasurementCreate(**{**VALID_PAYLOAD, "value": value})


@pytest.mark.parametrize(
    "field",
    ["measurement_id", "device_id", "sensor_id", "metric", "unit"],
)
def test_reject_blank_strings(field):
    with pytest.raises(ValidationError):
        MeasurementCreate(**{**VALID_PAYLOAD, field: "   "})


def test_accept_valid_measurement():
    measurement = MeasurementCreate(**VALID_PAYLOAD)

    assert measurement.value == 2450
    assert measurement.metric == "soil_moisture"



def test_post_measurement_rejects_blank_identifier():
    payload = {
        **VALID_PAYLOAD,
        "measurement_id": "   ",
    }

    with patch.dict("os.environ", {"SENSOR_API_KEY": "test-api-key"}):
        with TestClient(app) as client:
            response = client.post(
                "/api/garden/measurements",
                json=payload,
                headers={"X-API-Key": "test-api-key"},
            )

    assert response.status_code == 422