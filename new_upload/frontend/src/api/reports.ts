import api from './axios';

export type ReportType =
  | 'student_list'
  | 'attendance_register'
  | 'fee_collection'
  | 'fee_defaulters'
  | 'exam_results'
  | 'staff_list'
  | 'payroll_summary'
  | 'income_expense'
  | 'transport_students'
  | 'library_issues'
  | 'inventory_stock'
  | 'bulk_message_delivery'
  | 'admission_report'
  | 'student_attendance_summary'
  | 'staff_attendance_summary'
  | 'budget_vs_actual';

export interface ReportFilter {
  report_type: ReportType;
  academic_year_id?: string;
  class_id?: string;
  section_id?: string;
  from_date?: string;
  to_date?: string;
  status?: string;
  format?: 'json' | 'csv' | 'pdf' | 'excel';
}

export interface ReportResult {
  report_type: ReportType;
  generated_at: string;
  filters: ReportFilter;
  total_records: number;
  data: Record<string, unknown>[];
  summary?: Record<string, unknown>;
}

export const reportsApi = {
  generate: (params: ReportFilter) =>
    api.get<ReportResult>('/reports/generate', { params }),

  // Download as file (PDF / Excel / CSV)
  download: (params: ReportFilter & { format: 'pdf' | 'excel' | 'csv' }) =>
    api.get('/reports/generate', {
      params,
      responseType: 'blob',
    }),

  // Get available report types (groups)
  getAvailableReports: () =>
    api.get('/reports/available'),

  // Async report generation (stub — not implemented in backend, falls back to sync)
  generateAsync: (params: ReportFilter) =>
    api.post('/reports/generate', params),

  checkAsyncStatus: (_taskId: string) =>
    Promise.resolve({ task_id: _taskId, status: 'complete' }),
};
