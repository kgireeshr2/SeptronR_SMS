import '../../../core/constants.dart';
import '../../../shared/models/user.dart';

/// Logical roles. The backend has no explicit role field on `/auth/me` — the
/// role is inferred from `is_super_admin` + the permission list. Ported
/// verbatim from `mobile/hooks/usePermissions.ts` (`inferRole`).
enum AppRole {
  superAdmin,
  admin,
  teacher,
  staff,
  parent,
  student;

  String get wire => switch (this) {
        AppRole.superAdmin => Roles.superAdmin,
        AppRole.admin => Roles.admin,
        AppRole.teacher => Roles.teacher,
        AppRole.staff => Roles.staff,
        AppRole.parent => Roles.parent,
        AppRole.student => Roles.student,
      };

  String get label => switch (this) {
        AppRole.superAdmin => 'Super Admin',
        AppRole.admin => 'Administrator',
        AppRole.teacher => 'Teacher',
        AppRole.staff => 'Staff',
        AppRole.parent => 'Parent',
        AppRole.student => 'Student',
      };
}

AppRole inferRole(User user) {
  final perms = user.permissions;

  if (user.isSuperAdmin) return AppRole.superAdmin;

  // School admin / principal: broad write permissions across many modules.
  final writeCount = perms
      .where((p) => p.endsWith(':create') || p.endsWith(':manage'))
      .length;
  if (writeCount >= 5) return AppRole.admin;

  // Teacher: can mark attendance and/or manage homework.
  const teacherSignals = {'attendance:mark', 'homework:create', 'timetable:view'};
  if (perms.any(teacherSignals.contains)) return AppRole.teacher;

  // Parent: limited, typically fees:view but not student management.
  if (perms.contains('fees:view') && !perms.contains('students:create')) {
    return AppRole.parent;
  }

  // Student: very limited permission set.
  if (perms.isNotEmpty && perms.length < 6) return AppRole.student;

  return AppRole.admin;
}
