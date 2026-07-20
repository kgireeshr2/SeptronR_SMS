# PHASE 10 — TRANSPORT MANAGEMENT

## Pre-Requisite
Phases 1–9 complete. Students enrolled, school configured.

## Objective
School transport module: routes, stops, vehicles, driver/conductor assignment, student transport subscription, fee integration, GPS tracking hooks, and smart notifications.

---

## 10.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 13: Transport
vehicles (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    registration_number VARCHAR(30),
    vehicle_type VARCHAR(50),       -- bus|van|auto
    make VARCHAR(100), model VARCHAR(100), year SMALLINT,
    capacity SMALLINT,
    driver_id UUID FK→staff (nullable),      -- ⚠️ driver/conductor on vehicles table
    conductor_id UUID FK→staff (nullable),   -- ⚠️ NOT on routes table
    insurance_expiry DATE, fitness_expiry DATE, permit_expiry DATE,
    gps_device_id VARCHAR(100),
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, registration_number)
)

-- ⚠️ TABLE NAME: routes (NOT transport_routes)
routes (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL, description TEXT,
    vehicle_id UUID FK→vehicles (nullable),
    start_time TIME, end_time TIME,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, name)
)
-- NOTE: driver_id and conductor_id are on vehicles (not on routes)

-- ⚠️ TABLE NAME: stops (NOT route_stops); field: stop_order (NOT sequence_order)
stops (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    route_id UUID FK→routes ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    stop_order SMALLINT NOT NULL,     -- ⚠️ 'stop_order' not 'sequence_order'
    pickup_time TIME, drop_time TIME,
    latitude DECIMAL(10,7), longitude DECIMAL(10,7),
    fare BIGINT DEFAULT 0,           -- paise — monthly fare for this stop
    created_at, updated_at,
    UNIQUE(route_id, stop_order)
)

student_transport (
    id UUID PK, student_id UUID FK→students ON DELETE CASCADE,
    school_id UUID FK→schools ON DELETE CASCADE,
    route_id UUID FK→routes,        -- ⚠️ FK→routes not transport_routes
    stop_id UUID FK→stops,          -- ⚠️ FK→stops not route_stops
    academic_year_id UUID FK→academic_years,
    subscription_type VARCHAR(20) DEFAULT 'both',  -- both|pickup|drop
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(student_id, academic_year_id)
)

-- ⚠️ ADDITIONAL TABLES (in schema but missing from original prompt):
vehicle_maintenance (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    vehicle_id UUID FK→vehicles ON DELETE CASCADE,
    maintenance_type VARCHAR(100),   -- oil_change|tire|engine|brake|service|other
    description TEXT,
    maintenance_date DATE NOT NULL,
    next_due_date DATE,
    cost BIGINT DEFAULT 0,           -- paise
    vendor_name VARCHAR(200),
    odometer_reading INTEGER,
    status VARCHAR(20) DEFAULT 'completed',  -- scheduled|in_progress|completed
    notes TEXT,
    created_at, updated_at
)

