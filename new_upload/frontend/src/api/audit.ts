import api from './axios';

export type AuditAction = 'CREATE' | 'UPDATE' | 'DELETE' | 'VIEW' | 'EXPORT' | 'APPROVE' | 'LOGIN' | 'LOGOUT';

export interface AuditLog {
  id: string;
  school_id: string;
  user_id?: string;
  user_name: string;
  role?: string;
  module: string;
  action: AuditAction;
  record_id?: string;
  record_type?: string;
  old_values?: Record<string, unknown>;
  new_values?: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
}

export interface AuditLogsFilter {
  module?: string;
  action?: AuditAction;
  user_id?: string;
  record_type?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

export const auditApi = {
  list: (params?: AuditLogsFilter) =>
    api.get<AuditLog[]>('/audit-logs', { params }),

  exportCsv: (params?: Omit<AuditLogsFilter, 'limit' | 'offset'>) =>
    api.get('/audit-logs/export', {
      params: { ...params, format: 'csv' },
      responseType: 'blob',
    }),

  getModules: () =>
    api.get<string[]>('/audit-logs/modules'),
};
