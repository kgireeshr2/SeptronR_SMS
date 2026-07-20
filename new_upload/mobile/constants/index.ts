// ─── API Base URL ──────────────────────────────────────────────────────────────
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
export const API_V1 = `${API_BASE_URL}/api/v1`;

// ─── Token storage keys ────────────────────────────────────────────────────────
export const TOKEN_KEY         = 'sms_access_token';
export const REFRESH_TOKEN_KEY = 'sms_refresh_token';
export const SCHOOL_SLUG_KEY   = 'sms_school_slug';

// ─── Query stale/cache times ──────────────────────────────────────────────────
export const STALE_1MIN  = 60 * 1000;
export const STALE_5MIN  = 5  * 60 * 1000;
export const STALE_15MIN = 15 * 60 * 1000;

// ─── Roles ────────────────────────────────────────────────────────────────────
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN:       'admin',
  TEACHER:     'teacher',
  STAFF:       'staff',
  PARENT:      'parent',
  STUDENT:     'student',
} as const;

export type Role = typeof ROLES[keyof typeof ROLES];

// ─── Attendance status ─────────────────────────────────────────────────────────
export const ATTENDANCE_STATUS = {
  PRESENT: 'present',
  ABSENT:  'absent',
  LATE:    'late',
  EXCUSED: 'excused',
} as const;

// ─── Colors ────────────────────────────────────────────────────────────────────
export const COLORS = {
  primary:    '#1e40af',
  primaryLight:'#3b82f6',
  success:    '#22c55e',
  warning:    '#f59e0b',
  danger:     '#ef4444',
  info:       '#06b6d4',
  gray100:    '#f3f4f6',
  gray200:    '#e5e7eb',
  gray500:    '#6b7280',
  gray700:    '#374151',
  white:      '#ffffff',
  black:      '#000000',
} as const;

// ─── Page sizes ────────────────────────────────────────────────────────────────
export const PAGE_SIZE = 20;
