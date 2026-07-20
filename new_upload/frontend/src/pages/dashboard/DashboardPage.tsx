import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';
import { formatDateTime } from '@utils/formatters';
import {
  CheckCircle, ArrowRight, Calendar, BookOpen,
  Users, UserCog, DollarSign, Clock, FileText, ClipboardList,
} from 'lucide-react';
import { useAuthStore } from '@store/authStore';

// ─── Types ──────────────────────────────────────────────────────────────────

interface AdminDashboard {
  total_students: number;
  total_staff: number;
  total_fee_collected_this_month: number;
  total_fee_outstanding: number;
  total_present_today: number;
  total_absent_today: number;
  attendance_pct_today: number;
  pending_leave_requests: number;
  monthly_fee_collection: { month: string; amount: number }[];
  student_by_class: { class_name: string; count: number }[];
  student_by_gender: { male: number; female: number; other: number };
  upcoming_events: { title: string; event_type: string; start_datetime: string }[];
  low_stock_alerts: { name: string; current_stock: number; reorder_level: number }[];
}

// ─── Setup Wizard ────────────────────────────────────────────────────────────

const SETUP_STEPS = [
  {
    id: 1,
    label: 'Set Academic Year',
    desc: 'Create and activate the current academic year (e.g. 2025-2026)',
    icon: <Calendar size={20} />,
    link: '/admin/academic-years',
    color: 'blue',
  },
  {
    id: 2,
    label: 'Add Classes & Sections',
    desc: 'Create grade classes (Grade 1-10) and their sections (A, B, C)',
    icon: <BookOpen size={20} />,
    link: '/admin/classes',
    color: 'purple',
  },
  {
    id: 3,
    label: 'Add Staff',
    desc: 'Register teachers, principals, and administrative staff',
    icon: <UserCog size={20} />,
    link: '/admin/staff',
    color: 'orange',
  },
  {
    id: 4,
    label: 'Enroll Students',
    desc: 'Register students and assign them to classes and sections',
    icon: <Users size={20} />,
    link: '/admin/students',
    color: 'green',
  },
  {
    id: 5,
    label: 'Configure Fees',
    desc: 'Set up fee categories, structures, and assign fee plans per class',
    icon: <DollarSign size={20} />,
    link: '/admin/fees',
    color: 'yellow',
  },
  {
    id: 6,
    label: 'Build Timetable',
    desc: 'Assign subjects and teachers to time slots for each section',
    icon: <Clock size={20} />,
    link: '/admin/timetable',
    color: 'teal',
  },
  {
    id: 7,
    label: 'Create Exams',
    desc: 'Schedule exam types, subjects, and configure mark sheets',
    icon: <FileText size={20} />,
    link: '/admin/exams',
    color: 'red',
  },
  {
    id: 8,
    label: 'Manage Attendance',
    desc: 'Track daily student and staff attendance by section',
    icon: <ClipboardList size={20} />,
    link: '/admin/attendance',
    color: 'indigo',
  },
];

const colorMap: Record<string, string> = {
  blue:   'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
  purple: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
  orange: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400',
  green:  'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
  yellow: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400',
  teal:   'bg-teal-100 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400',
  red:    'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
  indigo: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400',
};

