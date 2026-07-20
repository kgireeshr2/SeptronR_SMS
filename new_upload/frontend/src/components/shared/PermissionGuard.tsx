import React from 'react';
import { usePermission } from '@hooks/usePermission';

interface Props {
  module: string;
  action: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const PermissionGuard: React.FC<Props> = ({
  module,
  action,
  children,
  fallback = null,
}) => {
  const { hasPermission } = usePermission();
  return hasPermission(module, action) ? <>{children}</> : <>{fallback}</>;
};
