import api from './axios';

export type ExpenseStatus = 'pending' | 'partial' | 'paid' | 'waived';

export interface PersonalExpenseCategory {
  id: string;
  school_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
}

export interface PersonalExpense {
  id: string;
  school_id: string;
  student_id: string;
  student_name?: string;
  admission_number?: string;
  category_id?: string;
  title: string;
  amount: number;       // billed amount
  paid_amount: number;  // collected so far
  balance: number;      // amount - paid_amount
  expense_date?: string;
  notes?: string;
  status: ExpenseStatus;
  paid_at?: string;
  payment_method?: string;
  collected_by?: string;
  created_at: string;
  updated_at: string;
}

export interface StudentExpenseSummary {
  total_count: number;
  total_amount: number;
  paid_amount: number;
  pending_amount: number;
  balance_due: number;
}

export interface ExpenseListResponse {
  expenses: PersonalExpense[];
  summary: StudentExpenseSummary;
  total?: number;
}

export const personalExpensesApi = {
  // Categories
  listCategories: () => api.get('/personal-expenses/categories'),
  createCategory: (data: { name: string; description?: string; is_active?: boolean }) =>
    api.post('/personal-expenses/categories', data),
  updateCategory: (id: string, data: { name?: string; description?: string; is_active?: boolean }) =>
    api.put(`/personal-expenses/categories/${id}`, data),
  deleteCategory: (id: string) => api.delete(`/personal-expenses/categories/${id}`),

  // List (supports class_id / section_id / student_id filters)
  list: (params?: { student_id?: string; class_id?: string; section_id?: string; status?: string; skip?: number; limit?: number }) =>
    api.get('/personal-expenses', { params }),
  listByStudent: (studentId: string, status?: string) =>
    api.get('/personal-expenses', { params: { student_id: studentId, status, limit: 200 } }),
  getStudentSummary: (studentId: string) =>
    api.get(`/personal-expenses/student/${studentId}/summary`),
  getSchoolSummary: () =>
    api.get('/personal-expenses/school-summary'),

  // Create / Edit
  createExpense: (data: {
    student_id: string;
    category_id?: string;
    title: string;
    amount: number;
    expense_date?: string;
    notes?: string;
  }) => api.post('/personal-expenses', data),
  updateExpense: (id: string, data: {
    category_id?: string;
    title?: string;
    amount?: number;
    expense_date?: string;
    notes?: string;
  }) => api.put(`/personal-expenses/${id}`, data),

  // Bulk assign to class / section
  bulkAssign: (data: {
    title: string;
    amount: number;
    category_id?: string;
    expense_date?: string;
    notes?: string;
    class_id?: string;
    section_id?: string;
    academic_year_id?: string;
    student_ids?: string[];
  }) => api.post('/personal-expenses/bulk-assign', data),

  // Actions
  markPaid: (id: string, data: { payment_method?: string; paid_at?: string; amount_paid?: number }) =>
    api.post(`/personal-expenses/${id}/mark-paid`, data),
  waiveExpense: (id: string, reason?: string) =>
    api.post(`/personal-expenses/${id}/waive`, { reason }),
  deleteExpense: (id: string) => api.delete(`/personal-expenses/${id}`),
};
