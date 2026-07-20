# PHASE 14 — COMMUNICATION & NOTIFICATIONS

## Pre-Requisite
Phases 1–13 complete. Users (students, parents, staff) exist with phones/emails.

## Objective
Centralized messaging: bulk SMS, WhatsApp, email and in-app notifications; notification templates; push notifications (FCM); real-time updates via WebSocket; notification history and delivery tracking.

---

## 14.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 17: Communication & Notifications
notification_templates (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    channel notification_channel,    -- ⚠️ ENUM type: sms|email|whatsapp|push|in_app
    event_trigger notification_trigger NOT NULL,  -- ⚠️ field: event_trigger (not event_key), ENUM type
        -- ENUM values: attendance_absent|fee_due|fee_receipt|result_published|homework_assigned|
        --              ptm_reminder|birthday|custom|...
    subject VARCHAR(300),     -- for email
    body TEXT,                -- Jinja2 template string
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, channel, event_trigger)
)

-- ⚠️ TABLE NAME: notifications (NOT in_app_notifications)
notifications (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    user_id UUID FK→users ON DELETE CASCADE,
    type notification_trigger,    -- ⚠️ field: 'type' (not 'event_key')
    channel notification_channel,
    title VARCHAR(300), body TEXT,
    data JSONB,           -- event-specific payload
    is_read BOOL DEFAULT FALSE, read_at TIMESTAMPTZ,
    created_at
)

-- ⚠️ TABLE NAME: bulk_messages (NOT message_broadcasts)
bulk_messages (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    title VARCHAR(300), body TEXT,
    channels JSONB,              -- ["sms","whatsapp","email"]
    target_type VARCHAR(50),     -- all|class|section|students|parents|staff|custom
    target_ids JSONB DEFAULT '[]',
    target_class_id UUID (nullable), target_section_id UUID (nullable),
    scheduled_at TIMESTAMPTZ (nullable), sent_at TIMESTAMPTZ,
    total_recipients INT DEFAULT 0,
    sent_count INT DEFAULT 0, failed_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',   -- draft|scheduled|sending|sent|failed
    created_by UUID FK→users, created_at, updated_at
)

-- ⚠️ TABLE NAME: message_logs (NOT notification_logs) — tracks per-recipient delivery
message_logs (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    bulk_message_id UUID FK→bulk_messages (nullable),
    recipient_user_id UUID (nullable),
    recipient_phone VARCHAR(20), recipient_email VARCHAR(200),
    channel notification_channel,
    event_trigger notification_trigger,
    subject VARCHAR(300), body TEXT,
    status VARCHAR(20) DEFAULT 'queued',  -- queued|sent|failed|delivered
    gateway_response TEXT,
    sent_at TIMESTAMPTZ, delivered_at TIMESTAMPTZ,
    error_message TEXT,
    created_at
)

-- ⚠️ ADDITIONAL TABLE: announcements (missing from original prompt)
announcements (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    content TEXT,
    attachment_url TEXT,
    audience VARCHAR(20) DEFAULT 'all',  -- all|students|parents|staff|class|section
    target_class_id UUID FK→classes (nullable),
    target_section_id UUID FK→sections (nullable),
    is_published BOOL DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_by UUID FK→users,
    created_at, updated_at
)
```

---

## 14.2 Notification Gateway Abstraction (`backend/app/utils/notifications.py`)

```python
class NotificationService:
    async def send_sms(self, phone: str, message: str, school_id: str) -> dict:
        """
        Use SMS gateway from school settings (msg91|twilio).
        Log to notification_logs regardless of success/failure.
        """

    async def send_whatsapp(self, phone: str, message: str, template: str, params: dict, school_id: str) -> dict:
        """Use Meta Cloud API or gupshup. Uses pre-approved templates."""

    async def send_email(self, to: str, subject: str, body: str, school_id: str) -> dict:
        """Use SMTP or SendGrid based on school settings."""

    async def send_push(self, user_id: str, title: str, body: str, data: dict, school_id: str) -> dict:
        """Use FCM. Look up FCM token for user from redis or DB."""

    async def send_in_app(self, user_id: str, title: str, body: str, data: dict, event_key: str, school_id: str):
        """Create notifications record + broadcast via WebSocket to user's room."""

    async def render_template(self, school_id: str, event_key: str, channel: str, context: dict) -> dict:
        """Load template from notification_templates, render with Jinja2, return {subject, body}."""
