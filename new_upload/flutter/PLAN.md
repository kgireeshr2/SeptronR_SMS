# SMS Flutter App — Implementation Plan

A native **Flutter** client (Android + iOS) for the School Management System, serving
all five user roles: **admin/principal, teacher, staff, parent, student** (plus super_admin).

> **Scope decision (locked):** Flutter targets **mobile only** (Android + iOS). The
> existing React app under `frontend/` remains the **web** client. The existing Expo
> React Native app under `mobile/` is **not** touched — this Flutter app is a parallel,
> independent client living under `flutter/`.
>
> **Build note:** Flutter/Dart is *not* installed on the authoring machine. All code is
> written here; compilation, `flutter pub get`, codegen, and device runs happen on a
> machine with the Flutter SDK. Every phase below ends with the exact commands to run there.

---

## 1. Backend contract (ground truth — already verified against the codebase)

These facts are taken from the live backend (`backend/app/api/v1`) and the existing
Expo client (`mobile/services`). The Flutter client must match them exactly.

| Concern | Contract |
|---|---|
| Base URL | `EXPO_PUBLIC_API_URL` value = `http://localhost:8000` (from `mobile/.env.local`). API root = `{BASE}/api/v1`. |
| Response envelope | Many endpoints wrap as `{ "success": true, "data": <T>, "message": ..., "pagination": ... }`. Others return raw arrays/objects. Client must **unwrap** `data` when the envelope shape is present, else pass through. |
| Auth — access token | JWT `access_token` returned by `/auth/login`. Sent as `Authorization: Bearer <token>` on every request. |
| Auth — refresh token | Backend sets an **HttpOnly cookie** `refresh_token` scoped to `/api/v1/auth/refresh`. Mobile clients persist the token and replay it as a `Cookie: refresh_token=<t>` header on `POST /auth/refresh`. Response `{ access_token, expires_in }`. |
| Multi-tenancy | Optional `X-School-Slug: <slug>` header selects the tenant. Stored alongside tokens. |
| Login body | `{ "identifier": <email|username|phone>, "password": ... }`. (`identifier`, **not** `username`.) |
| OTP | `POST /auth/send-otp { phone }`, `POST /auth/verify-otp { phone, otp }` → same login response shape. |
| Current user | `GET /auth/me` → `{ id, school_id, username, email, phone, is_super_admin, avatar_url, permissions: string[] }`. **No explicit role field** — role is *inferred* (see §3). |
| Password | `/auth/forgot-password { email }`, `/auth/reset-password { token, new_password }`, `/auth/change-password { current_password, new_password }`. |
| Logout | `POST /auth/logout` (blacklists tokens). |

### Permissions & role inference (port verbatim from `mobile/hooks/usePermissions.ts`)
`/auth/me` returns a flat `permissions` list (e.g. `attendance:mark`, `students:create`,
`fees:view`). Role is derived:
- `is_super_admin == true` → **super_admin**
- ≥5 perms ending in `:create`/`:manage` → **admin** (principal)
- has any of `attendance:mark`, `homework:create`, `timetable:view` → **teacher**
- has `fees:view` and **not** `students:create` → **parent**
- 1–5 perms → **student**
- else → **admin**

### Feature endpoints confirmed present (subset, for the core slice)
- Attendance: `POST /attendance/mark-bulk`, `GET /attendance/summary`, `GET /attendance/monthly`, `POST /staff-attendance/mark`, `GET /staff-attendance/my`
- Homework: `GET/POST /homework`, `DELETE /homework/{id}`, lesson plans, PTM
- Fees: `GET /fees/collection-summary`, `GET /fees/invoices`, `GET /fees/invoices/{id}/pdf`, `/fees/structures`
- Students: `GET /students`, `POST /students/{id}/photo`, `GET /students/{id}/attendance-summary`
- Staff: `GET /staff`, `POST /staff/{id}/photo`, `GET /staff/{id}/leave-balance`, `GET /payroll`
- Exams: `GET /exams`, `POST /exams/{examId}/marks`, `GET /exams/{examId}/report-card/{student_id}`
- Leaves: `GET/POST /leaves`, `PATCH /leaves/{id}/approve|reject|cancel`
- Announcements/Notifications: `/announcements`, `PATCH /announcements/{id}/read`, `/notifications`, `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all`
- Timetable: `/timetable`
- Full module surface (40+): academic_years, admissions, classes, subjects, departments, payroll, holidays, transport, inventory, accounting, library, calendar, documents, reports, settings, chat, super_admin, etc. — built out in later phases.

