import api from './api';
import { AttendanceRecord } from '@/types';

export const attendanceService = {
  // Student attendance
  getByDate: (date: string, class_id: string, section_id: string) =>
    api.get<AttendanceRecord[]>('/attendance', { params: { date, class_id, section_id } }).then((r) => r.data),

  markBulk: (date: string, class_id: string, section_id: string, records: Array<{ student_id: string; status: string; remarks?: string }>) =>
    api.post('/attendance/mark-bulk', { date, class_id, section_id, records }).then((r) => r.data),

  getStudentSummary: (student_id: string, month: number, year: number) =>
    api.get('/attendance/summary', { params: { student_id, month, year } }).then((r) => r.data),

  getStudentMonthly: (student_id: string, month: number, year: number) =>
    api.get('/attendance/monthly', { params: { student_id, month, year } }).then((r) => r.data),

  // Staff attendance
  staffMark: (data: { date: string; status: string; checkIn?: string; checkOut?: string }) =>
    api.post('/staff-attendance/mark', data).then((r) => r.data),

  staffGetMyAttendance: (month: number, year: number) =>
    api.get('/staff-attendance/my', { params: { month, year } }).then((r) => r.data),
};
