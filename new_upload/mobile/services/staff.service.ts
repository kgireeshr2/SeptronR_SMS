import api from './api';
import { PaginationParams, Staff } from '@/types';

export const staffService = {
  list: (params: PaginationParams & { department_id?: string; status?: string }) =>
    api.get<Staff[]>('/staff', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Staff>(`/staff/${id}`).then((r) => r.data),

  update: (id: string, data: Partial<Staff>) =>
    api.patch<Staff>(`/staff/${id}`, data).then((r) => r.data),

  uploadPhoto: (id: string, photo: FormData) =>
    api.post(`/staff/${id}/photo`, photo, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data),

  getLeaveBalance: (id: string) =>
    api.get(`/staff/${id}/leave-balance`).then((r) => r.data),

  getPayslips: (id: string) =>
    api.get(`/payroll`, { params: { staff_id: id } }).then((r) => r.data),
};
