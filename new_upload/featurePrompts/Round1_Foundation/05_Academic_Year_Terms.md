# Feature Prompt 05 — Academic Year & Terms

## Round: 1 of 4 — Foundation
## Prerequisites: Prompts 01–04 complete

---

## Objective

Implement academic years (`academic_years`) and term/semester management (`academic_terms`). Support set-current year, lock completed years, promotion utility, and a persistent academic-year selector in the navbar that scopes all module data. Every module in later rounds filters by `school_id + academic_year_id`.

---

## 1. Database Models (`backend/app/models/academic.py`)

```python
import uuid
from datetime import date, datetime
from sqlalchemy import String, Boolean, Date, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.models.base import Base, TimestampMixin

class AcademicYear(Base, TimestampMixin):
    __tablename__ = "academic_years"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "2025-2026"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    terms: Mapped[list["AcademicTerm"]] = relationship("AcademicTerm", back_populates="academic_year",
                                                        cascade="all, delete-orphan")

    __table_args__ = (
        # Only one current year per school (partial unique index)
        Index("uq_academic_years_current_school",
              "school_id", unique=True,
              postgresql_where=(is_current == True)),
    )


class AcademicTerm(Base, TimestampMixin):
    __tablename__ = "academic_terms"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Term 1"
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    academic_year: Mapped[AcademicYear] = relationship("AcademicYear", back_populates="terms")

    __table_args__ = (
        Index("uq_academic_terms_current",
              "academic_year_id", unique=True,
              postgresql_where=(is_current == True)),
    )
```

---

## 2. Alembic Migration

```sql
CREATE TABLE academic_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE NOT NULL,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Partial unique index: only one current year per school
CREATE UNIQUE INDEX uq_academic_years_current_school
    ON academic_years(school_id) WHERE is_current = TRUE;

CREATE INDEX ix_academic_years_school_id ON academic_years(school_id);

CREATE TABLE academic_terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    sequence_number INTEGER NOT NULL DEFAULT 1,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE UNIQUE INDEX uq_academic_terms_current
    ON academic_terms(academic_year_id) WHERE is_current = TRUE;
```

---

## 3. Pydantic Schemas

```python
from pydantic import BaseModel, model_validator
from uuid import UUID
from datetime import date

class AcademicYearCreate(BaseModel):
    name: str  # e.g. "2025-2026"
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class AcademicYearUpdate(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None

class AcademicYearResponse(BaseModel):
    id: UUID
    schoolId: UUID
    name: str
    startDate: date
    endDate: date
    isCurrent: bool
    isLocked: bool
    termCount: int = 0
    model_config = {"from_attributes": True}

class AcademicTermCreate(BaseModel):
    name: str
    sequenceNumber: int = 1
    start_date: date
    end_date: date

class AcademicTermResponse(BaseModel):
    id: UUID
    academicYearId: UUID
    name: str
    sequenceNumber: int
    startDate: date
    endDate: date
    isCurrent: bool
    model_config = {"from_attributes": True}
```

---

## 4. Repository (`backend/app/repositories/academic_repository.py`)

```python
async def get_academic_years(db, school_id: UUID) -> list[AcademicYear]: ...
async def get_academic_year_by_id(db, year_id: UUID, school_id: UUID) -> AcademicYear | None: ...
async def get_current_academic_year(db, school_id: UUID) -> AcademicYear | None: ...
async def create_academic_year(db, school_id: UUID, data: AcademicYearCreate, created_by: UUID) -> AcademicYear: ...
async def update_academic_year(db, year: AcademicYear, data: dict) -> AcademicYear: ...
async def set_current_year(db, school_id: UUID, year_id: UUID) -> None:
    """SET is_current=FALSE for all years in school, then SET is_current=TRUE for target year."""
    ...
async def lock_year(db, year: AcademicYear) -> None:
    """SET is_locked=TRUE."""
    ...
async def get_terms_for_year(db, academic_year_id: UUID) -> list[AcademicTerm]: ...
async def create_term(db, school_id: UUID, academic_year_id: UUID, data: AcademicTermCreate) -> AcademicTerm: ...
async def set_current_term(db, academic_year_id: UUID, term_id: UUID) -> None: ...
async def delete_term(db, term: AcademicTerm) -> None: ...
```

---

## 5. Service (`backend/app/services/academic_service.py`)

```python
async def create_academic_year(db, school_id, data, current_user) -> AcademicYear:
    """
    Validate: name must be unique per school.
    Validate: dates must not overlap with existing years.
    Create year. Audit log.
    """
    ...

async def set_current_year(db, redis, school_id, year_id, current_user) -> None:
    """
    Cannot set a locked year as current.
    Update is_current. Invalidate Redis cache for settings (which may reference current year).
    Audit log.
    """
    ...

async def lock_year(db, school_id, year_id, current_user) -> None:
    """
    Cannot lock if it's the current year.
    Lock year. All subsequent writes to this year in any module raise 400.
    Audit log.
    """
    ...

async def delete_academic_year(db, school_id, year_id, current_user) -> None:
    """
    Cannot delete current year.
    Cannot delete if any students enrolled, exams scheduled, or attendance recorded in this year.
    Soft delete otherwise.
    Audit log.
    """
    ...

def is_year_locked(year: AcademicYear) -> bool:
    """Helper used by all services to check before writes."""
    return year.is_locked

async def validate_year_not_locked(db, school_id, year_id):
    """Utility: call at the start of any write operation that touches year-scoped data."""
    year = await academic_repository.get_academic_year_by_id(db, year_id, school_id)
    if not year: raise HTTPException(404, "Academic year not found")
    if year.is_locked: raise HTTPException(400, "Academic year is locked and cannot be modified")
    return year
```

