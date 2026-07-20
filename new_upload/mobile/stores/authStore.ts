import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { User } from '@/types';
import { API_V1, TOKEN_KEY, REFRESH_TOKEN_KEY, SCHOOL_SLUG_KEY } from '@/constants';
import { authService } from '@/services/auth.service';

// Helper: normalise permissions to string[]
function parsePermissions(raw: string | string[] | undefined): string[] {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  return raw.split(/\s+/).filter(Boolean);
}

// Helper: derive a simple role string from user flags
function deriveRole(user: User): string {
  if (user.is_super_admin) return 'super_admin';
  // Heuristic: school_id present → school-level user; role comes from permissions scope
  return 'admin';
}

interface AuthState {
  user:            User | null;
  isLoading:       boolean;
  schoolSlug:      string;
  schoolName:      string;
  isAuthenticated: boolean;
  /** Derived array of permission strings e.g. ['students:view', 'fees:create'] */
  permissionSet:   string[];

  // Actions
  login:        (identifier: string, password: string, schoolSlug: string) => Promise<void>;
  logout:       () => Promise<void>;
  refreshUser:  () => Promise<void>;
  setSchoolSlug:(slug: string) => void;
  hasPermission:(module: string, action: string) => boolean;
  hasRole:      (roles: string | string[]) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user:            null,
      isLoading:       false,
      schoolSlug:      '',
      schoolName:      '',
      isAuthenticated: false,
      permissionSet:   [],

      login: async (identifier, password, schoolSlug) => {
        set({ isLoading: true });
        try {
          // Persist school slug so the request interceptor can include it
          await SecureStore.setItemAsync(SCHOOL_SLUG_KEY, schoolSlug);

          // Use native fetch so we can read Set-Cookie response header
          const baseUrl = API_V1.replace(/\/$/, '');
          const resp = await fetch(`${baseUrl}/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Accept: 'application/json',
              ...(schoolSlug ? { 'X-School-Slug': schoolSlug } : {}),
            },
            body: JSON.stringify({ identifier, password }),
          });

          if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error((err as any)?.detail ?? `Login failed (${resp.status})`);
          }

          const body = await resp.json();
          // Backend returns {success, data: {access_token, user, school}}
          const payload = body?.data ?? body;
          const accessToken: string = payload.access_token;
          const rawUser: User       = payload.user;
          const school              = payload.school ?? null;

          // Try to extract refresh token from Set-Cookie header
          // React Native fetch exposes Set-Cookie as a header value
          const setCookie = resp.headers.get('set-cookie') ?? '';
          const rtMatch   = setCookie.match(/refresh_token=([^;]+)/);
          const refreshToken = rtMatch ? rtMatch[1] : '';

          await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
          if (refreshToken) {
            await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
          }

          const permissions = parsePermissions(rawUser.permissions);

          set({
            user:            rawUser,
            isAuthenticated: true,
            schoolSlug:      school?.slug ?? schoolSlug,
            schoolName:      school?.name ?? '',
            permissionSet:   permissions,
            isLoading:       false,
          });
        } catch (err) {
          set({ isLoading: false });
          throw err;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try { await authService.logout(); } catch (_) {}
        await SecureStore.deleteItemAsync(TOKEN_KEY);
        await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
        await SecureStore.deleteItemAsync(SCHOOL_SLUG_KEY);
        set({
          user:            null,
          isAuthenticated: false,
          permissionSet:   [],
          schoolSlug:      '',
          schoolName:      '',
          isLoading:       false,
        });
      },

      refreshUser: async () => {
        try {
          const rawUser = await authService.me();
          const permissions = parsePermissions(rawUser.permissions);
          set({ user: rawUser, isAuthenticated: true, permissionSet: permissions });
        } catch (_) {
          set({ user: null, isAuthenticated: false, permissionSet: [] });
        }
      },

      setSchoolSlug: (slug) => {
        set({ schoolSlug: slug });
        SecureStore.setItemAsync(SCHOOL_SLUG_KEY, slug).catch(() => {});
      },

      hasPermission: (module, action) => {
        const { user, permissionSet } = get();
        if (!user) return false;
        if (user.is_super_admin) return true;
        return permissionSet.includes(`${module}:${action}`);
      },

      hasRole: (roles) => {
        const { user } = get();
        if (!user) return false;
        const arr = Array.isArray(roles) ? roles : [roles];
        const role = deriveRole(user);
        return arr.includes(role);
      },
    }),
    {
      name:    'auth-store',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        user:            state.user,
        isAuthenticated: state.isAuthenticated,
        schoolSlug:      state.schoolSlug,
        schoolName:      state.schoolName,
        permissionSet:   state.permissionSet,
      }),
    },
  ),
);
