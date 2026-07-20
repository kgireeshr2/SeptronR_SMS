@echo off
REM ============================================
REM Fix Migration Chain - Reset & Rebuild DB
REM ============================================

echo.
echo ============================================
echo   SMS Database Reset ^& Migration Script
echo ============================================
echo.
echo Migration chain is now fixed:
echo   Phase 3 -^> Phase 4-7 -^> Phase 8
echo.
echo This will:
echo   1. Drop and recreate database
echo   2. Run all migrations
echo   3. Seed platform data
echo.
echo WARNING: This will DELETE all existing data!
echo.
echo MANUAL STEP REQUIRED:
echo Before continuing, drop and recreate your PostgreSQL database:
echo   1. Open pgAdmin or psql
echo   2. Drop database: DROP DATABASE sms_db;
echo   3. Create database: CREATE DATABASE sms_db;
echo   4. Press any key here to continue...
echo.
pause
echo.

REM Go to backend
cd /d "%~dp0backend"

set "PYTHON_EXE=.venv312\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python executable not found at %PYTHON_EXE%
    pause
    exit /b 1
)

REM Use project virtual environment python
echo.
echo [1/3] Using project Python virtual environment...

REM Run migrations
echo.
echo [2/3] Running all migrations...
echo   fa0af85a7400 (base)
echo   -^> 72a653d7fd53
echo   -^> d4c29e3b39a6 (Phase 3: academic, admissions)
echo   -^> phases4to7abc123 (Phase 4-7: classes, students, staff, attendance)
echo   -^> 94aca4ee63c9 (Phase 8: fees)
echo.
"%PYTHON_EXE%" -m alembic upgrade head

if errorlevel 1 (
    echo.
    echo ERROR: Migration failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Seeding platform data...
"%PYTHON_EXE%" -m app.scripts.seed_data

if errorlevel 1 (
    echo.
    echo ERROR: Seed script failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   ✓ Database reset and migrations applied!
echo ============================================
echo.
"%PYTHON_EXE%" -m alembic current
echo.
echo Next steps:
echo   1. Start backend: uvicorn app.main:app --reload
echo   2. Start frontend: cd frontend ^&^& npm run dev
echo.
echo Future updates: use catchup-migrations.bat
echo.

pause
