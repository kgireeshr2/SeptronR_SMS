import axios, { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { API_V1, TOKEN_KEY, REFRESH_TOKEN_KEY, SCHOOL_SLUG_KEY } from '@/constants';

// ─── Create axios instance ────────────────────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: API_V1,
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ─── Request interceptor — inject Bearer token + school slug ──────────────────
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await SecureStore.getItemAsync(TOKEN_KEY);
    const slug  = await SecureStore.getItemAsync(SCHOOL_SLUG_KEY);
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    if (slug) {
      config.headers['X-School-Slug'] = slug;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ─── Response interceptor — unwrap {success, data} envelope ──────────────────
// Some endpoints return {success:true, data: T, message, pagination}
// Others return raw arrays or objects directly.
// This interceptor normalises: if the envelope shape is detected, unwrap it.
api.interceptors.response.use(
  (response) => {
    const body = response.data;
    if (
      body !== null &&
      typeof body === 'object' &&
      !Array.isArray(body) &&
      'success' in body &&
      body.success === true &&
      'data' in body
    ) {
      response.data = body.data;
    }
    return response;
  },
  // error path handled below in the 401/refresh interceptor
  (error) => Promise.reject(error),
);

// ─── Track whether we're already refreshing ──────────────────────────────────
let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  failedQueue = [];
};

// ─── 401 interceptor — silent token refresh on unauthorized ──────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest: AxiosRequestConfig & { _retry?: boolean } = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers = {
            ...(originalRequest.headers ?? {}),
            Authorization: `Bearer ${token}`,
          };
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
        if (!refreshToken) throw new Error('No refresh token');

        // Backend reads from Cookie header only (HttpOnly cookie)
        const { data } = await axios.post(
          `${API_V1}/auth/refresh`,
          {},
          {
            headers: {
              Cookie: `refresh_token=${refreshToken}`,
            },
          },
        );

        // After envelope unwrapping the interceptor already ran on this instance,
        // but we used a bare axios call — handle both wrapped and unwrapped shapes:
        const newAccessToken: string =
          data?.access_token ?? data?.data?.access_token ?? data;

        if (!newAccessToken) throw new Error('No access token in refresh response');

        await SecureStore.setItemAsync(TOKEN_KEY, newAccessToken);
        processQueue(null, newAccessToken);

        originalRequest.headers = {
          ...(originalRequest.headers ?? {}),
          Authorization: `Bearer ${newAccessToken}`,
        };
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        await SecureStore.deleteItemAsync(TOKEN_KEY);
        await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
        authEventEmitter.emit('logout');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

// ─── Simple event emitter for auth events ────────────────────────────────────
type Listener = () => void;
const listeners: Record<string, Listener[]> = {};
export const authEventEmitter = {
  on:   (event: string, fn: Listener) => { listeners[event] = [...(listeners[event] ?? []), fn]; },
  off:  (event: string, fn: Listener) => { listeners[event] = (listeners[event] ?? []).filter((l) => l !== fn); },
  emit: (event: string)               => { (listeners[event] ?? []).forEach((fn) => fn()); },
};

export default api;
