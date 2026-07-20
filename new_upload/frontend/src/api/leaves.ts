import api from './axios';

export interface LeaveType {
  id: string;
  school_id: string;
  name: string;
  max_days_per_year: number;
  is_paid: boolean;
  is_active: boolean;
  created_at: string;
}

export interface LeaveTypeCreate {
  name: string;
  max_days_per_year: number;
  is_paid: boolean;
}

export interface LeaveTypeUpdate {
  name?: string;
  max_days_per_year?: number;
  is_paid?: boolean;
  is_active?: boolean;
}

export interface LeaveApplication {
  id: string;
  school_id: string;
  staff_id: string;
  leave_type_id: string;
  from_date: string;
  to_date: string;
  total_days: number;
  reason?: string;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  approved_by?: string;
  approved_at?: string;
  remarks?: string;
  staff_name?: string;
  leave_type_name?: string;
  approver_name?: string;
  created_at: string;
  updated_at: string;
}

export interface LeaveApplicationCreate {
  leave_type_id: string;
  from_date: string;
  to_date: string;
  total_days: number;
  reason?: string;
}

export interface LeaveApplicationReview {
  status: 'approved' | 'rejected';
  remarks?: string;
}

export interface LeaveBalance {
  id: string;
  school_id: string;
  staff_id: string;
  leave_type_id: string;
  academic_year_id: string;
  entitled_days: number;
  used_days: number;
  remaining_days: number;
  leave_type_name?: string;
  academic_year_name?: string;
}

export interface LeaveAllocationRequest {
  staff_id: string;
  leave_type_id: string;
  academic_year_id: string;
  entitled_days: number;
}

export interface LeaveBalanceUpdate {
  entitled_days: number;
}

export interface LeaveStatistics {
  total_leaves: number;
  pending_leaves: number;
  approved_leaves: number;
  rejected_leaves: number;
  by_leave_type: Record<string, number>;
}

export const leaveApi = {
  // Leave Types
  listLeaveTypes: (params?: { is_active?: boolean; skip?: number; limit?: number }) =>
    api.get<LeaveType[]>('/leaves/types', { params }),

  createLeaveType: (data: LeaveTypeCreate) =>
    api.post<LeaveType>('/leaves/types', data),

  getLeaveType: (leaveTypeId: string) =>
    api.get<LeaveType>(`/leaves/types/${leaveTypeId}`),

  updateLeaveType: (leaveTypeId: string, data: LeaveTypeUpdate) =>
    api.put<LeaveType>(`/leaves/types/${leaveTypeId}`, data),

  deleteLeaveType: (leaveTypeId: string) =>
    api.delete(`/leaves/types/${leaveTypeId}`),

  // Leave Applications
  listLeaveApplications: (params?: {
    staff_id?: string;
    status?: 'pending' | 'approved' | 'rejected' | 'cancelled';
    from_date?: string;
    to_date?: string;
    skip?: number;
    limit?: number;
  }) => api.get<LeaveApplication[]>('/leaves/applications', { params }),

  getMyLeaveApplications: (params?: {
    status?: 'pending' | 'approved' | 'rejected' | 'cancelled';
    skip?: number;
    limit?: number;
  }) => api.get<LeaveApplication[]>('/leaves/applications/my', { params }),

  applyLeave: (data: LeaveApplicationCreate) =>
    api.post<LeaveApplication>('/leaves/applications', data),

  getLeaveApplication: (leaveId: string) =>
    api.get<LeaveApplication>(`/leaves/applications/${leaveId}`),

  reviewLeaveApplication: (leaveId: string, data: LeaveApplicationReview) =>
    api.patch<LeaveApplication>(`/leaves/applications/${leaveId}/review`, data),

  cancelLeaveApplication: (leaveId: string) =>
    api.patch<LeaveApplication>(`/leaves/applications/${leaveId}/cancel`),

  // Leave Balances
  listLeaveBalances: (params?: {
    staff_id?: string;
    academic_year_id?: string;
  }) => api.get<LeaveBalance[]>('/leaves/balances', { params }),

  getMyLeaveBalances: (params?: { academic_year_id?: string }) =>
    api.get<LeaveBalance[]>('/leaves/balances/my', { params }),

  allocateLeaveBalance: (data: LeaveAllocationRequest) =>
    api.post<LeaveBalance>('/leaves/balances/allocate', data),

  updateLeaveBalance: (balanceId: string, data: LeaveBalanceUpdate) =>
    api.put<LeaveBalance>(`/leaves/balances/${balanceId}`, data),

  // Statistics
  getLeaveStatistics: () =>
    api.get<LeaveStatistics>('/leaves/stats/summary'),
};