```

---

## 14.3 WebSocket Setup (`backend/app/api/ws/notifications.py`)

```python
from fastapi import WebSocket
import asyncio
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # user_id → sockets

    async def connect(self, websocket: WebSocket, user_id: str, school_id: str):
        await websocket.accept()
        self.active_connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.get(user_id, set()).discard(websocket)

    async def send_to_user(self, user_id: str, message: dict):
        for ws in list(self.active_connections.get(user_id, set())):
            try:
                await ws.send_json(message)
            except:
                self.active_connections.get(user_id, set()).discard(ws)

manager = ConnectionManager()

@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str, school_slug: str):
    """
    1. Decode JWT from token query param → user_id
    2. Verify school_slug
    3. Connect to manager
    4. On receive: handle ping/pong
    5. On disconnect: call manager.disconnect
    """
```

---

## 14.4 API Endpoints

```
# Notification Templates (⚠️ field: event_trigger not event_key)
GET  /api/v1/notifications/templates           → list [notifications:manage]
POST /api/v1/notifications/templates           → create/upsert
PUT  /api/v1/notifications/templates/{id}      → update
DELETE /api/v1/notifications/templates/{id}    → delete
POST /api/v1/notifications/templates/{id}/test → send test to current user [notifications:manage]

# Broadcast Messages (⚠️ maps to bulk_messages table, not message_broadcasts)
GET  /api/v1/notifications/broadcasts          → list bulk_messages [notifications:view]
POST /api/v1/notifications/broadcasts          → create bulk_message [notifications:send]
GET  /api/v1/notifications/broadcasts/{id}     → detail with delivery stats
POST /api/v1/notifications/broadcasts/{id}/send → send immediately (or confirm)
DELETE /api/v1/notifications/broadcasts/{id}   → delete draft

# Logs (⚠️ maps to message_logs table, not notification_logs)
GET  /api/v1/notifications/logs                → list message_logs [notifications:view]
GET  /api/v1/notifications/logs/stats          → channel delivery stats [notifications:view]

# In-App (⚠️ maps to notifications table, not in_app_notifications)
GET  /api/v1/notifications/inbox               → list own notifications
POST /api/v1/notifications/inbox/{id}/read     → mark as read
POST /api/v1/notifications/inbox/read-all      → mark all read
GET  /api/v1/notifications/inbox/unread-count  → badge count

# Announcements (⚠️ NEW — announcements table in schema)
GET  /api/v1/announcements                     → list (filter: audience, published) [announcements:view]
POST /api/v1/announcements                     → create [announcements:manage]
GET  /api/v1/announcements/{id}                → detail
PUT  /api/v1/announcements/{id}                → update
DELETE /api/v1/announcements/{id}              → delete
POST /api/v1/announcements/{id}/publish        → publish [announcements:manage]

# WebSocket
WS   /ws/notifications?token=JWT&school_slug=X → real-time channel
```

---

## 14.5 Celery Tasks

```python
@celery.task(queue="sms", bind=True, max_retries=3)
def send_sms_task(self, phone: str, message: str, school_id: str, log_id: str):
    """Send SMS, update message_logs record with status. Retry on failure."""
    # ⚠️ log_id is FK→message_logs (not notification_logs)

@celery.task(queue="emails", bind=True, max_retries=3)
def send_email_task(self, to: str, subject: str, html_body: str, school_id: str, log_id: str): ...

@celery.task(queue="whatsapp", bind=True, max_retries=3)
def send_whatsapp_task(self, phone: str, template: str, params: dict, school_id: str, log_id: str): ...

@celery.task(queue="push")
def send_push_task(self, user_id: str, title: str, body: str, data: dict, school_id: str): ...

@celery.task(queue="notifications")
def process_broadcast(broadcast_id: str):
    """
    Load broadcast, resolve recipients (students/parents/staff based on target_type).
    For each recipient: enqueue individual send tasks per channel.
    Update broadcast: sent_count, failed_count, status.
    """

@celery.task(queue="notifications", eta=scheduled_at)
def scheduled_broadcast(broadcast_id: str):
    """Triggered at scheduled_at time → call process_broadcast."""
