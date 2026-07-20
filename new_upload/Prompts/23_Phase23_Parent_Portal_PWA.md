# PHASE 23 — PARENT PORTAL + PWA

## Pre-Requisite
Phases 1–22 complete. Parent user accounts created during student registration. Online payment settings configured.

## Objective
Mobile-first PWA (Progressive Web App) for parents. Offline support, add-to-homescreen, real-time push notifications via FCM and WebSocket. Multi-child support. All parent-facing views fully responsive.

---

## 23.1 PWA Configuration

### Vite PWA Plugin Setup (`vite.config.ts` addition)

```typescript
import { VitePWA } from 'vite-plugin-pwa';

// In defineConfig plugins array:
VitePWA({
  registerType: 'autoUpdate',
  includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'mask-icon.svg'],
  manifest: {
    name: 'School Management Portal',
    short_name: 'SchoolPortal',
    description: 'Parent portal for school management',
    theme_color: '#1a56db',
    background_color: '#ffffff',
    display: 'standalone',
    orientation: 'portrait',
    icons: [
      { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
      { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
    ],
    start_url: '/parent/dashboard',
    scope: '/',
  },
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/.*\/api\/v1\/dashboard\/parent/,
        handler: 'NetworkFirst',
        options: { cacheName: 'api-cache', expiration: { maxAgeSeconds: 300 } },
      },
    ],
  },
})
```

### Install package:
```
npm install vite-plugin-pwa workbox-window
```

---

## 23.2 Parent Portal Routes (`/parent/*`)

```tsx
// frontend/src/routes/parentRoutes.tsx
const ParentLayout = React.lazy(() => import('../layouts/ParentLayout'));
const ParentDashboard = React.lazy(() => import('../pages/parent/Dashboard'));
const ParentAttendance = React.lazy(() => import('../pages/parent/Attendance'));
const ParentFees = React.lazy(() => import('../pages/parent/Fees'));
const ParentResults = React.lazy(() => import('../pages/parent/Results'));
const ParentHomework = React.lazy(() => import('../pages/parent/Homework'));
const ParentLibrary = React.lazy(() => import('../pages/parent/Library'));
const ParentTransport = React.lazy(() => import('../pages/parent/Transport'));
const ParentNotifications = React.lazy(() => import('../pages/parent/Notifications'));
const ParentProfile = React.lazy(() => import('../pages/parent/Profile'));
```

Route guard: user must have role `Parent` or `Student` to access `/parent/*`.

---

## 23.3 Parent Layout (`frontend/src/layouts/ParentLayout.tsx`)

Mobile-first bottom navigation bar (like a native app):

```
[ Dashboard ] [ Fees ] [ Attendance ] [ Results ] [ More ]
```

- Top header: school logo | child name + class | notification bell (with unread count)
- Child selector: if parent has multiple children, show horizontal chip bar at top

```tsx
function ParentLayout() {
  const { children } = useParentChildren();   // fetch linked students
  const [selectedChild, setSelectedChild] = useParentStore(s => [s.selectedChild, s.setSelectedChild]);

  return (
    <div className="min-h-screen pb-16">  {/* pb-16 = space for bottom nav */}
      <ParentTopBar />
      {children.length > 1 && <ChildSelectorBar />}
      <main className="p-4">
        <Outlet />
      </main>
      <BottomNavBar />
    </div>
  );
}
```

---

## 23.4 Parent State Management (`frontend/src/stores/parentStore.ts`)

```typescript
interface ParentStore {
  selectedChildId: string | null;
  setSelectedChildId: (id: string) => void;
  selectedAcademicYearId: string | null;
}

export const useParentStore = create<ParentStore>()(
  persist(
    (set) => ({
      selectedChildId: null,
      setSelectedChildId: (id) => set({ selectedChildId: id }),
      selectedAcademicYearId: null,
    }),
    { name: 'parent-store' }
  )
);
```

---

## 23.5 Parent Dashboard Page

```tsx
// Fetches from GET /api/v1/dashboard/parent?year_id=...

- Child cards (if multiple, show all cards, click to switch)
- Today's attendance status card (big green/red indicator)
- Fee balance card with "Pay Now" button
- Upcoming exam in next 7 days
- Pending homework (count badge)
- Upcoming PTM slot if booked
- Latest notification (last 1)
- Quick links: [Mark Absent Request] [Download TC] [Contact School]
```

---

## 23.6 Attendance Page (`/parent/attendance`)

```tsx
// Provides calendar view of child's attendance

- Month/year picker
- Calendar grid: each day colored (present = green, absent = red, holiday = grey, weekend = light grey)
- Summary counts: Present / Absent / Late / Total Days
- Click day → detail (morning/afternoon if sessions enabled)
- Bottom: monthly attendance % as circular progress

API: GET /api/v1/attendance?student_id=&month=&year=&year_id=
```

---

## 23.7 Fees Page (`/parent/fees`)

```tsx
// Shows all fee dues + payment history

Outstanding Section:
- List of unpaid/partial fees (category, amount, due date, days overdue in red if > 0)
- Each item has "Pay Online" button (if online_payment_enabled setting = true)

Payment History Section:
- Table: Date | Receipt No. | Category | Amount | Mode | [Download Receipt]

Online Payment Flow:
1. Parent clicks "Pay Online" → opens PaymentModal
2. PaymentModal: shows breakdown (principal + fine), total, Razorpay Checkout button
3. On Razorpay success: call POST /api/v1/fees/payments (Razorpay mode)
4. Show receipt PDF download link

API:
  GET /api/v1/students/{id}/fees/outstanding
  GET /api/v1/fees/payments?student_id=
  POST /api/v1/online-payments/initiate
  POST /api/v1/online-payments/verify
```

