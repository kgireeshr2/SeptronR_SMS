import api from './axios';

export interface ExamType {
  id: string;
  school_id: string;
  name: string;
  weightage: number;
  is_active: boolean;
}

export interface Exam {
  id: string;
  school_id: string;
  academic_year_id: string;
  term_id?: string;
  exam_type_id: string;
  name: string;
  class_id: string;
  subject_id: string;
  section_id?: string;
  exam_date?: string;
  start_time?: string;
  end_time?: string;
  room_number?: string;
  invigilator_id?: string;
  full_marks: number;
  pass_marks: number;
  status: string;
  description?: string;
}

export interface GradeRange {
  grade: string;
  min_pct: number;
  max_pct: number;
  grade_point: number;
  description?: string;
}

export interface GradingScale {
  id: string;
  school_id: string;
  name: string;
  ranges: GradeRange[];
  is_active: boolean;
}

export interface MarkEntryItem {
  student_id: string;
  marks_obtained?: number;
  is_absent: boolean;
  is_exempted: boolean;
  remarks?: string;
}

export interface ExamMarkResponse {
  student_id: string;
  student_name: string;
  admission_number: string;
  roll_number?: string;
  marks_obtained?: number;
  full_marks: number;
  pass_marks: number;
  grade?: string;
  grade_point?: number;
  percentage?: number;
  is_absent: boolean;
  is_exempted: boolean;
  result: string;
}

export interface ClassResultResponse {
  exam_type_name: string;
  class_name: string;
  academic_year_name: string;
  results: ClassResultRow[];
  total_students: number;
  passed_students: number;
  failed_students: number;
  class_average: number;
}

export interface ClassResultRow {
  rank: number;
  student_id: string;
  student_name: string;
  admission_number: string;
  roll_number?: string;
  subject_marks: Array<{ subject_name: string; marks?: number; full_marks: number; grade?: string; result: string }>;
  total_marks: number;
  total_full_marks: number;
  percentage: number;
  overall_grade?: string;
  is_pass: boolean;
}

export const examsApi = {
  // Exam Types
  listExamTypes: () => api.get<ExamType[]>('/exam-types'),
  createExamType: (data: { name: string; weightage?: number; is_active?: boolean }) =>
    api.post<ExamType>('/exam-types', data),
  updateExamType: (id: string, data: Partial<{ name: string; weightage: number; is_active: boolean }>) =>
    api.put<ExamType>(`/exam-types/${id}`, data),
  deleteExamType: (id: string) => api.delete(`/exam-types/${id}`),

  // Grading Scales
  getGradingScale: () => api.get<GradingScale | null>('/grading-scales'),
  upsertGradingScale: (data: { name: string; ranges: GradeRange[] }) =>
    api.put<GradingScale>('/grading-scales', data),

  // Exams
  listExams: (params?: { year_id?: string; class_id?: string; exam_type_id?: string; status?: string }) =>
    api.get<Exam[]>('/exams', { params }),
  getExam: (id: string) => api.get<Exam>(`/exams/${id}`),
  createExam: (data: Partial<Exam>) => api.post<Exam>('/exams', data),
  updateExam: (id: string, data: Partial<Exam>) => api.put<Exam>(`/exams/${id}`, data),
  deleteExam: (id: string) => api.delete(`/exams/${id}`),

  // Marks
  getMarks: (examId: string) => api.get<ExamMarkResponse[]>(`/exams/${examId}/marks`),
  enterMarks: (examId: string, entries: MarkEntryItem[]) =>
    api.post<ExamMarkResponse[]>(`/exams/${examId}/marks`, { entries }),

  // Results
  getClassResults: (examId: string, classId: string, yearId: string) =>
    api.get<ClassResultResponse>(`/exams/${examId}/results/${classId}`, { params: { year_id: yearId } }),
  publishResults: (examIdOrData: string | { exam_type_id: string; class_id: string; year_id: string; notify_parents: boolean }) =>
    typeof examIdOrData === 'string'
      ? api.post(`/exams/${examIdOrData}/publish`, {})
      : api.post('/exams/publish', examIdOrData),
};
