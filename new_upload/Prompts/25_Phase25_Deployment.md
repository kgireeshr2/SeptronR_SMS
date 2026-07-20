# PHASE 25 — DEPLOYMENT & PRODUCTION SETUP

## Pre-Requisite
Phases 1–24 complete. All tests passing. Coverage ≥ 75%.

## Objective
Production-ready Docker Compose, Nginx with SSL, environment management, CI/CD pipeline (GitHub Actions), database backup automation, health check endpoints, and monitoring via Prometheus + Grafana.

---

## 25.1 Production Docker Compose (`docker-compose.prod.yml`)

```yaml
version: "3.9"

services:
  # ─── PostgreSQL ───────────────────────────────────────────
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s; timeout: 5s; retries: 5

  # ─── Redis ────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --save 60 1 --loglevel warning
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD}", "ping"]
      interval: 10s; timeout: 5s; retries: 5

  # ─── FastAPI (Gunicorn + Uvicorn workers) ─────────────────
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    restart: always
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s; timeout: 10s; start_period: 40s; retries: 3
    deploy:
      replicas: 2

  # ─── Celery Worker ────────────────────────────────────────
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    restart: always
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - postgres
      - redis

  # ─── Celery Beat (Scheduler) ──────────────────────────────
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.celery_app beat --loglevel=info --scheduler celery.beat:PersistentScheduler
    restart: always
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis

  # ─── Celery Flower (Monitor) ──────────────────────────────
  celery-flower:
    image: mher/flower:2.0
    restart: always
    command: celery flower --broker=redis://:${REDIS_PASSWORD}@redis:6379/0 --port=5555 --basic_auth=${FLOWER_USER}:${FLOWER_PASSWORD}
    expose:
      - "5555"
    depends_on:
      - redis

  # ─── Frontend (Nginx serving static files) ────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    restart: always
    expose:
      - "80"

  # ─── Nginx (Reverse Proxy + SSL) ──────────────────────────
  nginx:
    image: nginx:1.25-alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - api
      - frontend

  # ─── Prometheus ───────────────────────────────────────────
  prometheus:
    image: prom/prometheus:v2.47.0
    restart: always
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    expose:
      - "9090"

  # ─── Grafana ──────────────────────────────────────────────
  grafana:
    image: grafana/grafana:10.1.0
    restart: always
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    expose:
      - "3000"

volumes:
  postgres_data:
  redis_data:
  nginx_logs:
  prometheus_data:
  grafana_data:
```

---

## 25.2 Backend Dockerfile (`backend/Dockerfile.prod`)

```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app

# Install build dependencies for WeasyPrint, psycopg2, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libffi-dev libcairo2 libpango-1.0-0 \
    libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libssl-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Non-root user
RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keepalive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

---

## 25.3 Frontend Dockerfile (`frontend/Dockerfile.prod`)

```dockerfile
FROM node:20-alpine as builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build   # outputs to dist/

FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/spa.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

`frontend/nginx/spa.conf`:
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 25.4 Nginx Production Config (`nginx/nginx.prod.conf`)

```nginx
worker_processes auto;
events { worker_connections 1024; }

http {
    include mime.types;
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Rate limit zone
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

    upstream api_backend {
        server api:8000;
    }

    upstream frontend_backend {
        server frontend:80;
    }

    # Redirect HTTP → HTTPS
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate     /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers on;
        ssl_session_cache   shared:SSL:10m;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        client_max_body_size 20M;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api_backend;
            proxy_read_timeout 120s;
        }

        location /ws/ {
            proxy_pass http://api_backend;
            proxy_read_timeout 86400s;   # long timeout for WebSocket
        }

        location / {
            proxy_pass http://frontend_backend;
        }
    }
}
```

---

## 25.5 Environment Variables (`backend/.env.prod.example`)

