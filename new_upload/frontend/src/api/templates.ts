import api from './axios';

export const templatesApi = {
  list: (params?: { template_type?: string; is_active?: boolean; skip?: number; limit?: number }) =>
    api.get('/document-templates', { params }),
  create: (data: Record<string, unknown>) =>
    api.post('/document-templates', data),
  get: (id: string) =>
    api.get(`/document-templates/${id}`),
  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/document-templates/${id}`, data),
  delete: (id: string) =>
    api.delete(`/document-templates/${id}`),
  setDefault: (id: string) =>
    api.post(`/document-templates/${id}/set-default`),
  bulkPrint: (data: { template_id: string; record_ids: string[]; options?: Record<string, unknown> }) =>
    api.post('/document-templates/bulk-print', data),
};
