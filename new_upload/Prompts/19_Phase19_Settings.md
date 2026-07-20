# PHASE 19 — SCHOOL SETTINGS PAGE

## Pre-Requisite
Phases 1–18 complete. `school_settings` table populated with defaults.

## Objective
Complete Settings page with all configuration categories: General, Admission, Attendance, Fees, Exam, Library, Communication, Security, Integrations. Each category has typed form controls backed by the `school_settings` key-value store.

---

## 19.1 Settings Categories & Complete Key Specification

All stored in `school_settings(school_id, category, key, value, data_type, is_public)`.

### General
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| school_name | string | — | text input |
| tagline | string | — | text input |
| timezone | string | Asia/Kolkata | dropdown (pytz zone list) |
| currency | string | INR | dropdown |
| date_format | string | DD/MM/YYYY | dropdown |
| academic_start_month | integer | 4 | dropdown (Jan-Dec) |
| primary_color | string | #1a56db | color picker |
| school_website | string | — | url input |

### Admission
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| admission_number_prefix | string | STU | text |
| admission_number_start | integer | 1001 | number |
| admission_number_format | string | {PREFIX}-{YEAR}-{SEQ:04d} | text with preview |
| auto_create_student_on_approval | boolean | true | toggle |
| admission_form_fields_json | json | [] | JSON editor |

### Attendance
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| working_days | json | [1,2,3,4,5] | multi-checkbox (Mon-Sun) |
| sessions_enabled | string | full_day | radio (full_day/morning_afternoon) |
| low_attendance_threshold_pct | integer | 75 | number slider |
| absent_notify_delay_minutes | integer | 30 | number |
| notify_parents_sms | boolean | true | toggle |
| notify_parents_whatsapp | boolean | true | toggle |
| mark_attendance_before_minutes | integer | 30 | number |

### Fees
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| fine_enabled | boolean | true | toggle |
| fine_per_day_paise | integer | 0 | money input (display as ₹/day) |
| receipt_number_prefix | string | RCP | text |
| receipt_number_start | integer | 1 | number |
| due_reminder_days_before | integer | 3 | number |
| late_fee_grace_days | integer | 0 | number |
| online_payment_enabled | boolean | false | toggle |
| razorpay_key_id | string | — | text (masked) |
| razorpay_key_secret | string | — | password (masked) |

### Exam
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| default_pass_percentage | integer | 35 | number |
| result_sms_on_publish | boolean | true | toggle |
| show_rank_on_report_card | boolean | true | toggle |
| show_attendance_on_report_card | boolean | true | toggle |
| report_card_footer_text | string | — | textarea |

### Library
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| max_books_student | integer | 3 | number |
| max_books_staff | integer | 5 | number |
| default_loan_days | integer | 14 | number |
| fine_per_day_overdue_paise | integer | 100 | money input |
| overdue_reminder_frequency_days | integer | 3 | number |

### Communication
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| sms_gateway | string | msg91 | dropdown |
| sms_api_key | string | — | password |
| sms_sender_id | string | — | text |
| whatsapp_enabled | boolean | false | toggle |
| whatsapp_api_key | string | — | password |
| whatsapp_phone_number_id | string | — | text |
| email_backend | string | smtp | dropdown (smtp/sendgrid) |
| smtp_host | string | — | text |
| smtp_port | integer | 587 | number |
| smtp_username | string | — | text |
| smtp_password | string | — | password |
| smtp_from_email | string | — | email |
| smtp_use_tls | boolean | true | toggle |
| sendgrid_api_key | string | — | password |
| fcm_server_key | string | — | password |

### Security
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| password_min_length | integer | 8 | number |
| password_require_uppercase | boolean | true | toggle |
| password_require_numbers | boolean | true | toggle |
| session_timeout_minutes | integer | 60 | number |
| max_login_attempts | integer | 5 | number |
| lockout_duration_minutes | integer | 15 | number |
| tfa_enabled | boolean | false | toggle |
| allowed_ip_ranges | json | [] | tag input |

### Integrations
| Key | Type | Default | UI Control |
|-----|------|---------|-----------|
| google_analytics_id | string | — | text |
| facebook_pixel_id | string | — | text |
| gps_tracking_enabled | boolean | false | toggle |
| biometric_device_type | string | — | dropdown |

---

## 19.2 API Endpoints

These were stubbed in Phase 3 — now implement fully:

```
GET /api/v1/schools/settings                    → all settings grouped by category
GET /api/v1/schools/settings?category=fees      → settings for one category
PUT /api/v1/schools/settings                    → bulk update (body: {key: value, ...})
GET /api/v1/schools/settings/public             → public settings (no auth needed for e.g. admission form)
POST /api/v1/schools/settings/test-sms          → send test SMS with current gateway config
POST /api/v1/schools/settings/test-email        → send test email
POST /api/v1/schools/settings/test-whatsapp     → send test WhatsApp
```

---

## 19.3 Service Layer

```python
async def update_settings(school_id: str, settings: dict, updated_by: str) -> List[SchoolSetting]:
    """
    1. Validate each value against data_type (int, bool, json, string)
    2. For boolean: accept "true"/"false" string or bool
    3. For json: validate JSON parseable
    4. For integer: validate int
    5. Bulk upsert
    6. Invalidate any settings cache for school
    7. Log audit: action=UPDATE, module='settings', record_type='SchoolSettings'
    """

async def get_settings_dict(school_id: str, category: Optional[str] = None) -> dict:
    """Return {key: typed_value} — cast based on data_type."""

async def test_sms_gateway(school_id: str, test_phone: str) -> dict:
    """Load SMS settings → send test message → return {success, message}."""
```

---

## 19.4 Settings Cache

```python
# backend/app/core/settings_cache.py
import json
from app.core.redis_client import redis

# Cache key: settings:{school_id}:{category_or_all}
# TTL: 300 seconds (5 min)

async def get_cached_settings(school_id: str) -> Optional[dict]: ...
async def set_settings_cache(school_id: str, settings: dict): ...
async def invalidate_settings_cache(school_id: str): ...
```

---

## 19.5 Frontend Settings Page (`/admin/settings`)

Permission: `settings:view` (read), `settings:update` (write)

**Layout:**
- Left sidebar: settings categories as navigation
- Right: form for selected category

**Component Pattern per Category:**
```tsx
function FeeSettingsForm() {
  const { data } = useQuery(['settings', 'fees'], () => settingsApi.getByCategory('fees'));
  const mutation = useMutation((values: Record<string, string>) => settingsApi.bulkUpdate(values));

  // Use react-hook-form + Zod validation
  // Each field maps to a setting key
  // On submit: send only changed values
}
```

**Special Controls:**
- Working days checkboxes → serialize to JSON array `[1,2,3,4,5]`
- Money inputs: user enters ₹ → multiply by 100 before saving to API
- Color picker for primary_color
- Password fields masked with show/hide toggle
- "Send Test" buttons for SMS/Email/WhatsApp gateways

**School Profile Section** (sub-section within General):
- Logo upload (image preview)
- Principal signature and school seal uploads

### `frontend/src/api/settings.ts`
```typescript
export const settingsApi = {
  getAll: () => api.get('/schools/settings'),
  getByCategory: (category: string) => api.get(`/schools/settings?category=${category}`),
  bulkUpdate: (settings: Record<string, string>) => api.put('/schools/settings', settings),
  getPublic: (schoolSlug: string) => api.get(`/schools/settings/public?slug=${schoolSlug}`),
  testSms: (phone: string) => api.post('/schools/settings/test-sms', { phone }),
  testEmail: (email: string) => api.post('/schools/settings/test-email', { email }),
};
```

---

## 19.6 Tests

```python
async def test_update_settings_type_validation(): ...    # integer key with "abc" → 422
async def test_update_settings_json_validation(): ...    # json key with invalid JSON → 422
async def test_settings_cache_invalidated_on_update(): ...
async def test_public_settings_no_auth_required(): ...
async def test_sensitive_settings_not_in_public(): ...   # api_keys not in public endpoint
async def test_test_sms_gateway(): ...
```

---

## 19.7 Deliverables Checklist

- [ ] All settings categories implemented with correct keys and data types
- [ ] Type-validated bulk update (string/integer/boolean/json)
- [ ] Settings cache in Redis (5-min TTL, invalidated on update)
- [ ] Public settings endpoint (is_public=True only)
- [ ] Test SMS/Email/WhatsApp gateway endpoints
- [ ] Frontend settings page with all categories
- [ ] Password fields masked, money fields show ₹ symbol
- [ ] Working days checkboxes serialized correctly
- [ ] Color picker for primary_color propagates to app theme
- [ ] All previous modules reading settings from cache (not per-request DB query)