---

## 6. API Endpoints (`backend/app/api/v1/endpoints/academic_years.py`)

```
GET    /academic-years                           → list all years for school
POST   /academic-years                           → create new year     [academic_years:create]
GET    /academic-years/current                   → get current year (shortcut)
GET    /academic-years/{year_id}                 → get year detail with terms
PUT    /academic-years/{year_id}                 → update year         [academic_years:update]
DELETE /academic-years/{year_id}                 → soft delete year    [academic_years:delete]
POST   /academic-years/{year_id}/set-current     → set as current      [academic_years:manage]
POST   /academic-years/{year_id}/lock            → lock year           [academic_years:manage]

GET    /academic-years/{year_id}/terms           → list terms in year
POST   /academic-years/{year_id}/terms           → add term to year    [academic_years:create]
PUT    /academic-years/{year_id}/terms/{term_id} → update term         [academic_years:update]
DELETE /academic-years/{year_id}/terms/{term_id} → delete term         [academic_years:delete]
POST   /academic-years/{year_id}/terms/{term_id}/set-current → set current term
```

---

## 7. Frontend: Types

```typescript
export interface AcademicYear {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
  isLocked: boolean;
  termCount: number;
}

export interface AcademicTerm {
  id: string;
  academicYearId: string;
  name: string;
  sequenceNumber: number;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
}
```

---

## 8. Frontend: API Layer (`frontend/src/api/academicYears.ts`)

```typescript
import api from './axios';

export const getAcademicYearsApi = async () => {
  const res = await api.get<{ data: AcademicYear[] }>('/academic-years');
  return res.data.data;
};

export const createAcademicYearApi = async (data: { name: string; startDate: string; endDate: string }) => {
  const res = await api.post<{ data: AcademicYear }>('/academic-years', data);
  return res.data.data;
};

export const setCurrentYearApi = async (yearId: string) =>
  api.post(`/academic-years/${yearId}/set-current`);

export const lockYearApi = async (yearId: string) =>
  api.post(`/academic-years/${yearId}/lock`);

export const deleteAcademicYearApi = async (yearId: string) =>
  api.delete(`/academic-years/${yearId}`);

export const getTermsApi = async (yearId: string) => {
  const res = await api.get<{ data: AcademicTerm[] }>(`/academic-years/${yearId}/terms`);
  return res.data.data;
};

export const createTermApi = async (yearId: string, data: Partial<AcademicTerm>) => {
  const res = await api.post<{ data: AcademicTerm }>(`/academic-years/${yearId}/terms`, data);
  return res.data.data;
};
```

---

## 9. Frontend: Custom Hooks

```typescript
// frontend/src/hooks/useAcademicYears.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAcademicYearsApi, setCurrentYearApi, lockYearApi } from '@api/academicYears';
import { useAcademicYearStore } from '@store/academicYearStore';
import { toast } from 'sonner';

export const useAcademicYears = () =>
  useQuery({ queryKey: ['academic-years'], queryFn: getAcademicYearsApi });

export const useSetCurrentYear = () => {
  const qc = useQueryClient();
  const { setSelectedYear } = useAcademicYearStore();
  return useMutation({
    mutationFn: setCurrentYearApi,
    onSuccess: (_, yearId) => {
      qc.invalidateQueries({ queryKey: ['academic-years'] });
      toast.success('Current academic year updated');
    },
  });
};
```

---

## 10. Frontend: Academic Years Page (`frontend/src/pages/academic/AcademicYearsPage.tsx`)

Build at `/academic-years`:

- **PageHeader**: "Academic Years" + "New Academic Year" button
- **Years Table**: columns: Name, Start Date, End Date, Terms Count, Status (Current / Locked badge), Actions
- **Actions per row**:
  - "Set as Current" (if not current and not locked)
  - "Lock" button (confirmation dialog: "Lock year? This prevents any further edits.")
  - "Add Term" button
  - "Delete" button (disabled if current or has data)
- **Expandable row**: shows terms list for that year with "Add Term" / "Set Current Term" / "Delete Term"
- **"New Academic Year" dialog**: name, start date, end date inputs
- **"Add Term" dialog**: name, sequence, start date, end date

---

## 11. Frontend: Academic Year Selector in Navbar

In `frontend/src/components/layout/Navbar.tsx`:

```tsx
// Load years on app startup
const { data: years } = useAcademicYears();
const { selectedYear, setSelectedYear, setYears } = useAcademicYearStore();

useEffect(() => {
  if (years) {
    setYears(years);
    if (!selectedYear) {
      const current = years.find((y) => y.isCurrent);
      if (current) setSelectedYear(current);
    }
  }
}, [years]);

// Render a <Select> dropdown in the navbar
// Shows current year name; change triggers setSelectedYear in store
// All pages read year from store via: const { selectedYear } = useAcademicYearStore();
```

---

## Verification Checklist

- [ ] `GET /academic-years` lists all years for the school
- [ ] `POST /academic-years` creates a year; year with overlapping dates returns 400
- [ ] `POST /academic-years/{id}/set-current` flips `is_current`; previous current year becomes false
- [ ] Partial unique index prevents two `is_current=TRUE` rows for same school
- [ ] `POST /academic-years/{id}/lock` sets `is_locked=TRUE`
- [ ] Locked year rejects write operations (returns 400 from service)
- [ ] Terms CRUD works; only one term can be `is_current=TRUE` per year
- [ ] Navbar academic year dropdown renders and persists selection to Zustand + localStorage
- [ ] Changing the year in navbar updates `academicYearStore.selectedYear`
- [ ] Academic Years page shows expandable terms rows
