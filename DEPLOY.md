# SeptroSchool Backend — Deployment Guide

## Requirements
- Ubuntu 22.04 (or Debian 12)
- Python 3.11+
- PostgreSQL 14+
- 1 GB RAM minimum

---

## Quick Deploy

### Step 1 — Server Setup (first time only)
```bash
sudo bash setup.sh
```
This installs: Python 3.11, PostgreSQL, Nginx, creates the DB user/database, and sets up the virtual environment.

### Step 2 — Configure Environment
```bash
cp .env.example .env
nano .env
```
**Required changes:**
- `DATABASE_URL` — use your actual PostgreSQL credentials
- `SECRET_KEY` — generate a random 64-char string: `openssl rand -hex 32`
- `INSTALL_SECRET_KEY` — set a strong secret (you'll use this once to initialize the system)
- `SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD` — your admin credentials

### Step 3 — Start the Server
```bash
bash run.sh
```

### Step 4 — Initialize the System
Make a single POST request to create all database tables, seed system data, and create the super admin:

```bash
curl -X POST http://localhost:8000/api/v1/install \
  -H "Content-Type: application/json" \
  -d '{
    "secret_key": "your-INSTALL_SECRET_KEY-from-env",
    "admin_email": "admin@yourschool.com",
    "admin_password": "YourStrongPassword123!"
  }'
```

**Note**: After successful installation, remove `INSTALL_SECRET_KEY` from your `.env` to disable the endpoint.

### Step 5 — Login
```
POST /api/v1/auth/login
{
  "username": "admin@yourschool.com",
  "password": "YourStrongPassword123!"
}
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/install/status` | Check if system is installed |
| POST | `/api/v1/install` | Install: create schema + seed data + super admin |
| POST | `/api/v1/auth/login` | Login (returns JWT token) |
| GET | `/api/v1/health` | Health check |

---

## Nginx Reverse Proxy (optional)

Example `/etc/nginx/sites-available/sms`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    location /uploads/ {
        alias /path/to/backend/uploads/;
    }
}
```

Enable: `ln -s /etc/nginx/sites-available/sms /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx`

---

## Systemd Service (keep running after reboot)

Create `/etc/systemd/system/sms-backend.service`:
```ini
[Unit]
Description=SeptroSchool Backend
After=network.target postgresql.service

[Service]
Type=exec
WorkingDirectory=/opt/sms/backend
ExecStart=/opt/sms/backend/venv/bin/bash run.sh
Restart=always
RestartSec=5
User=www-data
EnvironmentFile=/opt/sms/backend/.env

[Install]
WantedBy=multi-user.target
```

Enable: `systemctl enable sms-backend && systemctl start sms-backend`

---

## Troubleshooting

**DB connection error**: Verify `DATABASE_URL` in `.env` matches your PostgreSQL credentials.

**Tables not found**: Run install endpoint first, or run `alembic upgrade head` manually.

**Permission denied on uploads**: `chmod 775 uploads && chown www-data:www-data uploads`

**Port already in use**: Change `PORT=8001` in `.env` and update Nginx proxy_pass.
