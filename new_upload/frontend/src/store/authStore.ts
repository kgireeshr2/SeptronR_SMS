import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { queryClient } from '@/lib/queryClient';
import { useAcademicYearStore } from '@store/academicYearStore';

export interface CurrentUser {
  id: string;
  school_id?: string | null;
  username?: string | null;
  email?: string | null;
  phone?: string | null;
  avatar_url?: string | null;
  is_super_admin: boolean;
  is_active: boolean;
  is_verified: boolean;
  last_login?: string | null;
  created_at: string;
  permissions: string[];
}

export interface SchoolInfo {
  id: string;
  name: string;
  slug: string;
  logo_url?: string | null;
}

interface AuthState {
  accessToken: string | null;
  currentUser: CurrentUser | null;
  schoolInfo: SchoolInfo | null;
  permissions: string[]; // format: "module:action"
  isAuthenticated: boolean;
  setAccessToken: (token: string) => void;
  setUser: (user: CurrentUser, school: SchoolInfo | null, permissions: string[]) => void;
  /** Switch the active school (super-admin manage/impersonate) without touching the user. */
  setSchool: (school: SchoolInfo | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      currentUser: null,
      schoolInfo: null,
      permissions: [],
      isAuthenticated: false,

      setAccessToken: (token) =>
        set({ accessToken: token, isAuthenticated: true }),

      setUser: (user, school, permissions) =>
        set({
          currentUser: user,
          schoolInfo: school,
          permissions,
          isAuthenticated: true,
        }),

      // Atomic active-school switch: update the single source of truth for the
      // X-School-Id header, keep the legacy localStorage key in sync, and wipe
      // any tenant-scoped state so no previous school's data can bleed through.
      setSchool: (school) => {
        if (school) localStorage.setItem('sms-school-id', school.id);
        else localStorage.removeItem('sms-school-id');
        useAcademicYearStore.getState().reset();
        queryClient.clear();
        set({ schoolInfo: school });
      },

      logout: () => {
        localStorage.removeItem('sms-school-id');
        useAcademicYearStore.getState().reset();
        queryClient.clear();
        set({
          accessToken: null,
          currentUser: null,
          schoolInfo: null,
          permissions: [],
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'sms-auth',
      // SECURITY: the access token is deliberately NOT persisted — keeping it out of
      // localStorage prevents XSS token theft. It lives in memory only; on reload the
      // axios layer silently refreshes it via the httpOnly refresh cookie (401 → /auth/refresh).
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        currentUser: state.currentUser,
        schoolInfo: state.schoolInfo,
        permissions: state.permissions,
      }),
    }
  )
);