vehicle_fuel_log (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    vehicle_id UUID FK→vehicles ON DELETE CASCADE,
    fuel_date DATE NOT NULL,
    fuel_quantity DECIMAL(8,2),      -- litres
    fuel_cost BIGINT DEFAULT 0,      -- paise
    odometer_reading INTEGER,
    pump_name VARCHAR(200),
    created_at
)
```

> **Schema note**: `driver_id` and `conductor_id` are assigned at the **vehicle** level, not route level. To get the driver for a route, JOIN `routes → vehicles` and read `vehicles.driver_id`. The `stops` table uses `stop_order` (not `sequence_order`).


---

## 10.2 SQLAlchemy Models (`backend/app/models/transport.py`)

```python
class Vehicle(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class Route(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...           # table: routes
class Stop(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...            # table: stops
class StudentTransport(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class VehicleMaintenance(Base, UUIDPrimaryKeyMixin, TimestampMixin): ...
class VehicleFuelLog(Base, UUIDPrimaryKeyMixin): ...
```

---

## 10.3 Pydantic Schemas

```python
class VehicleCreate(BaseModel):
    registration_number: str
    vehicle_type: str
    make: Optional[str]; model: Optional[str]; year: Optional[int]
    capacity: int
    insurance_expiry: Optional[date]; fitness_expiry: Optional[date]; permit_expiry: Optional[date]
    gps_device_id: Optional[str]

class StopCreate(BaseModel):    # ⚠️ 'StopCreate' not 'RouteStopCreate'
    name: str
    stop_order: int              # ⚠️ 'stop_order' not 'sequence_order'
    pickup_time: Optional[time]; drop_time: Optional[time]
    latitude: Optional[float]; longitude: Optional[float]
    fare: int = 0   # paise

class RouteCreate(BaseModel):   # ⚠️ 'RouteCreate' not 'TransportRouteCreate'
    name: str; description: Optional[str]
    vehicle_id: Optional[UUID]
    # NOTE: driver_id/conductor_id are on vehicles, not routes
    start_time: Optional[time]; end_time: Optional[time]
    stops: List[StopCreate] = []

class StudentTransportAssign(BaseModel):
    student_id: UUID
    route_id: UUID
    stop_id: UUID
    academic_year_id: UUID
    subscription_type: str = "both"

class TransportRouteResponse(BaseModel):
    id: UUID; name: str; description: Optional[str]
    vehicle_info: Optional[VehicleInfo]
    driver_name: Optional[str]; conductor_name: Optional[str]
    student_count: int
    stops: List[RouteStopResponse]
    is_active: bool

class RouteStopResponse(RouteStopCreate):
    id: UUID
    students_at_stop: Optional[int]

class StudentTransportResponse(BaseModel):
    student_id: UUID; student_name: str
    route_name: str; stop_name: str
    pickup_time: Optional[time]; drop_time: Optional[time]
    fare: int; subscription_type: str
```

---

## 10.4 Repository Layer

```python
class TransportRepository:
    async def list_vehicles(self, school_id: str) -> List[Vehicle]: ...
    async def create_vehicle(self, school_id: str, data: dict) -> Vehicle: ...
    async def update_vehicle(self, vehicle_id: str, data: dict) -> Vehicle: ...
    async def expiring_documents(self, school_id: str, days_ahead: int) -> List[dict]: ...

    async def create_route(self, school_id: str, data: dict) -> TransportRoute: ...
    async def get_route_with_stops(self, route_id: str) -> TransportRoute: ...
    async def list_routes(self, school_id: str) -> List[TransportRoute]: ...
    async def update_route(self, route_id: str, data: dict) -> TransportRoute: ...
    async def reorder_stops(self, route_id: str, stop_orders: List[dict]) -> None: ...

    async def assign_student(self, data: dict) -> StudentTransport: ...
    async def unassign_student(self, student_id: str, year_id: str) -> None: ...
    async def get_students_on_route(self, route_id: str, year_id: str) -> List[StudentTransport]: ...
    async def get_students_at_stop(self, stop_id: str, year_id: str) -> List[StudentTransport]: ...
    async def get_student_transport(self, student_id: str, year_id: str) -> Optional[StudentTransport]: ...

    async def count_per_route(self, school_id: str, year_id: str) -> List[dict]: ...
    async def unassigned_students(self, school_id: str, year_id: str, class_id: Optional[str]) -> List[dict]: ...
```

---

## 10.5 Service Layer

```python
async def assign_student_transport(school_id: str, data: StudentTransportAssign, assigned_by: str) -> StudentTransport:
    """
    1. Validate stop belongs to route
    2. Validate route belongs to school
    3. Upsert student_transport (one per academic year)
    4. Create/update transport fee invoice in fee_invoices based on stop.fare
    """

async def update_fee_on_stop_change(student_id: str, old_stop_id: str, new_stop_id: str, year_id: str):
    """Update the fee_structure-linked StudentFee for transport category."""

async def check_expiring_documents(school_id: str) -> List[dict]:
    """Find vehicles where insurance/fitness/permit expiry <= 30 days from today."""

async def get_route_manifest(route_id: str, year_id: str) -> bytes:
    """PDF list of all students on route, stop by stop, with parent phone."""

async def send_vehicle_location(route_id: str, lat: float, lng: float, speed: float):
    """Store GPS point to Redis sorted set; broadcast via WebSocket to subscribed parents."""
```

---

## 10.6 API Endpoints

```
# Vehicles
GET  /api/v1/transport/vehicles           → list [transport:view]
POST /api/v1/transport/vehicles           → create [transport:manage]
PUT  /api/v1/transport/vehicles/{id}      → update
DELETE /api/v1/transport/vehicles/{id}    → delete
GET  /api/v1/transport/vehicles/expiring  → expiring documents alert [transport:view]

# Routes
GET  /api/v1/transport/routes             → list with student counts [transport:view]
POST /api/v1/transport/routes             → create route+stops [transport:manage]
GET  /api/v1/transport/routes/{id}        → get with stops + students
PUT  /api/v1/transport/routes/{id}        → update
DELETE /api/v1/transport/routes/{id}      → delete
PUT  /api/v1/transport/routes/{id}/stops  → reorder/update stops
POST /api/v1/transport/routes/{id}/manifest → PDF route manifest [transport:export]

# Student Assignment
GET  /api/v1/transport/students           → list assigned students (filter: route, class) [transport:view]
POST /api/v1/transport/students           → assign student to route/stop [transport:manage]
PUT  /api/v1/transport/students/{student_id} → change stop/route
DELETE /api/v1/transport/students/{student_id} → unassign
GET  /api/v1/transport/students/unassigned → students without transport [transport:view]
GET  /api/v1/transport/students/export    → Excel export [transport:export]

# GPS (WebSocket hook — implement in Phase 14/22 or stub here)
POST /api/v1/transport/gps/update         → receive GPS ping (no auth, use API key) → Redis

# Stats
GET  /api/v1/transport/stats              → summary: routes, vehicles, assigned students
```

---

## 10.7 Frontend Pages

### `/admin/transport` Page (Permission: `transport:view`)

**Vehicles Tab:**
- Table: Registration No, Type, Make+Model, Capacity, Insurance Expiry, Fitness Expiry, Permit Expiry, Active
- Expiry badges: amber (≤30 days), red (expired)
- Add / Edit / Delete vehicle

**Routes Tab:**
- Cards or table: Route Name, Vehicle, Driver, Conductor, Students Count, Active
- Route detail expander: list of stops in order with time + fare
- Add Route form: name, vehicle, driver, conductor, stops builder (add/reorder stops with drag)

**Students Tab:**
- Select Route → show students assigned to this route grouped by stop
- Assign Student: search student → pick route → pick stop → save
- Transfer student from one stop to another
- Export to Excel

**Route Map View (optional, stub):**
- Google Maps / Leaflet.js showing stops as pins
- Show live vehicle location if GPS data available in Redis

### `frontend/src/api/transport.ts`
```typescript
export const transportApi = {
  listVehicles: () => api.get('/transport/vehicles'),
  createVehicle: (data: VehicleCreate) => api.post('/transport/vehicles', data),
  updateVehicle: (id: string, data: Partial<VehicleCreate>) => api.put(`/transport/vehicles/${id}`, data),
  getExpiringDocs: () => api.get('/transport/vehicles/expiring'),
  listRoutes: () => api.get('/transport/routes'),
  createRoute: (data: TransportRouteCreate) => api.post('/transport/routes', data),
  getRoute: (id: string) => api.get(`/transport/routes/${id}`),
  updateRoute: (id: string, data: Partial<TransportRouteCreate>) => api.put(`/transport/routes/${id}`, data),
  getManifest: (routeId: string) =>
    api.post(`/transport/routes/${routeId}/manifest`, {}, { responseType: 'blob' }),
  listAssigned: (params: TransportStudentParams) => api.get('/transport/students', { params }),
  assignStudent: (data: StudentTransportAssign) => api.post('/transport/students', data),
  unassignStudent: (studentId: string) => api.delete(`/transport/students/${studentId}`),
  unassignedStudents: (yearId: string, classId?: string) =>
    api.get(`/transport/students/unassigned?year_id=${yearId}${classId ? `&class_id=${classId}` : ''}`),
  exportStudents: () => api.get('/transport/students/export', { responseType: 'blob' }),
  getStats: () => api.get('/transport/stats'),
};
```

---

## 10.8 Celery Tasks

```python
@celery.task(queue="notifications")
def check_vehicle_document_expiry():
    """
    Daily: For all schools, find vehicles with expiry in ≤30 days.
    Send email to school admin: "Vehicle {reg_no} insurance expires on {date}."
    """

@celery.task(queue="notifications")
def send_bus_arrival_notification(route_id: str, stop_id: str, eta_minutes: int):
    """
    Called when GPS shows bus nearing a stop.
    Send push notification to parents with students at that stop.
    """
```

---

## 10.9 Fee Integration

When a student is assigned to transport:
1. Look up `fee_category` named "Transport" (or nearest) in school's fee categories
2. If a `fee_structure` exists for transport fee for student's class+year: apply it, OR
3. Use `stop.fare` as the monthly transport fee
4. Create/update `fee_invoices` record for transport category

When student is unassigned from transport — set transport student_fee to waived or zero.

---

## 10.10 Tests

```python
async def test_create_route_with_stops(): ...
async def test_stop_sequence_reorder(): ...
async def test_assign_student_creates_transport_fee(): ...
async def test_assign_student_duplicate_year_forbidden(): ...   # UNIQUE(student_id, academic_year_id)
async def test_stop_must_belong_to_route(): ...
async def test_vehicle_expiry_alert(): ...
async def test_unassigned_students_list(): ...
```

---

## 10.11 Deliverables Checklist

- [ ] Vehicle CRUD with document expiry tracking
- [ ] Route CRUD with ordered stops (drag-reorder in UI)
- [ ] Driver/conductor assignment to route
- [ ] Student-to-route/stop assignment
- [ ] Transport fee auto-created/updated on assignment
- [ ] Route manifest PDF (WeasyPrint)
- [ ] Expiring document alerts UI + Celery daily check
- [ ] Export assigned students to Excel
- [ ] Unassigned students list with class filter
- [ ] GPS update endpoint stubbed (ready for Phase 22 live tracking)
- [ ] Bus arrival notification task stubbed
- [ ] Transport stats for dashboard widget
