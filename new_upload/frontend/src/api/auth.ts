import api from './axios';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface VerifyOtpRequest {
  phone: string;
  otp: string;
}

export const authApi = {
  login: (data: LoginRequest) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  refresh: () => api.post('/auth/refresh'),
  sendOtp: (phone: string) => api.post('/auth/send-otp', { phone }),
  verifyOtp: (data: VerifyOtpRequest) => api.post('/auth/verify-otp', data),
  forgotPassword: (email: string) => api.post('/auth/forgot-password', { email }),
  resetPassword: (data: ResetPasswordRequest) => api.post('/auth/reset-password', data),
  changePassword: (data: ChangePasswordRequest) => api.post('/auth/change-password', data),
  me: () => api.get('/auth/me'),
};
