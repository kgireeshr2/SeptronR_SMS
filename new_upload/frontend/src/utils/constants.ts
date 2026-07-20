export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  SCHOOL_ADMIN: 'school_admin',
  PRINCIPAL: 'principal',
  VICE_PRINCIPAL: 'vice_principal',
  TEACHER: 'teacher',
  CLASS_TEACHER: 'class_teacher',
  ACCOUNTANT: 'accountant',
  LIBRARIAN: 'librarian',
  TRANSPORT_MANAGER: 'transport_manager',
  INVENTORY_MANAGER: 'inventory_manager',
  RECEPTIONIST: 'receptionist',
  PARENT: 'parent',
  STUDENT: 'student',
} as const;

export const MODULES = [
  'dashboard', 'schools', 'users', 'roles', 'academic_years', 'admissions',
  'classes', 'subjects', 'timetable', 'staff', 'leaves', 'payroll', 'students',
  'attendance', 'fees', 'exams', 'library', 'transport', 'inventory',
  'accounting', 'communication', 'calendar', 'homework', 'ptm',
  'reports', 'audit_logs', 'settings',
] as const;

export const ACTIONS = ['view', 'create', 'update', 'delete', 'export', 'approve', 'manage'] as const;

export const GENDER_OPTIONS = ['Male', 'Female', 'Other'] as const;

export const BLOOD_GROUP_OPTIONS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const;

export const PAGE_SIZES = [10, 20, 50, 100] as const;

export const DATE_FORMAT = 'dd/MM/yyyy';
export const DATETIME_FORMAT = 'dd/MM/yyyy HH:mm';
