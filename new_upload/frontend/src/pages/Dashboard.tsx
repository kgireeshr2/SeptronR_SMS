import React from 'react';
import { PageHeader } from '@components/shared/PageHeader';

const Dashboard: React.FC = () => (
  <div>
    <PageHeader
      title="Dashboard"
      subtitle="Welcome to SeptroSchool"
      breadcrumbs={[{ label: 'Home' }, { label: 'Dashboard' }]}
    />
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {['Total Students', 'Total Staff', 'Fee Collected', 'Attendance Today'].map(
        (label) => (
          <div
            key={label}
            className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800"
          >
            <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
            <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
              —
            </p>
          </div>
        )
      )}
    </div>
    <p className="mt-8 text-center text-sm text-gray-400">
      Dashboard widgets will be implemented in Phase 20.
    </p>
  </div>
);

export default Dashboard;
