import os
import secrets

from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

load_dotenv()

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def require_sensor_api_key(
    provided_key: str | None = Security(api_key_header),
) -> None:
    expected_key = os.getenv("SENSOR_API_KEY")

    if not expected_key:
        raise RuntimeError("SENSOR_API_KEY is not configured")

    if not provided_key or not secrets.compare_digest(
        provided_key, expected_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )