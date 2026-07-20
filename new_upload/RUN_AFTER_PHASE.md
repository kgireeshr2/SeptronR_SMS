# Runbook: Commands to run after each phase implementation

Use these commands from the project root (`SMS`) on Windows PowerShell.

## 1) One-time setup (first time on a machine)

### Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
Copy-Item .env.example .env
cd ..
```

### Frontend
```powershell
cd frontend
npm install
if (Test-Path .env.example) { Copy-Item .env.example .env -Force }
cd ..
```

### Infrastructure (Postgres + Redis)

**Manual Setup:** Ensure PostgreSQL is running locally
- Database: `sms_db`
- Username/password: configured in `backend/.env`
- Default: `postgresql+asyncpg://postgres:postgres@localhost/sms_db`

---

## 2) After every new phase pull/merge

### Update backend dependencies
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
cd ..
```

### Update frontend dependencies
```powershell
cd frontend
npm install
cd ..
```

### Update DB schema
> If phase includes DB/model changes, run migrations:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
cd ..
```

> If migration file is not yet created for your latest model change, create it first:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic revision --autogenerate -m "phase-update"
alembic upgrade head
cd ..
```

> Important: always open the generated migration file and verify it contains only current phase changes before running `alembic upgrade head`.

### (Optional, usually first setup only) Seed default data
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.scripts.seed_data
cd ..
```

### Missed previous phases? Catch up all migrations + seed at once

#### Quick Run (Recommended - Command Prompt)

**Double-click** `catchup-migrations.bat` in the project root, or run from CMD:

```cmd
catchup-migrations.bat
```

This script will automatically:
1. Activate virtual environment
2. Check current migration state (`alembic current`)
3. Apply all pending migrations (`alembic upgrade head`)
4. Seed platform data (permissions, roles, super admin)

#### Option A (Manual - Keep existing data)
```powershell
# from project root
cd backend
.\.venv\Scripts\Activate.ps1
alembic current
alembic upgrade head
python -m app.scripts.seed_data
cd ..
```

#### Option B (Manual - Fresh rebuild, destructive)
```cmd
# 1) Drop and recreate database manually
# Using pgAdmin or psql:
#   DROP DATABASE sms_db;
#   CREATE DATABASE sms_db;

# Or using psql command line:
psql -U postgres -c "DROP DATABASE IF EXISTS sms_db;"
psql -U postgres -c "CREATE DATABASE sms_db;"

# 2) migrate from base to latest + seed
cd backend
.venv312\Scripts\activate.bat
alembic upgrade head
python -m app.scripts.seed_data
cd ..
```

> Notes:
> - `alembic upgrade head` runs **all pending phase migrations** in sequence.
> - `python -m app.scripts.seed_data` seeds platform permissions, roles, and super admin (idempotent-safe for repeats).
> - If Alembic revision is out of sync, do **not** stamp blindly. First validate DB state, then either:
>   - use **Option A** (`alembic upgrade head`) if schema is mostly intact, or
>   - use **Option B** (fresh rebuild) for a guaranteed clean baseline.

---

## 3) Run app (local development)

### Terminal 1: backend API
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: frontend
```powershell
cd frontend
npm run dev
```

---

## 4) Quick health checks

```powershell
# Backend docs
Start-Process http://localhost:8000/docs

# Frontend
Start-Process http://localhost:5173
```

