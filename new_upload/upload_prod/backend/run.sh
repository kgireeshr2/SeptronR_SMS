#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  SeptroSchool Backend — Production Startup Script
#  Usage: bash run.sh
# ═══════════════════════════════════════════════════════════
set -e

echo ""
echo "══════════════════════════════════════════════════"
echo "   SeptroSchool — Backend"
echo "══════════════════════════════════════════════════"
echo ""

# Load environment
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

export $(grep -v '^#' .env | xargs -d '\n')

# Activate virtualenv if present
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Run Alembic migrations
echo "→ Running database migrations..."
alembic upgrade head
echo "✓ Migrations complete"

# Start the server
WORKERS=${WORKERS:-4}
PORT=${PORT:-8000}
echo "→ Starting server on port $PORT with $WORKERS workers..."
echo ""

exec gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    --workers $WORKERS \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
