# Feature Prompt 31 — Parent Portal PWA

## Round: 4 of 4 — Advanced Features
## Prerequisites: All core modules complete

---

## Objective

Implement a Progressive Web App (PWA) for parents: children dashboard, attendance tracking, fee payments, exam results, homework, notifications with FCM push, and offline support.

---

## 1. Parent Auth & Linking

Parents use the same `users` table with role=PARENT. Linked to students via `student_parents` table (from Prompt 09).

```python
class StudentParent(Base, TimestampMixin):
    __tablename__ = "student_parents"
    student_id: UUID
    parent_user_id: UUID | None   # linked user account
    name: str
    relation: str   # father/mother/guardian
    phone: str
    email: str | None
    is_primary: bool
```

### Parent Login Flow
1. Parent logs in with phone/email → JWT (same as staff login)
2. `GET /parent/children` → lists all students linked to this parent

---

## 2. Backend: Parent API Routes

```
# Parent self-service endpoints (all require auth, role=PARENT)
GET    /parent/children                       → list linked children
GET    /parent/children/{student_id}/dashboard → student mini dashboard
GET    /parent/children/{student_id}/attendance?month=&year= → attendance data
GET    /parent/children/{student_id}/fees     → fee invoices + balance
POST   /parent/fees/{invoice_id}/pay-online  → initiate Razorpay payment
GET    /parent/children/{student_id}/results  → published exam results
GET    /parent/children/{student_id}/homework → pending homework
GET    /parent/children/{student_id}/timetable → today's timetable
GET    /parent/notifications                  → notification history
POST   /parent/notifications/{id}/read       → mark read

# Parent FCM token registration
POST   /parent/fcm-token                     → register device token
```

All endpoints validate that `student_id` is linked to `current_user` (parent).

---

## 3. Frontend: React PWA

### Vite PWA Plugin Setup

```typescript
// vite.config.ts additions
import { VitePWA } from 'vite-plugin-pwa'

plugins: [
  VitePWA({
    registerType: 'autoUpdate',
    workbox: {
      runtimeCaching: [
        { urlPattern: /\/api\/parent\//, handler: 'NetworkFirst',
          options: { cacheName: 'parent-api', expiration: { maxAgeSeconds: 300 } } }
      ]
    },
    manifest: {
      name: 'School Parent Portal',
      short_name: 'SchoolApp',
      theme_color: '#1E40AF',
    }
  })
]
```

### Public Manifest (`frontend/public/manifest.json`)
```json
{
  "name": "School Parent Portal",
  "short_name": "SchoolApp",
  "start_url": "/parent",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1E40AF",
  "icons": [
    {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

### Parent Routes

```typescript
// Separate route group /parent/*
/parent/login          → ParentLogin (phone OTP)
/parent/dashboard      → ParentHome (child selector + summary)
/parent/:childId/attendance → AttendanceView
/parent/:childId/fees  → FeesView (+ pay online)
/parent/:childId/results → ResultsView
/parent/:childId/homework → HomeworkView
/parent/:childId/timetable → TimetableView
```

---

## 4. Parent Home Page (`/parent/dashboard`)

**Child Selector** (tab row if multiple children)

**Summary Cards** (per child):
- Attendance % today + monthly mini calendar
- Fee Due (red badge if outstanding)
- Last Exam Result snapshot
- Pending Homework count

**Quick Links**: View Timetable | Check Results | Pay Fees | Contact School

---

## 5. FCM Push Notifications (Web Push)

```typescript
// frontend/src/utils/fcm.ts
import { getMessaging, getToken } from 'firebase/messaging'

export async function registerFCMToken(userId: string) {
  const messaging = getMessaging()
  const token = await getToken(messaging, { vapidKey: import.meta.env.VITE_FCM_VAPID_KEY })
  await api.post('/parent/fcm-token', { token })
}

// Service Worker: firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/10.x.x/firebase-app-compat.js')
importScripts('https://www.gstatic.com/firebasejs/10.x.x/firebase-messaging-compat.js')
// Handle background messages
```

Backend: `send_push()` in NotificationEngine uses `firebase-admin` to send to all tokens for a user.

---

## 6. Offline Support

`vite-plugin-pwa` workbox caches:
- `/parent/dashboard` as shell (precache)
- API responses: NetworkFirst with 5-min stale fallback
- Offline fallback page: "You're offline. Last sync: X minutes ago."

---

## Verification Checklist

- [ ] Parent can only see data for their linked children (validated server-side)
- [ ] `POST /parent/fcm-token` stores token linked to user_id
- [ ] FCM push sent on absent notification, fee reminder, exam publish
- [ ] PWA manifest produces installable app on mobile
- [ ] Workbox caches parent API responses for 5 minutes offline use
- [ ] Razorpay online payment flow works from Parent Portal
- [ ] `feature_flags.parent_portal` checked before serving parent routes
- [ ] Parent phone OTP login (same flow as staff OTP auth from Prompt 02)
