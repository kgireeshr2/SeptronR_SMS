import api from './axios';

export interface AcademicTerm {
  id: string;
  academic_year_id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

export interface AcademicYear {
  id: string;
  school_id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  is_locked: boolean;
  terms?: AcademicTerm[];
}

export interface AcademicYearCreate {
  name: string;
  start_date: string;
  end_date: string;
}

export interface AcademicTermCreate {
  name: string;
  start_date: string;
  end_date: string;
}

export const academicYearsApi = {
  list: () => api.get('/academic-years'),
  get: (id: string) => api.get(`/academic-years/${id}`),
  create: (data: AcademicYearCreate) => api.post('/academic-years', data),
  update: (id: string, data: Partial<AcademicYearCreate>) => api.put(`/academic-years/${id}`, data),
  remove: (id: string) => api.delete(`/academic-years/${id}`),
  setCurrent: (id: string) => api.post(`/academic-years/${id}/set-current`),
  lock: (id: string) => api.post(`/academic-years/${id}/lock`),
  unlock: (id: string) => api.post(`/academic-years/${id}/unlock`),
  listTerms: (id: string) => api.get(`/academic-years/${id}/terms`),
  createTerm: (id: string, data: AcademicTermCreate) => api.post(`/academic-years/${id}/terms`, data),
  updateTerm: (id: string, termId: string, data: Partial<AcademicTermCreate>) =>
    api.put(`/academic-years/${id}/terms/${termId}`, data),
  setCurrentTerm: (id: string, termId: string) => api.post(`/academic-years/${id}/terms/${termId}/set-current`),
  removeTerm: (id: string, termId: string) => api.delete(`/academic-years/${id}/terms/${termId}`),
};
