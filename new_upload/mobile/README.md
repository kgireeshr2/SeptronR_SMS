# SeptroSchool Mobile App

Production-grade React Native + Expo mobile app for SeptroSchool.  
Targets **Android** (APK / AAB) and **iOS** (IPA) from a single codebase.

---

## Architecture

| Layer | Technology |
|---|---|
| Framework | Expo SDK 52 (managed workflow) |
| Navigation | Expo Router v4 (file-based) |
| Styling | NativeWind v4 (Tailwind CSS for RN) |
| State | Zustand v5 |
| Server State | TanStack Query v5 (with offline cache) |
| Forms | react-hook-form + zod |
| HTTP | Axios (auto token refresh interceptor) |
| Auth storage | expo-secure-store (encrypted keychain/keystore) |
| Push notifications | expo-notifications + FCM |
| Error tracking | Sentry |
| Build & deploy | Expo EAS Build |

---

## Folder Structure

```
mobile/
  app/
    _layout.tsx              ← Root layout (providers, Sentry, auth event listener)
    +not-found.tsx           ← 404 screen
    (auth)/                  ← Unauthenticated screens
      _layout.tsx
      login.tsx
      otp.tsx
      forgot-password.tsx
    (app)/                   ← Protected screens (tab navigator + role-based tabs)
      _layout.tsx
      dashboard/index.tsx
      students/index.tsx
      students/[id].tsx
      staff/index.tsx
      staff/[id].tsx
      attendance/index.tsx
      fees/index.tsx
      fees/[id].tsx
      exams/index.tsx
      homework/index.tsx
      timetable/index.tsx
      leaves/index.tsx
      announcements/index.tsx
      transport/index.tsx
      library/index.tsx
      calendar/index.tsx
      notifications/index.tsx
      settings/index.tsx
      reports/index.tsx
      more/index.tsx
  components/               ← Shared UI components
  hooks/                    ← usePermissions, useNotifications
  services/                 ← axios api.ts + per-module service files
  stores/                   ← authStore, academicYearStore (Zustand)
  types/index.ts            ← All TypeScript interfaces
  constants/index.ts        ← API URL, token keys, colors, roles
  assets/                   ← icon.png, splash.png, adaptive-icon.png
  app.json                  ← Expo config
  eas.json                  ← EAS Build profiles
  tailwind.config.js        ← NativeWind config
  babel.config.js
  metro.config.js
```

---

## Prerequisites

- Node.js ≥ 18
- npm ≥ 10 or yarn
- Expo CLI: `npm install -g expo-cli` (optional, npx works too)
- EAS CLI: `npm install -g eas-cli` (for builds)
- Expo Go app on your phone or an Android emulator / iOS simulator

---

## Environment Setup

Copy `.env.example` to `.env.local` and fill in:

```bash
cp .env.local.example .env.local
```

```env
EXPO_PUBLIC_API_URL=https://api.yourschool.com    # or http://YOUR_LAN_IP:8000 for local dev
EXPO_PUBLIC_APP_ENV=development
EXPO_PUBLIC_SENTRY_DSN=https://...@sentry.io/...  # optional
```

---

## Local Development

```bash
cd mobile

# Install dependencies
npm install --legacy-peer-deps

# Start metro bundler
npx expo start

# Scan QR code with Expo Go (Android/iOS)
# OR press 'a' for Android emulator, 'i' for iOS simulator
```

### Connecting to local backend

Make sure the FastAPI backend is running (`docker-compose up` or `uvicorn`).  
Set `EXPO_PUBLIC_API_URL` to your machine's LAN IP so the phone can reach it:

```env
EXPO_PUBLIC_API_URL=http://192.168.1.100:8000
```

---

## Building

### Prerequisites for building

1. Create an EAS account: `eas login`
2. Link project: `eas init` (updates `app.json#extra.eas.projectId`)
3. For Android production: add `google-services.json` (Firebase) to `mobile/`
4. For iOS: requires Apple Developer account

### Development build (with dev client)

```bash
# Android APK (debug)
eas build --platform android --profile development

# iOS (simulator)
eas build --platform ios --profile development
```

### Preview build (internal distribution)

```bash
# Android APK — share directly with testers
eas build --platform android --profile preview

# Download the APK and install on Android device
```

### Production build

```bash
# Android AAB — for Google Play Store
eas build --platform android --profile production

# iOS IPA — for Apple App Store
eas build --platform ios --profile production
```

### Submit to stores

```bash
# Android
eas submit --platform android --profile production

# iOS
eas submit --platform ios --profile production
```

---

## Role-Based Navigation

The tab bar adapts based on the logged-in user's role:

| Role | Tabs |
|---|---|
| Admin / Super Admin | Dashboard, Students, Staff, Fees, More |
| Teacher / Staff | Dashboard, Attendance, Homework, Timetable, More |
| Parent | Home, Fees, Attendance, Notices, More |
| Student | Home, Timetable, Homework, Exams, More |

The "More" tab is a full grid of all secondary modules.

---

## Offline Support

- TanStack Query caches all GET responses to AsyncStorage
- Stale-while-revalidate: app shows cached data immediately, fetches fresh in background
- Network status banner via `@react-native-community/netinfo`

---

## Push Notifications

The backend already has FCM tasks wired (Celery). The mobile app:

1. Requests notification permissions on first launch (after login)
2. Gets the Expo Push Token
3. Registers it with the backend via `POST /api/v1/settings/fcm-token`
4. Handles foreground notifications (shows in-app toast)
5. Deep-links to the relevant screen when user taps a notification

---

## Authentication Flow

```
Login screen → POST /api/v1/auth/login
  → access token + refresh token stored in expo-secure-store
  → user + permissions stored in Zustand (persisted to AsyncStorage)

API calls → axios interceptor injects Bearer token
401 response → interceptor calls POST /api/v1/auth/refresh
  → swaps access token silently, retries original request
  → if refresh also fails → clears tokens → redirects to login
```

---

## Assets Required

Place these files in `mobile/assets/`:
- `icon.png` — 1024×1024 PNG app icon
- `adaptive-icon.png` — 1024×1024 PNG for Android adaptive icon
- `splash.png` — 1284×2778 PNG splash screen
- `favicon.png` — 48×48 PNG for web
- `notification-icon.png` — 96×96 PNG (white, transparent bg) for Android notifications

---

## Scripts

| Command | Description |
|---|---|
| `npm start` | Start Expo Metro bundler |
| `npm run android` | Open on Android emulator |
| `npm run ios` | Open on iOS simulator |
| `npm test` | Run Jest tests |
| `npm run lint` | Run ESLint |
| `npm run build:android:preview` | EAS build Android APK (preview) |
| `npm run build:android:prod` | EAS build Android AAB (production) |
| `npm run build:ios:preview` | EAS build iOS (preview) |
| `npm run build:ios:prod` | EAS build iOS IPA (production) |
