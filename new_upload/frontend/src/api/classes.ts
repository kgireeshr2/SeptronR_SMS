import api from './axios';

export interface ClassItem {
  id: string;
  school_id: string;
  academic_year_id: string;
  name: string;
  is_active: boolean;
  student_count?: number;
}

export interface SectionItem {
  id: string;
  class_id: string;
  name: string;
  capacity: number;
  class_teacher_id?: string | null;
  class_teacher_name?: string | null;
  room_number?: string | null;
  is_active: boolean;
  student_count?: number;
}

export interface SubjectItem {
  id: string;
  school_id: string;
  name: string;
  code?: string | null;
  is_elective: boolean;
  full_marks: number;
  pass_marks: number;
  is_active: boolean;
}

export interface TimetableEntryInput {
  subject_id: string;
  teacher_id?: string | null;
  day_of_week: number;
  period_number: number;
  start_time: string;
  end_time: string;
}

export const classesApi = {
  list: (academicYearId: string) => api.get(`/classes?academic_year_id=${academicYearId}`),
  get: (classId: string) => api.get(`/classes/${classId}`),
  create: (payload: { name: string; academic_year_id: string }) => api.post('/classes', payload),
  update: (classId: string, payload: Partial<{ name: string; is_active: boolean }>) =>
    api.put(`/classes/${classId}`, payload),
  remove: (classId: string) => api.delete(`/classes/${classId}`),

  listSections: (classId: string) => api.get(`/classes/${classId}/sections`),
  createSection: (
    classId: string,
    payload: { name: string; capacity: number; class_teacher_id?: string | null; room_number?: string | null }
  ) => api.post(`/classes/${classId}/sections`, payload),
  updateSection: (
    classId: string,
    sectionId: string,
    payload: Partial<{ name: string; capacity: number; class_teacher_id?: string | null; room_number?: string | null; is_active: boolean }>
  ) => api.put(`/classes/${classId}/sections/${sectionId}`, payload),
  removeSection: (classId: string, sectionId: string) => api.delete(`/classes/${classId}/sections/${sectionId}`),

  listClassSubjects: (classId: string) => api.get(`/classes/${classId}/subjects`),
  assignSubject: (classId: string, payload: { subject_id: string; teacher_id?: string | null }) =>
    api.post(`/classes/${classId}/subjects`, payload),
  updateSubjectAssignment: (classId: string, subjectId: string, payload: { subject_id: string; teacher_id?: string | null }) =>
    api.put(`/classes/${classId}/subjects/${subjectId}`, payload),
  removeSubjectAssignment: (classId: string, subjectId: string) => api.delete(`/classes/${classId}/subjects/${subjectId}`),
};

export const subjectsApi = {
  list: () => api.get('/subjects'),
  create: (payload: { name: string; code?: string; is_elective?: boolean; full_marks?: number; pass_marks?: number }) =>
    api.post('/subjects', payload),
  update: (
    subjectId: string,
    payload: Partial<{ name: string; code?: string; is_elective: boolean; full_marks: number; pass_marks: number; is_active: boolean }>
  ) => api.put(`/subjects/${subjectId}`, payload),
  remove: (subjectId: string) => api.delete(`/subjects/${subjectId}`),
};

export const timetableApi = {
  getSection: (sectionId: string, academicYearId: string) =>
    api.get(`/timetable/section/${sectionId}?academic_year_id=${academicYearId}`),
  upsertSlot: (sectionId: string, academicYearId: string, payload: TimetableEntryInput) =>
    api.put(`/timetable/section/${sectionId}/slot?academic_year_id=${academicYearId}`, payload),
  removeSlot: (timetableId: string) => api.delete(`/timetable/${timetableId}`),
  bulkUpsert: (sectionId: string, academicYearId: string, entries: TimetableEntryInput[]) =>
    api.post(`/timetable/section/${sectionId}/bulk?academic_year_id=${academicYearId}`, { entries }),
  exportPdfUrl: (sectionId: string, academicYearId: string) =>
    `${(import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')}/timetable/section/${sectionId}/export?academic_year_id=${academicYearId}`,
};
