import api from './axios';

export interface Payroll {
  id: string;
  school_id: string;
  staff_id: string;
  academic_year_id: string;
  month: number;
  year: number;
  basic_salary: number;
  allowances: {
    hra?: number;
    da?: number;
    ta?: number;
    other?: number;
  };
  deductions: {
    pf?: number;
    esi?: number;
    tds?: number;
    loan?: number;
    other?: number;
  };
  gross_salary: number;
  net_salary: number;
  payment_date?: string;
  payment_method?: 'cash' | 'cheque' | 'online' | 'card' | 'neft' | 'upi';
  is_paid: boolean;
  receipt_url?: string;
  staff_name?: string;
  employee_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PayrollGenerateRequest {
  month: number;
  year: number;
  academic_year_id: string;
  staff_ids?: string[];
}

export interface PayrollUpdate {
  basic_salary?: number;
  allowances?: {
    hra?: number;
    da?: number;
    ta?: number;
    other?: number;
  };
  deductions?: {
    pf?: number;
    esi?: number;
    tds?: number;
    loan?: number;
    other?: number;
  };
  gross_salary?: number;
  net_salary?: number;
  payment_date?: string;
  payment_method?: 'cash' | 'cheque' | 'online' | 'card' | 'neft' | 'upi';
  is_paid?: boolean;
}

export interface PayrollMarkPaidRequest {
  payroll_ids: string[];
  payment_date: string;
  payment_method: 'cash' | 'cheque' | 'online' | 'card' | 'neft' | 'upi';
}

export const payrollApi = {
  // Payroll
  listPayroll: (params?: {
    academic_year_id?: string;
    staff_id?: string;
    month?: number;
    year?: number;
    is_paid?: boolean;
    skip?: number;
    limit?: number;
  }) => api.get<Payroll[]>('/payroll', { params }),

  generatePayroll: (data: PayrollGenerateRequest) =>
    api.post<Payroll[]>('/payroll/generate', data),

  getPayroll: (payrollId: string) =>
    api.get<Payroll>(`/payroll/${payrollId}`),

  updatePayroll: (payrollId: string, data: PayrollUpdate) =>
    api.put<Payroll>(`/payroll/${payrollId}`, data),

  deletePayroll: (payrollId: string) =>
    api.delete(`/payroll/${payrollId}`),

  markPayrollAsPaid: (data: PayrollMarkPaidRequest) =>
    api.patch<{ message: string; count: number }>('/payroll/mark-paid', data),

  downloadPayslip: (payrollId: string) =>
    api.get(`/payroll/${payrollId}/slip`, { responseType: 'blob' }),

  getStaffPayrollHistory: (staffId: string, params?: { skip?: number; limit?: number }) =>
    api.get<Payroll[]>(`/payroll/staff/${staffId}`, { params }),

  getMyPayrollHistory: (params?: { skip?: number; limit?: number }) =>
    api.get<Payroll[]>('/payroll/my/history', { params }),
};
