"""
Pydantic v2 schemas — Phase 10: Transport Management (Enhanced)
Includes: GPS tracking, route pickup/drop schedules, starting/ending points
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    registration_number: str = Field(..., max_length=30)
    vehicle_type: str = Field("bus", max_length=50)
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    capacity: int = Field(40, ge=1)
    color: Optional[str] = None
    chassis_number: Optional[str] = None
    odometer_reading: Optional[int] = None
    vehicle_status: str = Field("active", pattern="^(active|on_route|maintenance|breakdown)$")
    driver_id: Optional[UUID] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_license: Optional[str] = None
    conductor_id: Optional[UUID] = None
    conductor_name: Optional[str] = None
    conductor_phone: Optional[str] = None
    insurance_expiry: Optional[date] = None
    fitness_expiry: Optional[date] = None
    permit_expiry: Optional[date] = None
    gps_device_id: Optional[str] = None


class VehicleUpdate(BaseModel):
    vehicle_type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    capacity: Optional[int] = None
    color: Optional[str] = None
    chassis_number: Optional[str] = None
    odometer_reading: Optional[int] = None
    vehicle_status: Optional[str] = None
    driver_id: Optional[UUID] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_license: Optional[str] = None
    conductor_id: Optional[UUID] = None
    conductor_name: Optional[str] = None
    conductor_phone: Optional[str] = None
    insurance_expiry: Optional[date] = None
    fitness_expiry: Optional[date] = None
    permit_expiry: Optional[date] = None
    gps_device_id: Optional[str] = None
    is_active: Optional[bool] = None


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    registration_number: str
    vehicle_type: str
    make: Optional[str]
    model: Optional[str]
    year: Optional[int]
    capacity: int
    color: Optional[str]
    chassis_number: Optional[str]
    odometer_reading: Optional[int]
    vehicle_status: str
    driver_id: Optional[UUID]
    driver_name: Optional[str]
    driver_phone: Optional[str]
    driver_license: Optional[str]
    conductor_id: Optional[UUID]
    conductor_name: Optional[str]
    conductor_phone: Optional[str]
    insurance_expiry: Optional[date]
    fitness_expiry: Optional[date]
    permit_expiry: Optional[date]
    gps_device_id: Optional[str]
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    last_gps_update: Optional[datetime]
    is_active: bool


# ─── GPS Tracking ─────────────────────────────────────────────────────────────

class GPSUpdateRequest(BaseModel):
    """Sent by GPS device or driver app to record a vehicle position ping."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed_kmph: Optional[float] = Field(None, ge=0)
    heading_degrees: Optional[int] = Field(None, ge=0, le=360)
    altitude_meters: Optional[float] = None
    accuracy_meters: Optional[float] = None
    recorded_at: Optional[datetime] = None   # uses server time when None
    source: str = Field("driver_app", pattern="^(device|driver_app|manual)$")


class GPSLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID
    latitude: float
    longitude: float
    speed_kmph: Optional[float]
    heading_degrees: Optional[int]
    altitude_meters: Optional[float]
    accuracy_meters: Optional[float]
    recorded_at: datetime
    source: str
    created_at: datetime


class VehicleLocationResponse(BaseModel):
    """Current location summary for a vehicle (for fleet overview)."""
    vehicle_id: UUID
    registration_number: str
    vehicle_type: str
    driver_name: Optional[str]
    driver_phone: Optional[str]
    vehicle_status: str
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    last_gps_update: Optional[datetime]
    is_active: bool


class StopCreate(BaseModel):
    name: str = Field(..., max_length=200)
    address: Optional[str] = None
    landmark: Optional[str] = Field(None, max_length=200)
    stop_order: int = Field(..., ge=1)
    pickup_time: Optional[time] = None    # morning: when bus arrives to pick up
    drop_time: Optional[time] = None      # evening: when bus arrives to drop off
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fare: int = Field(0, ge=0)


class StopUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    landmark: Optional[str] = None
    stop_order: Optional[int] = None
    pickup_time: Optional[time] = None
    drop_time: Optional[time] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fare: Optional[int] = None


class StopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    name: str
    address: Optional[str]
    landmark: Optional[str]
    stop_order: int
    pickup_time: Optional[time]    # morning pickup time at this stop
    drop_time: Optional[time]      # evening drop time at this stop
    latitude: Optional[float]
    longitude: Optional[float]
    fare: int


class RouteCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    vehicle_id: Optional[UUID] = None
    route_type: str = Field("both", pattern="^(morning|evening|both)$")
    # Starting point (origin / depot / first pickup)
    starting_point_name: Optional[str] = Field(None, max_length=300)
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    # Ending point (school or last destination)
    ending_point_name: Optional[str] = Field(None, max_length=300)
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    # Morning schedule (starting point → school)
    morning_departure_time: Optional[time] = None   # bus departs starting point
    school_arrival_time: Optional[time] = None      # bus arrives at school
    # Evening schedule (school → home drops)
    evening_departure_time: Optional[time] = None   # bus departs school
    # Distance / ETA
    total_distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    # Legacy generic times
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    stops: list[StopCreate] = []


class RouteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    vehicle_id: Optional[UUID] = None
    route_type: Optional[str] = None
    starting_point_name: Optional[str] = None
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    ending_point_name: Optional[str] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    morning_departure_time: Optional[time] = None
    school_arrival_time: Optional[time] = None
    evening_departure_time: Optional[time] = None
    total_distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    description: Optional[str]
    vehicle_id: Optional[UUID]
    route_type: str
    starting_point_name: Optional[str]
    start_latitude: Optional[float]
    start_longitude: Optional[float]
    ending_point_name: Optional[str]
    end_latitude: Optional[float]
    end_longitude: Optional[float]
    morning_departure_time: Optional[time]
    school_arrival_time: Optional[time]
    evening_departure_time: Optional[time]
    total_distance_km: Optional[float]
    estimated_duration_minutes: Optional[int]
    start_time: Optional[time]
    end_time: Optional[time]
    is_active: bool
    stops: list[StopResponse] = []


class StudentTransportAssign(BaseModel):
    student_id: UUID
    route_id: UUID
    stop_id: UUID
    academic_year_id: UUID
    subscription_type: str = Field("both", pattern="^(both|pickup|drop)$")


class StudentTransportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    school_id: UUID
    route_id: UUID
    stop_id: UUID
    academic_year_id: UUID
    subscription_type: str
    is_active: bool


class VehicleMaintenanceCreate(BaseModel):
    vehicle_id: UUID
    maintenance_type: str = Field(..., max_length=100)
    description: Optional[str] = None
    maintenance_date: date
    next_due_date: Optional[date] = None
    cost: int = Field(0, ge=0)
    vendor_name: Optional[str] = None
    odometer_reading: Optional[int] = None
    status: str = "completed"
    notes: Optional[str] = None


class VehicleMaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID
    maintenance_type: str
    description: Optional[str]
    maintenance_date: date
    next_due_date: Optional[date]
    cost: int
    vendor_name: Optional[str]
    odometer_reading: Optional[int]
    status: str
    notes: Optional[str]


class FuelLogCreate(BaseModel):
    vehicle_id: UUID
    fuel_date: date
    fuel_quantity: Optional[float] = None
    fuel_cost: int = Field(0, ge=0)
    odometer_reading: Optional[int] = None
    pump_name: Optional[str] = None


class FuelLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID
    fuel_date: date
    fuel_quantity: Optional[float]
    fuel_cost: int
    odometer_reading: Optional[int]
    pump_name: Optional[str]
