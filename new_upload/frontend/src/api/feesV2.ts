import api from './axios';

export type PaymentMethod = 'cash' | 'cheque' | 'online' | 'card' | 'neft' | 'upi';

export interface FeeType {
  id: string;
  school_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FeeGroup {
  id: string;
  school_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  fee_types: FeeType[];
  created_at: string;
  updated_at: string;
}

export interface FeeMasterItem {
  id: string;
  fee_type_id: string;
  fee_type_name?: string;
  amount: number;
}

export interface FeeMaster {
  id: string;
  school_id: string;
  name: string;
  class_id: string;
  class_name?: string;
  academic_year_id: string;
  academic_year_name?: string;
  fee_group_id: string;
  fee_group_name?: string;
  is_active: boolean;
  items: FeeMasterItem[];
  created_at: string;
  updated_at: string;
}

export interface StudentFeeAssignment {
  id: string;
  student_id: string;
  student_name?: string;
  fee_master_id: string;
  fee_master_name?: string;
  academic_year_id: string;
  created_at: string;
}

export interface FeeTypeLedgerEntry {
  fee_type_id: string;
  fee_type_name: string;
  amount_due: number;
  amount_paid: number;
  discount_given: number;
  balance: number;
}

export interface StudentFeeLedger {
  student_id: string;
  student_name: string;
  class_name?: string;
  fee_master_id: string;
  fee_master_name: string;
  total_due: number;
  total_paid: number;
  total_discount: number;
  total_balance: number;
  entries: FeeTypeLedgerEntry[];
}

export interface FeeCollectionItem {
  id: string;
  fee_type_id: string;
  fee_type_name?: string;
  amount_paid: number;
  discount_amount: number;
  discount_reason?: string;
}

export interface FeeCollection {
  id: string;
  school_id: string;
  student_id: string;
  student_name?: string;
  class_name?: string;
  fee_master_id: string;
  fee_master_name?: string;
  academic_year_id: string;
  receipt_number: string;
  payment_date: string;
  total_amount: number;
  total_discount: number;
  payment_method: PaymentMethod;
  transaction_ref?: string;
  collected_by: string;
  collected_by_name?: string;
  remarks?: string;
  is_reversed: boolean;
  reversal_reason?: string;
  reversed_at?: string;
  items: FeeCollectionItem[];
  created_at: string;
}

export const feesV2Api = {
  // Fee Types
  listFeeTypes: () => api.get('/fees-v2/fee-types'),
  createFeeType: (payload: { name: string; description?: string; is_active?: boolean }) =>
    api.post('/fees-v2/fee-types', payload),
  updateFeeType: (id: string, payload: Partial<{ name: string; description?: string; is_active: boolean }>) =>
    api.put(`/fees-v2/fee-types/${id}`, payload),
  deleteFeeType: (id: string) => api.delete(`/fees-v2/fee-types/${id}`),

  // Fee Groups
  listFeeGroups: () => api.get('/fees-v2/fee-groups'),
  createFeeGroup: (payload: { name: string; description?: string; fee_type_ids: string[]; is_active?: boolean }) =>
    api.post('/fees-v2/fee-groups', payload),
  updateFeeGroup: (id: string, payload: Partial<{ name: string; description?: string; fee_type_ids: string[]; is_active: boolean }>) =>
    api.put(`/fees-v2/fee-groups/${id}`, payload),
  deleteFeeGroup: (id: string) => api.delete(`/fees-v2/fee-groups/${id}`),

  // Fee Masters
  listFeeMasters: (params?: { class_id?: string; academic_year_id?: string }) =>
    api.get('/fees-v2/fee-masters', { params }),
  createFeeMaster: (payload: {
    name: string; class_id: string; academic_year_id: string; fee_group_id: string;
    items: Array<{ fee_type_id: string; amount: number }>; is_active?: boolean;
  }) => api.post('/fees-v2/fee-masters', payload),
  updateFeeMaster: (id: string, payload: Partial<{
    name: string; is_active: boolean;
    items: Array<{ fee_type_id: string; amount: number }>;
  }>) => api.put(`/fees-v2/fee-masters/${id}`, payload),
  deleteFeeMaster: (id: string) => api.delete(`/fees-v2/fee-masters/${id}`),

  // Assignments
  listAssignments: (params?: { academic_year_id?: string; class_id?: string }) =>
    api.get('/fees-v2/assignments', { params }),
  assignFeeMaster: (payload: { student_ids: string[]; fee_master_id: string; academic_year_id: string }) =>
    api.post('/fees-v2/assignments', payload),
  removeAssignment: (id: string) => api.delete(`/fees-v2/assignments/${id}`),

  // Ledger
  getStudentLedger: (studentId: string, academic_year_id: string) =>
    api.get(`/fees-v2/ledger/${studentId}`, { params: { academic_year_id } }),

  // Collections
  listCollections: (params?: { student_id?: string; academic_year_id?: string; include_reversed?: boolean }) =>
    api.get('/fees-v2/collections', { params }),
  collectFee: (payload: {
    student_id: string; fee_master_id: string; academic_year_id: string;
    payment_date: string; payment_method: PaymentMethod; transaction_ref?: string; remarks?: string;
    items: Array<{ fee_type_id: string; amount_paid: number; discount_amount: number; discount_reason?: string }>;
  }) => api.post('/fees-v2/collections', payload),
  reverseCollection: (id: string, reason: string) =>
    api.post(`/fees-v2/collections/${id}/reverse`, { reason }),
};
