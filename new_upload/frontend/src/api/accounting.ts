import api from './axios';

export interface IncomeCategory {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface ExpenseCategory {
  id: string;
  name: string;
  description?: string;
  budget_amount: number;
  is_active: boolean;
}

export interface IncomeRecord {
  id: string;
  category_id: string;
  amount: number;
  income_date: string;
  description?: string;
  reference_number?: string;
  received_by?: string;
}

export interface ExpenseRecord {
  id: string;
  category_id: string;
  amount: number;
  expense_date: string;
  description?: string;
  vendor_name?: string;
  payment_mode: string;
  reference_number?: string;
  approved_by?: string;
}

export interface BudgetHead {
  id: string;
  category_id: string;
  academic_year_id: string;
  allocated_amount: number;
  notes?: string;
}

export interface MonthlySummaryItem {
  month: number;
  year: number;
  total_income: number;
  total_expense: number;
  net: number;
}

export const accountingApi = {
  // Income Categories
  listIncomeCategories: (): Promise<IncomeCategory[]> =>
    api.get('/accounting/income-categories').then((r: any) => Array.isArray(r) ? r : (r?.data ?? [])),
  createIncomeCategory: (data: Partial<IncomeCategory>) =>
    api.post('/accounting/income-categories', data),

  // Expense Categories
  listExpenseCategories: (): Promise<ExpenseCategory[]> =>
    api.get('/accounting/expense-categories').then((r: any) => Array.isArray(r) ? r : (r?.data ?? [])),
  createExpenseCategory: (data: Partial<ExpenseCategory>) =>
    api.post('/accounting/expense-categories', data),
  updateExpenseCategory: (id: string, data: Partial<ExpenseCategory>) =>
    api.put(`/accounting/expense-categories/${id}`, data),

  // Income Records
  listIncome: (filters?: { month?: number; year?: number; category_id?: string }): Promise<IncomeRecord[]> =>
    api.get('/accounting/income', { params: filters }).then((r: any) => Array.isArray(r) ? r : (r?.data ?? [])),
  createIncome: (data: Partial<IncomeRecord>) =>
    api.post('/accounting/income', data),
  updateIncome: (id: string, data: Partial<IncomeRecord>) =>
    api.put(`/accounting/income/${id}`, data),
  deleteIncome: (id: string) => api.delete(`/accounting/income/${id}`),

  // Expense Records
  listExpenses: (filters?: { month?: number; year?: number; category_id?: string }): Promise<ExpenseRecord[]> =>
    api.get('/accounting/expenses', { params: filters }).then((r: any) => Array.isArray(r) ? r : (r?.data ?? [])),
  createExpense: (data: Partial<ExpenseRecord>) =>
    api.post('/accounting/expenses', data),
  updateExpense: (id: string, data: Partial<ExpenseRecord>) =>
    api.put(`/accounting/expenses/${id}`, data),
  deleteExpense: (id: string) => api.delete(`/accounting/expenses/${id}`),

  // Budget Heads
  listBudgetHeads: (): Promise<BudgetHead[]> =>
    api.get('/accounting/budgets').then((r: any) => Array.isArray(r) ? r : (r?.data ?? [])),
  createBudgetHead: (data: Partial<BudgetHead>) =>
    api.post('/accounting/budgets', data),
  updateBudgetHead: (id: string, data: Partial<BudgetHead>) =>
    api.put(`/accounting/budgets/${id}`, data),

  // Summary
  getMonthlySummary: (year: number): Promise<MonthlySummaryItem[]> =>
    api.get('/accounting/summary/monthly', { params: { year } }).then((r: any) => Array.isArray(r) ? r : (r?.data ?? [])),
};
