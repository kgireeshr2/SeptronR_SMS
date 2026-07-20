import { useAuthStore } from '@/stores/authStore';

/**
 * Derive a logical role from the user's flags and permissions.
 * The backend has no explicit role field on /auth/me — role is inferred.
 */
function inferRole(permissionSet: string[], isSuperAdmin: boolean): string {
  if (isSuperAdmin) return 'super_admin';
  // School admin / principal: broad write permissions across multiple modules
  if (
    permissionSet.filter(p => p.endsWith(':create') || p.endsWith(':manage')).length >= 5
  ) return 'admin';
  // Teacher: can mark attendance and/or manage homework
  if (permissionSet.some((p) => ['attendance:mark', 'homework:create', 'timetable:view'].includes(p))) return 'teacher';
  // Parent: limited, typically fees:view + a few others
  if (permissionSet.includes('fees:view') && !permissionSet.includes('students:create')) return 'parent';
  // Student: very limited
  if (permissionSet.length > 0 && permissionSet.length < 6) return 'student';
  return 'admin';
}

/**
 * Returns helpers for RBAC checks.
 * Usage:
 *   const { can, isAdmin, isTeacher } = usePermissions();
 *   if (can('students', 'create')) { ... }
 */
export function usePermissions() {
  const { hasPermission, hasRole, user, permissionSet } = useAuthStore();

  const role = user ? inferRole(permissionSet, user.is_super_admin) : null;
  const isSuperAdmin = user?.is_super_admin ?? false;
  const isAdmin   = isSuperAdmin || role === 'admin';
  const isTeacher = role === 'teacher';
  const isStaff   = role === 'teacher' || role === 'admin';
  const isParent  = role === 'parent';
  const isStudent = role === 'student';

  return {
    can: hasPermission,
    isRole: hasRole,
    isAdmin,
    isSuperAdmin,
    isTeacher,
    isStaff,
    isParent,
    isStudent,
    role,
  };
}
