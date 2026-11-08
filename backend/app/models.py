from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class TrafficObservation(Base):
    __tablename__ = "traffic_observations"
    __table_args__ = (UniqueConstraint("sensor_id", "timestamp", name="uq_sensor_timestamp"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_id: Mapped[str] = mapped_column(String(120), index=True)
    timestamp: Mapped[object] = mapped_column(DateTime, index=True)
    vehicle_count: Mapped[int] = mapped_column(Integer, default=0)
    cars: Mapped[int] = mapped_column(Integer, default=0)
    vans: Mapped[int] = mapped_column(Integer, default=0)
    trucks: Mapped[int] = mapped_column(Integer, default=0)
    other: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(30), default="demo")

class RefreshLog(Base):
    __tablename__ = "refresh_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[object] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(String(500))
    rows_imported: Mapped[int] = mapped_column(Integer, default=0)
