# Feature Prompt 33 — Deployment

## Round: 4 of 4 — Advanced Features
## Prerequisites: All modules implemented and tested

---

## Objective

Set up production deployment with Docker Compose, Nginx reverse proxy with SSL, GitHub Actions CI/CD pipeline, environment configuration, backup strategy, and health monitoring.

---

## 1. Production Docker Compose (`docker-compose.prod.yml`)

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static_files:/app/static
    depends_on:
      - backend
      - frontend
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    volumes:
      - uploads:/app/uploads
    depends_on:
      - postgres
      - redis
    restart: always
    command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.celery_app worker -Q notifications,emails,reports,scheduled -c 2
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: always

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    volumes:
      - static_files:/app/dist
    environment:
      - VITE_API_URL=/api
      - VITE_FCM_VAPID_KEY=${FCM_VAPID_KEY}

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --save 60 1
    volumes:
      - redis_data:/data
    restart: always

  flower:
    image: mher/flower
    command: celery flower --broker=${REDIS_URL}
    ports:
      - "5555:5555"
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
  uploads:
  static_files:
```

---

## 2. Production Nginx Config (`nginx/nginx.prod.conf`)

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 20M;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend static
    root /app/static;
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Uploads
    location /uploads/ {
        alias /app/uploads/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}
```

---

## 3. Production Dockerfiles

### `backend/Dockerfile.prod`
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# System deps for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

### `frontend/Dockerfile.prod`
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM alpine:latest
COPY --from=builder /app/dist /app/dist
```

---

## 4. Environment Variables (`.env.production`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:STRONG_PASS@postgres:5432/sms_prod
POSTGRES_USER=postgres
POSTGRES_PASSWORD=STRONG_PASS
POSTGRES_DB=sms_prod

# Redis
REDIS_URL=redis://:REDIS_PASS@redis:6379/0
REDIS_PASSWORD=REDIS_PASS

# Security
SECRET_KEY=<64-char random hex>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=school@gmail.com
SMTP_PASSWORD=app_password

# FCM
FCM_SERVER_KEY=
FCM_VAPID_KEY=

# Razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# Environment
ENVIRONMENT=production
CORS_ORIGINS=["https://school.domain.com"]
```

---

## 5. GitHub Actions CI/CD (`.github/workflows/deploy.yml`)

```yaml
name: CI/CD

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env: { POSTGRES_PASSWORD: test }
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r backend/requirements.txt -r backend/requirements-dev.txt
      - run: cd backend && pytest --cov=app --cov-fail-under=80

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/sms
            git pull origin main
            docker compose -f docker-compose.prod.yml build
            docker compose -f docker-compose.prod.yml up -d
            docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
```

---

## 6. Database Backup Script (`scripts/backup.sh`)

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups
mkdir -p $BACKUP_DIR

docker compose exec -T postgres pg_dump -U postgres sms_prod | \
    gzip > $BACKUP_DIR/sms_prod_$DATE.sql.gz

# Keep last 7 days
find $BACKUP_DIR -mtime +7 -delete

echo "Backup complete: $BACKUP_DIR/sms_prod_$DATE.sql.gz"
```

Add to crontab: `0 2 * * * /opt/sms/scripts/backup.sh >> /var/log/sms_backup.log 2>&1`

---

## 7. Health Check Endpoints (already in `main.py`)

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": utcnow()}

@app.get("/health/db")
async def db_health(db=Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"database": "ok"}

@app.get("/health/redis")
async def redis_health(redis=Depends(get_redis)):
    await redis.ping()
    return {"redis": "ok"}
```

---

## 8. Post-Deployment Checklist

### First Deploy
- [ ] Copy `.env.production` to server
- [ ] `docker compose -f docker-compose.prod.yml up -d`
- [ ] `docker compose exec backend alembic upgrade head`
- [ ] `docker compose exec backend python -m app.scripts.seed_super_admin`
- [ ] Test `/health`, `/health/db`, `/health/redis`
- [ ] Configure SSL certificates (Let's Encrypt certbot)

### Ongoing
- [ ] GitHub Actions runs tests on every push to main
- [ ] Successful tests trigger auto-deploy to server
- [ ] Daily backup cron job running
- [ ] Flower monitoring at `:5555` (behind auth)

---

## Verification Checklist

- [ ] `docker compose -f docker-compose.prod.yml up -d` starts all 7 services
- [ ] Nginx redirects HTTP → HTTPS
- [ ] `/api/health` returns 200 in production
- [ ] Alembic migrations run in CI/CD pipeline
- [ ] Celery workers process notifications queue
- [ ] Celery Beat runs scheduled tasks
- [ ] Backup script produces compressed SQL dump
- [ ] GitHub Actions: tests must pass before deploy job runs
- [ ] CORS blocks requests from non-configured origins
- [ ] WeasyPrint PDF generation works inside Docker (pango libs installed)
