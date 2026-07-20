# Feature Prompt 30 — Settings Page

## Round: 4 of 4 — Advanced Features
## Prerequisites: Prompt 04 (School Profile)

---

## Objective

Implement the comprehensive 9-tab Settings Page that connects to `SchoolSettings` key-value store, allowing administrators to configure all aspects of the school system through the UI.

---

## 1. Settings Architecture

All settings stored in `school_settings` table as key-value pairs (from Prompt 04):
```
school_settings: school_id | key | value | data_type | category
```

Redis cache: `settings:{school_id}` — full school settings dict, TTL 5 minutes.

---

## 2. Settings API

```
GET    /settings                              → get all settings as dict       [settings:view]
PUT    /settings                              → update multiple settings       [settings:update]
PUT    /settings/{key}                        → update single setting          [settings:update]
POST   /settings/test-smtp                    → test SMTP connection           [settings:update]
POST   /settings/test-sms                     → send test SMS                  [settings:update]
```

---

## 3. Settings Categories & Keys

### Tab 1: General
| Key | Type | Default |
|-----|------|---------|
| `school_name` | string | "" |
| `school_logo_url` | string | "" |
| `school_address` | string | "" |
| `school_phone` | string | "" |
| `school_email` | string | "" |
| `school_website` | string | "" |
| `timezone` | string | "Asia/Kolkata" |
| `currency` | string | "INR" |
| `date_format` | string | "DD/MM/YYYY" |
| `academic_start_month` | int | 4 (April) |

### Tab 2: Admission
| Key | Type | Default |
|-----|------|---------|
| `admission_prefix` | string | "ADM" |
| `admission_auto_number` | bool | true |
| `admission_number_digits` | int | 5 |
| `admission_form_fields` | json | [...] |

### Tab 3: Attendance
| Key | Type | Default |
|-----|------|---------|
| `attendance_start_time` | string | "08:00" |
| `late_mark_grace_minutes` | int | 15 |
| `absent_notify_delay_minutes` | int | 60 |
| `min_attendance_pct` | float | 75.0 |
| `working_days_per_week` | int | 6 |

### Tab 4: Fee
| Key | Type | Default |
|-----|------|---------|
| `fee_receipt_prefix` | string | "RCP" |
| `fee_invoice_prefix` | string | "INV" |
| `late_fee_fine_type` | string | "daily" |
| `late_fee_grace_days` | int | 5 |
| `razorpay_key_id` | string | "" |
| `razorpay_key_secret` | string (encrypted) | "" |

### Tab 5: Exam
| Key | Type | Default |
|-----|------|---------|
| `default_passing_marks` | float | 35.0 |
| `grade_display` | string | "both" (letter+pct) |

### Tab 6: Library
| Key | Type | Default |
|-----|------|---------|
| `default_loan_days` | int | 14 |
| `library_fine_per_day_paise` | int | 200 |
| `max_books_student` | int | 3 |
| `max_books_staff` | int | 5 |

### Tab 7: Communication
| Key | Type | Default |
|-----|------|---------|
| `sms_provider` | string | "msg91" |
| `msg91_auth_key` | string (encrypted) | "" |
| `msg91_sender_id` | string | "" |
| `smtp_host` | string | "" |
| `smtp_port` | int | 587 |
| `smtp_user` | string | "" |
| `smtp_password` | string (encrypted) | "" |
| `smtp_from_name` | string | "" |
| `whatsapp_phone_id` | string | "" |
| `whatsapp_token` | string (encrypted) | "" |
| `fcm_server_key` | string (encrypted) | "" |

### Tab 8: Security
| Key | Type | Default |
|-----|------|---------|
| `password_min_length` | int | 8 |
| `session_timeout_minutes` | int | 60 |
| `max_login_attempts` | int | 5 |
| `lockout_duration_minutes` | int | 30 |
| `two_factor_enabled` | bool | false |

### Tab 9: Integrations
| Key | Type | Default |
|-----|------|---------|
| `google_maps_api_key` | string | "" |
| `google_analytics_id` | string | "" |
| `razorpay_webhook_secret` | string (encrypted) | "" |

---

## 4. Frontend: Settings Page (`/settings`)

```
9-Tab Layout:
[General] [Admission] [Attendance] [Fee] [Exam] [Library] [Communication] [Security] [Integrations]
```

Each tab:
- Form with settings fields
- Field types: text, number, boolean toggle, select, secret (password field with show/hide)
- "Save Changes" button per tab (PATCH only that category's keys)
- Loading / success / error toast feedback

### Communication Tab Special:
- SMTP Test button → calls `POST /settings/test-smtp`
- SMS Test button → enter phone, send test message
- Shows delivery status inline

---

## 5. Settings Service

```python
async def get_all_settings(db, redis, school_id) -> dict:
    """Get from Redis or DB. Returns flat dict of all key→value."""

async def update_settings(db, redis, school_id, updates: dict, current_user):
    """
    For each key in updates:
      - Validate key is a known setting key.
      - Encrypt if data_type == 'secret'.
      - Upsert in school_settings table.
    Invalidate Redis cache.
    Audit log.
    """

async def test_smtp(db, school_id) -> dict:
    """Send test email to current_user's email. Return {success, message}."""

async def test_sms(db, school_id, phone: str) -> dict:
    """Send test SMS. Return {success, provider, message}."""
```

---

## Verification Checklist

- [ ] Settings loaded from `school_settings` table (not hardcoded)
- [ ] Encrypted settings (secret type) stored encrypted, never returned in plain text
- [ ] Redis cache invalidated on any settings update
- [ ] Each tab saves independently (only that tab's keys)
- [ ] SMTP test sends actual email to current user's email
- [ ] Unknown setting keys in PUT payload return 422 validation error
- [ ] `absent_notify_delay_minutes` used by Celery attendance task (Prompt 12)
- [ ] `razorpay_key_id` / `razorpay_key_secret` used by fee payment endpoints (Prompt 14)
