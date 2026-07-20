import api from './axios';

export const calendarApi = {
  list: (params?: { event_type?: string; from_dt?: string; to_dt?: string; skip?: number; limit?: number }) =>
    api.get('/calendar', { params }),
  create: (data: Record<string, unknown>) =>
    api.post('/calendar', data),
  get: (id: string) =>
    api.get(`/calendar/${id}`),
  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/calendar/${id}`, data),
  delete: (id: string) =>
    api.delete(`/calendar/${id}`),
};
