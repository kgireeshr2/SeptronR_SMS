import { useAuthStore } from '@store/authStore';

export function usePermission() {
  const permissions = useAuthStore((s) => s.permissions);

  const hasPermission = (module: string, action: string): boolean => {
    const isSuperAdmin =
      useAuthStore.getState().currentUser?.is_super_admin ?? false;
    if (isSuperAdmin) return true;
    return permissions.includes(`${module}:${action}`);
  };

  const hasAnyPermission = (checks: Array<[string, string]>): boolean =>
    checks.some(([m, a]) => hasPermission(m, a));

  const hasAllPermissions = (checks: Array<[string, string]>): boolean =>
    checks.every(([m, a]) => hasPermission(m, a));

  return { hasPermission, hasAnyPermission, hasAllPermissions };
}
