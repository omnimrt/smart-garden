from pydantic import BaseModel, Field


class MeasurementCreate(BaseModel):
    measurement_id: str = Field(min_length=1, max_length=100)
    device_id: str = Field(min_length=1, max_length=100)
    sensor_id: str = Field(min_length=1, max_length=100)
    metric: str = Field(min_length=1, max_length=50)
    value: float
    unit: str = Field(min_length=1, max_length=50)


class MeasurementResponse(BaseModel):
    id: int
    status: str
    recorded_at: str