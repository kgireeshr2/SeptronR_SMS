@echo off
REM ============================================
REM Catch-up All Missed Phase Migrations + Seed
REM ============================================
REM Usage: Double-click this file or run from CMD
REM        catchup-migrations.bat

echo.
echo ============================================
echo   SMS Migrations Catch-Up Script
echo ============================================
echo.

REM Change to backend directory
cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist ".venv312\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at backend\.venv312
    echo Please run setup first from RUN_AFTER_PHASE.md section 1
    pause
    exit /b 1
)

set "PYTHON_EXE=.venv312\Scripts\python.exe"

REM Use project virtual environment python
echo [1/4] Using project Python virtual environment...

REM Show current migration state
echo.
echo [2/4] Checking current migration state...
"%PYTHON_EXE%" -m alembic current
echo.

REM Run all pending migrations
echo [3/4] Applying all pending migrations...
"%PYTHON_EXE%" -m alembic upgrade head

if errorlevel 1 (
    echo.
    echo ERROR: Migration failed!
    echo Check the error above and fix before proceeding.
    pause
    exit /b 1
)

echo.
echo ✓ Migrations completed successfully
echo.

REM Seed platform data
echo [4/4] Seeding platform data (permissions, roles, super admin)...
"%PYTHON_EXE%" -m app.scripts.seed_data

if errorlevel 1 (
    echo.
    echo ERROR: Seed script failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   ✓ All migrations and seed data applied!
echo ============================================
echo.
echo Migration status:
echo.
echo Next steps:
echo   1. Start backend: uvicorn app.main:app --reload
echo   2. Start frontend: cd frontend ^&^& npm run dev
echo.

pause
