import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { Shield, LogOut, Sun, Moon } from 'lucide-react';
import { useAuthStore } from '@store/authStore';
import { authApi } from '@api/auth';
import { ErrorBoundary } from '@components/shared/ErrorBoundary';

const SuperAdminLayout: React.FC = () => {
  const { currentUser, logout } = useAuthStore();
  const navigate = useNavigate();
  const [dark, setDark] = React.useState(
    () => document.documentElement.classList.contains('dark')
  );

  const toggleDark = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle('dark', next);
  };

  const handleLogout = async () => {
    try { await authApi.logout(); } catch { /* ignore */ }
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Top navbar */}
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600">
            <Shield size={18} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-gray-900 dark:text-white">Super Admin Panel</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">SeptroSchool</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleDark}
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-700 dark:hover:text-white"
            aria-label="Toggle dark mode"
          >
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300">
              {(currentUser?.username ?? 'S')[0].toUpperCase()}
            </div>
            <span className="hidden text-sm font-medium text-gray-700 dark:text-gray-300 sm:block">
              {currentUser?.username ?? 'Super Admin'}
            </span>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:bg-red-50 hover:border-red-200 hover:text-red-600 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-red-900/20 dark:hover:text-red-400"
          >
            <LogOut size={14} />
            Logout
          </button>
        </div>
      </header>

      {/* Page content */}
      <main className="mx-auto max-w-7xl p-6">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  );
};

export default SuperAdminLayout;
