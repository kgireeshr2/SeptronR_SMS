import api from './api';
import { PaginatedResponse, PaginationParams, Student } from '@/types';

export const studentsService = {
  list: (params: PaginationParams & { class_id?: string; section_id?: string; status?: string }) =>
    api.get<PaginatedResponse<Student> | Student[]>('/students', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Student>(`/students/${id}`).then((r) => r.data),

  create: (data: FormData) =>
    api.post<Student>('/students', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data),

  update: (id: string, data: Partial<Student>) =>
    api.patch<Student>(`/students/${id}`, data).then((r) => r.data),

  uploadPhoto: (id: string, photo: FormData) =>
    api.post(`/students/${id}/photo`, photo, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data),

  getAttendanceSummary: (id: string, month: number, year: number) =>
    api.get(`/students/${id}/attendance-summary`, { params: { month, year } }).then((r) => r.data),

  getFeeInvoices: (id: string) =>
    api.get(`/fees/invoices`, { params: { student_id: id } }).then((r) => r.data),
};
