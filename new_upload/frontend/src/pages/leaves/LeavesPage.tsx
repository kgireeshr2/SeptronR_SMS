import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';
import { toast } from 'sonner';
import { Plus, X, Check, XCircle, RefreshCw } from 'lucide-react';

const unwrap = (r: any): any[] => {
  if (Array.isArray(r)) return r;
  if (Array.isArray(r?.data)) return r.data;
  if (Array.isArray(r?.items)) return r.items;
  return [];
};

type LeaveStatus = 'pending' | 'approved' | 'rejected' | 'cancelled';

interface LeaveType { id: string; name: string; max_days_per_year: number; is_paid: boolean; is_active: boolean; }
interface LeaveApplication { id: string; staff_name?: string; leave_type_name?: string; leave_type_id: string; from_date: string; to_date: string; total_days: number; status: LeaveStatus; reason: string; remarks?: string; }
interface LeaveBalance { staff_name?: string; leave_type_name?: string; allocated: number; used: number; remaining: number; }

const StatusBadge: React.FC<{ status: LeaveStatus }> = ({ status }) => {
  const cls: Record<LeaveStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
    cancelled: 'bg-gray-100 text-gray-600',
  };
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${cls[status] ?? 'bg-gray-100 text-gray-600'}`}>{status}</span>;
};

const LeavesPage: React.FC = () => {
  const [tab, setTab] = useState<'applications' | 'types' | 'balances' | 'my_leaves'>('applications');
  const [applications, setApplications] = useState<LeaveApplication[]>([]);
  const [myLeaves, setMyLeaves] = useState<LeaveApplication[]>([]);
  const [types, setTypes] = useState<LeaveType[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [filterStatus, setFilterStatus] = useState('');

  // New application form
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [applyForm, setApplyForm] = useState({ leave_type_id: '', from_date: '', to_date: '', reason: '' });
  const [submitting, setSubmitting] = useState(false);

  // New leave type form
  const [showTypeModal, setShowTypeModal] = useState(false);
  const [typeForm, setTypeForm] = useState({ name: '', max_days_per_year: 12, is_paid: true, description: '' });
  const [editType, setEditType] = useState<LeaveType | null>(null);

  // Review modal
  const [reviewApp, setReviewApp] = useState<LeaveApplication | null>(null);
  const [reviewRemarks, setReviewRemarks] = useState('');

  useEffect(() => {
    if (tab === 'applications') loadApplications();
    else if (tab === 'types') loadTypes();
    else if (tab === 'balances') loadBalances();
    else if (tab === 'my_leaves') loadMyLeaves();
  }, [tab, filterStatus]);

  const loadApplications = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      const r = await api.get('/leaves/applications', { params });
      setApplications(unwrap(r));
    } catch { toast.error('Failed to load applications'); }
    finally { setLoading(false); }
  };

  const loadMyLeaves = async () => {
    setLoading(true);
    try {
      const r = await api.get('/leaves/applications/my');
      setMyLeaves(unwrap(r));
    } catch { toast.error('Failed to load your leaves'); }
    finally { setLoading(false); }
  };

  const loadTypes = async () => {
    setLoading(true);
    try {
      const r = await api.get('/leaves/types');
      setTypes(unwrap(r));
    } catch { toast.error('Failed to load leave types'); }
    finally { setLoading(false); }
  };

  const loadBalances = async () => {
    setLoading(true);
    try {
      const r = await api.get('/leaves/balances');
      setBalances(unwrap(r));
    } catch { toast.error('Failed to load balances'); }
    finally { setLoading(false); }
  };

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/leaves/applications', applyForm);
      toast.success('Leave application submitted');
      setShowApplyModal(false);
      setApplyForm({ leave_type_id: '', from_date: '', to_date: '', reason: '' });
      if (tab === 'my_leaves') loadMyLeaves(); else loadApplications();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to submit application');
    } finally { setSubmitting(false); }
  };

  const handleReview = async (approve: boolean) => {
    if (!reviewApp) return;
    try {
      await api.patch(`/leaves/applications/${reviewApp.id}/review`, { status: approve ? 'approved' : 'rejected', remarks: reviewRemarks });
      toast.success(`Application ${approve ? 'approved' : 'rejected'}`);
      setReviewApp(null); setReviewRemarks('');
      loadApplications();
    } catch (err: any) { toast.error(err?.response?.data?.detail ?? 'Failed to review'); }
  };

  const handleCancelLeave = async (id: string) => {
    if (!confirm('Cancel this leave application?')) return;
    try {
      await api.patch(`/leaves/applications/${id}/cancel`);
      toast.success('Application cancelled');
      loadMyLeaves();
    } catch (err: any) { toast.error(err?.response?.data?.detail ?? 'Failed to cancel'); }
  };

  const handleSaveType = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editType) {
        await api.put(`/leaves/types/${editType.id}`, typeForm);
        toast.success('Leave type updated');
      } else {
        await api.post('/leaves/types', typeForm);
        toast.success('Leave type created');
      }
      setShowTypeModal(false); setEditType(null);
      setTypeForm({ name: '', max_days_per_year: 12, is_paid: true, description: '' });
      loadTypes();
    } catch (err: any) { toast.error(err?.response?.data?.detail ?? 'Failed to save'); }
  };

  const openEditType = (t: LeaveType) => {
    setEditType(t);
    setTypeForm({ name: t.name, max_days_per_year: t.max_days_per_year, is_paid: t.is_paid, description: '' });
    setShowTypeModal(true);
  };

  const handleDeleteType = async (id: string) => {
    if (!confirm('Deactivate this leave type?')) return;
    try {
      await api.delete(`/leaves/types/${id}`);
      toast.success('Leave type deactivated');
      loadTypes();
    } catch { toast.error('Failed to delete'); }
  };

  return (
    <div>
      <PageHeader title="Leave Management" subtitle="Track and manage staff leave applications" />

      {/* Tabs */}
      <div className="mb-5 flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {([
          { key: 'applications', label: '📋 All Applications' },
          { key: 'my_leaves', label: '👤 My Leaves' },
          { key: 'types', label: '🏷️ Leave Types' },
          { key: 'balances', label: '⚖️ Balances' },
        ] as const).map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t.key ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Applications Tab */}
      {tab === 'applications' && (
        <div>
          <div className="mb-4 flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-xs text-gray-500">Status</label>
              <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="">All</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <button onClick={loadApplications} className="flex items-center gap-2 rounded bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-700"><RefreshCw size={14} /> Refresh</button>
            <button onClick={() => setShowApplyModal(true)} className="flex items-center gap-2 rounded bg-green-600 px-3 py-2 text-sm text-white hover:bg-green-700"><Plus size={14} /> New Application</button>
          </div>

          {loading ? <div className="py-10 text-center text-gray-400">Loading…</div> : (
            <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    {['Staff', 'Leave Type', 'From', 'To', 'Days', 'Reason', 'Status', 'Actions'].map(h => (
                      <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {applications.length === 0 ? (
                    <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No applications found.</td></tr>
                  ) : applications.map(app => (
                    <tr key={app.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{app.staff_name ?? '—'}</td>
                      <td className="px-4 py-3">{app.leave_type_name ?? '—'}</td>
                      <td className="px-4 py-3">{app.from_date}</td>
                      <td className="px-4 py-3">{app.to_date}</td>
                      <td className="px-4 py-3 text-center">{app.total_days}</td>
                      <td className="px-4 py-3 max-w-[200px] truncate text-gray-500">{app.reason}</td>
                      <td className="px-4 py-3"><StatusBadge status={app.status} /></td>
                      <td className="px-4 py-3">
                        {app.status === 'pending' && (
                          <button onClick={() => { setReviewApp(app); setReviewRemarks(''); }} className="rounded px-2 py-1 text-xs text-indigo-600 hover:bg-indigo-50">Review</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* My Leaves Tab */}
      {tab === 'my_leaves' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => setShowApplyModal(true)} className="flex items-center gap-2 rounded bg-green-600 px-3 py-2 text-sm text-white hover:bg-green-700"><Plus size={14} /> Apply for Leave</button>
          </div>
          {loading ? <div className="py-10 text-center text-gray-400">Loading…</div> : (
            <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    {['Leave Type', 'From', 'To', 'Days', 'Reason', 'Status', 'Remarks', 'Actions'].map(h => (
                      <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {myLeaves.length === 0 ? (
                    <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No leave applications found.</td></tr>
                  ) : myLeaves.map(app => (
                    <tr key={app.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3">{app.leave_type_name ?? '—'}</td>
                      <td className="px-4 py-3">{app.from_date}</td>
                      <td className="px-4 py-3">{app.to_date}</td>
                      <td className="px-4 py-3 text-center">{app.total_days}</td>
                      <td className="px-4 py-3 max-w-[180px] truncate text-gray-500">{app.reason}</td>
                      <td className="px-4 py-3"><StatusBadge status={app.status} /></td>
                      <td className="px-4 py-3 text-xs text-gray-400">{app.remarks ?? '—'}</td>
                      <td className="px-4 py-3">
                        {app.status === 'pending' && (
                          <button onClick={() => handleCancelLeave(app.id)} className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50">Cancel</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Leave Types Tab */}
      {tab === 'types' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => { setEditType(null); setTypeForm({ name: '', max_days_per_year: 12, is_paid: true, description: '' }); setShowTypeModal(true); }}
              className="flex items-center gap-2 rounded bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-700"><Plus size={14} /> Add Leave Type</button>
          </div>
          {loading ? <div className="py-10 text-center text-gray-400">Loading…</div> : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {types.length === 0 ? <p className="text-gray-400">No leave types found.</p> : types.map(t => (
                <div key={t.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">{t.name}</p>
                      <p className="text-sm text-gray-500">{t.max_days_per_year} days/year • {t.is_paid ? 'Paid' : 'Unpaid'}</p>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs ${t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {t.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button onClick={() => openEditType(t)} className="text-xs text-indigo-600 hover:underline">Edit</button>
                    <button onClick={() => handleDeleteType(t.id)} className="text-xs text-red-500 hover:underline">Deactivate</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Balances Tab */}
      {tab === 'balances' && (
        <div>
          {loading ? <div className="py-10 text-center text-gray-400">Loading…</div> : (
            <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    {['Staff', 'Leave Type', 'Allocated', 'Used', 'Remaining'].map(h => (
                      <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {balances.length === 0 ? (
                    <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No balance data found.</td></tr>
                  ) : balances.map((b, i) => (
                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3 font-medium">{b.staff_name ?? '—'}</td>
                      <td className="px-4 py-3">{b.leave_type_name ?? '—'}</td>
                      <td className="px-4 py-3">{b.allocated}</td>
                      <td className="px-4 py-3 text-yellow-600">{b.used}</td>
                      <td className="px-4 py-3 font-semibold text-green-600">{b.remaining}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Apply for Leave Modal */}
      {showApplyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold dark:text-white">Apply for Leave</h3>
              <button onClick={() => setShowApplyModal(false)}><X size={18} className="text-gray-400" /></button>
            </div>
            <form onSubmit={handleApply} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium">Leave Type *</label>
                <select required value={applyForm.leave_type_id} onChange={e => setApplyForm(f => ({ ...f, leave_type_id: e.target.value }))}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                  <option value="">— Select —</option>
                  {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium">From Date *</label>
                  <input required type="date" value={applyForm.from_date} onChange={e => setApplyForm(f => ({ ...f, from_date: e.target.value }))}
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">To Date *</label>
                  <input required type="date" value={applyForm.to_date} onChange={e => setApplyForm(f => ({ ...f, to_date: e.target.value }))}
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Reason *</label>
                <textarea required rows={3} value={applyForm.reason} onChange={e => setApplyForm(f => ({ ...f, reason: e.target.value }))}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setShowApplyModal(false)} className="rounded-lg border px-4 py-2 text-sm dark:border-gray-600">Cancel</button>
                <button type="submit" disabled={submitting} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-60">
                  {submitting ? 'Submitting…' : 'Submit Application'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Leave Type Modal */}
      {showTypeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold dark:text-white">{editType ? 'Edit Leave Type' : 'Add Leave Type'}</h3>
              <button onClick={() => setShowTypeModal(false)}><X size={18} className="text-gray-400" /></button>
            </div>
            <form onSubmit={handleSaveType} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium">Name *</label>
                <input required value={typeForm.name} onChange={e => setTypeForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" placeholder="e.g. Sick Leave" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Max Days per Year *</label>
                <input required type="number" min={1} value={typeForm.max_days_per_year} onChange={e => setTypeForm(f => ({ ...f, max_days_per_year: +e.target.value }))}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="is_paid" checked={typeForm.is_paid} onChange={e => setTypeForm(f => ({ ...f, is_paid: e.target.checked }))} className="rounded" />
                <label htmlFor="is_paid" className="text-sm">Paid Leave</label>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Description</label>
                <textarea rows={2} value={typeForm.description} onChange={e => setTypeForm(f => ({ ...f, description: e.target.value }))}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setShowTypeModal(false)} className="rounded-lg border px-4 py-2 text-sm dark:border-gray-600">Cancel</button>
                <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Review Modal */}
      {reviewApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold dark:text-white">Review Application</h3>
              <button onClick={() => setReviewApp(null)}><X size={18} className="text-gray-400" /></button>
            </div>
            <div className="mb-4 space-y-2 text-sm">
              <p><span className="text-gray-500">Staff:</span> <span className="font-medium">{reviewApp.staff_name}</span></p>
              <p><span className="text-gray-500">Leave Type:</span> {reviewApp.leave_type_name}</p>
              <p><span className="text-gray-500">Duration:</span> {reviewApp.from_date} → {reviewApp.to_date} ({reviewApp.total_days} days)</p>
              <p><span className="text-gray-500">Reason:</span> {reviewApp.reason}</p>
            </div>
            <div className="mb-4">
              <label className="mb-1 block text-sm font-medium">Remarks</label>
              <textarea rows={2} value={reviewRemarks} onChange={e => setReviewRemarks(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" placeholder="Optional remarks…" />
            </div>
            <div className="flex gap-3">
              <button onClick={() => handleReview(true)} className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-600 py-2 text-sm text-white hover:bg-green-700">
                <Check size={14} /> Approve
              </button>
              <button onClick={() => handleReview(false)} className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-red-500 py-2 text-sm text-white hover:bg-red-600">
                <XCircle size={14} /> Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LeavesPage;
