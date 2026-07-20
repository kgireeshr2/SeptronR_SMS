import api from './api';
import { LoginRequest, LoginResponse } from '@/types';

export const authService = {
  /** Backend expects `identifier` (email or username), not `username` */
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/auth/login', {
      identifier: data.identifier,
      password:   data.password,
    }).then((r) => r.data),

  /** Refresh is handled via Cookie header in api.ts interceptor */
  refreshToken: () =>
    api.post<{ access_token: string }>('/auth/refresh', {}).then((r) => r.data),

  logout: () =>
    api.post('/auth/logout').catch(() => {}),

  sendOtp: (identifier: string, schoolSlug: string) =>
    api.post('/auth/send-otp', { identifier, schoolSlug }).then((r) => r.data),

  verifyOtp: (identifier: string, otp: string, schoolSlug: string) =>
    api.post('/auth/verify-otp', { identifier, otp, schoolSlug }).then((r) => r.data),

  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }).then((r) => r.data),

  resetPassword: (token: string, newPassword: string) =>
    api.post('/auth/reset-password', { token, new_password: newPassword }).then((r) => r.data),

  changePassword: (oldPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }).then((r) => r.data),

  registerFcmToken: (fcmToken: string) =>
    api.post('/devices/register', { token: fcmToken, provider: 'expo', platform: 'mobile' }).then((r) => r.data),

  /** Returns User object (envelope auto-unwrapped by interceptor) */
  me: () =>
    api.get('/auth/me').then((r) => r.data),
};
