import api from './axios';

export type SessionType = 'morning' | 'afternoon' | 'full_day';
export type AttendanceStatus = 'present' | 'absent' | 'late' | 'half_day' | 'leave' | 'holiday';

export interface AttendanceMarkEntry {
  student_id: string;
  status: AttendanceStatus;
  remarks?: string;
}

export interface AttendanceMarkRequest {
  section_id: string;
  academic_year_id: string;
  date: string;
  session_type?: SessionType;
  entries: AttendanceMarkEntry[];
}

export interface SectionAttendanceRecord {
  id: string;
  student_id: string;
  student_name: string;
  admission_number: string;
  date: string;
  status: AttendanceStatus;
  session: SessionType;
  remarks?: string;
  marked_at?: string;
}

export interface SectionAttendanceSummary {
  section_id: string;
  date: string;
  session: SessionType;
  total: number;
  present: number;
  absent: number;
  late: number;
  half_day: number;
  leave: number;
  attendance_pct: number;
  entries: SectionAttendanceRecord[];
}

export interface StaffAttendanceMarkRequest {
  staff_id: string;
  date: string;
  status: 'present' | 'absent' | 'late' | 'half_day' | 'on_leave' | 'holiday';
  check_in?: string;
  check_out?: string;
  source?: 'manual' | 'biometric' | 'qr';
  remarks?: string;
}

export interface HolidayCreate {
  academic_year_id: string;
  name: string;
  date: string;
  holiday_type?: 'national' | 'state' | 'school' | 'religious' | 'other';
}

export const attendanceApi = {
  getSectionForDate: (sectionId: string, date: string, session: SessionType = 'full_day') =>
    api.get<SectionAttendanceSummary>(`/attendance/section/${sectionId}`, {
      params: { date, session },
    }),

  markAttendance: (sectionId: string, data: AttendanceMarkRequest) =>
    api.post<SectionAttendanceSummary>(`/attendance/section/${sectionId}`, data),

  updateRecord: (id: string, data: { status: AttendanceStatus; remarks?: string }) =>
    api.put(`/attendance/${id}`, data),

  getStudentSummary: (studentId: string, from: string, to: string) =>
    api.get(`/attendance/student/${studentId}`, { params: { from, to } }),

  getReport: (params: {
    academic_year_id: string;
    from_date: string;
    to_date: string;
    section_id?: string;
    class_id?: string;
    student_id?: string;
  }) => api.get('/attendance/report', { params }),

  getLowAttendance: (yearId: string, threshold = 75) =>
    api.get('/attendance/low-attendance', { params: { year_id: yearId, threshold } }),

  exportAttendance: (params: {
    academic_year_id: string;
    from_date: string;
    to_date: string;
    section_id?: string;
    class_id?: string;
    student_id?: string;
  }) => api.get('/attendance/export', { params, responseType: 'blob' }),

  getMonthlySheetPdf: (sectionId: string, academicYearId: string, month: number, year: number) =>
    api.get(`/attendance/section/${sectionId}/monthly-sheet`, {
      params: { academic_year_id: academicYearId, month, year },
      responseType: 'blob',
    }),

  listStaffAttendance: (date: string) =>
    api.get('/staff-attendance', { params: { date } }),

  markStaffAttendance: (data: StaffAttendanceMarkRequest[]) =>
    api.post('/staff-attendance', data),

  importBiometric: (file: File, date: string) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/staff-attendance/biometric-import', form, {
      params: { date },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  staffMonthlyReport: (month: number, year: number) =>
    api.get('/staff-attendance/report', { params: { month, year } }),

  listHolidays: (yearId?: string) => api.get('/holidays', { params: { year_id: yearId } }),
  createHoliday: (data: HolidayCreate) => api.post('/holidays', data),
  updateHoliday: (id: string, data: Partial<HolidayCreate>) => api.put(`/holidays/${id}`, data),
  deleteHoliday: (id: string) => api.delete(`/holidays/${id}`),
  bulkCreateHolidays: (data: HolidayCreate[]) => api.post('/holidays/bulk', data),
};
