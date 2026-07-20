import api from './axios';

export const homeworkApi = {
  // Homework
  list: (params?: { class_id?: string; subject_id?: string; due_from?: string; due_to?: string; skip?: number; limit?: number }) =>
    api.get('/homework', { params }),
  create: (data: Record<string, unknown>) =>
    api.post('/homework', data),
  get: (id: string) =>
    api.get(`/homework/${id}`),
  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/homework/${id}`, data),
  delete: (id: string) =>
    api.delete(`/homework/${id}`),

  // Submissions
  listSubmissions: (homeworkId: string, params?: { student_id?: string }) =>
    api.get(`/homework/${homeworkId}/submissions`, { params }),
  submitHomework: (homeworkId: string, data: Record<string, unknown>) =>
    api.post(`/homework/${homeworkId}/submissions`, data),
  gradeSubmission: (homeworkId: string, subId: string, data: { marks_given: number; remarks?: string }) =>
    api.put(`/homework/${homeworkId}/submissions/${subId}/grade`, data),

  // Lesson Plans
  listLessonPlans: (params?: { class_id?: string; subject_id?: string; from_date?: string; to_date?: string; skip?: number; limit?: number }) =>
    api.get('/lesson-plans', { params }),
  createLessonPlan: (data: Record<string, unknown>) =>
    api.post('/lesson-plans', data),
  updateLessonPlan: (id: string, data: Record<string, unknown>) =>
    api.put(`/lesson-plans/${id}`, data),
  deleteLessonPlan: (id: string) =>
    api.delete(`/lesson-plans/${id}`),

  // PTM Events
  listPTMEvents: (params?: { academic_year_id?: string; skip?: number; limit?: number }) =>
    api.get('/ptm/events', { params }),
  createPTMEvent: (data: Record<string, unknown>) =>
    api.post('/ptm/events', data),
  updatePTMEvent: (id: string, data: Record<string, unknown>) =>
    api.put(`/ptm/events/${id}`, data),

  // PTM Slots
  listSlots: (eventId: string) =>
    api.get(`/ptm/events/${eventId}/slots`),
  createSlot: (eventId: string, data: Record<string, unknown>) =>
    api.post(`/ptm/events/${eventId}/slots`, data),

  // PTM Bookings
  bookSlot: (slotId: string, data: Record<string, unknown>) =>
    api.post(`/ptm/slots/${slotId}/book`, data),
  cancelBooking: (bookingId: string) =>
    api.delete(`/ptm/bookings/${bookingId}`),
  myBookings: (params?: { student_id?: string }) =>
    api.get('/ptm/bookings/mine', { params }),
};
