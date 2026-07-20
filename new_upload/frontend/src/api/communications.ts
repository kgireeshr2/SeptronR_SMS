import api from './axios';

export interface NotificationTemplate {
  id: string;
  school_id: string;
  name: string;
  event_trigger: string;
  channels: string[];
  subject?: string | null;
  body_template: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export const communicationsApi = {
  // Notification Templates
  listTemplates: (params?: { event_type?: string; is_active?: boolean }) =>
    api.get<NotificationTemplate[]>('/communications/templates', { params }),
  createTemplate: (data: Record<string, unknown>) =>
    api.post<NotificationTemplate>('/communications/templates', data),
  updateTemplate: (id: string, data: Record<string, unknown>) =>
    api.put<NotificationTemplate>(`/communications/templates/${id}`, data),
  setDefaultTemplate: (id: string) =>
    api.post<NotificationTemplate>(`/communications/templates/${id}/set-default`),
  deleteTemplate: (id: string) =>
    api.delete(`/communications/templates/${id}`),

  // Notifications (in-app center) — contract shared with the mobile app
  listNotifications: (params?: { unread_only?: boolean }) =>
    api.get('/notifications', { params }),
  unreadCount: () => api.get<{ unread: number }>('/notifications/unread-count'),
  createNotification: (data: Record<string, unknown>) =>
    api.post('/notifications', data),
  markRead: (ids: string[]) =>
    api.post('/notifications/mark-read', { notification_ids: ids }),
  markOneRead: (id: string) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch('/notifications/read-all'),

  // Notification preferences (per-user opt-out)
  getPreferences: () => api.get('/notifications/preferences'),
  setPreferences: (prefs: Array<{ channel: string; event_trigger: string; enabled: boolean }>) =>
    api.put('/notifications/preferences', prefs),

  // Device tokens (push)
  registerDevice: (data: { token: string; provider: string; platform?: string }) =>
    api.post('/devices/register', data),
  unregisterDevice: (token: string) => api.post('/devices/unregister', { token, provider: 'webpush' }),
  getWebPushKey: () => api.get<{ public_key: string }>('/devices/web-push-key'),

  // Bulk Messages
  listBulkMessages: (params?: { skip?: number; limit?: number }) =>
    api.get('/communications/bulk-messages', { params }),
  createBulkMessage: (data: Record<string, unknown>) =>
    api.post('/communications/bulk-messages', data),
  getBulkMessage: (id: string) =>
    api.get(`/communications/bulk-messages/${id}`),

  // Delivery reports (MessageLog)
  listMessageLogs: (params?: { channel?: string; msg_status?: string; limit?: number }) =>
    api.get('/communications/message-logs', { params }),

  // Announcements
  listAnnouncements: (params?: { active_only?: boolean }) =>
    api.get('/announcements', { params }),
  createAnnouncement: (data: Record<string, unknown>) =>
    api.post('/announcements', data),
  updateAnnouncement: (id: string, data: Record<string, unknown>) =>
    api.put(`/announcements/${id}`, data),
  deleteAnnouncement: (id: string) =>
    api.delete(`/announcements/${id}`),
};
