import React, { Suspense, useEffect } from 'react';
import AppRoutes from './routes';
import { useAuthStore } from '@store/authStore';
import apiClient from '@/api/axios';

const App: React.FC = () => {
  const { accessToken, setUser, currentUser, schoolInfo } = useAuthStore();

  // Refresh permissions from server on every app load so new permissions
  // seeded after login are picked up without re-login.
  useEffect(() => {
    if (!accessToken || !currentUser) return;
    apiClient.get('/auth/me').then(res => {
      const u = res.data?.data ?? res.data;
      if (u) setUser(u, schoolInfo, u.permissions ?? []);
    }).catch(() => { /* silent — user stays logged in with cached permissions */ });
  }, []);

  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
        </div>
      }
    >
      <AppRoutes />
    </Suspense>
  );
};

export default App;
