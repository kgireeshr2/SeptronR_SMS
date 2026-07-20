import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { ErrorBoundary } from '@components/shared/ErrorBoundary';
import ChatWidget from '@components/ui/ChatWidget';
import { useSchoolFormats } from '@hooks/useSchoolFormats';
import { registerWebPush } from '@/lib/push';

const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const { pathname } = useLocation();
  // Publish the active school's date format app-wide for formatDate()/formatDateTime().
  useSchoolFormats();
  // Subscribe this browser to Web Push (best-effort; no-ops if unsupported/unconfigured).
  React.useEffect(() => { registerWebPush(); }, []);
  // Hide the AI Assistant widget on pages that have their own message/send buttons in the same corner
  const hideChat = pathname.includes('whatsapp') || pathname.includes('communication');

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* ── Main Content ────────────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      {/* ── Chat Assistant Widget ──────────────────────────────────────── */}
      {!hideChat && <ChatWidget />}
    </div>
  );
};

export default AppLayout;
