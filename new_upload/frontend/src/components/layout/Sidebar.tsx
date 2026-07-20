import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, GraduationCap, Users, UserCog, Calendar,
  ClipboardList, DollarSign, BookOpen, Bus, Package, Calculator,
  MessageSquare, CalendarDays, BookMarked, Handshake, BarChart2,
  FileText, Settings, Shield, X, School, ChevronLeft, Layout,
  Banknote, CalendarCheck, KeyRound, Smartphone, ShoppingBag, Globe,
} from 'lucide-react';
import { usePermission } from '@hooks/usePermission';
import { useAuthStore } from '@store/authStore';

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
  module: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'MAIN',
    items: [
      { label: 'Dashboard', to: '/dashboard', icon: <LayoutDashboard size={16} />, module: 'dashboard' },
    ],
  },
  {
    title: 'ACADEMIC',
    items: [
      { label: 'Academic Years', to: '/admin/academic-years', icon: <Calendar size={16} />, module: 'academic_years' },
      { label: 'Admissions', to: '/admin/admissions', icon: <ClipboardList size={16} />, module: 'admissions' },
      { label: 'Classes & Sections', to: '/admin/classes', icon: <GraduationCap size={16} />, module: 'classes' },
      { label: 'Subjects', to: '/admin/subjects', icon: <BookMarked size={16} />, module: 'subjects' },
      { label: 'Timetable', to: '/admin/timetable', icon: <CalendarDays size={16} />, module: 'timetable' },
    ],
  },
  {
    title: 'PEOPLE',
    items: [
      { label: 'Students', to: '/admin/students', icon: <Users size={16} />, module: 'students' },
      { label: 'Staff', to: '/admin/staff', icon: <UserCog size={16} />, module: 'staff' },
      { label: 'Payroll', to: '/admin/payroll', icon: <Banknote size={16} />, module: 'payroll' },
      { label: 'Leave Management', to: '/admin/leaves', icon: <CalendarCheck size={16} />, module: 'leaves' },
    ],
  },
  {
    title: 'OPERATIONS',
    items: [
      { label: 'Attendance', to: '/admin/attendance', icon: <ClipboardList size={16} />, module: 'attendance' },
      { label: 'Fees', to: '/admin/fees', icon: <DollarSign size={16} />, module: 'fees' },
      { label: 'Advanced Fees', to: '/admin/fees-advanced', icon: <DollarSign size={16} />, module: 'fees' },
      { label: 'Personal Expenses', to: '/admin/personal-expenses', icon: <DollarSign size={16} />, module: 'fees' },
      { label: 'Exams', to: '/admin/exams', icon: <BookOpen size={16} />, module: 'exams' },
      { label: 'Library', to: '/admin/library', icon: <BookOpen size={16} />, module: 'library' },
      { label: 'Transport', to: '/admin/transport', icon: <Bus size={16} />, module: 'transport' },
      { label: 'Inventory', to: '/admin/inventory', icon: <Package size={16} />, module: 'inventory' },
      { label: 'Vendor Inventory', to: '/admin/vendor-inventory', icon: <ShoppingBag size={16} />, module: 'vendor_inventory' },
      { label: 'Accounting', to: '/admin/accounting', icon: <Calculator size={16} />, module: 'accounting' },
    ],
  },
  {
    title: 'COMMUNICATION',
    items: [
      { label: 'Messages', to: '/admin/communication', icon: <MessageSquare size={16} />, module: 'communication' },
      { label: 'WA Simulator', to: '/admin/whatsapp-test', icon: <Smartphone size={16} />, module: 'communication' },
      { label: 'Calendar', to: '/admin/calendar', icon: <CalendarDays size={16} />, module: 'calendar' },
      { label: 'Homework', to: '/admin/homework', icon: <BookMarked size={16} />, module: 'homework' },
      { label: 'PTM', to: '/admin/ptm', icon: <Handshake size={16} />, module: 'ptm' },
    ],
  },
  {
    title: 'ADMIN',
    items: [
      { label: 'Website', to: '/admin/website', icon: <Globe size={16} />, module: 'website' },
      { label: 'Reports', to: '/admin/reports', icon: <BarChart2 size={16} />, module: 'reports' },
      { label: 'Audit Logs', to: '/admin/audit-logs', icon: <FileText size={16} />, module: 'audit' },
      { label: 'Templates', to: '/admin/templates', icon: <Layout size={16} />, module: 'settings' },
      { label: 'Credentials', to: '/admin/credentials', icon: <KeyRound size={16} />, module: 'settings' },
      { label: 'Settings', to: '/admin/settings', icon: <Settings size={16} />, module: 'settings' },
      { label: 'Roles & Perms', to: '/admin/roles', icon: <Shield size={16} />, module: 'roles' },
    ],
  },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { hasPermission } = usePermission();
  const { schoolInfo, currentUser, setSchool } = useAuthStore();
  const navigate = useNavigate();
  const isSuperAdmin = currentUser?.is_super_admin ?? false;

  const handleBackToSuperAdmin = () => {
    // Atomic clear: drops schoolInfo + X-School-Id, resets the academic year,
    // and clears the React Query cache so no school's data lingers.
    setSchool(null);
    onClose();
    navigate('/super-admin/dashboard');
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-sidebar-bg
          transition-transform duration-300 ease-in-out
          lg:relative lg:translate-x-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Logo / School name */}
        <div className="flex h-16 items-center justify-between border-b border-slate-700 px-4">
          <div className="flex items-center gap-2">
            <School size={24} className="text-brand-400" />
            <span className="truncate text-sm font-semibold text-white">
              {schoolInfo?.name ?? 'SeptroSchool'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white lg:hidden"
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        {/* Super Admin back button */}
        {isSuperAdmin && (
          <button
            onClick={handleBackToSuperAdmin}
            className="flex w-full items-center gap-2 border-b border-slate-700 bg-indigo-900/40 px-4 py-2 text-xs font-medium text-indigo-300 hover:bg-indigo-900/60 hover:text-white transition-colors"
          >
            <ChevronLeft size={14} />
            Back to Super Admin Panel
          </button>
        )}

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4">
          {NAV_GROUPS.map((group) => {
            const visibleItems = group.items.filter((item) =>
              hasPermission(item.module, 'view')
            );
            if (visibleItems.length === 0) return null;

            return (
              <div key={group.title} className="mb-4">
                <p className="mb-1 px-4 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                  {group.title}
                </p>
                {visibleItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                        isActive
                          ? 'bg-sidebar-active text-white font-medium'
                          : 'text-sidebar-text hover:bg-sidebar-hover hover:text-white'
                      }`
                    }
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            );
          })}
        </nav>

        {/* Version */}
        <div className="border-t border-slate-700 px-4 py-3 text-[10px] text-slate-600">
          v1.0.0
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
