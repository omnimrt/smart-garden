from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    device_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )


class Pot(Base):
    __tablename__ = "pots"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    pot_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )
    plant_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    sensor_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False
    )

    pot_id: Mapped[int | None] = mapped_column(
        ForeignKey("pots.id"),
        nullable=True
    )

    metric: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    measurement_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensors.id"),
        nullable=False
    )

    pot_id: Mapped[int | None] = mapped_column(
        ForeignKey("pots.id"),
        nullable=True
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
    )

    metric: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )