import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';

interface TeacherDash {
  pending_homework_reviews: number;
  upcoming_exams: { name: string; exam_date: string }[];
}

const Page: React.FC = () => {
  const [data, setData] = useState<TeacherDash | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/dashboard/teacher')
      .then((r: any) => setData(r?.data ?? r))
      .catch(() => { /* ignore */ })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Teacher Portal" />

      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {/* Pending Reviews */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Pending Homework Reviews</p>
            <p className="mt-2 text-4xl font-bold text-yellow-600">{data?.pending_homework_reviews ?? 0}</p>
            <p className="text-sm text-gray-500 mt-1">Submissions awaiting marks</p>
          </div>

          {/* Upcoming Exams */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="font-semibold mb-3">Upcoming Exams (14 days)</h3>
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

          {/* Quick Links */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800 md:col-span-2">
            <h3 className="font-semibold mb-3">Quick Actions</h3>
            <div className="flex flex-wrap gap-2">
              {[
                { label: 'Mark Attendance', href: '/attendance' },
                { label: 'Assign Homework', href: '/homework' },
                { label: 'Lesson Plans', href: '/homework' },
                { label: 'View Timetable', href: '/classes/timetable' },
              ].map(l => (
                <a
                  key={l.label}
                  href={l.href}
                  className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700 hover:bg-blue-100"
                >
                  {l.label}
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Page;

