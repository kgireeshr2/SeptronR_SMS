import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';
import { formatDate } from '@utils/formatters';

type Tab = 'overview' | 'attendance' | 'homework' | 'fees' | 'results';

interface ChildInfo {
  id: string;
  name: string;
  admission_number: string;
  class_name?: string;
  section_name?: string;
  profile_photo?: string;
}

interface AttendanceSummary {
  present_days: number;
  absent_days: number;
  total_days: number;
  attendance_pct: number;
}

interface HomeworkItem {
  id: string;
  title: string;
  subject_id: string;
  due_date: string;
}

interface FeeInvoice {
  id: string;
  invoice_number: string;
  total_amount_paise: number;
  balance_paise: number;
  due_date: string;
  status: string;
}

const fmt = (paise: number) => `₹${(paise / 100).toLocaleString('en-IN')}`;

const Page: React.FC = () => {
  const [tab, setTab] = useState<Tab>('overview');
  const [child, setChild] = useState<ChildInfo | null>(null);
  const [attendance, setAttendance] = useState<AttendanceSummary | null>(null);
  const [homework, setHomework] = useState<HomeworkItem[]>([]);
  const [fees, setFees] = useState<FeeInvoice[]>([]);
  const [announcements, setAnnouncements] = useState<{ title: string; body: string; created_at: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load child info via /students/me or the dashboard student endpoint
    const loadData = async () => {
      setLoading(true);
      try {
        const [dashRes, annRes] = await Promise.allSettled([
          api.get('/dashboard/student'),
          api.get('/announcements?target_audience=parents&is_active=true&limit=5'),
        ]);
        if (dashRes.status === 'fulfilled') {
          const d = (dashRes.value as any) ?? {};
          setAttendance(null); // student dashboard doesn't include attendance breakdown directly
          setHomework(d.homework_due ?? []);
          setFees(d.fee_outstanding ? [{ id: 'total', invoice_number: 'Total Outstanding', total_amount_paise: d.fee_outstanding, balance_paise: d.fee_outstanding, due_date: '', status: 'pending' }] : []);
        }
        if (annRes.status === 'fulfilled') {
          setAnnouncements((annRes.value as any) ?? []);
        }
      } catch { /* ignore */ } finally { setLoading(false); }
    };
    loadData();
  }, []);

  const TABS: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'attendance', label: 'Attendance' },
    { key: 'homework', label: 'Homework' },
    { key: 'fees', label: 'Fee Status' },
  ];

  return (
    <div>
      <PageHeader title="Parent Portal" />

      {/* Child info banner */}
      {child && (
        <div className="mb-5 flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="h-14 w-14 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xl font-bold">
            {child.name.charAt(0)}
          </div>
          <div>
            <p className="font-semibold text-gray-900 dark:text-white">{child.name}</p>
            <p className="text-sm text-gray-500">{child.admission_number} · {child.class_name} {child.section_name}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-gray-200 dark:border-gray-700">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : (
        <>
          {/* Overview */}
          {tab === 'overview' && (
            <div className="grid gap-5 lg:grid-cols-2">
              {/* Announcements */}
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800 lg:col-span-2">
                <h3 className="mb-3 font-semibold text-gray-900 dark:text-white">School Announcements</h3>
                {announcements.length === 0 ? (
                  <p className="text-sm text-gray-500">No announcements.</p>
                ) : (
                  <div className="space-y-3">
                    {announcements.map((ann, i) => (
                      <div key={i} className="border-l-4 border-blue-500 pl-3">
                        <p className="font-medium text-sm">{ann.title}</p>
                        <p className="text-xs text-gray-600 mt-0.5">{ann.body}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{formatDate(ann.created_at)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Homework Due */}
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h3 className="mb-3 font-semibold text-gray-900 dark:text-white">Upcoming Homework</h3>
                {homework.length === 0 ? (
                  <p className="text-sm text-gray-500">No pending homework.</p>
                ) : (
                  <div className="space-y-2">
                    {homework.map((hw: HomeworkItem) => (
                      <div key={hw.id} className="flex items-center justify-between text-sm">
                        <span className="font-medium">{hw.title}</span>
                        <span className="text-gray-500 text-xs">{hw.due_date}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Fee Outstanding */}
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h3 className="mb-3 font-semibold text-gray-900 dark:text-white">Fee Outstanding</h3>
                {fees.length === 0 ? (
                  <p className="text-sm text-green-600 font-medium">All fees paid ✓</p>
                ) : (
                  <div className="space-y-2">
                    {fees.map(f => (
                      <div key={f.id} className="rounded-lg bg-red-50 dark:bg-red-900/20 p-3 text-sm">
                        <p className="font-medium text-red-700">{fmt(f.balance_paise)} due</p>
                        {f.due_date && <p className="text-xs text-red-500 mt-0.5">Due: {f.due_date}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Attendance */}
          {tab === 'attendance' && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <h3 className="mb-4 font-semibold">Attendance Summary</h3>
              {attendance ? (
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  {[
                    { label: 'Present', value: attendance.present_days, color: 'text-green-600' },
                    { label: 'Absent', value: attendance.absent_days, color: 'text-red-600' },
                    { label: 'Total', value: attendance.total_days, color: 'text-gray-700' },
                    { label: 'Attendance', value: `${attendance.attendance_pct}%`, color: 'text-blue-600' },
                  ].map(s => (
                    <div key={s.label} className="text-center">
                      <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
                      <p className="text-sm text-gray-500 mt-1">{s.label}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">Attendance details are available through the school portal.</p>
              )}
            </div>
          )}

          {/* Homework */}
          {tab === 'homework' && (
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    {['Title', 'Subject', 'Due Date'].map(h => (
                      <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {homework.length === 0 ? (
                    <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-500">No pending homework.</td></tr>
                  ) : homework.map((hw: HomeworkItem) => (
                    <tr key={hw.id} className="border-t border-gray-100 dark:border-gray-700">
                      <td className="px-4 py-3 font-medium">{hw.title}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{hw.subject_id}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{hw.due_date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Fees */}
          {tab === 'fees' && (
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    {['Invoice', 'Total', 'Balance', 'Due Date', 'Status'].map(h => (
                      <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fees.length === 0 ? (
                    <tr><td colSpan={5} className="px-4 py-8 text-center text-green-600 font-medium">All fees are paid ✓</td></tr>
                  ) : fees.map(f => (
                    <tr key={f.id} className="border-t border-gray-100 dark:border-gray-700">
                      <td className="px-4 py-3 font-medium">{f.invoice_number}</td>
                      <td className="px-4 py-3">{fmt(f.total_amount_paise)}</td>
                      <td className="px-4 py-3 font-medium text-red-600">{fmt(f.balance_paise)}</td>
                      <td className="px-4 py-3 text-gray-500">{f.due_date || '—'}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                          f.status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>{f.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Page;
