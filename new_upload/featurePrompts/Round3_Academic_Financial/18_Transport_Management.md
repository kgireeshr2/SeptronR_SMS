# Feature Prompt 18 — Transport Management

## Round: 3 of 4 — Academic & Financial
## Prerequisites: Prompts 09 (Students)

---

## Objective

Implement school transport management: vehicle fleet, routes with stops and fares, student transport assignments, driver management, and fee integration hook.

> **CRITICAL MODEL NAMES** (from Fix 01):
> - Model `Route` aliased as `TransportRoute` in exports (not a separate model)
> - Model `StudentTransport` aliased as `TransportAssignment` in exports
> - Use these exact table/model names throughout

---

## 1. Database Models (`backend/app/models/transport.py`)

```python
import uuid
from datetime import date
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin

class Vehicle(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    registration_number: Mapped[str] = mapped_column(String(30), nullable=False)
    vehicle_name: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(50), default="bus")  # bus/van/auto
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    driver_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driver_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    driver_license: Mapped[str | None] = mapped_column(String(50), nullable=True)
    insurance_expiry: Mapped[date | None] = mapped_column(nullable=True)  # Date
    fitness_expiry: Mapped[date | None] = mapped_column(nullable=True)    # Date
    gps_device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("school_id", "registration_number", name="uq_vehicle_reg"),
    )


class Route(Base, TimestampMixin, SoftDeleteMixin):
    """Also exported/aliased as TransportRoute."""
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("vehicles.id"), nullable=True)
    start_point: Mapped[str | None] = mapped_column(String(200), nullable=True)
    end_point: Mapped[str | None] = mapped_column(String(200), nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    stops: Mapped[list["RouteStop"]] = relationship(
        "RouteStop", back_populates="route", order_by="RouteStop.stop_order")

# Alias for consumers
TransportRoute = Route


class RouteStop(Base, TimestampMixin):
    __tablename__ = "route_stops"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    stop_name: Mapped[str] = mapped_column(String(200), nullable=False)
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False)
    pickup_time: Mapped[str | None] = mapped_column(String(10), nullable=True)   # "07:30"
    drop_time: Mapped[str | None] = mapped_column(String(10), nullable=True)     # "14:30"
    fare_paise: Mapped[int] = mapped_column(Integer, default=0)  # fare for this stop
    landmark: Mapped[str | None] = mapped_column(String(200), nullable=True)

    route: Mapped[Route] = relationship("Route", back_populates="stops")


class StudentTransport(Base, TimestampMixin):
    """Also exported/aliased as TransportAssignment."""
    __tablename__ = "student_transport"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    route_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("routes.id"), nullable=False)
    stop_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("route_stops.id"), nullable=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    pickup_type: Mapped[str] = mapped_column(String(20), default="both")  # pickup / drop / both
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id", name="uq_student_transport_year"),
    )

# Alias for consumers
TransportAssignment = StudentTransport
```

---

## 2. Alembic Migration

```sql
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    registration_number VARCHAR(30) NOT NULL,
    vehicle_name VARCHAR(100) NOT NULL,
    vehicle_type VARCHAR(50) DEFAULT 'bus' NOT NULL,
    capacity INTEGER NOT NULL,
    driver_name VARCHAR(100),
    driver_phone VARCHAR(20),
    driver_license VARCHAR(50),
    insurance_expiry DATE,
    fitness_expiry DATE,
    gps_device_id VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_vehicle_reg UNIQUE (school_id, registration_number)
);

CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    vehicle_id UUID REFERENCES vehicles(id),
    start_point VARCHAR(200),
    end_point VARCHAR(200),
    distance_km FLOAT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE route_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    stop_name VARCHAR(200) NOT NULL,
    stop_order INTEGER NOT NULL,
    pickup_time VARCHAR(10),
    drop_time VARCHAR(10),
    fare_paise INTEGER DEFAULT 0 NOT NULL,
    landmark VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE student_transport (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    route_id UUID NOT NULL REFERENCES routes(id),
    stop_id UUID REFERENCES route_stops(id),
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    pickup_type VARCHAR(20) DEFAULT 'both' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_student_transport_year UNIQUE (student_id, academic_year_id)
);

CREATE INDEX ix_student_transport_school ON student_transport(school_id, academic_year_id);
```

---

## 3. Pydantic Schemas