---

## 2. Flutter tech stack (chosen as 1:1 analogs of the Expo app)

| Expo app | Flutter equivalent | Why |
|---|---|---|
| Axios + interceptors | **dio** + `Interceptor`s | token inject, refresh-on-401, envelope unwrap |
| TanStack Query (server cache) | **Riverpod** `AsyncNotifier` + `FutureProvider` | async caching, invalidation, loading/error states |
| Zustand (client state) | **Riverpod** `Notifier` providers | auth/session/academic-year state |
| Expo Router (file-based) | **go_router** | declarative routes + redirect guards by auth/role |
| expo-secure-store | **flutter_secure_storage** | encrypted token storage (Keychain/Keystore) |
| zod + react-hook-form | **plain Dart models** (hand-written `fromJson`/`toJson`) + `Form`/`TextFormField` validators | typed models + validation, **no codegen step** |
| NativeWind/Tailwind | **Material 3 ThemeData** (+ shared widgets) | theming with the existing color palette |
| dayjs | **intl** | date formatting |
| expo-notifications (FCM) | **firebase_messaging** (Phase later) | push |

**Color palette** (from `mobile/constants`): primary `#1e40af`, primaryLight `#3b82f6`,
success `#22c55e`, warning `#f59e0b`, danger `#ef4444`, info `#06b6d4`.

### Project layout
```
flutter/
  pubspec.yaml
                            # config via --dart-define=APP_API_URL=... (no .env file)
  analysis_options.yaml
  lib/
    main.dart
    app.dart                # MaterialApp.router + theme
    core/
      config/env.dart       # reads .env
      constants.dart        # roles, storage keys, colors, page size
      network/
        dio_client.dart     # base dio + interceptors (auth, refresh, envelope)
        api_result.dart     # success/error wrapper
        api_exception.dart
      storage/secure_storage.dart
      theme/app_theme.dart
      router/app_router.dart # go_router + auth/role redirect
      router/role_tabs.dart  # per-role bottom-nav config (ports _layout.tsx)
    features/
      auth/      (data/ domain/ presentation/)
      dashboard/
      attendance/
      homework/
      fees/
      announcements/
      ... (later phases)
    shared/
      models/    (user, school, paginated, ...)
      widgets/   (StatCard, Loading, ErrorView, SearchBar, Badge, AppScaffold)
      utils/
  test/
  android/  ios/            # generated by `flutter create`
```

---

## 3. Phased delivery (step-wise — each phase is independently compilable)

Legend: ☐ todo · ☑ done. I will work top-to-bottom, marking items as I go.

### Phase 0 — Scaffold & tooling  ☑
- ☑ `pubspec.yaml` with deps: dio, flutter_riverpod, go_router, flutter_secure_storage, intl, cached_network_image, fl_chart, image_picker, url_launcher. (No codegen, no dotenv — config via `--dart-define`.)
- ☑ `analysis_options.yaml`, `.gitignore` additions.
- ☑ `main.dart` (ProviderScope) and `app.dart` (MaterialApp.router).
- ☑ Note: `android/`+`ios/` folders are produced by `flutter create .` on the SDK machine (Phase 0 run-step), then committed.

### Phase 1 — Core infrastructure  ☑
- ☑ `core/constants.dart` (roles, storage keys, colors, page size, attendance statuses).
- ☑ `core/config/env.dart`, `core/theme/app_theme.dart` (Material 3 from palette).
- ☑ `core/storage/secure_storage.dart` (access token, refresh token, school slug).
- ☑ `core/network/dio_client.dart`:
  - request interceptor → inject `Authorization` + `X-School-Slug`
  - response interceptor → unwrap `{success,data}` envelope
  - error interceptor → on 401, single-flight refresh via `Cookie: refresh_token=…`, queue & retry; on refresh fail → emit logout.
- ☑ `core/network/api_exception.dart`, `api_result.dart`.
- ☑ `shared/models/`: `User`, `School`, `LoginResponse`, `Paginated<T>` (plain Dart fromJson/toJson).

### Phase 2 — Auth & session  ☑
- ☑ `features/auth/data/auth_repository.dart` (login, otp, refresh, me, logout, password flows).
- ☑ `features/auth/domain/role.dart` — port `inferRole` logic exactly.
- ☑ `features/auth/presentation/auth_controller.dart` — Riverpod `AsyncNotifier` holding session (user, permissions, inferred role, isAuthenticated); bootstrap from storage on launch.
- ☑ Screens: `login` (identifier+password+optional school slug), `otp`, `forgot_password`, `change_password`.
- ☑ Permission helper provider (`can('students','create')`, `isAdmin`, `isParent`, …).

