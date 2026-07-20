import api from './axios';

export interface Department {
  id: string;
  school_id: string;
  name: string;
  hod_id?: string;
  is_active: boolean;
  hod_name?: string;
  staff_count?: number;
  created_at: string;
  updated_at: string;
}

export interface DepartmentCreate {
  name: string;
  hod_id?: string;
}

export interface DepartmentUpdate {
  name?: string;
  hod_id?: string;
  is_active?: boolean;
}

export interface Designation {
  id: string;
  school_id: string;
  name: string;
  is_active: boolean;
  staff_count?: number;
  created_at: string;
  updated_at: string;
}

export interface DesignationCreate {
  name: string;
}

export interface DesignationUpdate {
  name?: string;
  is_active?: boolean;
}

export interface Staff {
  id: string;
  school_id: string;
  employee_id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  age?: number;
  date_of_birth?: string;
  gender?: string;
  photo_url?: string;
  department_id?: string;
  department_name?: string;
  designation_id?: string;
  designation_name?: string;
  date_of_joining?: string;
  employment_type: 'permanent' | 'contract' | 'part_time' | 'probation';
  is_active: boolean;
  salary_type: 'monthly' | 'hourly' | 'daily';
  monthly_salary: number;
  bank_account_no?: string;
  bank_name?: string;
  ifsc_code?: string;
  address?: string;
  emergency_contact?: {
    name?: string;
    phone?: string;
    relation?: string;
  };
  qualifications: Array<{
    degree?: string;
    institute?: string;
    year?: string;
  }>;
  experience_years?: number;
  email?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

export interface StaffCreate {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role_ids: string[];
  date_of_birth?: string;
  gender?: string;
  department_id?: string;
  designation_id?: string;
  date_of_joining?: string;
  employment_type?: 'permanent' | 'contract' | 'part_time' | 'probation';
  salary_type?: 'monthly' | 'hourly' | 'daily';
  monthly_salary?: number;
  bank_account_no?: string;
  bank_name?: string;
  ifsc_code?: string;
  address?: string;
  emergency_contact?: object;
  qualifications?: object[];
  experience_years?: number;
}

export interface StaffUpdate {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  gender?: string;
  department_id?: string;
  designation_id?: string;
  date_of_joining?: string;
  employment_type?: 'permanent' | 'contract' | 'part_time' | 'probation';
  salary_type?: 'monthly' | 'hourly' | 'daily';
  monthly_salary?: number;
  bank_account_no?: string;
  bank_name?: string;
  ifsc_code?: string;
  address?: string;
  emergency_contact?: object;
  qualifications?: object[];
  experience_years?: number;
  is_active?: boolean;
}

export interface StaffDocument {
  id: string;
  school_id: string;
  staff_id: string;
  doc_type: string;
  file_url: string;
  uploaded_at: string;
}

export interface StaffStatistics {
  total_staff: number;
  active_staff: number;
  inactive_staff: number;
  by_department: Record<string, number>;
  by_designation: Record<string, number>;
  by_employment_type: Record<string, number>;
}

export const staffApi = {
  // Departments
  listDepartments: (params?: { is_active?: boolean; skip?: number; limit?: number }) =>
    api.get<Department[]>('/departments', { params }),
  
  createDepartment: (data: DepartmentCreate) =>
    api.post<Department>('/departments', data),
  
  getDepartment: (departmentId: string) =>
    api.get<Department>(`/departments/${departmentId}`),
  
  updateDepartment: (departmentId: string, data: DepartmentUpdate) =>
    api.put<Department>(`/departments/${departmentId}`, data),
  
  deleteDepartment: (departmentId: string) =>
    api.delete(`/departments/${departmentId}`),

  // Designations
  listDesignations: (params?: { is_active?: boolean; skip?: number; limit?: number }) =>
    api.get<Designation[]>('/designations', { params }),
  
  createDesignation: (data: DesignationCreate) =>
    api.post<Designation>('/designations', data),
  
  getDesignation: (designationId: string) =>
    api.get<Designation>(`/designations/${designationId}`),
  
  updateDesignation: (designationId: string, data: DesignationUpdate) =>
    api.put<Designation>(`/designations/${designationId}`, data),
  
  deleteDesignation: (designationId: string) =>
    api.delete(`/designations/${designationId}`),

  // Staff
  listStaff: (params?: {
    department_id?: string;
    designation_id?: string;
    employment_type?: string;
    is_active?: boolean;
    search?: string;
    skip?: number;
    limit?: number;
  }) => api.get<Staff[]>('/staff', { params }),

  createStaff: (data: StaffCreate) =>
    api.post<Staff>('/staff', data),

  getStaff: (staffId: string) =>
    api.get<Staff>(`/staff/${staffId}`),

  updateStaff: (staffId: string, data: StaffUpdate) =>
    api.put<Staff>(`/staff/${staffId}`, data),

  deleteStaff: (staffId: string) =>
    api.delete(`/staff/${staffId}`),

  terminateStaff: (staffId: string, reason?: string) =>
    api.post<Staff>(`/staff/${staffId}/terminate`, { reason }),

  uploadStaffPhoto: (staffId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Staff>(`/staff/${staffId}/photo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Staff Documents
  listStaffDocuments: (staffId: string) =>
    api.get<StaffDocument[]>(`/staff/${staffId}/documents`),

  uploadStaffDocument: (staffId: string, docType: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<StaffDocument>(
      `/staff/${staffId}/documents?doc_type=${encodeURIComponent(docType)}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },

  deleteStaffDocument: (staffId: string, documentId: string) =>
    api.delete(`/staff/${staffId}/documents/${documentId}`),

  // Statistics
  getStaffStatistics: () =>
    api.get<StaffStatistics>('/staff/stats/summary'),

  // Role Assignment
  getStaffRoles: (staffId: string) =>
    api.get<{ id: string; name: string; slug: string }[]>(`/staff/${staffId}/roles`),

  assignStaffRoles: (staffId: string, roleIds: string[]) =>
    api.put<{ id: string; name: string; slug: string }[]>(`/staff/${staffId}/roles`, { role_ids: roleIds }),
};
