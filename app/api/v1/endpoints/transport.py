"""
API Endpoints — Phase 10: Transport Management
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, permission_required
import app.services.transport_service as svc
from app.schemas.phase10 import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    RouteCreate, RouteUpdate, RouteResponse,
    StopCreate, StopUpdate, StopResponse,
    StudentTransportAssign, StudentTransportResponse,
    VehicleMaintenanceCreate, VehicleMaintenanceResponse,
    FuelLogCreate, FuelLogResponse,
    GPSUpdateRequest, GPSLogResponse, VehicleLocationResponse,
)

vehicles_router = APIRouter(prefix="/transport/vehicles", tags=["Transport - Vehicles"])
routes_router = APIRouter(prefix="/transport/routes", tags=["Transport - Routes"])
transport_router = APIRouter(prefix="/transport", tags=["Transport"])


# ─── Vehicles ────────────────────────────────────────────────────────────────

@vehicles_router.get("", response_model=List[VehicleResponse])
async def list_vehicles(
    active_only: bool = Query(True),
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.list_vehicles(db, school_id, active_only)


@vehicles_router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: VehicleCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    vehicle = await svc.create_vehicle(db, school_id, data)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@vehicles_router.get("/expiry-alerts", response_model=List[dict])
async def expiry_alerts(
    days: int = Query(30, ge=1, le=365),
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.get_expiry_alerts(db, school_id, days)


@vehicles_router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.get_vehicle_or_404(db, school_id, str(vehicle_id))


@vehicles_router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    data: VehicleUpdate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    vehicle = await svc.update_vehicle(db, school_id, str(vehicle_id), data)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@vehicles_router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    await svc.delete_vehicle(db, school_id, str(vehicle_id))
    await db.commit()


# ─── Maintenance & Fuel per Vehicle ──────────────────────────────────────────

@vehicles_router.get("/{vehicle_id}/maintenance", response_model=List[VehicleMaintenanceResponse])
async def list_maintenance(
    vehicle_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.list_maintenance(db, school_id, str(vehicle_id))


@vehicles_router.post("/{vehicle_id}/maintenance", response_model=VehicleMaintenanceResponse,
                      status_code=status.HTTP_201_CREATED)
async def add_maintenance(
    vehicle_id: UUID,
    data: VehicleMaintenanceCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    record = await svc.add_maintenance(db, school_id, data)
    await db.commit()
    await db.refresh(record)
    return record


@vehicles_router.get("/{vehicle_id}/fuel-logs", response_model=List[FuelLogResponse])
async def list_fuel_logs(
    vehicle_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.list_fuel_logs(db, school_id, str(vehicle_id))


@vehicles_router.post("/{vehicle_id}/fuel-logs", response_model=FuelLogResponse,
                      status_code=status.HTTP_201_CREATED)
async def add_fuel_log(
    vehicle_id: UUID,
    data: FuelLogCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    log = await svc.add_fuel_log(db, school_id, data)
    await db.commit()
    await db.refresh(log)
    return log


# ─── Routes ──────────────────────────────────────────────────────────────────

@routes_router.get("", response_model=List[RouteResponse])
async def list_routes(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.list_routes(db, school_id)


@routes_router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    data: RouteCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    route = await svc.create_route(db, school_id, data)
    await db.commit()
    return await svc.get_route_or_404(db, school_id, str(route.id))


@routes_router.get("/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.get_route_or_404(db, school_id, str(route_id))


@routes_router.put("/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: UUID,
    data: RouteUpdate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    route = await svc.update_route(db, school_id, str(route_id), data)
    await db.commit()
    return await svc.get_route_or_404(db, school_id, str(route.id))


@routes_router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    await svc.delete_route(db, school_id, str(route_id))
    await db.commit()


@routes_router.get("/{route_id}/stops", response_model=List[StopResponse])
async def list_stops(
    route_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.list_stops(db, school_id, str(route_id))


@routes_router.post("/{route_id}/stops", response_model=StopResponse,
                    status_code=status.HTTP_201_CREATED)
async def add_stop(
    route_id: UUID,
    data: StopCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    stop = await svc.add_stop(db, school_id, str(route_id), data)
    await db.commit()
    await db.refresh(stop)
    return stop


@routes_router.put("/{route_id}/stops/{stop_id}", response_model=StopResponse)
async def update_stop(
    route_id: UUID,
    stop_id: UUID,
    data: StopUpdate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    stop = await svc.update_stop(db, school_id, str(route_id), str(stop_id), data)
    await db.commit()
    await db.refresh(stop)
    return stop


@routes_router.delete("/{route_id}/stops/{stop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stop(
    route_id: UUID,
    stop_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    await svc.delete_stop(db, school_id, str(route_id), str(stop_id))
    await db.commit()


# ─── Student Transport Assignments ──────────────────────────────────────────

@transport_router.get("/students", response_model=List[StudentTransportResponse])
async def list_student_transport(
    route_id: Optional[UUID] = Query(None),
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.list_student_transport(db, school_id, str(route_id) if route_id else None)


@transport_router.post("/students", response_model=StudentTransportResponse,
                       status_code=status.HTTP_201_CREATED)
async def assign_student(
    data: StudentTransportAssign,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    st = await svc.assign_student(db, school_id, data)
    await db.commit()
    await db.refresh(st)
    return st


@transport_router.delete("/students/{transport_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student_transport(
    transport_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "manage")),
):
    await svc.remove_student_transport(db, school_id, str(transport_id))
    await db.commit()


# ─── GPS Tracking ─────────────────────────────────────────────────────────────

@vehicles_router.post(
    "/{vehicle_id}/gps",
    response_model=GPSLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a GPS ping for a vehicle",
    description="Called by GPS hardware device or driver mobile app to push current location.",
)
async def record_gps(
    vehicle_id: UUID,
    data: GPSUpdateRequest,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),   # driver app uses view-level auth
):
    log = await svc.record_gps_ping(db, school_id, str(vehicle_id), data)
    await db.commit()
    await db.refresh(log)
    return log


@vehicles_router.get(
    "/{vehicle_id}/gps",
    response_model=List[GPSLogResponse],
    summary="Get GPS location history for a vehicle",
)
async def get_gps_history(
    vehicle_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    return await svc.get_gps_history(db, school_id, str(vehicle_id), limit)


@transport_router.get(
    "/fleet/locations",
    response_model=List[VehicleLocationResponse],
    summary="Get current GPS locations of all active vehicles (fleet overview)",
)
async def fleet_locations(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _=Depends(permission_required("transport", "view")),
):
    vehicles = await svc.get_fleet_locations(db, school_id)
    return [
        VehicleLocationResponse(
            vehicle_id=v.id,
            registration_number=v.registration_number,
            vehicle_type=v.vehicle_type,
            driver_name=v.driver_name,
            driver_phone=v.driver_phone,
            vehicle_status=v.vehicle_status,
            current_latitude=float(v.current_latitude) if v.current_latitude else None,
            current_longitude=float(v.current_longitude) if v.current_longitude else None,
            last_gps_update=v.last_gps_update,
            is_active=v.is_active,
        )
        for v in vehicles
    ]

