// ─── Common ───────────────────────────────────────────────────────────────────
export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface APIResponse<T = unknown> {
  success: boolean;
  data: T;
  message: string;
  pagination?: PaginationMeta;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface LoginPayload {
  username: string;
  password: string;
}

export interface AuthResponse {
  accessToken: string;
  user: {
    id: string;
    name: string;
    email: string;
    phone?: string;
    avatarUrl?: string;
    isSuperAdmin: boolean;
  };
  school: {
    id: string;
    name: string;
    slug: string;
    logoUrl?: string;
  } | null;
  permissions: string[];
}

// ─── School ───────────────────────────────────────────────────────────────────
export interface School {
  id: string;
  name: string;
  slug: string;
  phone?: string;
  email?: string;
  address?: string;
  logoUrl?: string;
  isActive: boolean;
  createdAt: string;
}

// ─── Academic Year ────────────────────────────────────────────────────────────
export interface AcademicYear {
  id: string;
  schoolId: string;
  name: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
  isLocked: boolean;
  createdAt: string;
}

// ─── User ─────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  schoolId?: string;
  name: string;
  email: string;
  phone?: string;
  username?: string;
  avatarUrl?: string;
  isSuperAdmin: boolean;
  isActive: boolean;
  createdAt: string;
}

// ─── Role & Permission ────────────────────────────────────────────────────────
export interface Role {
  id: string;
  schoolId?: string;
  name: string;
  slug: string;
  description?: string;
  isSystem: boolean;
  isActive: boolean;
}

export interface Permission {
  id: string;
  module: string;
  action: string;
  description?: string;
}

// ─── Student ──────────────────────────────────────────────────────────────────
export interface Student {
  id: string;
  schoolId: string;
  admissionNumber: string;
  name: string;
  dateOfBirth?: string;
  gender: string;
  bloodGroup?: string;
  photoUrl?: string;
  email?: string;
  phone?: string;
  address?: string;
  isActive: boolean;
  createdAt: string;
}

// ─── Staff ───────────────────────────────────────────────────────────────────
export interface Staff {
  id: string;
  schoolId: string;
  employeeId: string;
  name: string;
  email?: string;
  phone?: string;
  gender?: string;
  dateOfBirth?: string;
  photoUrl?: string;
  departmentId?: string;
  designationId?: string;
  employmentType: string;
  joiningDate?: string;
  isActive: boolean;
}

// ─── Notification ─────────────────────────────────────────────────────────────
export interface Notification {
  id: string;
  title: string;
  body: string;
  type: string;
  isRead: boolean;
  link?: string;
  createdAt: string;
}

// ─── Fee ──────────────────────────────────────────────────────────────────────
export interface FeeInvoice {
  id: string;
  schoolId: string;
  studentId: string;
  invoiceNumber: string;
  totalAmount: number; // paise
  paidAmount: number;  // paise
  balanceAmount: number; // paise
  status: 'draft' | 'sent' | 'partial' | 'paid' | 'overdue' | 'cancelled';
  dueDate: string;
  createdAt: string;
}
