import api from './axios';

export interface AdmissionListParams {
  status?: string;
  academic_year_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface ReviewRequest {
  status: 'approved' | 'rejected' | 'waitlisted' | 'under_review';
  remarks?: string;
  assigned_admission_number?: string;
}

export const admissionsApi = {
  getConfig: (yearId?: string) => api.get(`/admissions/config${yearId ? `?year_id=${yearId}` : ''}`),
  getPublicConfig: (schoolSlug: string, yearId?: string) =>
    api.get(`/admissions/public-config/${schoolSlug}${yearId ? `?year_id=${yearId}` : ''}`),
  updateConfig: (data: any) => api.put('/admissions/config', data),
  submitApplication: (data: FormData) =>
    api.post('/admissions/apply', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  checkStatus: (reference: string) => api.get(`/admissions/check/${reference}`),
  list: (params: AdmissionListParams) => api.get('/admissions', { params }),
  get: (id: string) => api.get(`/admissions/${id}`),
  review: (id: string, data: ReviewRequest) => api.put(`/admissions/${id}/review`, data),
  bulkApprove: (data: { form_ids: string[] }) => api.post('/admissions/bulk-approve', data),
  export: (params: AdmissionListParams) => api.get('/admissions/export', { params }),
  stats: (yearId: string) => api.get(`/admissions/stats?year_id=${yearId}`),

  /** Front-desk manual submission — same as public apply but called internally */
  frontdeskSubmit: (data: {
    school_slug: string;
    academic_year_id: string;
    applicant_name: string;
    date_of_birth: string;
    gender?: string;
    applying_for_class_id?: string;
    parent_name: string;
    parent_phone: string;
    parent_email?: string;
    address?: string;
    previous_school?: string;
  }) => {
    const fd = new FormData();
    Object.entries(data).forEach(([k, v]) => {
      if (v !== undefined && v !== '') fd.append(k, String(v));
    });
    return api.post('/admissions/apply', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};