```

---

## 14.6 Event Triggers Reference

> **Field name is `event_trigger` (enum type `notification_trigger`), not `event_key` VARCHAR**

| event_trigger value | Description | Default Channels |
|---------------------|-------------|------------------|
| attendance_absent | Student absent | sms, whatsapp |
| attendance_late | Student late | sms |
| fee_due | Fee due in N days | sms, email |
| fee_receipt | Fee payment confirmation | sms, email |
| result_published | Exam results available | sms, push |
| homework_assigned | New homework | push, in_app |
| ptm_reminder | PTM reminder | sms, push |
| birthday | Student/staff birthday | push, in_app |
| custom | Custom broadcast | custom |

---

## 14.7 Frontend Pages

### `/admin/communications` Page (Permission: `notifications:view`)

**Compose Tab:**
- Target: Radio (All Parents | All Staff | Specific Class | Specific Section | Custom list)
- Channels: checkboxes (SMS, WhatsApp, Email, Push)
- Message body (for SMS/WhatsApp) + Subject + HTML body (for email)
- Schedule: send now or pick date/time
- Preview recipients count before sending

**Templates Tab:**
- List by event_key
- Edit template body (Jinja2 vars shown as chips: {{student_name}}, {{amount}}, etc.)
- Send test notification button

**Logs Tab:**
- Filter: channel, status, date range
- Table: Recipient, Channel, Event, Status, Sent At, Error (if any)
- Delivery stats: total sent, delivered, failed per channel

**Inbox Bell (all users):**
- Bell icon in navbar with unread badge count (from WebSocket or polling)
- Dropdown showing latest 10 in-app notifications
- Mark all read / click notification → navigate to related page

### `frontend/src/api/notifications.ts`
```typescript
export const notificationsApi = {
  getTemplates: () => api.get('/notifications/templates'),
  saveTemplate: (data: TemplateCreate) => api.post('/notifications/templates', data),
  updateTemplate: (id: string, data: Partial<TemplateCreate>) => api.put(`/notifications/templates/${id}`, data),
  testTemplate: (id: string) => api.post(`/notifications/templates/${id}/test`),
  listBroadcasts: () => api.get('/notifications/broadcasts'),
  createBroadcast: (data: BroadcastCreate) => api.post('/notifications/broadcasts', data),
  sendBroadcast: (id: string) => api.post(`/notifications/broadcasts/${id}/send`),
  getLogs: (params: LogParams) => api.get('/notifications/logs', { params }),
  getInbox: () => api.get('/notifications/inbox'),
  markRead: (id: string) => api.post(`/notifications/inbox/${id}/read`),
  markAllRead: () => api.post('/notifications/inbox/read-all'),
  getUnreadCount: () => api.get('/notifications/inbox/unread-count'),
};
```

### WebSocket Hook (`frontend/src/hooks/useNotificationSocket.ts`)
```typescript
export function useNotificationSocket() {
  const { token } = useAuthStore();
  const schoolSlug = /* from env or context */;

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/notifications?token=${token}&school_slug=${schoolSlug}`);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'notification') {
        toast.info(data.title);  // shadcn toast
        queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
      }
    };
    return () => ws.close();
  }, [token]);
}
```

---

## 14.8 Tests

```python
async def test_sms_task_logs_on_success(): ...
async def test_sms_task_retries_on_failure(): ...
async def test_broadcast_resolves_recipients_by_class(): ...
async def test_template_rendering_with_jinja2(): ...
async def test_in_app_notification_created(): ...
async def test_mark_read_updates_flag(): ...
async def test_websocket_connection_auth(): ...     # invalid token → close
```

---

## 14.9 Deliverables Checklist

- [ ] Notification template CRUD per event_key + channel
- [ ] Jinja2 template rendering with context variables
- [ ] SMS sending via configured gateway (MSG91/Twilio)
- [ ] Email sending via SMTP/SendGrid
- [ ] WhatsApp message sending via Meta Cloud API / Gupshup
- [ ] FCM push notification sending
- [ ] In-app notification creation + WebSocket broadcast
- [ ] Real-time WebSocket endpoint with JWT auth
- [ ] Broadcast composer (target: class/section/all/custom)
- [ ] Scheduled broadcast via Celery ETA
- [ ] Delivery tracking in notification_logs
- [ ] Notification inbox in frontend with unread badge
- [ ] Bell icon with live unread count (WebSocket update)
- [ ] Retry on failure (max 3 attempts) for SMS/email
