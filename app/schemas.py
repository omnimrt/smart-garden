from pydantic import BaseModel, Field, field_validator


class MeasurementCreate(BaseModel):
    measurement_id: str = Field(min_length=1, max_length=100)
    device_id: str = Field(min_length=1, max_length=100)
    sensor_id: str = Field(min_length=1, max_length=100)
    metric: str = Field(min_length=1, max_length=50)
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=50)

    @field_validator(
        "measurement_id",
        "device_id",
        "sensor_id",
        "metric",
        "unit",
    )
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank")
        return value


class MeasurementResponse(BaseModel):
    id: int
    status: str
    recorded_at: str