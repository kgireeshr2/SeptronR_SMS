# SeptroSchool E2E UI Automation Tests

Playwright-based UI automation for SeptroSchool.  
Tests run in **Chrome (headed)** so you can watch them execute in the browser.

---

## Prerequisites

- Node.js installed
- Frontend running at `http://localhost:5173`
- Backend running at `http://localhost:8000`

### Start the backend (if not already running)
```powershell
cd backend
.venv312\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
```

### Start the frontend (if not already running)
```powershell
cd frontend
npm run dev
```

---

## Running the Tests

Open PowerShell and navigate to the `e2e` folder:

```powershell
cd e2e
```

### Run ALL tests (Chrome, headed — you'll see the browser)
```powershell
node node_modules/@playwright/test/cli.js test --headed
```

### Run a specific test file
```powershell
node node_modules/@playwright/test/cli.js test tests/01-auth.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/02-superadmin.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/03-academic.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/04-students.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/05-staff.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/06-fees.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/07-attendance.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/08-exams.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/09-transport.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/10-library.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/11-communication.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/12-reports.spec.ts --headed
node node_modules/@playwright/test/cli.js test tests/13-settings-roles.spec.ts --headed
```

### Run with slow motion (500ms delay — easier to watch)
The config already has `slowMo: 500` so you can see each action.

### Debug mode (step-through with Playwright Inspector)
```powershell
node node_modules/@playwright/test/cli.js test tests/01-auth.spec.ts --debug
```

### View HTML test report after run
```powershell
node node_modules/@playwright/test/cli.js show-report
```

---

## Test Accounts

| Role | Username | Password | Notes |
|---|---|---|---|
| Super Admin | `superadmin@sms.com` | `SuperAdmin@123` | Access to all schools |
| School Admin | `admin@sunrise.edu` | `Sunrise@123` | Sunrise Public School |

---

## Test Files

| File | Description |
|---|---|
| `01-auth.spec.ts` | Login, logout, validation, redirect |
| `02-superadmin.spec.ts` | Super admin: schools list, toggle, create school, plans |
| `03-academic.spec.ts` | Academic years, classes, subjects, timetable |
| `04-students.spec.ts` | Student list, search, detail, create |
| `05-staff.spec.ts` | Staff list, add staff, departments |
| `06-fees.spec.ts` | Fee structure, collect fees, pending dues |
| `07-attendance.spec.ts` | Mark attendance, reports |
| `08-exams.spec.ts` | Create exam, enter marks, results |
| `09-transport.spec.ts` | Vehicles, routes |
| `10-library.spec.ts` | Books, search, issue/return |
| `11-communication.spec.ts` | Announcements, homework, calendar, PTM |
| `12-reports.spec.ts` | Reports, dashboard, export |
| `13-settings-roles.spec.ts` | Settings, roles/permissions, audit logs, inventory, accounting |

---

## Screenshots

Screenshots are saved to `e2e/screenshots/` after each test step.  
On test failure, screenshots + videos are saved to `e2e/test-results/`.

---

## Notes

- Tests use `slowMo: 500ms` so actions are visible
- Tests run **sequentially** (1 worker) to avoid conflicting DB changes
- Tests gracefully skip if a UI element is not found (using `test.skip()`)
- The `screenshots/` folder is auto-created — check it after test run for visual proof
