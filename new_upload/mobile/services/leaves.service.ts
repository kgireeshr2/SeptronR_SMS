import api from './api';
import { LeaveApplication, PaginatedResponse, PaginationParams } from '@/types';

export const leavesService = {
  list: (params: PaginationParams & { status?: string; staff_id?: string }) =>
    api.get<PaginatedResponse<LeaveApplication> | LeaveApplication[]>('/leaves', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<LeaveApplication>(`/leaves/${id}`).then((r) => r.data),

  apply: (data: { leave_type: string; start_date: string; end_date: string; reason: string }) =>
    api.post<LeaveApplication>('/leaves', data).then((r) => r.data),

  cancel: (id: string) =>
    api.patch(`/leaves/${id}/cancel`).then((r) => r.data),

  approve: (id: string, remarks?: string) =>
    api.patch(`/leaves/${id}/approve`, { remarks }).then((r) => r.data),

  reject: (id: string, remarks?: string) =>
    api.patch(`/leaves/${id}/reject`, { remarks }).then((r) => r.data),

  getMyLeaves: (params?: PaginationParams) =>
    api.get<PaginatedResponse<LeaveApplication> | LeaveApplication[]>('/leaves/my', { params }).then((r) => r.data),
};
