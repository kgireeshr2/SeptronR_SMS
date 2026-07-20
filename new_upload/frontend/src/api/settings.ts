import api from './axios';

export type SettingCategory =
  | 'general'
  | 'admission'
  | 'attendance'
  | 'fees'
  | 'communication'
  | 'library'
  | 'exam'
  | 'security'
  | 'integrations'
  | 'backup';

export interface SchoolSetting {
  key: string;
  value: string | number | boolean | null;
  category: SettingCategory;
  data_type: 'string' | 'number' | 'boolean' | 'json';
  is_public: boolean;
  updated_at?: string;
}

export interface SchoolProfile {
  school_name: string;
  tagline?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
  phone?: string;
  email?: string;
  website?: string;
  logo_url?: string;
  favicon_url?: string;
  established_year?: number;
  affiliation_board?: string;
  affiliation_number?: string;
  principal_name?: string;
  principal_signature_url?: string;
  school_seal_url?: string;
  timezone?: string;
  currency?: string;
  date_format?: string;
  academic_start_month?: number;
}

export interface AllSettings {
  general: Record<string, unknown>;
  admission: Record<string, unknown>;
  attendance: Record<string, unknown>;
  fees: Record<string, unknown>;
  communication: Record<string, unknown>;
  library: Record<string, unknown>;
  exam: Record<string, unknown>;
  security: Record<string, unknown>;
  integrations: Record<string, unknown>;
  backup: Record<string, unknown>;
}

export const settingsApi = {
  /** Get all settings grouped by category */
  getAll: () => api.get<AllSettings>('/settings'),

  /** Get settings for a specific category */
  getCategory: (category: SettingCategory) =>
    api.get<Record<string, unknown>>(`/settings/${category}`),

  /** Save settings for a specific category */
  saveCategory: (category: SettingCategory, data: Record<string, unknown>) =>
    api.put<Record<string, unknown>>(`/settings/${category}`, data),

  /** Get school profile */
  getProfile: () => api.get<SchoolProfile>('/schools/profile'),

  /** Update school profile */
  updateProfile: (data: Partial<SchoolProfile>) => api.put<SchoolProfile>('/schools/profile', data),

  /** Upload school logo */
  uploadLogo: (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return api.post<{ url: string }>('/schools/logo', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
