import api from './api';
import { FeeInvoice, PaginatedResponse, PaginationParams } from '@/types';

export const feesService = {
  getStructures: (params?: PaginationParams & { class_id?: string; academic_year_id?: string }) =>
    api.get<FeeInvoice[]>('/fees/structures', { params }).then((r) => r.data),

  getInvoices: (params: PaginationParams & { student_id?: string; status?: string }) =>
    api.get<PaginatedResponse<FeeInvoice> | FeeInvoice[]>('/fees/invoices', { params }).then((r) => r.data),

  getInvoice: (id: string) =>
    api.get<FeeInvoice>(`/fees/invoices/${id}`).then((r) => r.data),

  getMyInvoices: () =>
    api.get<FeeInvoice[]>('/fees/my-invoices').then((r) => r.data),

  getCollectionSummary: (month?: number, year?: number) =>
    api.get('/fees/collection-summary', { params: { month, year } }).then((r) => r.data),

  downloadInvoicePdf: (id: string) =>
    api.get(`/fees/invoices/${id}/pdf`, { responseType: 'blob' }).then((r) => r.data),
};
