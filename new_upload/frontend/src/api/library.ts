import api from './axios';

export interface BookCategory {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Book {
  id: string;
  accession_number: string;
  title: string;
  author?: string;
  isbn?: string;
  publisher?: string;
  edition?: string;
  publication_year?: number;
  category_id?: string;
  total_copies: number;
  available_copies: number;
  price: number;
  location?: string;
  description?: string;
  is_active: boolean;
}

export interface LibraryMember {
  id: string;
  member_id: string;
  user_id: string;
  member_type: string;
  max_books_allowed: number;
  is_active: boolean;
}

export interface BookIssue {
  id: string;
  book_id: string;
  member_id: string;
  issue_date: string;
  due_date: string;
  return_date?: string;
  is_returned: boolean;
  fine_amount: number;
  notes?: string;
}

const unwrap = (r: any) => Array.isArray(r) ? r : (r?.data ?? r);

export const libraryApi = {
  // Book Categories
  listCategories: (): Promise<BookCategory[]> => api.get('/library/categories').then(unwrap),
  createCategory: (data: Partial<BookCategory>) => api.post('/library/categories', data),

  // Books
  listBooks: (filters?: { category_id?: string; available_only?: boolean; search?: string }): Promise<Book[]> =>
    api.get('/library/books', { params: filters }).then(unwrap),
  getBook: (id: string) => api.get(`/library/books/${id}`),
  createBook: (data: Partial<Book>) => api.post('/library/books', data),
  updateBook: (id: string, data: Partial<Book>) => api.put(`/library/books/${id}`, data),

  // Members
  listMembers: (): Promise<LibraryMember[]> => api.get('/library/members').then(unwrap),
  createMember: (data: Partial<LibraryMember>) => api.post('/library/members', data),

  // Issues
  listIssues: (filters?: { member_id?: string; is_returned?: boolean }): Promise<BookIssue[]> =>
    api.get('/library/issues', { params: filters }).then(unwrap),
  issueBook: (data: { book_id: string; member_id: string; due_date: string; notes?: string }) =>
    api.post('/library/issues', data),
  returnBook: (issueId: string) => api.post(`/library/issues/${issueId}/return`),
  listOverdue: (): Promise<BookIssue[]> => api.get('/library/issues/overdue').then(unwrap),
};
