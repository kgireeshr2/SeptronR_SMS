import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';

interface StudentDash {
  fee_outstanding: number;
  upcoming_exams: { name: string; exam_date: string }[];
  homework_due: { title: string; due_date: string }[];
}

const fmt = (paise: number) => `₹${(paise / 100).toLocaleString('en-IN')}`;

const Page: React.FC = () => {
  const [data, setData] = useState<StudentDash | null>(null);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/dashboard/student')
      .then((r: any) => setData(r?.data ?? r))
      .catch(() => { /* ignore */ })
      .finally(() => setLoading(false));
    api.get('/announcements', { params: { active_only: true } })
      .then((r: any) => setAnnouncements((r?.data ?? r) || []))
      .catch(() => { /* ignore */ });
  }, []);

  return (
    <div>
      <PageHeader title="Student Portal" />

      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {/* Fee outstanding */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Fee Outstanding</p>
            <p className={`mt-2 text-3xl font-bold ${data?.fee_outstanding ? 'text-red-600' : 'text-green-600'}`}>
              {data?.fee_outstanding ? fmt(data.fee_outstanding) : 'All Clear ✓'}
            </p>
          </div>

          {/* Upcoming exams */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="font-semibold mb-3">Upcoming Exams</h3>
            {!data?.upcoming_exams?.length ? (
              <p className="text-sm text-gray-500">No upcoming exams.</p>
            ) : (
              <div className="space-y-2">
                {data.upcoming_exams.map((ex, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <span className="font-medium">{ex.name}</span>
                    <span className="text-gray-500">{ex.exam_date}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Homework due */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800 md:col-span-2">
            <h3 className="font-semibold mb-3">Pending Homework</h3>
            {!data?.homework_due?.length ? (
              <p className="text-sm text-gray-500">No pending homework.</p>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {data.homework_due.map((hw, i) => (
                  <div key={i} className="flex items-center justify-between py-2 text-sm">
                    <span className="font-medium">{hw.title}</span>
                    <span className="text-gray-500">Due: {hw.due_date}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Announcements */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800 md:col-span-2">
            <h3 className="font-semibold mb-3">School Announcements</h3>
            {!announcements.length ? (
              <p className="text-sm text-gray-500">No announcements.</p>
            ) : (
              <div className="space-y-3">
                {announcements.slice(0, 5).map((a: any) => (
                  <div key={a.id} className="border-l-4 border-brand-500 pl-3">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{a.title}</p>
                    <p className="text-sm text-gray-500">{a.body}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Page;