### Phase 3 — Routing & role-based shell  ☑
- ☑ `core/router/app_router.dart` — go_router with `redirect` guard (unauth → /login; auth → /app).
- ☑ `core/router/role_tabs.dart` — per-role bottom-nav (ports `mobile/app/(app)/_layout.tsx`):
  - admin: Dashboard · Students · Staff · Fees · More
  - teacher/staff: Dashboard · Attendance · Homework · Timetable · More
  - parent: Home · Fees · Attendance · Notices · More
  - student: Home · Timetable · Homework · Exams · More
- ☑ `AppShell` with `IndexedStack` + `NavigationBar`; "More" screen lists remaining modules filtered by permission.
- ☑ Shared widgets: `Loading`, `ErrorView`, `StatCard`, `SearchBar`, `Badge`, `AppScaffold`.

### Phase 4 — Core feature slice (works for all roles)  ☑
- ☑ **Dashboard** — role-aware stat cards (compose from lightweight queries, mirror `dashboard.service.ts`).
- ☑ **Attendance** — teacher: mark-bulk per class/section; parent/student: monthly summary view.
- ☑ **Homework** — teacher: create/list/delete; student/parent: list + detail.
- ☑ **Fees** — admin: collection summary; parent/student: invoices list + detail + PDF open.
- ☑ **Announcements/Notifications** — list, mark-read, unread badge.

### Phase 5 — Secondary modules  ☑
- ☑ Students directory (search) + profile; Staff directory (search) + profile.
- ☑ Timetable (day-grouped; my + by class/section), Exams (my-results + per-exam results viewing).
- ☑ Leaves (apply / cancel / approve / reject with role-aware tabs), Calendar (month agenda + holidays).
- ☑ Settings/Profile, Change password (done in Phase 3).
- ⏳ Deferred: exam **marks entry** (needs subject+student pickers), report-card PDF.

### Phase 6 — Remaining modules  ◐ (partial)
- ☑ Library (catalog search + my issued books), Transport (my route; admin routes + vehicles).
- ⏳ Pending: Reports, academic years, classes, subjects, admissions, departments,
  payroll, inventory, accounting, documents, super_admin. Surfaced via the "More"
  menu behind permission gates as they land (currently show a "coming soon" placeholder).

### Phase 7 — Platform polish  ◐ (partial)
- ☑ Unread notification badge on the Notices tab; pull-to-refresh across lists.
- ⏳ Requires the SDK machine + external config (cannot be authored/verified here):
  - Push notifications (firebase_messaging) + FCM token registration (`/notifications/fcm-token`)
    — needs `google-services.json` / `GoogleService-Info.plist`.
  - Image upload (student/staff photos via `image_picker` — dep already added).
  - Fee invoice / report-card **PDF open** (add `open_filex` or `printing`; download via dio).
  - App icons/splash (`flutter_launcher_icons`), bundle IDs, Android/iOS signing.

### Phase 8 — QA  ◐ (partial)
- ☑ Unit tests: role inference, permission parsing, envelope unwrap, pagination
  (`test/role_inference_test.dart`, `test/network_test.dart`).
- ⏳ Widget tests (login, dashboard per role) and `flutter analyze` clean — run on the SDK machine.

---

## 4. Commands to run on the Flutter-SDK machine

```bash
cd flutter
flutter create .                 # one-time: generate android/ ios/ around the existing lib/
flutter pub get
flutter analyze                  # no codegen step — models are hand-written
flutter run                      # device/emulator
# release:
flutter build apk --release      # Android
flutter build ipa                # iOS (on macOS)
```

Set the API URL at build time with `--dart-define` (no `.env` file needed):

```bash
flutter run --dart-define=APP_API_URL=http://10.0.2.2:8000     # Android emulator → host
flutter build apk --release --dart-define=APP_API_URL=https://api.yourschool.com
```

The default (when no define is passed) is `http://localhost:8000`, matching
`mobile/.env.local`. For an Android emulator hitting a host-machine backend, use
`http://10.0.2.2:8000`.

---

## 5. Open follow-ups (non-blocking)
- Confirm `send-otp`/`verify-otp` field name on this deployment (`phone` per backend vs
  `identifier` in the Expo service) — handle both, prefer backend's `phone`.
- Firebase config files (`google-services.json`, `GoogleService-Info.plist`) needed before push works.
- iOS signing / Apple Developer account required for `flutter build ipa`.