const SetupChecklist: React.FC<{ completedSteps: number }> = ({ completedSteps }) => (
  <div className="mb-8 rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-6 dark:border-blue-800 dark:from-blue-900/20 dark:to-indigo-900/20">
    <div className="mb-4 flex items-center justify-between">
      <div>
        <h2 className="text-lg font-bold text-gray-900 dark:text-white">
          🚀 School Setup Progress
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {completedSteps}/{SETUP_STEPS.length} steps complete — follow these steps to get your school running
        </p>
      </div>
      <div className="flex items-center gap-2">
        <div className="h-2 w-32 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all"
            style={{ width: `${(completedSteps / SETUP_STEPS.length) * 100}%` }}
          />
        </div>
        <span className="text-sm font-semibold text-indigo-600">
          {Math.round((completedSteps / SETUP_STEPS.length) * 100)}%
        </span>
      </div>
    </div>

    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {SETUP_STEPS.map((step, idx) => {
        const done = idx < completedSteps;
        const active = idx === completedSteps;
        return (
          <Link
            key={step.id}
            to={step.link}
            className={`group relative flex flex-col rounded-xl border p-4 transition-all hover:shadow-md ${
              done
                ? 'border-green-200 bg-white opacity-70 dark:border-green-800 dark:bg-gray-800'
                : active
                ? 'border-indigo-300 bg-white shadow-sm ring-2 ring-indigo-200 dark:border-indigo-600 dark:bg-gray-800 dark:ring-indigo-800'
                : 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'
            }`}
          >
            <div className="mb-3 flex items-center justify-between">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                  done ? 'bg-green-100 text-green-600 dark:bg-green-900/30' : colorMap[step.color]
                }`}
              >
                {done ? <CheckCircle size={18} /> : step.icon}
              </div>
              <span
                className={`text-xs font-bold ${
                  done ? 'text-green-600' : active ? 'text-indigo-600' : 'text-gray-400'
                }`}
              >
                Step {step.id}
              </span>
            </div>
            <p
              className={`text-sm font-semibold ${
                done ? 'text-gray-500 line-through' : 'text-gray-900 dark:text-white'
              }`}
            >
              {step.label}
            </p>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{step.desc}</p>
            {active && (
              <div className="mt-3 flex items-center gap-1 text-xs font-semibold text-indigo-600">
                Start now{' '}
                <ArrowRight size={12} className="transition-transform group-hover:translate-x-1" />
              </div>
            )}
            {done && (
              <div className="mt-3 flex items-center gap-1 text-xs font-medium text-green-600">
                <CheckCircle size={12} /> Completed
              </div>
            )}
          </Link>
        );
      })}
    </div>
  </div>
);

// ─── Helpers ─────────────────────────────────────────────────────────────────

const formatCurrency = (n: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(n);

const StatCard: React.FC<{
  label: string;
  value: string | number;
  sub?: string;
}> = ({ label, value, sub }) => (
  <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
    <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
      {label}
    </p>
    <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
    {sub && <p className="mt-0.5 text-xs text-gray-500">{sub}</p>}
  </div>
);

// ─── Page Component ───────────────────────────────────────────────────────────

const Page: React.FC = () => {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'finance' | 'alerts'>('overview');
  const schoolInfo = useAuthStore(s => s.schoolInfo);

  useEffect(() => {
    setLoading(true);
    api
      .get('/dashboard/admin')
      .then((r: any) => setData(r.data ?? r))
      .catch(() => {
        /* show setup wizard when dashboard data unavailable */
      })
      .finally(() => setLoading(false));
  }, [schoolInfo?.id]);

  // Compute how many setup steps are done based on API data
  const completedSteps = (() => {
    if (!data) return 0;
    let count = 0;
    if (data.total_students > 0 || data.total_staff > 0) count = 1; // AY set
    if (data.total_staff > 0) count = Math.max(count, 2);            // classes done
    if (data.total_staff > 0) count = Math.max(count, 3);            // staff added
    if (data.total_students > 0) count = Math.max(count, 4);         // students enrolled
    if (data.total_fee_collected_this_month > 0 || data.total_fee_outstanding > 0)
      count = Math.max(count, 5);                                     // fee structures
    if (data.student_by_class && data.student_by_class.length > 0)
      count = Math.max(count, 6);                                     // timetable (proxy: class data available)
    if (data.total_students > 0 && count >= 6)
      count = Math.max(count, 7);                                     // exams (proxy: students + classes done)
    if (data.total_present_today > 0 || data.total_absent_today > 0)
      count = Math.max(count, 8);                                     // attendance tracked
    return count;
  })();

  const isNewSchool = !data || (data.total_students === 0 && data.total_staff === 0);

  // ── Loading state ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div>
        <PageHeader title="Dashboard" />
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={schoolInfo?.name ? `Welcome to ${schoolInfo.name}` : undefined}
      />

      {/* Setup wizard — always shown; fades when all steps done */}
      <SetupChecklist completedSteps={completedSteps} />

      {/* KPI + tabs only when the school has meaningful data */}
      {!isNewSchool && data && (
        <>
          {/* KPI Cards */}
          <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Total Students" value={data.total_students.toLocaleString()} />
            <StatCard label="Total Staff" value={data.total_staff.toLocaleString()} />
            <StatCard
              label="Attendance Today"
              value={`${data.attendance_pct_today}%`}
              sub={`${data.total_present_today} present, ${data.total_absent_today} absent`}
            />
            <StatCard
              label="Pending Leave"
              value={data.pending_leave_requests}
              sub="Awaiting approval"
            />
          </div>

          {/* Tab switcher */}
          <div className="mb-5 flex gap-2 border-b border-gray-200 dark:border-gray-700">
            {(['overview', 'finance', 'alerts'] as const).map(t => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                className={`border-b-2 px-4 py-2 text-sm font-medium capitalize transition-colors ${
                  activeTab === t
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {/* ── Overview Tab ──────────────────────────────────────────────── */}
          {activeTab === 'overview' && (
            <div className="grid gap-5 lg:grid-cols-2">
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h3 className="mb-3 font-semibold text-gray-900 dark:text-white">
                  Students by Class
                </h3>
                <div className="space-y-2">
                  {data.student_by_class.length === 0 ? (
                    <p className="text-sm text-gray-500">No data available.</p>
                  ) : (
                    data.student_by_class.map(item => {
                      const max = Math.max(...data.student_by_class.map(c => c.count));
                      const pct = max > 0 ? (item.count / max) * 100 : 0;
                      return (
                        <div key={item.class_name} className="flex items-center gap-3">
                          <span className="w-20 truncate text-xs text-gray-600 dark:text-gray-400">
                            {item.class_name}
                          </span>
                          <div className="h-4 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
                            <div
                              className="h-4 rounded-full bg-blue-500"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="w-8 text-right text-xs font-medium">{item.count}</span>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h3 className="mb-3 font-semibold text-gray-900 dark:text-white">
                  Gender Breakdown
                </h3>
                <div className="flex items-center gap-4">
                  {[
                    { label: 'Male', count: data.student_by_gender.male, color: 'bg-blue-500' },
                    { label: 'Female', count: data.student_by_gender.female, color: 'bg-pink-500' },
                    { label: 'Other', count: data.student_by_gender.other, color: 'bg-gray-400' },
                  ].map(g => {
                    const total = data.total_students || 1;
                    return (
                      <div key={g.label} className="flex-1 text-center">
                        <div
                          className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full text-lg font-bold text-white ${g.color}`}
                        >
                          {Math.round((g.count / total) * 100)}%
                        </div>
                        <p className="mt-2 text-sm font-medium">{g.label}</p>
                        <p className="text-xs text-gray-500">{g.count}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800 lg:col-span-2">
                <h3 className="mb-3 font-semibold text-gray-900 dark:text-white">
                  Upcoming Events
                </h3>
                {data.upcoming_events.length === 0 ? (
                  <p className="text-sm text-gray-500">No upcoming events.</p>
                ) : (
                  <div className="divide-y divide-gray-100 dark:divide-gray-700">
                    {data.upcoming_events.map((ev, i) => (
                      <div key={i} className="flex items-center justify-between py-2">
                        <div>
                          <p className="text-sm font-medium">{ev.title}</p>
                          <p className="text-xs text-gray-500">
                            {formatDateTime(ev.start_datetime)}
                          </p>
                        </div>
                        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs capitalize text-blue-700">
                          {ev.event_type}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Finance Tab ───────────────────────────────────────────────── */}
          {activeTab === 'finance' && (
            <div className="grid gap-5 md:grid-cols-2">
              <StatCard
                label="Fee Collected This Month"
                value={formatCurrency(data.total_fee_collected_this_month)}
              />
              <StatCard
                label="Total Fee Outstanding"
                value={formatCurrency(data.total_fee_outstanding)}
                sub="Across all students"
              />
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800 md:col-span-2">
                <h3 className="mb-4 font-semibold text-gray-900 dark:text-white">
                  Monthly Fee Collection (Last 6 Months)
                </h3>
                {data.monthly_fee_collection.length === 0 ? (
                  <p className="text-sm text-gray-500">No fee records found.</p>
                ) : (
                  <div className="space-y-3">
                    {data.monthly_fee_collection.map(m => {
                      const max =
                        Math.max(...data.monthly_fee_collection.map(x => x.amount)) || 1;
                      return (
                        <div key={m.month} className="flex items-center gap-4">
                          <span className="w-20 text-xs text-gray-600 dark:text-gray-400">
                            {m.month}
                          </span>
                          <div className="h-5 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
                            <div
                              className="flex h-5 items-center justify-end rounded-full bg-green-500 pr-2"
                              style={{ width: `${(m.amount / max) * 100}%` }}
                            >
                              <span className="text-xs font-medium text-white">
                                {formatCurrency(m.amount)}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Alerts Tab ────────────────────────────────────────────────── */}
          {activeTab === 'alerts' && (
            <div className="grid gap-5 lg:grid-cols-2">
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h3 className="mb-3 font-semibold dark:text-white">Low Stock Alerts</h3>
                {data.low_stock_alerts.length === 0 ? (
                  <p className="text-sm text-gray-500">No low stock items.</p>
                ) : (
                  data.low_stock_alerts.map((item, i) => (
                    <div
                      key={i}
                      className="mb-2 flex items-center justify-between rounded-lg bg-red-50 px-3 py-2 dark:bg-red-900/20"
                    >
                      <span className="text-sm font-medium">{item.name}</span>
                      <span className="text-xs text-red-600">
                        {item.current_stock} / {item.reorder_level}
                      </span>
                    </div>
                  ))
                )}
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h3 className="mb-3 font-semibold dark:text-white">Leave Requests</h3>
                <div className="flex h-24 items-center justify-center">
                  <div className="text-center">
                    <p className="text-4xl font-bold text-yellow-600">
                      {data.pending_leave_requests}
                    </p>
                    <p className="mt-1 text-sm text-gray-500">Pending approval</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Page;
