# Feature Prompt 21 — Communication & Notifications

## Round: 4 of 4 — Advanced Features
## Prerequisites: Prompts 01–05, 09 (Students), 10 (Staff)

---

## Objective

Implement a 5-channel notification engine (SMS, WhatsApp, Email, FCM Push, in-app WebSocket), notification templates, bulk messaging, and notification history.

> **CRITICAL FIELD NAME** (from Fix 01):
> - `Notification.notification_metadata` mapped to DB column `"metadata"` (NOT `data`)

---

## 1. Database Models (`backend/app/models/notification.py`)

```python
import uuid
from sqlalchemy import String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
import enum

class NotificationChannel(str, enum.Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"

class NotificationTemplate(Base, TimestampMixin):
    __tablename__ = "notification_templates"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # absent_notification, fee_reminder, etc.
    channels: Mapped[list] = mapped_column(JSONB, default=[])  # ["sms", "email"]
    subject: Mapped[str | None] = mapped_column(String(300), nullable=True)  # email subject
    body_template: Mapped[str] = mapped_column(Text, nullable=False)  # Jinja2 template string
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)
    recipient_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(300), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(String(20), default=NotificationStatus.PENDING)
    sent_at: Mapped[str | None] = mapped_column(nullable=True)  # TIMESTAMPTZ
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # NOTE: notification_metadata mapped to DB column "metadata" (NOT data)
    notification_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default={})
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[str | None] = mapped_column(nullable=True)


class BulkMessage(Base, TimestampMixin):
    __tablename__ = "bulk_messages"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channels: Mapped[list] = mapped_column(JSONB, default=[])
    recipient_type: Mapped[str] = mapped_column(String(50), nullable=False)  # all/students/staff/parents/class
    recipient_filter: Mapped[dict] = mapped_column(JSONB, default={})  # {class_id, section_id}
    sent_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_recipients: Mapped[int] = mapped_column(default=0)
    sent_count: Mapped[int] = mapped_column(default=0)
    failed_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
```

---

## 2. Alembic Migration

```sql
CREATE TABLE notification_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    channels JSONB DEFAULT '[]' NOT NULL,
    subject VARCHAR(300),
    body_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    recipient_user_id UUID REFERENCES users(id),
    recipient_phone VARCHAR(20),
    recipient_email VARCHAR(255),
    channel VARCHAR(20) NOT NULL,
    subject VARCHAR(300),
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB DEFAULT '{}' NOT NULL,  -- field: notification_metadata → column: "metadata"
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_notifications_user ON notifications(recipient_user_id, is_read);
CREATE INDEX ix_notifications_school ON notifications(school_id, status);

CREATE TABLE bulk_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    message TEXT NOT NULL,
    channels JSONB DEFAULT '[]' NOT NULL,
    recipient_type VARCHAR(50) NOT NULL,
    recipient_filter JSONB DEFAULT '{}' NOT NULL,
    sent_by UUID NOT NULL REFERENCES users(id),
    total_recipients INTEGER DEFAULT 0 NOT NULL,
    sent_count INTEGER DEFAULT 0 NOT NULL,
    failed_count INTEGER DEFAULT 0 NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

---

## 3. Notification Engine (`backend/app/services/notification_engine.py`)

```python
class NotificationEngine:
    """5-channel notification dispatcher."""

    async def send(self, school_id, recipient, channel, message, subject=None, metadata={}):
        """
        1. Create Notification record with status=pending.
        2. Dispatch to appropriate provider.
        3. Update status=sent/failed.
        """

    async def send_sms(self, phone: str, message: str, school_id) -> bool:
        """
        Provider: MSG91 (default) or Twilio based on school settings.
        MSG91: POST https://api.msg91.com/api/v5/flow/
        Twilio: twilio-python SDK.
        Returns success bool.
        """

    async def send_whatsapp(self, phone: str, message: str, template_name: str, school_id) -> bool:
        """
        Meta WhatsApp Cloud API.
        POST /v17.0/{phone_number_id}/messages
        Requires WHATSAPP_TOKEN and WHATSAPP_PHONE_ID in settings.
        """

    async def send_email(self, to_email: str, subject: str, body: str, school_id) -> bool:
        """
        SMTP via aiosmtplib.
        Credentials from school settings: smtp_host, smtp_port, smtp_user, smtp_password.
        """

    async def send_push(self, fcm_token: str, title: str, body: str, data: dict) -> bool:
        """
        Firebase Cloud Messaging via firebase-admin.
        Uses FCM_SERVER_KEY from settings.
        """

    async def send_in_app(self, user_id: UUID, message: str, metadata: dict):
        """
        Write Notification record. Broadcast via WebSocket manager.
        """
