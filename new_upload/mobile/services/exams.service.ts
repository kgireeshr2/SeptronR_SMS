import api from './api';
import { Exam, ExamResult, PaginatedResponse, PaginationParams } from '@/types';

export const examsService = {
  list: (params: PaginationParams & { class_id?: string; academic_year_id?: string }) =>
    api.get<PaginatedResponse<Exam> | Exam[]>('/exams', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Exam>(`/exams/${id}`).then((r) => r.data),

  getResults: (examId: string, class_id?: string) =>
    api.get<ExamResult[]>(`/exams/${examId}/results`, { params: { class_id } }).then((r) => r.data),

  getMyResults: () =>
    api.get<ExamResult[]>('/exams/my-results').then((r) => r.data),

  enterMarks: (examId: string, marks: Array<{ student_id: string; subject_id: string; marks_obtained: number; remarks?: string }>) =>
    api.post(`/exams/${examId}/marks`, { marks }).then((r) => r.data),

  getReportCard: (student_id: string, examId: string) =>
    api.get(`/exams/${examId}/report-card/${student_id}`).then((r) => r.data),
};
