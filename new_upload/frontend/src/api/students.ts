import api from './axios';
import { AxiosResponse } from 'axios';

export interface Student {
  id: string;
  school_id: string;
  admission_number: string;
  user_id?: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  blood_group?: string;
  religion?: string;
  category?: string;
  nationality: string;
  photo_url?: string;
  admission_date: string;
  is_active: boolean;
  aadhaar_number?: string;
  pan_number?: string;
  apaar_number?: string;
  // Contact & Address
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
  // Additional Info
  caste?: string;
  mother_tongue?: string;
  previous_school?: string;
  // Emergency Contact
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relation?: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  deleted_by?: string;
  full_name: string;
  age: number;
}

export interface StudentParent {
  id: string;
  student_id: string;
  user_id?: string;
  relation: 'father' | 'mother' | 'guardian' | 'sibling' | 'other';
  name: string;
  phone?: string;
  email?: string;
  occupation?: string;
  address?: string;
  is_primary_contact: boolean;
  can_access_portal: boolean;
  aadhaar_number?: string;
  pan_number?: string;
  ration_card_number?: string;
  created_at: string;
  updated_at: string;
}

export interface StudentEnrollment {
  id: string;
  student_id: string;
  academic_year_id: string;
  class_id: string;
  section_id: string;
  roll_number?: string;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

export interface StudentDocument {
  id: string;
  student_id: string;
  doc_type: string;
  file_url: string;
  uploaded_at: string;
}

export interface StudentDetail extends Student {
  parents: StudentParent[];
  enrollments: StudentEnrollment[];
  documents: StudentDocument[];
}

export interface StudentCreate {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  blood_group?: string;
  religion?: string;
  category?: string;
  nationality?: string;
  photo_url?: string;
  admission_date: string;
  is_active?: boolean;
  admission_number?: string;
  enrollment?: {
    academic_year_id: string;
    class_id: string;
    section_id: string;
    roll_number?: string;
    is_current?: boolean;
  };
  parents?: Array<{
    relation: string;
    name: string;
    phone?: string;
    email?: string;
    occupation?: string;
    address?: string;
    is_primary_contact?: boolean;
    can_access_portal?: boolean;
    create_login?: boolean;
  }>;
}

export interface StudentUpdate {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  gender?: string;
  blood_group?: string;
  religion?: string;
  category?: string;
  nationality?: string;
  photo_url?: string;
  admission_date?: string;
  admission_number?: string;
  is_active?: boolean;
  aadhaar_number?: string;
  pan_number?: string;
  apaar_number?: string;
  // Contact & Address
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
  // Additional Info
  caste?: string;
  mother_tongue?: string;
  previous_school?: string;
  // Emergency Contact
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relation?: string;
}

export interface StudentParentUpdate {
  relation?: string;
  name?: string;
  phone?: string;
  email?: string;
  occupation?: string;
  address?: string;
  is_primary_contact?: boolean;
  can_access_portal?: boolean;
  aadhaar_number?: string;
  pan_number?: string;
  ration_card_number?: string;
}

export interface StudentStats {
  total_students: number;
  active_students: number;
  inactive_students: number;
  male_students: number;
  female_students: number;
  students_by_class: Array<{
    class_name: string;
    count: number;
  }>;
}

export interface PromoteStudentsRequest {
  student_ids: string[];
  from_academic_year_id: string;
  to_academic_year_id: string;
  to_class_id: string;
  to_section_id: string;
}

export interface IssueTCRequest {
  transfer_certificate_no: string;
  leaving_date: string;
  reason?: string;
}

export interface BulkImportResult {
  success_count: number;
  error_count: number;
  errors: Array<{
    row: number;
    error: string;
  }>;
}

export const studentsApi = {
  // Student CRUD
  createStudent: async (data: StudentCreate): Promise<AxiosResponse<StudentDetail>> => {
    return api.post('/students/', data);
  },

  listStudents: async (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    class_id?: string;
    section_id?: string;
    academic_year_id?: string;
    is_active?: boolean;
  }): Promise<AxiosResponse<Student[]>> => {
    return api.get('/students/', { params });
  },