```ini
# Database
POSTGRES_DB=sms_db
POSTGRES_USER=sms_user
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD
DATABASE_URL=postgresql+asyncpg://sms_user:CHANGE_ME@postgres:5432/sms_db

# Redis
REDIS_PASSWORD=CHANGE_ME_REDIS_PASSWORD
REDIS_URL=redis://:CHANGE_ME@redis:6379/0

# Security
SECRET_KEY=CHANGE_ME_64_CHAR_RANDOM_HEX_STRING
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]

# SMS (MSG91)
MSG91_AUTH_KEY=
MSG91_SENDER_ID=

# Email (SMTP default, or Sendgrid)
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@yourdomain.com

# WhatsApp (Meta Cloud API)
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_API_TOKEN=

# Firebase FCM
FCM_SERVER_KEY=

# Razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# Storage (use local or S3)
STORAGE_BACKEND=s3   # local or s3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_S3_REGION=ap-south-1

# Monitoring
FLOWER_USER=flower
FLOWER_PASSWORD=CHANGE_ME
GRAFANA_PASSWORD=CHANGE_ME
```

---

## 25.6 Health Check Endpoints

```python
# backend/app/api/v1/health.py

from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import get_db
from app.core.redis_client import redis

router = APIRouter()

@router.get("/health")
async def basic_health():
    """Basic liveness check — no dependencies."""
    return {"status": "ok", "service": "sms-api"}

@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check — verify DB and Redis connectivity."""
    checks = {"database": False, "redis": False}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception: pass

    try:
        await redis.ping()
        checks["redis"] = True
    except Exception: pass

    all_ok = all(checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks}
    )

@router.get("/health/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint (via prometheus-fastapi-instrumentator)."""
    # Handled automatically by instrumentator
    ...
```

```python
# In main.py:
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/api/v1/health/metrics")
```

Install: `pip install prometheus-fastapi-instrumentator`

---

## 25.7 Database Backup Script (`scripts/backup_db.sh`)

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sms_backup_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

echo "Starting backup at $DATE..."
docker exec sms-postgres-1 pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_FILE

echo "Backup created: $BACKUP_FILE"

# Upload to S3 (optional)
if [ -n "$AWS_S3_BUCKET" ]; then
    aws s3 cp $BACKUP_FILE s3://$AWS_S3_BUCKET/backups/
    echo "Uploaded to S3"
fi

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
echo "Old backups cleaned"
```

Add cron job on host: `0 2 * * * /opt/sms/scripts/backup_db.sh >> /var/log/sms_backup.log 2>&1`

---

## 25.8 Alembic Production Migration Strategy

```bash
# Before deploying any new version:
# 1. Create backup
# 2. Apply migrations
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# Rollback if needed:
docker compose -f docker-compose.prod.yml run --rm api alembic downgrade -1
```

---

## 25.9 CI/CD Pipeline (`.github/workflows/deploy.yml`)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: sms_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run backend tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml --cov-fail-under=75
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/sms_test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci-only-not-prod

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        run: cd frontend && npm ci

      - name: Frontend type check
        run: cd frontend && npm run type-check

      - name: Frontend tests
        run: cd frontend && npm run test:ci

      - name: Frontend build
        run: cd frontend && npm run build

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Build and push Docker images
        run: |
          docker build -t ghcr.io/${{ github.repository }}/api:${{ github.sha }} ./backend -f backend/Dockerfile.prod
          docker build -t ghcr.io/${{ github.repository }}/frontend:${{ github.sha }} ./frontend -f frontend/Dockerfile.prod
          echo "${{ secrets.GHCR_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/${{ github.repository }}/api:${{ github.sha }}
          docker push ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}

      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/sms
            # Pull new images
            docker pull ghcr.io/${{ github.repository }}/api:${{ github.sha }}
            docker pull ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
            # Update image tags in compose
            export API_IMAGE=ghcr.io/${{ github.repository }}/api:${{ github.sha }}
            export FRONTEND_IMAGE=ghcr.io/${{ github.repository }}/frontend:${{ github.sha }}
            # Run migrations
            docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
            # Rolling update
            docker compose -f docker-compose.prod.yml up -d --no-deps api celery-worker celery-beat frontend
            # Health check
            sleep 10
            curl -f http://localhost/api/v1/health/ready || (docker compose logs api; exit 1)
```

---

