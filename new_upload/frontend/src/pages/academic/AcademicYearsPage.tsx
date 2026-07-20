import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ChevronDown, ChevronUp, Edit2, Lock, LockOpen, Plus, Trash2, X } from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { academicYearsApi, AcademicYear } from '@api/academicYears';
import { useAcademicYearStore } from '@store/academicYearStore';
import { useAuthStore } from '@store/authStore';
import { formatDate } from '@utils/formatters';
import api from '@api/axios';

const unwrap = (res: any) => res?.data ?? res;

// ─── Delete with Password Confirmation ────────────────────────────────────────

interface DeleteConfirmProps {
  yearName: string;
  onConfirm: (password: string) => void;
  onCancel: () => void;
  loading: boolean;
}

const DeleteConfirmModal: React.FC<DeleteConfirmProps> = ({ yearName, onConfirm, onCancel, loading }) => {
  const [password, setPassword] = React.useState('');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-900">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
            <Trash2 size={18} className="text-red-600" />
          </div>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>
        </div>
        <h3 className="mb-1 text-base font-semibold text-gray-900 dark:text-white">
          Delete Academic Year
        </h3>
        <p className="mb-4 text-sm text-gray-500 dark:text-gray-400">
          You're about to permanently delete <strong className="text-gray-800 dark:text-gray-200">{yearName}</strong> and all its data. This cannot be undone.
        </p>
        <div className="mb-4">
          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
            Enter your password to confirm
          </label>
          <input
            type="password"
            autoFocus
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your account password"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
          />
        </div>
        <div className="flex gap-2">
          <button onClick={onCancel} className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
            Cancel
          </button>
          <button
            disabled={!password || loading}
            onClick={() => onConfirm(password)}
            className="flex-1 rounded-lg bg-red-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60 hover:bg-red-700"
          >
            {loading ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Edit Year Modal ──────────────────────────────────────────────────────────

interface EditYearProps {
  year: AcademicYear;
  onSave: (data: { name: string; start_date: string; end_date: string }) => void;
  onCancel: () => void;
  loading: boolean;
}

const EditYearModal: React.FC<EditYearProps> = ({ year, onSave, onCancel, loading }) => {
  const [form, setForm] = React.useState({
    name: year.name,
    start_date: year.start_date,
    end_date: year.end_date,
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-900">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">Edit Academic Year</h3>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Year Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              placeholder="e.g. 2025-2026"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Start Date</label>
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">End Date</label>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
              />
            </div>
          </div>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onCancel} className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
            Cancel
          </button>
          <button
            disabled={!form.name || !form.start_date || !form.end_date || loading}
            onClick={() => onSave(form)}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 hover:bg-brand-700"
          >
            {loading ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const AcademicYearsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { setYears, setSelectedYear } = useAcademicYearStore();
  const currentUser = useAuthStore((s) => s.currentUser);

  const [expanded, setExpanded] = React.useState<Record<string, boolean>>({});
  const [showCreate, setShowCreate] = React.useState(false);
  const [newYear, setNewYear] = React.useState({ name: '', start_date: '', end_date: '', set_as_active: true });
  const [newTerm, setNewTerm] = React.useState<Record<string, { name: string; start_date: string; end_date: string }>>({});

  // Edit / Delete state
  const [editYear, setEditYear] = React.useState<AcademicYear | null>(null);
  const [deleteYear, setDeleteYear] = React.useState<AcademicYear | null>(null);
  const [deleteLoading, setDeleteLoading] = React.useState(false);

  const yearsQuery = useQuery({
    queryKey: ['academic-years'],
    queryFn: async () => {
      const data = unwrap(await academicYearsApi.list());
      const items: AcademicYear[] = Array.isArray(data) ? data : (data?.items ?? []);
      const mapped = items.map((y: any) => ({ ...y, startDate: y.start_date, endDate: y.end_date, isCurrent: y.is_current }));
      setYears(mapped as any);
      const current = mapped.find((y: any) => y.is_current);
      if (current) setSelectedYear(current as any);
      return items;
    },
  });

  const createMutation = useMutation({
    mutationFn: () => academicYearsApi.create({ name: newYear.name, start_date: newYear.start_date, end_date: newYear.end_date }),
    onSuccess: async (res: any) => {
      const created = res?.data ?? res;
      toast.success('Academic year created');
      setShowCreate(false);
      setNewYear({ name: '', start_date: '', end_date: '', set_as_active: true });
      if (newYear.set_as_active && created?.id) {
        try {
          await academicYearsApi.setCurrent(created.id);
          queryClient.invalidateQueries({ queryKey: ['navbar-academic-years'] });
        } catch { /* ignore */ }
      }
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Failed to create academic year'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => academicYearsApi.update(id, data),
    onSuccess: () => {
      toast.success('Academic year updated');
      setEditYear(null);
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Failed to update'),
  });

  const setCurrentMutation = useMutation({
    mutationFn: (id: string) => academicYearsApi.setCurrent(id),
    onSuccess: () => {
      toast.success('Current year updated');
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
    },
  });

  const lockMutation = useMutation({
    mutationFn: (id: string) => academicYearsApi.lock(id),
    onSuccess: () => {
      toast.success('Year locked');
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
    },
  });

  const unlockMutation = useMutation({
    mutationFn: (id: string) => academicYearsApi.unlock(id),
    onSuccess: () => {
      toast.success('Year unlocked');
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
    },
  });

  const createTermMutation = useMutation({
    mutationFn: ({ yearId, payload }: { yearId: string; payload: any }) =>
      academicYearsApi.createTerm(yearId, payload),
    onSuccess: () => {
      toast.success('Term created');
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
    },
  });

  // Password-verified delete
  const handleDeleteConfirm = async (password: string) => {
    if (!deleteYear) return;
    setDeleteLoading(true);
    try {
      // Verify password by attempting login
      await api.post('/auth/login', {
        username: currentUser?.username ?? currentUser?.email,
        password,
      });
      // If login succeeds, proceed with deletion
      await academicYearsApi.remove(deleteYear.id);
      toast.success(`"${deleteYear.name}" deleted`);
      setDeleteYear(null);
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err?.detail ?? 'Incorrect password or delete failed';
      toast.error(msg);
    } finally {
      setDeleteLoading(false);
    }
  };

  const years = yearsQuery.data ?? [];

  return (
    <div>
      <PageHeader
        title="Academic Years"
        subtitle="Create sessions, lock them, edit, and manage terms"
      />

      <div className="mb-4 flex justify-end">
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
        >
          <Plus size={14} />
          Create Year
        </button>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-900/40">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Year</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Start</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">End</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Status</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">Actions</th>
            </tr>
          </thead>
          <tbody>
            {years.map((year: any) => (
              <React.Fragment key={year.id}>
                <tr className="border-t border-gray-100 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900/20">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{year.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{formatDate(year.start_date)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{formatDate(year.end_date)}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {year.is_current && (
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
                          Current
                        </span>
                      )}
                      {year.is_locked ? (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                          Locked
                        </span>
                      ) : (
                        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500 dark:bg-gray-700">
                          Active
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="inline-flex items-center gap-1.5 flex-wrap justify-end">
                      {/* Terms expand */}
                      <button
                        onClick={() => setExpanded((prev) => ({ ...prev, [year.id]: !prev[year.id] }))}
                        title="Terms"
                        className="rounded-lg border border-gray-300 p-1.5 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                      >
                        {expanded[year.id] ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                      </button>

                      {/* Edit */}
                      <button
                        onClick={() => setEditYear(year)}
                        title="Edit"
                        className="rounded-lg border border-gray-300 p-1.5 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                      >
                        <Edit2 size={13} />
                      </button>

                      {/* Set Current */}
                      {!year.is_current && (
                        <button
                          onClick={() => setCurrentMutation.mutate(year.id)}
                          className="rounded-lg border border-brand-200 px-2 py-1 text-xs text-brand-700 hover:bg-brand-50 dark:border-brand-800 dark:text-brand-400"
                        >
                          Set Current
                        </button>
                      )}

                      {/* Lock / Unlock */}
                      {year.is_locked ? (
                        <button
                          onClick={() => unlockMutation.mutate(year.id)}
                          title="Unlock"
                          className="inline-flex items-center gap-1 rounded-lg border border-green-200 px-2 py-1 text-xs font-medium text-green-700 hover:bg-green-50 dark:border-green-800 dark:text-green-400"
                        >
                          <LockOpen size={12} />
                          Unlock
                        </button>
                      ) : (
                        <button
                          onClick={() => lockMutation.mutate(year.id)}
                          title="Lock"
                          className="inline-flex items-center gap-1 rounded-lg border border-amber-200 px-2 py-1 text-xs font-medium text-amber-700 hover:bg-amber-50 dark:border-amber-800 dark:text-amber-400"
                        >
                          <Lock size={12} />
                          Lock
                        </button>
                      )}

                      {/* Delete */}
                      <button
                        onClick={() => setDeleteYear(year)}
                        title="Delete"
                        className="rounded-lg border border-red-200 p-1.5 text-red-400 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>

                {/* Terms panel */}
                {expanded[year.id] && (
                  <tr className="border-t border-gray-100 bg-gray-50/60 dark:border-gray-700 dark:bg-gray-900/10">
                    <td colSpan={5} className="px-4 py-3">
                      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                        Terms
                      </div>
                      <div className="mb-3 space-y-1">
                        {(year.terms ?? []).length === 0 ? (
                          <p className="text-xs text-gray-400">No terms yet.</p>
                        ) : (
                          (year.terms ?? []).map((t: any) => (
                            <div
                              key={t.id}
                              className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs dark:border-gray-700 dark:bg-gray-800"
                            >
                              <span>
                                {t.name}{' '}
                                <span className="text-gray-400">({formatDate(t.start_date)} → {formatDate(t.end_date)})</span>
                              </span>
                              {t.is_current && (
                                <span className="rounded-full bg-green-100 px-2 py-0.5 text-green-700">Current</span>
                              )}
                            </div>
                          ))
                        )}
                      </div>

                      {!year.is_locked && (
                        <div className="grid gap-2 md:grid-cols-4">
                          <input
                            placeholder="Term name (e.g. Term 1)"
                            value={newTerm[year.id]?.name ?? ''}
                            onChange={(e) =>
                              setNewTerm((prev) => ({
                                ...prev,
                                [year.id]: { ...(prev[year.id] ?? { name: '', start_date: '', end_date: '' }), name: e.target.value },
                              }))
                            }
                            className="rounded-lg border border-gray-300 px-3 py-2 text-xs dark:border-gray-600 dark:bg-gray-800"
                          />
                          <input
                            type="date"
                            value={newTerm[year.id]?.start_date ?? ''}
                            onChange={(e) =>
                              setNewTerm((prev) => ({
                                ...prev,
                                [year.id]: { ...(prev[year.id] ?? { name: '', start_date: '', end_date: '' }), start_date: e.target.value },
                              }))
                            }
                            className="rounded-lg border border-gray-300 px-3 py-2 text-xs dark:border-gray-600 dark:bg-gray-800"
                          />
                          <input
                            type="date"
                            value={newTerm[year.id]?.end_date ?? ''}
                            onChange={(e) =>
                              setNewTerm((prev) => ({
                                ...prev,
                                [year.id]: { ...(prev[year.id] ?? { name: '', start_date: '', end_date: '' }), end_date: e.target.value },
                              }))
                            }
                            className="rounded-lg border border-gray-300 px-3 py-2 text-xs dark:border-gray-600 dark:bg-gray-800"
                          />
                          <button
                            onClick={() => {
                              const payload = newTerm[year.id];
                              if (!payload?.name || !payload.start_date || !payload.end_date) {
                                toast.error('Fill all term fields');
                                return;
                              }
                              createTermMutation.mutate({ yearId: year.id, payload });
                            }}
                            className="rounded-lg bg-brand-600 px-3 py-2 text-xs font-semibold text-white hover:bg-brand-700"
                          >
                            Add Term
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Year Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-900">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-semibold">Create Academic Year</h3>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Year Name</label>
                <input
                  placeholder="2026-2027"
                  value={newYear.name}
                  onChange={(e) => setNewYear((p) => ({ ...p, name: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Start Date</label>
                  <input
                    type="date"
                    value={newYear.start_date}
                    onChange={(e) => setNewYear((p) => ({ ...p, start_date: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">End Date</label>
                  <input
                    type="date"
                    value={newYear.end_date}
                    onChange={(e) => setNewYear((p) => ({ ...p, end_date: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  />
                </div>
              </div>
              <label className="flex cursor-pointer items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  checked={newYear.set_as_active}
                  onChange={(e) => setNewYear((p) => ({ ...p, set_as_active: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Set as active year</span>
              </label>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50">
                Cancel
              </button>
              <button
                onClick={() => {
                  if (!newYear.name || !newYear.start_date || !newYear.end_date) {
                    toast.error('All fields are required');
                    return;
                  }
                  if (new Date(newYear.end_date) <= new Date(newYear.start_date)) {
                    toast.error('End date must be after start date');
                    return;
                  }
                  createMutation.mutate();
                }}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editYear && (
        <EditYearModal
          year={editYear}
          loading={updateMutation.isPending}
          onCancel={() => setEditYear(null)}
          onSave={(data) => updateMutation.mutate({ id: editYear.id, data })}
        />
      )}

      {/* Delete with Password Confirmation */}
      {deleteYear && (
        <DeleteConfirmModal
          yearName={deleteYear.name}
          loading={deleteLoading}
          onCancel={() => setDeleteYear(null)}
          onConfirm={handleDeleteConfirm}
        />
      )}
    </div>
  );
};

export default AcademicYearsPage;