  getStudent: async (studentId: string): Promise<AxiosResponse<StudentDetail>> => {
    return api.get(`/students/${studentId}`);
  },

  updateStudent: async (studentId: string, data: StudentUpdate): Promise<AxiosResponse<StudentDetail>> => {
    return api.put(`/students/${studentId}`, data);
  },

  deleteStudent: async (studentId: string): Promise<AxiosResponse<{ message: string }>> => {
    return api.delete(`/students/${studentId}`);
  },

  // Stats
  getStudentStats: async (): Promise<AxiosResponse<StudentStats>> => {
    return api.get('/students/stats');
  },

  // Parents
  addParent: async (
    studentId: string,
    data: {
      relation: string;
      name: string;
      phone?: string;
      email?: string;
      occupation?: string;
      address?: string;
      is_primary_contact?: boolean;
      can_access_portal?: boolean;
      create_login?: boolean;
    }
  ): Promise<AxiosResponse<StudentParent>> => {
    return api.post(`/students/${studentId}/parents`, data);
  },

  getParents: async (studentId: string): Promise<AxiosResponse<StudentParent[]>> => {
    return api.get(`/students/${studentId}/parents`);
  },

  deleteParent: async (parentId: string): Promise<AxiosResponse<{ message: string }>> => {
    return api.delete(`/students/parents/${parentId}`);
  },

  updateParent: async (parentId: string, data: StudentParentUpdate): Promise<AxiosResponse<StudentParent>> => {
    return api.put(`/students/parents/${parentId}`, data);
  },

  // Enrollments
  addEnrollment: async (
    studentId: string,
    data: {
      academic_year_id: string;
      class_id: string;
      section_id: string;
      roll_number?: string;
      is_current?: boolean;
    }
  ): Promise<AxiosResponse<StudentEnrollment>> => {
    return api.post(`/students/${studentId}/enrollments`, data);
  },

  // Documents
  addDocument: async (
    studentId: string,
    data: {
      doc_type: string;
      file_url: string;
    }
  ): Promise<AxiosResponse<StudentDocument>> => {
    return api.post(`/students/${studentId}/documents`, data);
  },

  uploadDocument: async (studentId: string, docType: string, file: File): Promise<AxiosResponse<StudentDocument>> => {
    const formData = new FormData();
    formData.append('doc_type', docType);
    formData.append('file', file);
    return api.post(`/students/${studentId}/documents/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  getDocuments: async (studentId: string): Promise<AxiosResponse<StudentDocument[]>> => {
    return api.get(`/students/${studentId}/documents`);
  },

  deleteDocument: async (documentId: string): Promise<AxiosResponse<{ message: string }>> => {
    return api.delete(`/students/documents/${documentId}`);
  },

  // Photo upload
  uploadPhoto: async (studentId: string, file: File): Promise<AxiosResponse<{ photo_url: string }>> => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/students/${studentId}/photo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Bulk operations
  promoteStudents: async (data: PromoteStudentsRequest): Promise<AxiosResponse<any[]>> => {
    return api.post('/students/promote', data);
  },

  bulkImport: async (file: File): Promise<AxiosResponse<BulkImportResult>> => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/students/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  exportCSV: async (): Promise<AxiosResponse<Blob>> => {
    return api.get('/students/export/csv', {
      responseType: 'blob',
    });
  },

  // Transfer Certificate
  issueTC: async (studentId: string, data: IssueTCRequest): Promise<AxiosResponse<any>> => {
    return api.post(`/students/${studentId}/transfer-certificate`, data);
  },

  getTC: async (studentId: string): Promise<AxiosResponse<any>> => {
    return api.get(`/students/${studentId}/transfer-certificate`);
  },

  // ID Card
  generateIDCard: async (studentId: string): Promise<AxiosResponse<any>> => {
    return api.get(`/students/${studentId}/id-card`);
  },
};