```python
class VehicleCreate(BaseModel):
    registrationNumber: str
    vehicleName: str
    vehicleType: str = "bus"
    capacity: int
    driverName: str | None = None
    driverPhone: str | None = None
    driverLicense: str | None = None

class RouteCreate(BaseModel):
    name: str
    vehicleId: UUID | None = None
    startPoint: str | None = None
    endPoint: str | None = None
    distanceKm: float | None = None
    stops: list[RouteStopCreate] = []

class RouteStopCreate(BaseModel):
    stopName: str
    stopOrder: int
    pickupTime: str | None = None
    dropTime: str | None = None
    farePaise: int = 0
    landmark: str | None = None

class StudentTransportAssign(BaseModel):
    studentId: UUID
    routeId: UUID
    stopId: UUID | None = None
    academicYearId: UUID
    pickupType: str = "both"

class RouteResponse(BaseModel):
    id: UUID
    name: str
    vehicleName: str | None
    driverName: str | None
    studentCount: int = 0
    stops: list[dict]
    model_config = {"from_attributes": True}
```

---

## 4. Service (`backend/app/services/transport_service.py`)

```python
async def create_route_with_stops(db, school_id, data: RouteCreate, current_user) -> Route:
    """Create Route + all RouteStop records in transaction."""

async def assign_student(db, school_id, data: StudentTransportAssign, current_user) -> StudentTransport:
    """
    Assign student to route.
    Validate: student enrolled in current year, route is_active.
    Check vehicle capacity: current assignments on route < vehicle.capacity.
    fare_paise = stop.fare_paise for the selected stop.
    """

async def get_route_students(db, route_id, school_id, academic_year_id) -> list:
    """Students on a route grouped by stop, with board/alight point."""

async def get_vehicle_expiry_alerts(db, school_id) -> list:
    """Vehicles where insurance_expiry or fitness_expiry is within 30 days."""

async def generate_route_sheet_pdf(db, route_id, school_id) -> bytes:
    """PDF: route name, vehicle, driver, stops ordered, student list per stop."""

async def check_gps_status(vehicle_id: str) -> dict:
    """
    Stub for GPS integration. Read from Redis key `gps:{vehicle_id}`.
    Returns {lat, lng, speed, timestamp} or None.
    """
```

---

## 5. API Endpoints

```
# Vehicles
GET    /vehicles                              → list vehicles + expiry alerts  [transport:view]
POST   /vehicles                              → add vehicle                   [transport:create]
PUT    /vehicles/{id}                         → update vehicle                [transport:update]
DELETE /vehicles/{id}                         → deactivate vehicle            [transport:delete]

# Routes (aliases: also exposed as TransportRoute)
GET    /routes                                → list routes                   [transport:view]
POST   /routes                                → create route with stops       [transport:create]
GET    /routes/{id}                           → route detail with students    [transport:view]
PUT    /routes/{id}                           → update route                  [transport:update]
DELETE /routes/{id}                           → deactivate route              [transport:delete]
GET    /routes/{id}/sheet                     → route sheet PDF               [transport:export]

# Stops
PUT    /routes/{id}/stops                     → replace all stops             [transport:update]

# Student Assignments (aliases: also exposed as TransportAssignment)
POST   /transport/assign                      → assign student to route       [transport:create]
DELETE /transport/assign/{student_id}         → unassign student              [transport:delete]
GET    /transport/students?route_id=&year_id= → students on route             [transport:view]

# GPS (stub)
GET    /vehicles/{id}/location                → GPS location from Redis       [transport:view]

# Reports
GET    /transport/alerts/expiry               → expiring vehicles             [transport:view]
```

---

## 6. Frontend: Transport Pages

### Transport Dashboard (`/transport`)
- **Vehicles tab**: Fleet list with capacity, driver, insurance/fitness expiry badges (red if <30 days)
- **Routes tab**: Route cards with stop count + assigned students count
- **Assign Students tab**: Student search → assign to route/stop
- **Alerts**: Vehicles expiring soon

### Route Detail Page
- Route map stub (placeholder)
- Stop order list with times and fares
- Student list per stop

---

## Verification Checklist

- [ ] Model named `Route` (Table: `routes`); aliased as `TransportRoute`
- [ ] Model named `StudentTransport` (Table: `student_transport`); aliased as `TransportAssignment`
- [ ] `fare_paise` stored on `route_stops` (not on student_transport)
- [ ] Vehicle capacity check before student assignment
- [ ] UNIQUE constraint `uq_student_transport_year` on (student_id, academic_year_id)
- [ ] Route sheet PDF lists stops in order with student names
- [ ] GPS stub reads from Redis key `gps:{vehicle_id}`
- [ ] Insurance/fitness expiry alerts triggered within 30 days
- [ ] `student_transport.is_active=False` when student is unassigned (soft delete)
