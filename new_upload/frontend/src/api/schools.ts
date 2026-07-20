import api from './axios';

export interface SchoolProfileUpdate {
  school_name?: string;
  tagline?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
  phone?: string;
  email?: string;
  website?: string;
  established_year?: number;
  affiliation_board?: string;
  affiliation_number?: string;
  principal_name?: string;
  timezone?: string;
  currency?: string;
  date_format?: string;
  academic_start_month?: number;
}

export interface SchoolBootstrapCreate {
  school_name: string;
  phone?: string;
  email?: string;
  website?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
}

export const schoolsApi = {
  bootstrapSchool: (data: SchoolBootstrapCreate) => api.post('/schools/bootstrap', data),
  getProfile: () => api.get('/schools/profile'),
  updateProfile: (data: SchoolProfileUpdate) => api.put('/schools/profile', data),
  uploadLogo: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/schools/profile/logo', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getSettings: () => api.get('/schools/settings'),
  updateSettings: (settings: Record<string, string>) => api.put('/schools/settings', { settings }),
  getSetting: (key: string) => api.get(`/schools/settings/${key}`),
  updateSetting: (key: string, value: string) => api.put(`/schools/settings/${key}`, { value }),
};
