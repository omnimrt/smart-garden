import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from collections.abc import Generator
from sqlalchemy.orm import Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not configured"
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session