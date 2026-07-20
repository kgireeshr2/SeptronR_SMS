# SeptroSchool Flutter App (Android + iOS)

Native Flutter client for SeptroSchool, serving all roles —
**admin/principal, teacher, staff, parent, student** (and super_admin). The
existing `frontend/` React app remains the web client; this app is mobile-only.

> Full design & phase breakdown: [PLAN.md](PLAN.md).

## Architecture

| Concern | Choice |
|---|---|
| State | Riverpod (plain, no codegen) |
| Routing | go_router with auth/role redirect guard |
| HTTP | dio + interceptors (auth header, `{success,data}` envelope unwrap, 401 silent refresh) |
| Auth storage | flutter_secure_storage (Keychain / encrypted Keystore) |
| Models | hand-written `fromJson`/`toJson` (no build_runner) |
| Config | `--dart-define` (no `.env` asset) |

```
lib/
  core/          constants, config, theme, storage, network, router, providers
  shared/        models, widgets, utils
  features/
    auth/        login, otp, forgot/change password, role inference, session
    shell/       AppShell (role tabs), splash
    dashboard/   role-aware home (/dashboard/{role})
    attendance/  teacher mark-bulk; parent/student info
    homework/    teacher create/delete; all roles list/detail
    fees/        admin summary + invoices; parent/student own invoices
    announcements/ announcements + notifications
    academic/    academic years + classes/sections (shared)
    students/    student directory (shared)
    more/ settings/
```

## Backend contract (must match the FastAPI backend)
- API root: `{APP_API_URL}/api/v1`.
- Login: `POST /auth/login { identifier, password }` → `{ access_token, user, school }`.
  Refresh token arrives as a `Set-Cookie` header and is replayed as
  `Cookie: refresh_token=…` on `POST /auth/refresh`.
- Optional multi-tenant header `X-School-Slug`.
- Role is **inferred** from `is_super_admin` + the `permissions` list
  (see `features/auth/domain/app_role.dart`), mirroring the React/Expo clients.

## Build & run (on a machine with the Flutter SDK)

```bash
cd flutter
flutter create .          # one-time: generate android/ and ios/ around lib/
flutter pub get
flutter analyze

# Run (Android emulator → host backend):
flutter run --dart-define=APP_API_URL=http://10.0.2.2:8000

# Release:
flutter build apk  --release --dart-define=APP_API_URL=https://api.yourschool.com
flutter build ipa            --dart-define=APP_API_URL=https://api.yourschool.com   # macOS only
```

Default `APP_API_URL` (no define) is `http://localhost:8000`.

## App name (SeptroSchool)
The in-app display name (title, splash, login) comes from `kAppName` in
[lib/core/constants.dart](lib/core/constants.dart) and is already set to
**SeptroSchool**. After running `flutter create .`, set the OS-level launcher
label too:
- **Android** — `android/app/src/main/AndroidManifest.xml`: `android:label="SeptroSchool"`.
- **iOS** — `ios/Runner/Info.plist`: set `CFBundleDisplayName` and `CFBundleName` to `SeptroSchool`.

## Status
All five roles supported. Endpoints were **reconciled against the real FastAPI
backend** (earlier code had been ported from the Expo client and used several
routes that don't exist here — attendance, timetable, leaves, fees, exams,
transport, notifications). Self-service data is resolved via the parent
dashboard's `children[]` and an active-child switcher.

**Implemented**
- Auth/session, role-based shell + tabs, dashboards (role-specific endpoints).
- Parent/Student: child switcher, monthly attendance summary, fee statement,
  report-card PDF, homework submission, personal expenses, PTM booking.
- Teacher: section attendance marking, exam **marks entry**, homework **grading**,
  post announcement, create calendar event, leave balances.
- Admin (light): collection summary, **defaulters**, **reports viewer**, leave approvals.
- Directories (students/staff), timetable, library, transport.
- Push notifications (FCM), PDF open (receipts/report cards), skeleton loaders,
  unread badges, pull-to-refresh, role-aware empty states.

**Student self-service** is enabled by a backend endpoint `GET /students/me`
(added in `backend/app/api/v1/endpoints/student_self.py`) which resolves the
logged-in student's own record + current class/section from `student_enrollments`.
The app calls it via `studentSelfProvider`, so `currentStudentIdProvider` now
returns a real id for students — attendance, fees statement, report card,
personal expenses and timetable all work. (Two backend reads were also relaxed
to support this: the fee-statement endpoint now accepts `fees:view` and defaults
the academic year; the report-card PDF endpoint defaults the year — see below.)

**Known backend constraints (graceful-degrade in UI)**
- A student with no linked `students.user_id` (or no current enrollment) sees an
  informative empty state.
- Fee **collection recording** and deep back-office config (inventory, accounting,
  payroll runs, website builder, roles) intentionally stay on the web app.

## Push notifications setup (required before push works)
1. Create a Firebase project; add Android & iOS apps.
2. Place `android/app/google-services.json` and
   `ios/Runner/GoogleService-Info.plist` (and configure the Android Gradle
   google-services plugin; for iOS add an APNs key in Firebase).
3. The app calls `Firebase.initializeApp()` guarded — it builds and runs without
   these files; push just stays disabled until they're added.
   Token is registered at login via `POST /devices/register`.

Run tests: `flutter test`. Analyze + run on the SDK machine (`flutter analyze`).

> The `android/` and `ios/` platform folders are intentionally not committed yet —
> run `flutter create .` once on the SDK machine to generate them around `lib/`.
