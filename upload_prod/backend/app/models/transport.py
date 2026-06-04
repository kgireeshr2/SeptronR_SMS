"""
SQLAlchemy models — Phase 10: Transport Management
Tables: vehicles, routes, stops, student_transport, vehicle_maintenance, vehicle_fuel_log
"""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger,
    String, Text, Time, UniqueConstraint,
)
from app.models.compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.staff import Staff
    from app.models.students import Student
    from app.models.academic import AcademicYear


class Vehicle(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("school_id", "registration_number", name="vehicles_school_reg_ux"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    registration_number: Mapped[str] = mapped_column(String(30), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False, default="bus")
    make: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=40)
    driver_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True
    )
    conductor_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True
    )
    insurance_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fitness_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    permit_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gps_device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    driver_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    driver_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    driver_license: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    conductor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    conductor_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Additional vehicle details
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    chassis_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    odometer_reading: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vehicle_status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')  # active|on_route|maintenance|breakdown
    # Live GPS state (cached last known position)
    current_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    current_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    last_gps_update: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    routes: Mapped[list["Route"]] = relationship("Route", back_populates="vehicle", lazy="noload")
    maintenance_logs: Mapped[list["VehicleMaintenance"]] = relationship(
        "VehicleMaintenance", back_populates="vehicle", lazy="noload", cascade="all, delete-orphan"
    )
    fuel_logs: Mapped[list["VehicleFuelLog"]] = relationship(
        "VehicleFuelLog", back_populates="vehicle", lazy="noload", cascade="all, delete-orphan"
    )
    gps_logs: Mapped[list["VehicleGPSLog"]] = relationship(
        "VehicleGPSLog", back_populates="vehicle", lazy="noload", cascade="all, delete-orphan"
    )


class Route(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "routes"
    __table_args__ = (UniqueConstraint("school_id", "name", name="routes_school_name_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vehicle_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True
    )
    route_type: Mapped[str] = mapped_column(String(10), nullable=False, default='both')  # morning|evening|both
    # Start/end geography
    starting_point_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    ending_point_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    start_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    start_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    end_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    end_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    # Schedule — morning (depot→school)
    morning_departure_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)  # bus leaves starting point
    school_arrival_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)     # bus reaches school
    # Schedule — evening (school→home)
    evening_departure_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)  # bus leaves school
    # Legacy / generic times kept for backward compat
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    # Distance / ETA
    total_distance_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", back_populates="routes", lazy="noload")
    stops: Mapped[list["Stop"]] = relationship(
        "Stop", back_populates="route", lazy="noload",
        cascade="all, delete-orphan", order_by="Stop.stop_order",
    )


class Stop(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stops"
    __table_args__ = (UniqueConstraint("route_id", "stop_order", name="stops_route_order_ux"),)

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    route_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    landmark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    stop_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    pickup_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)   # morning: bus arrives at stop
    drop_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)     # evening: bus drops at stop
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    fare: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    route: Mapped["Route"] = relationship("Route", back_populates="stops", lazy="noload")


class StudentTransport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_transport"
    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id", name="student_transport_student_year_ux"),
    )

    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    route_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False
    )
    stop_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stops.id"), nullable=False
    )
    academic_year_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    subscription_type: Mapped[str] = mapped_column(String(20), nullable=False, default="both")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class VehicleMaintenance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "vehicle_maintenance"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    maintenance_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    maintenance_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vendor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    odometer_reading: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="maintenance_logs", lazy="noload")


class VehicleGPSLog(Base, UUIDPrimaryKeyMixin):
    """Stores individual GPS pings from vehicle GPS devices or driver app."""
    __tablename__ = "vehicle_gps_logs"
    __table_args__ = (
        Index("ix_vehicle_gps_logs_vehicle_recorded", "vehicle_id", "recorded_at"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    speed_kmph: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    heading_degrees: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    altitude_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    accuracy_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default='driver_app')  # device|driver_app|manual
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="gps_logs", lazy="noload")


class VehicleFuelLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "vehicle_fuel_log"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    fuel_date: Mapped[date] = mapped_column(Date, nullable=False)
    fuel_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    fuel_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    odometer_reading: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pump_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="fuel_logs", lazy="noload")
