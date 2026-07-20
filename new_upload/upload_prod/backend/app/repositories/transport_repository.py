"""
Repository — Phase 10: Transport Management
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.transport import (
    Vehicle, Route, Stop, StudentTransport, VehicleMaintenance, VehicleFuelLog, VehicleGPSLog,
)
from app.schemas.phase10 import (
    VehicleCreate, VehicleUpdate,
    RouteCreate, RouteUpdate,
    StopCreate, StopUpdate,
    StudentTransportAssign,
    VehicleMaintenanceCreate,
    FuelLogCreate,
    GPSUpdateRequest,
)


# ─── Vehicle ────────────────────────────────────────────────────────────────

async def list_vehicles(db: AsyncSession, school_id: str, active_only: bool = True) -> List[Vehicle]:
    q = select(Vehicle).where(Vehicle.school_id == school_id)
    if active_only:
        q = q.where(Vehicle.is_active == True)
    result = await db.execute(q.order_by(Vehicle.registration_number))
    return list(result.scalars().all())


async def get_vehicle(db: AsyncSession, school_id: str, vehicle_id: str) -> Optional[Vehicle]:
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.school_id == school_id)
    )
    return result.scalar_one_or_none()


async def create_vehicle(db: AsyncSession, school_id: str, data: VehicleCreate) -> Vehicle:
    vehicle = Vehicle(school_id=school_id, **data.model_dump())
    db.add(vehicle)
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


async def update_vehicle(db: AsyncSession, vehicle: Vehicle, data: VehicleUpdate) -> Vehicle:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(vehicle, k, v)
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


async def delete_vehicle(db: AsyncSession, vehicle: Vehicle) -> None:
    await db.delete(vehicle)
    await db.flush()


# ─── Route ──────────────────────────────────────────────────────────────────

async def list_routes(db: AsyncSession, school_id: str) -> List[Route]:
    result = await db.execute(
        select(Route)
        .where(Route.school_id == school_id)
        .options(selectinload(Route.stops))
        .order_by(Route.name)
    )
    return list(result.scalars().all())


async def get_route(db: AsyncSession, school_id: str, route_id: str) -> Optional[Route]:
    result = await db.execute(
        select(Route)
        .where(Route.id == route_id, Route.school_id == school_id)
        .options(selectinload(Route.stops))
    )
    return result.scalar_one_or_none()


async def create_route(db: AsyncSession, school_id: str, data: RouteCreate) -> Route:
    route = Route(school_id=school_id, **data.model_dump())
    db.add(route)
    await db.flush()
    await db.refresh(route)
    return route


async def update_route(db: AsyncSession, route: Route, data: RouteUpdate) -> Route:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(route, k, v)
    await db.flush()
    await db.refresh(route)
    return route


async def delete_route(db: AsyncSession, route: Route) -> None:
    await db.delete(route)
    await db.flush()


# ─── Stop ───────────────────────────────────────────────────────────────────

async def list_stops(db: AsyncSession, route_id: str) -> List[Stop]:
    result = await db.execute(
        select(Stop).where(Stop.route_id == route_id).order_by(Stop.stop_order)
    )
    return list(result.scalars().all())


async def get_stop(db: AsyncSession, stop_id: str) -> Optional[Stop]:
    result = await db.execute(select(Stop).where(Stop.id == stop_id))
    return result.scalar_one_or_none()


async def create_stop(db: AsyncSession, school_id: str, route_id: str, data: StopCreate) -> Stop:
    stop = Stop(school_id=school_id, route_id=route_id, **data.model_dump())
    db.add(stop)
    await db.flush()
    await db.refresh(stop)
    return stop


async def delete_stop(db: AsyncSession, stop: Stop) -> None:
    await db.delete(stop)
    await db.flush()


async def update_stop(db: AsyncSession, stop: Stop, data: StopUpdate) -> Stop:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(stop, k, v)
    await db.flush()
    await db.refresh(stop)
    return stop


# ─── Student Transport ──────────────────────────────────────────────────────

async def list_student_transport(
    db: AsyncSession, school_id: str, route_id: Optional[str] = None
) -> List[StudentTransport]:
    q = select(StudentTransport).where(StudentTransport.school_id == school_id)
    if route_id:
        q = q.where(StudentTransport.route_id == route_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_student_transport(
    db: AsyncSession, school_id: str, transport_id: str
) -> Optional[StudentTransport]:
    result = await db.execute(
        select(StudentTransport).where(
            StudentTransport.id == transport_id, StudentTransport.school_id == school_id
        )
    )
    return result.scalar_one_or_none()


async def assign_student_transport(
    db: AsyncSession, school_id: str, data: StudentTransportAssign
) -> StudentTransport:
    st = StudentTransport(school_id=school_id, **data.model_dump())
    db.add(st)
    await db.flush()
    await db.refresh(st)
    return st


async def delete_student_transport(db: AsyncSession, st: StudentTransport) -> None:
    await db.delete(st)
    await db.flush()


# ─── Maintenance ────────────────────────────────────────────────────────────

async def list_maintenance(db: AsyncSession, vehicle_id: str) -> List[VehicleMaintenance]:
    result = await db.execute(
        select(VehicleMaintenance)
        .where(VehicleMaintenance.vehicle_id == vehicle_id)
        .order_by(VehicleMaintenance.maintenance_date.desc())
    )
    return list(result.scalars().all())


async def create_maintenance(
    db: AsyncSession, data: VehicleMaintenanceCreate
) -> VehicleMaintenance:
    m = VehicleMaintenance(**data.model_dump())
    db.add(m)
    await db.flush()
    await db.refresh(m)
    return m


# ─── Fuel Log ───────────────────────────────────────────────────────────────

async def list_fuel_logs(db: AsyncSession, vehicle_id: str) -> List[VehicleFuelLog]:
    result = await db.execute(
        select(VehicleFuelLog)
        .where(VehicleFuelLog.vehicle_id == vehicle_id)
        .order_by(VehicleFuelLog.fuel_date.desc())
    )
    return list(result.scalars().all())


async def create_fuel_log(db: AsyncSession, data: FuelLogCreate) -> VehicleFuelLog:
    log = VehicleFuelLog(**data.model_dump())
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


# ─── Expiry Alerts ──────────────────────────────────────────────────────────

async def get_expiring_vehicles(db: AsyncSession, school_id: str, days: int = 30) -> List[dict]:
    """Return vehicles with documents expiring within `days` days."""
    from datetime import date, timedelta

    threshold = date.today() + timedelta(days=days)
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.school_id == school_id,
            Vehicle.is_active == True,
            (
                (Vehicle.insurance_expiry <= threshold)
                | (Vehicle.fitness_expiry <= threshold)
                | (Vehicle.permit_expiry <= threshold)
            ),
        )
    )
    vehicles = result.scalars().all()
    alerts = []
    today = date.today()
    for v in vehicles:
        for field in ("insurance_expiry", "fitness_expiry", "permit_expiry"):
            exp = getattr(v, field)
            if exp and exp <= threshold:
                alerts.append({
                    "vehicle_id": str(v.id),
                    "registration_number": v.registration_number,
                    "document": field.replace("_expiry", ""),
                    "expiry_date": exp.isoformat(),
                    "days_remaining": (exp - today).days,
                })
    return alerts


# ─── GPS Tracking ─────────────────────────────────────────────────────────────

async def record_gps_ping(
    db: AsyncSession,
    school_id: str,
    vehicle_id: str,
    data: GPSUpdateRequest,
) -> VehicleGPSLog:
    """Store a GPS ping and update the vehicle's cached current location."""
    now = datetime.now(timezone.utc)
    recorded = data.recorded_at or now

    log = VehicleGPSLog(
        school_id=school_id,
        vehicle_id=vehicle_id,
        latitude=data.latitude,
        longitude=data.longitude,
        speed_kmph=data.speed_kmph,
        heading_degrees=data.heading_degrees,
        altitude_meters=data.altitude_meters,
        accuracy_meters=data.accuracy_meters,
        recorded_at=recorded,
        source=data.source,
        created_at=now,
    )
    db.add(log)

    # Update vehicle's cached current location
    vehicle = await db.get(Vehicle, vehicle_id)
    if vehicle:
        vehicle.current_latitude = data.latitude
        vehicle.current_longitude = data.longitude
        vehicle.last_gps_update = recorded

    await db.flush()
    await db.refresh(log)
    return log


async def get_gps_history(
    db: AsyncSession,
    vehicle_id: str,
    limit: int = 100,
) -> list[VehicleGPSLog]:
    """Get recent GPS logs for a vehicle, most recent first."""
    result = await db.execute(
        select(VehicleGPSLog)
        .where(VehicleGPSLog.vehicle_id == vehicle_id)
        .order_by(VehicleGPSLog.recorded_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_fleet_locations(db: AsyncSession, school_id: str) -> list[Vehicle]:
    """Get all active vehicles with their cached GPS positions."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.school_id == school_id,
            Vehicle.is_active == True,
        ).order_by(Vehicle.registration_number)
    )
    return list(result.scalars().all())
