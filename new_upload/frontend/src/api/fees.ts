import api from './axios';

export type FeeFrequency = 'monthly' | 'quarterly' | 'annual' | 'one_time' | 'semi_annual';
export type InvoiceStatus = 'unpaid' | 'partial' | 'paid' | 'overdue' | 'waived' | 'cancelled';
export type PaymentMethod = 'cash' | 'cheque' | 'online' | 'card' | 'neft' | 'upi';

export interface FeeCategory {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface FeeStructure {
  id: string;
  academic_year_id: string;
  class_id: string;
  fee_category_id: string;
  fee_category_name?: string;
  amount: number;
  frequency: FeeFrequency;
  due_day?: number;
  is_active: boolean;
}

export interface FeeDiscount {
  id: string;
  name: string;
  type: 'percentage' | 'fixed';
  value: number;
  applicable_to: 'student' | 'category' | 'class';
  is_active: boolean;
}

export interface FeeInvoice {
  id: string;
  student_id: string;
  student_name?: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  status: InvoiceStatus;
  total_amount: number;
  paid_amount: number;
  balance_amount: number;
}

export interface FeePayment {
  id: string;
  invoice_id: string;
  invoice_number?: string;
  student_id?: string;
  student_name?: string;
  amount: number;
  payment_date: string;
  payment_method: PaymentMethod;
  receipt_number: string;
}

export const feesApi = {
  listCategories: () => api.get('/fees/categories'),
  createCategory: (payload: { name: string; description?: string; is_active?: boolean }) =>
    api.post('/fees/categories', payload),
  updateCategory: (id: string, payload: Partial<{ name: string; description?: string; is_active: boolean }>) =>
    api.put(`/fees/categories/${id}`, payload),
  deleteCategory: (id: string) => api.delete(`/fees/categories/${id}`),

  listStructures: (params?: { academic_year_id?: string; class_id?: string }) =>
    api.get('/fees/structures', { params }),
  upsertStructures: (payload: {
    class_id: string;
    academic_year_id: string;
    items: Array<{ fee_category_id: string; amount: number; frequency: FeeFrequency; due_day?: number; is_active?: boolean }>;
  }) => api.post('/fees/structures', payload),

  listDiscounts: () => api.get('/fees/discounts'),
  createDiscount: (payload: {
    name: string;
    type: 'percentage' | 'fixed';
    value: number;
    applicable_to?: 'student' | 'category' | 'class';
    is_active?: boolean;
  }) => api.post('/fees/discounts', payload),

  assignFees: (payload: { academic_year_id: string; class_id?: string; discount_map?: Record<string, string> }) =>
    api.post('/fees/assign', payload),

  generateInvoices: (payload: { academic_year_id: string; month: number; year: number; class_id?: string; student_id?: string }) =>
    api.post('/fees/invoices/generate', payload),
  listInvoices: (params?: {
    academic_year_id?: string;
    student_id?: string;
    section_id?: string;
    status?: InvoiceStatus;
    month?: number;
    year?: number;
  }) => api.get('/fees/invoices', { params }),

  collectPayment: (payload: {
    invoice_id: string;
    amount: number;
    payment_date: string;
    payment_method: PaymentMethod;
    transaction_id?: string;
    remarks?: string;
  }) => api.post('/fees/payments', payload),
  listPayments: (params?: { from_date?: string; to_date?: string; invoice_id?: string }) =>
    api.get('/fees/payments', { params }),

  getDefaulters: (academic_year_id: string, as_of_date?: string) =>
    api.get('/fees/reports/defaulters', { params: { academic_year_id, as_of_date } }),
  getDailyCollection: (day?: string) => api.get('/fees/reports/daily-collection', { params: { day } }),
  getMonthlyCollection: (month: number, year: number) =>
    api.get('/fees/reports/monthly-collection', { params: { month, year } }),

  reversePayment: (paymentId: string, reason: string) =>
    api.post(`/fees/payments/${paymentId}/reverse`, { reason }),

  getStudentDiscounts: (studentId: string, academic_year_id?: string) =>
    api.get(`/fees/students/${studentId}/discounts`, { params: { academic_year_id } }),
  assignStudentDiscount: (studentId: string, payload: { discount_id: string; academic_year_id: string; remarks?: string }) =>
    api.post(`/fees/students/${studentId}/discounts`, payload),
  removeStudentDiscount: (studentId: string, assignmentId: string) =>
    api.delete(`/fees/students/${studentId}/discounts/${assignmentId}`),

  getFeeClearance: (studentId: string, academic_year_id: string) =>
    api.get(`/fees/students/${studentId}/clearance`, { params: { academic_year_id } }),

  rolloverStructures: (from_year_id: string, to_year_id: string) =>
    api.post('/fees/structures/rollover', { from_year_id, to_year_id }),

  getStudentStatement: (studentId: string, academic_year_id: string) =>
    api.get(`/fees/students/${studentId}/statement`, { params: { academic_year_id } }),

  getFineConfig: () => api.get('/fees/fines'),
  upsertFineConfig: (payload: {
    name: string;
    type: 'fixed' | 'percentage_per_day';
    value: number;
    applicable_after_days: number;
    is_active?: boolean;
  }) => api.post('/fees/fines', payload),
  applyFines: (as_of_date?: string) => api.post('/fees/fines/apply', undefined, { params: { as_of_date } }),

  downloadReceipt: (paymentId: string) =>
    api.get(`/fees/payments/${paymentId}/receipt`, { responseType: 'blob' }),
};