---

## 23.8 Results Page (`/parent/results`)

```tsx
// Shows exam results

- Exam type filter (mid-term, annual, etc.)
- List of exams with date
- Select exam → show subject-wise marks table:
  | Subject | Max Marks | Obtained | Grade | Remark |
- Overall percentage and rank (if show_rank_on_report_card = true)
- Download Report Card PDF button

API: GET /api/v1/exams/{exam_id}/students/{student_id}/marks
     GET /api/v1/exams/{exam_id}/report-card/{student_id}/pdf
```

---

## 23.9 Homework Page (`/parent/homework`)

```tsx
// Shows homework assigned to child's class

- Tabs: Pending | Submitted | All
- Each card: Subject | Title | Due Date | Teacher Name | [View Details]
- Detail drawer: description, attached files, submission status
- If student account linked: show submission form (not for parent view — parent view only)

API: GET /api/v1/homework?section_id=&status=
```

---

## 23.10 Notifications Page (`/parent/notifications`)

```tsx
// All notifications for this parent

- List with: icon (type) | title | body | time ago
- Toggle unread filter
- Click → mark as read
- Clear all button

Real-time WebSocket:
  - Connect to ws://HOST/ws/notifications (with JWT)
  - New notification → prepend to list + update bell count

API: GET  /api/v1/notifications
     PUT  /api/v1/notifications/{id}/read
     PUT  /api/v1/notifications/read-all
```

---

## 23.11 FCM Push Notifications

```python
# backend/app/core/fcm.py

import httpx

FCM_URL = "https://fcm.googleapis.com/fcm/send"

async def send_push_notification(fcm_token: str, title: str, body: str, data: dict = {}):
    """
    POST to FCM API with Authorization: key={FCM_SERVER_KEY}
    payload: { to: fcm_token, notification: {title, body}, data: {...} }
    """
```

**FCM Token Registration:**
```typescript
// frontend/src/hooks/useFCM.ts
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

export function useFCMSetup() {
  useEffect(() => {
    // 1. Request notification permission
    // 2. Get FCM token
    // 3. POST /api/v1/users/fcm-token to save token
    // 4. Listen for foreground messages → show toast
  }, []);
}
```

Backend endpoint:
```
POST /api/v1/users/fcm-token    body: { token: string }
```

`users` table `fcm_token VARCHAR(512)` column (add in migration).

---

## 23.12 Offline Support

Workbox service worker caches:
- Static assets (js, css, html, fonts, images) — CacheFirst
- API routes — NetworkFirst with 5-min cache fallback
- Parent dashboard data — NetworkFirst with 5-min fallback
- Attendance calendar — NetworkFirst with 10-min fallback

Offline indicator component:
```tsx
function OfflineBanner() {
  const [offline, setOffline] = useState(!navigator.onLine);
  useEffect(() => {
    window.addEventListener('online', () => setOffline(false));
    window.addEventListener('offline', () => setOffline(true));
  }, []);
  return offline ? <div className="bg-amber-500 text-center py-1 text-sm">You are offline. Showing cached data.</div> : null;
}
```

---

## 23.13 Additional Backend Endpoints for Parent Portal

```
GET /api/v1/students/{id}/attendance/summary?month=&year=
    → { present, absent, late, total_working_days, pct, day_wise: [{date, status},...] }

GET /api/v1/students/{id}/fees/outstanding
    → list of fee_invoices where status in (unpaid, partial)

GET /api/v1/students/{id}/library/current-issues
    → book_issues WHERE returned_at IS NULL

GET /api/v1/students/{id}/transport
    → student_transport with route and stop details

GET /api/v1/ptm/parent-slots?ptm_id=
    → parent's booked slots for a PTM event
```

---

## 23.14 Tests

```python
async def test_parent_sees_only_own_children(): ...
async def test_parent_cannot_access_other_student_fees(): ...
async def test_fcm_token_saved_per_user(): ...
async def test_parent_attendance_summary_correct(): ...

# Frontend: Vitest (unit tests)
# test('ChildSelectorBar shows correct children', () => { ... })
# test('AttendanceCalendar colors absent days red', () => { ... })
```

---

## 23.15 Deliverables Checklist

- [ ] vite-plugin-pwa installed and configured with workbox
- [ ] Web app manifest with icons (192x192 and 512x512 assets)
- [ ] Service worker with NetworkFirst caching for API routes
- [ ] Offline banner component
- [ ] Bottom navigation layout for mobile
- [ ] Child selector with persistent selection in Zustand
- [ ] Parent dashboard with all summary cards
- [ ] Attendance calendar with color-coded days and monthly summary
- [ ] Fees page with outstanding and payment history
- [ ] Razorpay online payment flow in parent portal
- [ ] Results page with subject-wise marks and report card PDF download
- [ ] Homework page showing child's class assignments
- [ ] Notifications page with real-time WebSocket updates
- [ ] FCM token registration endpoint and hook
- [ ] Push notification sending for all parent-relevant events
- [ ] All parent API endpoints returning only authorized child data
