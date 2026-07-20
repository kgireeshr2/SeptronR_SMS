---
name: deploy-mirror-upload-prod
description: Backend code must be mirrored into upload_prod/backend for deploys
metadata:
  type: feedback
---

The user manually deploys the backend and maintains a parallel copy at `upload_prod/backend/`. Any edit to a file under `backend/` must be copied to the matching path under `upload_prod/backend/`.

**Why:** prod is deployed from that copy, so a fix only in `backend/` won't reach production.

**How to apply:** after editing `backend/<path>`, `cp` it to `upload_prod/backend/<path>` and verify with `diff -q`. The only intended differences are `Dockerfile`, `tests/`, and stray output files (not app source). Ignore the stale `upload_prod/backend.zip` (old artifact, not used). See [[db-and-deploy-setup]].
