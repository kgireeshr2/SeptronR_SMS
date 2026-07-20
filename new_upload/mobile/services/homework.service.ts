import api from './api';
import { Homework, PaginatedResponse, PaginationParams } from '@/types';

export const homeworkService = {
  list: (params: PaginationParams & { class_id?: string; subject_id?: string; due_date?: string }) =>
    api.get<PaginatedResponse<Homework> | Homework[]>('/homework', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Homework>(`/homework/${id}`).then((r) => r.data),

  create: (data: Omit<Homework, 'id' | 'assigned_by_id' | 'assigned_by_name' | 'created_at'>) =>
    api.post<Homework>('/homework', data).then((r) => r.data),

  update: (id: string, data: Partial<Homework>) =>
    api.patch<Homework>(`/homework/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/homework/${id}`).then((r) => r.data),
};
