import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';
import { formatDateTime } from '@utils/formatters';

interface AuditLog {
  id: string;
  user_id?: string;
  user_name?: string;
  role_snapshot?: string;
  module: string;
  action: string;
  record_type?: string;
  record_id?: string;
  record_description?: string;
  ip_address?: string;
  old_values?: Record<string, unknown>;
  new_values?: Record<string, unknown>;
  user_agent?: string;
  created_at: string;
}

const MODULES = [
  'auth', 'users', 'roles', 'schools', 'settings',
  'students', 'staff', 'classes', 'sections', 'subjects',
  'academic_years', 'attendance', 'fees', 'exams', 'homework',
  'transport', 'library', 'inventory', 'accounting', 'calendar',
  'communications', 'templates', 'audit', 'reports', 'admissions',
];

const ACTIONS = ['create', 'update', 'delete', 'read', 'login', 'logout', 'export', 'import', 'approve', 'reject'];

const Page: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState({ module: '', action: '', user_id: '', from: '', to: '' });
  const [page, setPage] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const LIMIT = 50;

  useEffect(() => { loadLogs(); }, [page]);

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { offset: page * LIMIT, limit: LIMIT };
      if (filter.module) params.module = filter.module;
      if (filter.action) params.action = filter.action;
      if (filter.user_id) params.user_id = filter.user_id;
      if (filter.from) params.date_from = filter.from;
      if (filter.to) params.date_to = filter.to;
      const r: any = await api.get('/audit-logs', { params });
      setLogs(Array.isArray(r) ? r : (r?.data ?? []));
    } catch (e: any) {
      setError(e?.message ?? e?.detail ?? 'Failed to load audit logs.');
    } finally { setLoading(false); }
  };

  const applyFilter = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    loadLogs();
  };

  const selectCls = 'w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-700';
  const inputCls = 'w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-700';

  return (
    <div>
      <PageHeader title="Audit Logs" subtitle="Track all system activity and changes" />

      {/* Filters */}
      <form onSubmit={applyFilter} className="mb-5 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Module</label>
            <select value={filter.module} onChange={e => setFilter(p => ({ ...p, module: e.target.value }))} className={selectCls}>
              <option value="">All Modules</option>
              {MODULES.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Action</label>
            <select value={filter.action} onChange={e => setFilter(p => ({ ...p, action: e.target.value }))} className={selectCls}>
              <option value="">All Actions</option>
              {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">User ID</label>
            <input type="text" value={filter.user_id} placeholder="Paste UUID…" onChange={e => setFilter(p => ({ ...p, user_id: e.target.value }))} className={inputCls} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">From</label>
            <input type="date" value={filter.from} onChange={e => setFilter(p => ({ ...p, from: e.target.value }))} className={inputCls} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">To</label>
            <input type="date" value={filter.to} onChange={e => setFilter(p => ({ ...p, to: e.target.value }))} className={inputCls} />
          </div>
        </div>
        <div className="mt-3 flex justify-end gap-2">
          <button
            type="button"
            onClick={() => { setFilter({ module: '', action: '', user_id: '', from: '', to: '' }); setPage(0); setTimeout(loadLogs, 0); }}
            className="rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Clear
          </button>
          <button type="submit" className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700">
            Apply
          </button>
        </div>
      </form>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:border-red-800">{error}</div>
      )}

      {/* Table */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              {['Timestamp', 'User', 'Module', 'Action', 'Resource', 'IP', 'Role', ''].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300 whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500">No audit logs found.</td></tr>
            ) : logs.map(log => (
              <React.Fragment key={log.id}>
                <tr className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3 whitespace-nowrap text-gray-500 text-xs">{formatDateTime(log.created_at)}</td>
                  <td className="px-4 py-3 text-xs text-gray-600 dark:text-gray-400">{log.user_name ?? log.user_id?.slice(0, 8) ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono dark:bg-gray-700">{log.module}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-blue-50 px-1.5 py-0.5 text-xs font-mono text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">{log.action}</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600 dark:text-gray-400">
                    {log.record_type}{log.record_id ? ` / ${log.record_id.slice(0, 8)}…` : ''}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono">{log.ip_address ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono dark:bg-gray-700">
                      {log.role_snapshot ?? '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {(log.old_values || log.new_values) && (
                      <button
                        onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        {expandedId === log.id ? 'Hide' : 'Changes'}
                      </button>
                    )}
                  </td>
                </tr>
                {expandedId === log.id && (log.old_values || log.new_values) && (
                  <tr className="border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/30">
                    <td colSpan={8} className="px-8 py-3">
                      <div className="grid grid-cols-2 gap-4">
                        {log.old_values && (
                          <div>
                            <p className="text-xs font-semibold text-red-600 mb-1">Before</p>
                            <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">{JSON.stringify(log.old_values, null, 2)}</pre>
                          </div>
                        )}
                        {log.new_values && (
                          <div>
                            <p className="text-xs font-semibold text-green-600 mb-1">After</p>
                            <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">{JSON.stringify(log.new_values, null, 2)}</pre>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
        <span>Showing {page * LIMIT + 1}–{page * LIMIT + logs.length}</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="rounded-lg border px-3 py-1 text-sm disabled:opacity-40 hover:bg-gray-50"
          >
            ← Previous
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={logs.length < LIMIT}
            className="rounded-lg border px-3 py-1 text-sm disabled:opacity-40 hover:bg-gray-50"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
};

export default Page;
