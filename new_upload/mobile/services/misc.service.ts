import api from './api';

export const transportService = {
  getMyRoute: () =>
    api.get('/transport/my-route').then((r) => r.data),

  getVehicles: () =>
    api.get('/transport/vehicles').then((r) => r.data),

  getRoutes: () =>
    api.get('/transport/routes').then((r) => r.data),

  getStudentTransport: (studentId: string) =>
    api.get(`/transport/student/${studentId}`).then((r) => r.data),
};

export const libraryService = {
  searchBooks: (query: string, category_id?: string) =>
    api.get('/library/books', { params: { search: query, category_id } }).then((r) => r.data),

  getMyIssuedBooks: () =>
    api.get('/library/issues/my').then((r) => r.data),

  getCategories: () =>
    api.get('/library/categories').then((r) => r.data),
};

export const calendarService = {
  getEvents: (start: string, end: string) =>
    api.get('/calendar', { params: { start, end } }).then((r) => r.data),

  getHolidays: (academic_year_id?: string) =>
    api.get('/holidays', { params: { academic_year_id } }).then((r) => r.data),
};
