---
name: db-and-deploy-setup
description: SMS backend database engine, hosting, and how prod is deployed
metadata:
  type: project
---

The SMS backend runs on **PostgreSQL** (asyncpg) and is deeply coupled to Postgres-only SQL: ~114 raw `text()` queries across 19 files, plus `DATE_TRUNC`, `TO_CHAR`, `INTERVAL '…'`, `NULLS LAST`, `gen_random_uuid()`. A 2026 attempt to migrate to MySQL/asyncmy (commits c30de4d, 10d1f35) was **abandoned** because that SQL has no clean MySQL equivalent — the app is treated as Postgres-only.

Prod DB is **Aiven PostgreSQL** (host `sms-pg-db-eskoolyapplication-sms.e.aivencloud.com`, db `defaultdb`), requires SSL. `DATABASE_URL` is set in the Render dashboard (`sync: false` in render.yaml) as `postgres://…?sslmode=require`. asyncpg doesn't understand libpq's `sslmode`, so [session.py](backend/app/db/session.py) strips it and builds an SSL context (encrypt, no CA verify = sslmode=require). Backend runs on **Render** (free, Singapore), built from `backend/` via Docker.

First-time setup uses `POST /api/v1/install` (gated by `INSTALL_SECRET_KEY`) which runs `create_all` + seeds permissions/roles/super admin — there is no install UI. Default super admin: `superadmin@sms.com`.

**Deploy:** the user manually deploys and keeps a parallel copy in `upload_prod/backend/` — changes to `backend/` must be mirrored there. See [[deploy-mirror-upload-prod]].
