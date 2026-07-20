import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Menu, Bell, ChevronDown, LogOut, User, Moon, Sun } from 'lucide-react';
import { useAuthStore } from '@store/authStore';
import { useNotificationStore } from '@store/notificationStore';
import { useAcademicYearStore } from '@store/academicYearStore';
import { getInitials, formatDateTime } from '@utils/formatters';
import { academicYearsApi } from '@api/academicYears';
import { communicationsApi } from '@api/communications';

interface NavbarProps {
  onMenuClick: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const { currentUser, logout } = useAuthStore();
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const notifications = useNotificationStore((s) => s.notifications);
  const setNotifications = useNotificationStore((s) => s.setNotifications);
  const setUnreadCount = useNotificationStore((s) => s.setUnreadCount);
  const markAsReadLocal = useNotificationStore((s) => s.markAsRead);
  const markAllReadLocal = useNotificationStore((s) => s.markAllAsRead);
  const { selectedYear, years, setSelectedYear } = useAcademicYearStore();

  const unwrap = (res: any) => res?.data ?? res;

  // Poll the in-app notification center (unread badge + list).
  useQuery({
    queryKey: ['notifications-center'],
    queryFn: async () => {
      const list = unwrap(await communicationsApi.listNotifications()) || [];
      const mapped = (Array.isArray(list) ? list : []).map((n: any) => ({
        id: n.id, title: n.title, body: n.body || '', isRead: !!n.is_read,
        type: n.type || '', createdAt: n.created_at,
        link: (n.data && (n.data.link || n.data?.link)) || undefined,
      }));
      setNotifications(mapped);
      try {
        const c = unwrap(await communicationsApi.unreadCount());
        setUnreadCount(c?.unread ?? mapped.filter((m: any) => !m.isRead).length);
      } catch { /* keep computed count */ }
      return mapped;
    },
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });

  const openNotification = async (n: { id: string; isRead: boolean; link?: string }) => {
    if (!n.isRead) {
      markAsReadLocal(n.id);
      communicationsApi.markOneRead(n.id).catch(() => undefined);
    }
    setShowNotifications(false);
    if (n.link) navigate(n.link);
  };

  const markAllRead = async () => {
    markAllReadLocal();
    communicationsApi.markAllRead().catch(() => undefined);
  };

  const [showUserMenu, setShowUserMenu] = React.useState(false);
  const [showNotifications, setShowNotifications] = React.useState(false);
  const [showYearMenu, setShowYearMenu] = React.useState(false);
  const [darkMode, setDarkMode] = React.useState(false);

  useQuery({
    queryKey: ['navbar-academic-years'],
    queryFn: async () => {
      const res: any = await academicYearsApi.list();
      const items = (res?.data ?? res) || [];
      const mapped = (Array.isArray(items) ? items : []).map((y: any) => ({
        id: y.id,
        name: y.name,
        startDate: y.start_date,
        endDate: y.end_date,
        isCurrent: y.is_current,
      }));
      if (mapped.length) {
        useAcademicYearStore.getState().setYears(mapped as any);
        const current = mapped.find((y: any) => y.isCurrent);
        if (current && !useAcademicYearStore.getState().selectedYear) {
          useAcademicYearStore.getState().setSelectedYear(current as any);
        }
      }
      return items;
    },
    staleTime: 60_000,
  });

  const handleLogout = async () => {
    logout();
    navigate('/login');
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      {/* Left: Menu button */}
      <button
        onClick={onMenuClick}
        className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 lg:hidden"
        aria-label="Open sidebar"
      >
        <Menu size={22} />
      </button>

      {/* Center: Academic Year Selector */}
      <div className="relative ml-4 hidden lg:block">
        <button
          onClick={() => setShowYearMenu(!showYearMenu)}
          className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
        >
          <span>{selectedYear?.name ?? 'Select Year'}</span>
          <ChevronDown size={14} />
        </button>

        {showYearMenu && years.length > 0 && (
          <div className="absolute left-0 top-10 z-50 w-48 rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
            {years.map((year) => (
              <button
                key={year.id}
                onClick={() => {
                  setSelectedYear(year);
                  setShowYearMenu(false);
                }}
                className={`block w-full px-4 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 ${
                  selectedYear?.id === year.id
                    ? 'font-semibold text-brand-600'
                    : 'text-gray-700 dark:text-gray-200'
                }`}
              >
                {year.name}
                {year.isCurrent && (
                  <span className="ml-2 rounded bg-green-100 px-1 text-[10px] text-green-700">
                    Current
                  </span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right: actions */}
      <div className="ml-auto flex items-center gap-2">
        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
          aria-label="Toggle dark mode"
        >
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Notifications bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
            aria-label="Notifications"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute right-1 top-1 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 top-10 z-50 w-80 rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
              <div className="flex items-center justify-between border-b border-gray-200 p-3 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-white">Notifications</h3>
                {unreadCount > 0 && (
                  <button onClick={markAllRead} className="text-xs font-medium text-brand-600 hover:underline">
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="p-4 text-center text-sm text-gray-500">No notifications</p>
                ) : (
                  notifications.map((n) => (
                    <button
                      key={n.id}
                      onClick={() => openNotification(n)}
                      className={`block w-full border-b border-gray-100 px-4 py-3 text-left hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700/50 ${
                        n.isRead ? '' : 'bg-blue-50/60 dark:bg-blue-900/10'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {!n.isRead && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-600" />}
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-gray-900 dark:text-white">{n.title}</p>
                          {n.body && <p className="mt-0.5 line-clamp-2 text-xs text-gray-500">{n.body}</p>}
                          <p className="mt-0.5 text-[10px] text-gray-400">{formatDateTime(n.createdAt)}</p>
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User avatar menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 rounded-lg p-1.5 text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700"
            aria-label="User menu"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
              {currentUser ? getInitials((currentUser as any).username ?? (currentUser as any).email ?? 'U') : 'U'}
            </div>
            <span className="hidden text-sm font-medium lg:block">
              {(currentUser as any)?.username ?? (currentUser as any)?.email ?? 'User'}
            </span>
            <ChevronDown size={14} />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 top-12 z-50 w-48 rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
              <div className="border-b border-gray-200 p-3 dark:border-gray-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {(currentUser as any)?.username ?? (currentUser as any)?.first_name ?? 'User'}
                </p>
                <p className="text-xs text-gray-500">{currentUser?.email}</p>
              </div>
              <button
                onClick={() => { navigate('/profile'); setShowUserMenu(false); }}
                className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-200 dark:hover:bg-gray-700"
              >
                <User size={14} />
                Profile
              </button>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                <LogOut size={14} />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