```

---

## 4. WebSocket Manager (`backend/app/utils/websocket_manager.py`)

```python
class WebSocketManager:
    """Manages active WebSocket connections per user."""
    connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept + store connection."""

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove from connections dict."""

    async def broadcast_to_user(self, user_id: str, message: dict):
        """Send JSON to all connections for user_id."""

    async def broadcast_to_school(self, school_id: str, message: dict):
        """Send to all connected users in school."""

manager = WebSocketManager()
```

WebSocket endpoint:
```python
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

---

## 5. Celery Tasks

```python
@celery_app.task(name="send_bulk_message", queue="notifications")
def send_bulk_message(bulk_message_id: str, school_id: str):
    """
    1. Load BulkMessage and resolve recipient list.
    2. For each recipient: call notification_engine.send() on each channel.
    3. Update BulkMessage.sent_count / failed_count.
    4. Set status=completed.
    """

@celery_app.task(name="send_notification", queue="notifications")
def send_notification(notification_id: str):
    """Send single queued notification."""
```

---

## 6. API Endpoints

```
# Templates
GET    /notification-templates               → list templates                 [communication:view]
POST   /notification-templates               → create template                [communication:create]
PUT    /notification-templates/{id}          → update template                [communication:update]
POST   /notification-templates/{id}/test     → send test notification         [communication:create]

# Bulk Messages
POST   /bulk-messages                        → send bulk message              [communication:create]
GET    /bulk-messages                        → message history                [communication:view]
GET    /bulk-messages/{id}                   → delivery stats                 [communication:view]

# Notifications (in-app)
GET    /notifications/my                     → my unread notifications        [auth]
POST   /notifications/{id}/read              → mark as read                   [auth]
POST   /notifications/read-all              → mark all as read               [auth]

# WebSocket
WS     /ws/{user_id}                         → real-time notification stream  [auth via token param]
```

---

## 7. Frontend: Communication Pages

### Notifications Bell (navbar)
- Badge with unread count (from TanStack Query polling every 30s)
- Dropdown panel: last 10 notifications
- "Mark all read" button
- WebSocket listener updates count in real-time

### Communication Page (`/communication`)
- **Send Message tab**: Recipient selector (All/Students/Staff/Parents/Class/Section) + Channel checkboxes + Message composer
- **Templates tab**: CRUD for notification templates with preview
- **History tab**: Table of past bulk messages with delivery stats

---

## 8. Custom Hooks

```typescript
export function useNotifications() {
  // TanStack Query + WebSocket combined
  // Polls /notifications/my, updates on WS message
}
export function useSendBulkMessage() { ... }
export function useNotificationTemplates() { ... }
```

---

## Verification Checklist

- [ ] `notification_metadata` field mapped to DB column `"metadata"` (NOT `data`)
- [ ] WebSocket manager stores per-user connections
- [ ] SMS provider configured from school settings (MSG91 vs Twilio)
- [ ] WhatsApp requires WHATSAPP_TOKEN and WHATSAPP_PHONE_ID settings
- [ ] Bulk message resolves recipients from student_enrollments or staff table
- [ ] In-app notification count badge updates via WebSocket (no page refresh needed)
- [ ] `send_notification` Celery task retries on failure (max_retries=3)
- [ ] Template body_template uses Jinja2 syntax: `{{ student_name }}`
- [ ] Test notification endpoint sends to current_user's own contact