## 25.10 Prometheus Monitoring Config (`monitoring/prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: sms-api
    static_configs:
      - targets: ['api:8000']
    metrics_path: /api/v1/health/metrics

  - job_name: postgres
    static_configs:
      - targets: ['postgres-exporter:9187']  # optional: add postgres_exporter service

  - job_name: redis
    static_configs:
      - targets: ['redis-exporter:9121']     # optional: add redis_exporter service
```

**Grafana Dashboards to import:**
- Node Exporter Full: ID 1860
- FastAPI Monitoring: custom import from `monitoring/grafana_dashboard.json`

---

## 25.11 SSL Certificate Setup (Let's Encrypt)

```bash
# On host machine (not inside Docker), install certbot:
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certs to nginx ssl directory:
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/

# Auto-renew cron:
0 3 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/*.pem /opt/sms/nginx/ssl/ && docker compose -f /opt/sms/docker-compose.prod.yml exec nginx nginx -s reload
```

---

## 25.12 Production Deployment Runbook

```
1. Server Requirements:
   - Ubuntu 22.04 LTS
   - 4 vCPU, 8 GB RAM minimum (16 GB recommended)
   - 50 GB SSD
   - Docker + Docker Compose installed
   - Ports 80, 443 open in firewall

2. Initial Setup:
   git clone <repo> /opt/sms
   cd /opt/sms
   cp backend/.env.prod.example backend/.env.prod
   # Edit .env.prod with all production values
   cp frontend/.env.prod.example frontend/.env.prod

3. First Deploy:
   docker compose -f docker-compose.prod.yml build
   docker compose -f docker-compose.prod.yml up -d postgres redis
   sleep 5
   docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
   docker compose -f docker-compose.prod.yml run --rm api python -m app.scripts.seed_superadmin
   docker compose -f docker-compose.prod.yml up -d

4. Verify:
   curl https://yourdomain.com/api/v1/health          # → {"status":"ok"}
   curl https://yourdomain.com/api/v1/health/ready    # → {"status":"ready"}

5. Monitor:
   docker compose -f docker-compose.prod.yml logs -f api
   docker compose -f docker-compose.prod.yml ps
```

---

## 25.13 Seed Superadmin Script (`backend/app/scripts/seed_superadmin.py`)

```python
"""Run: python -m app.scripts.seed_superadmin"""
import asyncio
from app.db.session import AsyncSession, engine
from app.models.user import User
from app.core.security import hash_password

async def main():
    async with AsyncSession(engine) as db:
        existing = await db.execute(select(User).where(User.is_super_admin == True))
        if existing.scalar():
            print("Superadmin already exists")
            return
        user = User(
            email="superadmin@system.com",
            full_name="System Super Admin",
            password_hash=hash_password("CHANGE_ON_FIRST_LOGIN"),
            is_active=True,
            is_super_admin=True,
            school_id=None,
        )
        db.add(user)
        await db.commit()
        print(f"Superadmin created: {user.email}")

asyncio.run(main())
```

---

## 25.14 Deliverables Checklist

- [ ] `docker-compose.prod.yml` with all 9 services
- [ ] `backend/Dockerfile.prod` — multi-stage build, non-root user, Gunicorn
- [ ] `frontend/Dockerfile.prod` — multi-stage build, Nginx SPA serving
- [ ] `nginx/nginx.prod.conf` — SSL termination, gzip, WebSocket proxy, rate limiting
- [ ] `.env.prod.example` with all required variables documented
- [ ] Health endpoints: `/health` (liveness) and `/health/ready` (readiness)
- [ ] Prometheus metrics exposed via `prometheus-fastapi-instrumentator`
- [ ] `monitoring/prometheus.yml` scrape config
- [ ] Grafana data source configured for Prometheus
- [ ] Database backup script with S3 upload option
- [ ] Let's Encrypt SSL setup documented
- [ ] CI/CD GitHub Actions: test → build → push → deploy → verify
- [ ] Alembic migration run as part of deploy
- [ ] Superadmin seed script
- [ ] Production deployment runbook (README.md in `/deployment/`)
- [ ] Celery Flower UI accessible (behind basic auth)
- [ ] Log aggregation: all services log to stdout (Docker logging driver)
