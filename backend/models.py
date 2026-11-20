"""Database tables for residents, flats, monthly activity, and reports."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Flat(Base):
    __tablename__ = "flats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flat_no: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    block: Mapped[str] = mapped_column(String(20))
    type: Mapped[str] = mapped_column(String(10))
    area_sqft: Mapped[int] = mapped_column(Integer)
    users: Mapped[list["User"]] = relationship(back_populates="flat")
    bills: Mapped[list["Bill"]] = relationship(back_populates="flat")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    flat_id: Mapped[int | None] = mapped_column(ForeignKey("flats.id"), nullable=True)
    flat: Mapped[Flat | None] = relationship(back_populates="users")


class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = (UniqueConstraint("flat_id", "month", "year", "category"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id"), index=True)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column(Float)
    units: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    due_date: Mapped[date] = mapped_column(Date)
    flat: Mapped[Flat] = relationship(back_populates="bills")


class GymLog(Base):
    __tablename__ = "gym_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    minutes: Mapped[int] = mapped_column(Integer)


class MeterReading(Base):
    """Electricity or water usage recorded before a monthly bill is generated."""

    __tablename__ = "meter_readings"
    __table_args__ = (UniqueConstraint("flat_id", "month", "year", "category"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id"), index=True)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(30))
    units: Mapped[float] = mapped_column(Float)


class PointEntry(Base):
    __tablename__ = "point_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id"), index=True)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(30))
    points: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(500), default="")


class ReportHistory(Base):
    __tablename__ = "report_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id"), index=True)
    file_path: Mapped[str] = mapped_column(String(500))
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MaintenanceRequest(Base):
    """A repair or shared-space issue reported by a resident."""

    __tablename__ = "maintenance_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flat_id: Mapped[int] = mapped_column(ForeignKey("flats.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    created_on: Mapped[date] = mapped_column(Date, default=date.today)
