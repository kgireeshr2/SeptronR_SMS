"""
Service — Phase 10: Transport Management
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app import repositories as repos
import app.repositories.transport_repository as transport_repo
from app.schemas.phase10 import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    RouteCreate, RouteUpdate, RouteResponse,
    StopCreate, StopUpdate, StopResponse,
    StudentTransportAssign, StudentTransportResponse,
    VehicleMaintenanceCreate, VehicleMaintenanceResponse,
    FuelLogCreate, FuelLogResponse,
    GPSUpdateRequest, GPSLogResponse, VehicleLocationResponse,
)
from app.core.exceptions import NotFoundError


async def list_vehicles(db: AsyncSession, school_id: str, active_only: bool = True):
    return await transport_repo.list_vehicles(db, school_id, active_only)


async def get_vehicle_or_404(db: AsyncSession, school_id: str, vehicle_id: str):
    vehicle = await transport_repo.get_vehicle(db, school_id, vehicle_id)
    if not vehicle:
        raise NotFoundError("Vehicle not found")
    return vehicle


async def create_vehicle(db: AsyncSession, school_id: str, data: VehicleCreate):
    return await transport_repo.create_vehicle(db, school_id, data)


async def update_vehicle(db: AsyncSession, school_id: str, vehicle_id: str, data: VehicleUpdate):
    vehicle = await get_vehicle_or_404(db, school_id, vehicle_id)
    return await transport_repo.update_vehicle(db, vehicle, data)


async def delete_vehicle(db: AsyncSession, school_id: str, vehicle_id: str) -> None:
    vehicle = await get_vehicle_or_404(db, school_id, vehicle_id)
    await transport_repo.delete_vehicle(db, vehicle)


# ─── Routes ─────────────────────────────────────────────────────────────────

async def list_routes(db: AsyncSession, school_id: str):
    return await transport_repo.list_routes(db, school_id)


async def get_route_or_404(db: AsyncSession, school_id: str, route_id: str):
    route = await transport_repo.get_route(db, school_id, route_id)
    if not route:
        raise NotFoundError("Route not found")
    return route


async def create_route(db: AsyncSession, school_id: str, data: RouteCreate):
    # Create route, then create any stops provided inline
    stops_data = data.stops
    route_data = data.model_copy(update={"stops": []})
    route = await transport_repo.create_route(db, school_id, route_data)
    for stop in stops_data:
        await transport_repo.create_stop(db, school_id, str(route.id), stop)
    return route


async def update_route(db: AsyncSession, school_id: str, route_id: str, data: RouteUpdate):
    route = await get_route_or_404(db, school_id, route_id)
    return await transport_repo.update_route(db, route, data)


async def delete_route(db: AsyncSession, school_id: str, route_id: str) -> None:
    route = await get_route_or_404(db, school_id, route_id)
    await transport_repo.delete_route(db, route)


# ─── Stops ──────────────────────────────────────────────────────────────────

async def list_stops(db: AsyncSession, school_id: str, route_id: str):
    await get_route_or_404(db, school_id, route_id)
    return await transport_repo.list_stops(db, route_id)


async def add_stop(db: AsyncSession, school_id: str, route_id: str, data: StopCreate):
    await get_route_or_404(db, school_id, route_id)
    return await transport_repo.create_stop(db, school_id, route_id, data)


async def delete_stop(db: AsyncSession, school_id: str, route_id: str, stop_id: str) -> None:
    await get_route_or_404(db, school_id, route_id)
    stop = await transport_repo.get_stop(db, stop_id)
    if not stop:
        raise NotFoundError("Stop not found")
    await transport_repo.delete_stop(db, stop)


async def update_stop(db: AsyncSession, school_id: str, route_id: str, stop_id: str, data: StopUpdate):
    await get_route_or_404(db, school_id, route_id)
    stop = await transport_repo.get_stop(db, stop_id)
    if not stop:
        raise NotFoundError("Stop not found")
    return await transport_repo.update_stop(db, stop, data)


# ─── Student Transport ──────────────────────────────────────────────────────

async def list_student_transport(
    db: AsyncSession, school_id: str, route_id: Optional[str] = None
):
    return await transport_repo.list_student_transport(db, school_id, route_id)


async def assign_student(db: AsyncSession, school_id: str, data: StudentTransportAssign):
    return await transport_repo.assign_student_transport(db, school_id, data)


async def remove_student_transport(
    db: AsyncSession, school_id: str, transport_id: str
) -> None:
    st = await transport_repo.get_student_transport(db, school_id, transport_id)
    if not st:
        raise NotFoundError("Student transport assignment not found")
    await transport_repo.delete_student_transport(db, st)


# ─── Maintenance & Fuel ─────────────────────────────────────────────────────

async def list_maintenance(db: AsyncSession, school_id: str, vehicle_id: str):
    await get_vehicle_or_404(db, school_id, vehicle_id)
    return await transport_repo.list_maintenance(db, vehicle_id)


async def add_maintenance(db: AsyncSession, school_id: str, data: VehicleMaintenanceCreate):
    await get_vehicle_or_404(db, school_id, str(data.vehicle_id))
    return await transport_repo.create_maintenance(db, data)


async def list_fuel_logs(db: AsyncSession, school_id: str, vehicle_id: str):
    await get_vehicle_or_404(db, school_id, vehicle_id)
    return await transport_repo.list_fuel_logs(db, vehicle_id)


async def add_fuel_log(db: AsyncSession, school_id: str, data: FuelLogCreate):
    await get_vehicle_or_404(db, school_id, str(data.vehicle_id))
    return await transport_repo.create_fuel_log(db, data)


async def get_expiry_alerts(db: AsyncSession, school_id: str, days: int = 30):
    return await transport_repo.get_expiring_vehicles(db, school_id, days)


# ─── GPS Tracking ─────────────────────────────────────────────────────────────

async def record_gps_ping(
    db: AsyncSession, school_id: str, vehicle_id: str, data: GPSUpdateRequest
):
    """Record a GPS ping for a vehicle and update its cached location."""
    vehicle = await get_vehicle_or_404(db, school_id, vehicle_id)
    return await transport_repo.record_gps_ping(db, school_id, vehicle_id, data)


async def get_gps_history(db: AsyncSession, school_id: str, vehicle_id: str, limit: int = 100):
    """Return GPS history for a vehicle (most recent first)."""
    await get_vehicle_or_404(db, school_id, vehicle_id)
    return await transport_repo.get_gps_history(db, vehicle_id, limit)


async def get_fleet_locations(db: AsyncSession, school_id: str):
    """Return current GPS locations of all active vehicles."""
    return await transport_repo.get_fleet_locations(db, school_id)

