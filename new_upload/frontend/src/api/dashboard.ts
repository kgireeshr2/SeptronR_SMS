import api from './axios';

// ── Admin Dashboard ───────────────────────────────────────────────────────────
export interface AdminDashboardStats {
  total_students: number;
  total_staff: number;
  total_fee_collected_this_month: number;
  total_fee_outstanding: number;
  total_present_today: number;
  total_absent_today: number;
  attendance_pct_today: number;
  pending_leave_requests: number;
  low_stock_alerts: { name: string; current_stock: number; reorder_level: number }[];
  monthly_fee_collection: { month: string; amount: number }[];
  student_by_class: { class_name: string; count: number }[];
  student_by_gender: { male: number; female: number; other: number };
  upcoming_events: { title: string; event_type: string; start_datetime: string }[];
  recent_payments: { student_name: string; amount: number; payment_date: string }[];
  todays_birthdays_students: { name: string; class_name?: string }[];
  todays_birthdays_staff: { name: string; designation?: string }[];
  overdue_library_books: number;
  pending_admissions: number;
  recent_audit_logs: { user_name: string; action: string; module: string; timestamp: string }[];
  new_admissions_monthly: { month: string; count: number }[];
}

// ── Teacher Dashboard ─────────────────────────────────────────────────────────
export interface TeacherDashboardStats {
  my_classes: { class_name: string; section_name: string; students: number }[];
  attendance_today: { marked: number; total: number };
  pending_homework_reviews: number;
  upcoming_exams: { name: string; class_name: string; exam_date: string }[];
  todays_timetable: { subject: string; class_name: string; section_name: string; start_time: string; end_time: string }[];
}

// ── Student Dashboard ─────────────────────────────────────────────────────────
export interface StudentDashboardStats {
  fee_outstanding: number;
  attendance_pct: number;
  upcoming_exams: { name: string; exam_date: string }[];
  homework_due: { title: string; subject_id: string; due_date: string }[];
  recent_results: { exam_name: string; subject: string; marks: number; total: number }[];
  library_books_issued: number;
  timetable_today: { subject: string; start_time: string; end_time: string }[];
}

// ── Parent Dashboard ──────────────────────────────────────────────────────────
export interface ParentDashboardStats {
  children: {
    id: string;
    name: string;
    admission_number: string;
    class_name: string;
    section_name: string;
    attendance_pct: number;
    fee_outstanding: number;
    upcoming_exams: { name: string; exam_date: string }[];
    homework_due: { title: string; due_date: string }[];
  }[];
  announcements: { title: string; body: string; created_at: string }[];
  upcoming_events: { title: string; event_type: string; start_datetime: string }[];
}

export const dashboardApi = {
  getAdminStats: (yearId?: string) =>
    api.get<AdminDashboardStats>('/dashboard/admin', { params: yearId ? { year_id: yearId } : {} }),

  getTeacherStats: () =>
    api.get<TeacherDashboardStats>('/dashboard/teacher'),

  getStudentStats: () =>
    api.get<StudentDashboardStats>('/dashboard/student'),

  getParentStats: () =>
    api.get<ParentDashboardStats>('/dashboard/parent'),
};
