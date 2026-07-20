import 'package:flutter/material.dart';

/// Mirrors `mobile/constants/index.ts`.

// ─── App branding ───────────────────────────────────────────────────────────
const String kAppName = 'SeptroSchool';

// ─── Storage keys ─────────────────────────────────────────────────────────
const String kTokenKey = 'sms_access_token';
const String kRefreshTokenKey = 'sms_refresh_token';
const String kSchoolSlugKey = 'sms_school_slug';

// ─── Roles ────────────────────────────────────────────────────────────────
class Roles {
  static const superAdmin = 'super_admin';
  static const admin = 'admin';
  static const teacher = 'teacher';
  static const staff = 'staff';
  static const parent = 'parent';
  static const student = 'student';
}

// ─── Attendance status (matches backend StudentAttendanceStatus) ────────────
class AttendanceStatus {
  static const present = 'present';
  static const absent = 'absent';
  static const late = 'late';
  static const leave = 'leave';
  static const halfDay = 'half_day';

  static const all = [present, absent, late, leave, halfDay];
}

// ─── Colors (from mobile/constants) ─────────────────────────────────────────
class AppColors {
  static const primary = Color(0xFF1E40AF);
  static const primaryLight = Color(0xFF3B82F6);
  static const success = Color(0xFF22C55E);
  static const warning = Color(0xFFF59E0B);
  static const danger = Color(0xFFEF4444);
  static const info = Color(0xFF06B6D4);
  static const gray100 = Color(0xFFF3F4F6);
  static const gray200 = Color(0xFFE5E7EB);
  static const gray500 = Color(0xFF6B7280);
  static const gray700 = Color(0xFF374151);
}

// ─── Paging ───────────────────────────────────────────────────────────────
const int kPageSize = 20;

// ─── Cache durations ─────────────────────────────────────────────────────────
const Duration kStale1Min = Duration(minutes: 1);
const Duration kStale5Min = Duration(minutes: 5);
const Duration kStale15Min = Duration(minutes: 15);
