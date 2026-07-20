import api from './api';
import { Announcement, AppNotification, PaginatedResponse, PaginationParams } from '@/types';

export const announcementsService = {
  list: (params: PaginationParams) =>
    api.get<PaginatedResponse<Announcement>>('/announcements', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Announcement>(`/announcements/${id}`).then((r) => r.data),

  markRead: (id: string) =>
    api.patch(`/announcements/${id}/read`).then((r) => r.data),
};

export const notificationsService = {
  list: (params: PaginationParams) =>
    api.get<PaginatedResponse<AppNotification>>('/notifications', { params }).then((r) => r.data),

  markRead: (id: string) =>
    api.patch(`/notifications/${id}/read`).then((r) => r.data),

  markAllRead: () =>
    api.patch('/notifications/read-all').then((r) => r.data),

  getUnreadCount: () =>
    api.get<{ count: number }>('/notifications/unread-count').then((r) => r.data),
};
