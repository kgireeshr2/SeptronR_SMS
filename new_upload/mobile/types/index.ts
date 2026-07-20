// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface LoginRequest {
  /** `identifier` maps to the backend field (email or username) */
  identifier: string;
  password: string;
  schoolSlug: string;
}

/** Shape of response.data after the {success, data} envelope is unwrapped */
export interface LoginResponse {
  access_token: string;
  user: User;
  school: School | null;
}

/** Backend user object (snake_case, UUID ids) */
export interface User {
  id: string;           // UUID
  username: string;
  email: string;
  /** Concatenated display name; may be missing — fall back to username */
  full_name?: string;
  is_super_admin: boolean;
  is_active: boolean;
  is_verified?: boolean;
  avatar_url?: string | null;
  school_id: string | null;
  /** Space-separated permission string from /auth/me  OR  string[] from /auth/login */
  permissions: string | string[];
  profile_photo?: string | null;
}

export interface School {
  id: string;
  slug: string;
  name: string;
  logo_url?: string | null;
}

// ─── Pagination ───────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  search?: string;
}

// ─── Student ─────────────────────────────────────────────────────────────────
export interface Student {
  id: string;
  admission_number: string;
  full_name: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  gender?: string;
  class_id?: string;
  class_name?: string;
  section_id?: string;
  section_name?: string;
  parent_name?: string;
  parent_phone?: string;
  photo_url?: string | null;
  status?: string;
  is_active?: boolean;
  school_id?: string;
  user_id?: string;
  created_at?: string;
}

// ─── Staff ────────────────────────────────────────────────────────────────────
export interface Staff {
  id: string;
  employee_id: string;
  full_name: string;
  first_name?: string;
  last_name?: string;
  designation_name?: string | null;
  department_id?: string | null;
  department_name?: string | null;
  email: string;
  phone?: string;
  photo_url?: string | null;
  is_active?: boolean;
  experience_years?: number | null;
  date_of_joining?: string;
  school_id?: string;
  user_id?: string;
  created_at?: string;
}

// ─── Attendance ──────────────────────────────────────────────────────────────
export interface AttendanceRecord {
  student_id: string;
  student_name: string;
  date: string;
  status: 'present' | 'absent' | 'late' | 'excused';
  remarks?: string;
}

// ─── Fee ─────────────────────────────────────────────────────────────────────
export interface FeeInvoice {
  id: string;
  invoice_number?: string;
  student_id?: string;
  student_name?: string;
  total_amount: number;
  paid_amount: number;
  due_amount?: number;
  due_date?: string;
  status: 'paid' | 'pending' | 'overdue' | 'partial';
  items?: FeeItem[];
}

export interface FeeItem {
  id: string;
  fee_name?: string;
  fee_category_name?: string;
  amount: number;
  paid_amount?: number;
}

// ─── Exam ─────────────────────────────────────────────────────────────────────
export interface Exam {
  id: string;
  name: string;
  exam_type_id?: string;
  exam_type_name?: string;
  start_date?: string;
  end_date?: string;
  class_id?: string;
  class_name?: string;
  status?: string;
}

export interface ExamResult {
  id: string;
  student_id?: string;
  student_name?: string;
  subject_name?: string;
  marks_obtained?: number;
  total_marks?: number;
  percentage?: number;
  grade?: string;
  remarks?: string;
}

// ─── Homework ─────────────────────────────────────────────────────────────────
export interface Homework {
  id: string;
  title: string;
  description?: string;
  subject_id?: string;
  subject_name?: string;
  class_id?: string;
  class_name?: string;
  due_date?: string;
  assigned_by_id?: string;
  assigned_by_name?: string;
  created_at?: string;
}

// ─── Timetable ────────────────────────────────────────────────────────────────
export interface TimetableSlot {
  id: string;
  day_of_week?: number;
  day_name?: string;
  period_number?: number;
  start_time?: string;
  end_time?: string;
  subject_id?: string;
  subject_name?: string;
  staff_id?: string;
  staff_name?: string;
  class_id?: string;
  section_id?: string;
}

// ─── Leave ────────────────────────────────────────────────────────────────────
export interface LeaveApplication {
  id: string;
  staff_id?: string;
  staff_name?: string;
  leave_type?: string;
  start_date?: string;
  end_date?: string;
  reason?: string;
  status: 'pending' | 'approved' | 'rejected';
  applied_at?: string;
  approved_by?: string;
}

// ─── Announcement ────────────────────────────────────────────────────────────
export interface Announcement {
  id: string;
  title: string;
  content?: string;
  target_roles?: string[];
  published_at?: string;
  created_by_name?: string;
  is_read?: boolean;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export interface DashboardStats {
  total_students?: number;
  total_staff?: number;
  today_attendance_percent?: number;
  pending_fees?: number;
  pending_leaves?: number;
  recent_announcements?: Announcement[];
  fee_collection_this_month?: number;
  upcoming_exams?: Exam[];
}

// ─── Notification ────────────────────────────────────────────────────────────
export interface AppNotification {
  id: string;
  title: string;
  message?: string;
  type?: string;
  is_read?: boolean;
  created_at?: string;
  data?: Record<string, unknown>;
}
