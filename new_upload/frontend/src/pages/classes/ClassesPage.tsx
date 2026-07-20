import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  BookOpen, ChevronDown, ChevronUp, GripVertical,
  Layers, Plus, Tag, Trash2, X,
} from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { classesApi, subjectsApi } from '@api/classes';
import { academicYearsApi } from '@api/academicYears';
import { useAcademicYearStore } from '@store/academicYearStore';
import { useAuthStore } from '@store/authStore';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const unwrap = (res: any) => res?.data ?? res;

const PRESETS_STORAGE_KEY = 'sms-section-presets';

function loadPresets(): string[] {
  try {
    return JSON.parse(localStorage.getItem(PRESETS_STORAGE_KEY) ?? '[]');
  } catch {
    return [];
  }
}

function savePresets(presets: string[]) {
  localStorage.setItem(PRESETS_STORAGE_KEY, JSON.stringify(presets));
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = 'bg-indigo-100 text-indigo-700' }) => (
  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
    {label}
  </span>
);

// ─── Main Component ───────────────────────────────────────────────────────────

const ClassesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { selectedYear, setSelectedYear, setYears } = useAcademicYearStore();
  const isSuperAdmin = useAuthStore((s) => s.currentUser?.is_super_admin ?? false);

  const [activeTab, setActiveTab] = React.useState<'sections' | 'classes'>('sections');
  const [expanded, setExpanded] = React.useState<Record<string, boolean>>({});

  // ── Section Presets (localStorage) ────────────────────────────────────────
  const [presets, setPresets] = React.useState<string[]>(loadPresets);
  const [newPreset, setNewPreset] = React.useState('');

  const addPreset = () => {
    const name = newPreset.trim().toUpperCase();
    if (!name) return;
    if (presets.includes(name)) return toast.error('Preset already exists');
    const updated = [...presets, name];
    setPresets(updated);
    savePresets(updated);
    setNewPreset('');
    toast.success(`Section preset "${name}" added`);
  };

  const removePreset = (name: string) => {
    const updated = presets.filter((p) => p !== name);
    setPresets(updated);
    savePresets(updated);
  };

  // ── New Class Form ─────────────────────────────────────────────────────────
  const [newClass, setNewClass] = React.useState({ name: '' });
  const [selectedPresets, setSelectedPresets] = React.useState<string[]>([]);
  const [sectionCapacity, setSectionCapacity] = React.useState(40);

  const togglePresetSelection = (name: string) => {
    setSelectedPresets((prev) =>
      prev.includes(name) ? prev.filter((p) => p !== name) : [...prev, name]
    );
  };

  // ── Subject / section drafts ────────────────────────────────────────────────
  const [subjectDrafts, setSubjectDrafts] = React.useState<Record<string, { subject_id: string; teacher_id: string }>>({});

  // ── Queries ────────────────────────────────────────────────────────────────
  const yearsQuery = useQuery({
    queryKey: ['academic-years-select'],
    queryFn: async () => {
      const data = unwrap(await academicYearsApi.list());
      const items = Array.isArray(data) ? data : (data?.items ?? []);
      setYears(
        items.map((y: any) => ({
          id: y.id, name: y.name,
          startDate: y.start_date, endDate: y.end_date, isCurrent: y.is_current,
        }))
      );
      if (!selectedYear && items.length > 0) {
        const current = items.find((y: any) => y.is_current) || items[0];
        setSelectedYear({ id: current.id, name: current.name, startDate: current.start_date, endDate: current.end_date, isCurrent: current.is_current });
      }
      return items;
    },
  });

  const classesQuery = useQuery({
    queryKey: ['classes', selectedYear?.id],
    enabled: !!selectedYear?.id,
    queryFn: async () => {
      const data = unwrap(await classesApi.list(selectedYear!.id));
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  // Auto-populate section presets from existing DB sections
  React.useEffect(() => {
    if (!classesQuery.data) return;
    const dbSectionNames: string[] = [];
    for (const cls of classesQuery.data) {
      for (const sec of cls.sections ?? []) {
        if (sec.name && !dbSectionNames.includes(sec.name.toUpperCase())) {
          dbSectionNames.push(sec.name.toUpperCase());
        }
      }
    }
    if (dbSectionNames.length === 0) return;
    setPresets((prev) => {
      const merged = [...prev];
      for (const name of dbSectionNames) {
        if (!merged.includes(name)) merged.push(name);
      }
      if (merged.length === prev.length) return prev; // no change
      savePresets(merged);
      return merged;
    });
  }, [classesQuery.data]);

  const subjectsQuery = useQuery({
    queryKey: ['subjects-lite'],
    queryFn: async () => {
      const data = unwrap(await subjectsApi.list());
      const items = Array.isArray(data) ? data : (data?.items ?? []);
      return items.filter((x: any) => x.is_active !== false);
    },
  });

  const classDetailsQuery = useQuery({
    queryKey: ['class-details-expanded', expanded],
    enabled: Object.values(expanded).some(Boolean),
    queryFn: async () => {
      const map: Record<string, any> = {};
      for (const classId of Object.keys(expanded).filter((id) => expanded[id])) {
        map[classId] = unwrap(await classesApi.get(classId));
      }
      return map;
    },
  });

  const classSubjectsQuery = useQuery({
    queryKey: ['class-subjects-expanded', expanded],
    enabled: Object.values(expanded).some(Boolean),
    queryFn: async () => {
      const map: Record<string, any[]> = {};
      for (const classId of Object.keys(expanded).filter((id) => expanded[id])) {
        const data = unwrap(await classesApi.listClassSubjects(classId));
        map[classId] = data?.subjects ?? [];
      }
      return map;
    },
  });

  // ── Mutations ──────────────────────────────────────────────────────────────
  const createClassMutation = useMutation({
    mutationFn: async () => {
      if (!selectedYear?.id) throw new Error('Select academic year');
      if (!newClass.name.trim()) throw new Error('Class name is required');

      // Create class
      const res = unwrap(await classesApi.create({
        name: newClass.name.trim(),
        academic_year_id: selectedYear.id,
      }));
      const classId = res?.id ?? res?.data?.id;
      if (!classId) throw new Error('Class creation failed');

      // Auto-create chosen section presets
      for (const preset of selectedPresets) {
        try {
          await classesApi.createSection(classId, { name: preset, capacity: sectionCapacity });
        } catch {
          // non-fatal: log section creation errors but don't abort
        }
      }
      return classId;
    },
    onSuccess: () => {
      toast.success('Class created' + (selectedPresets.length ? ` with ${selectedPresets.length} section(s)` : ''));
      setNewClass({ name: '' });
      setSelectedPresets([]);
      queryClient.invalidateQueries({ queryKey: ['classes', selectedYear?.id] });
    },
    onError: (err: any) => toast.error(err?.message ?? err?.detail ?? 'Failed to create class'),
  });

  const addSectionMutation = useMutation({
    mutationFn: ({ classId, name }: { classId: string; name: string }) =>
      classesApi.createSection(classId, { name, capacity: 40 }),
    onSuccess: (_, vars) => {
      toast.success('Section added');
      queryClient.invalidateQueries({ queryKey: ['classes', selectedYear?.id] });
      queryClient.invalidateQueries({ queryKey: ['class-details-expanded'] });
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Failed to add section'),
  });

  const assignSubjectMutation = useMutation({
    mutationFn: ({ classId, payload }: { classId: string; payload: { subject_id: string } }) =>
      classesApi.assignSubject(classId, payload),
    onSuccess: (_, vars) => {
      toast.success('Subject assigned');
      setSubjectDrafts((p) => ({ ...p, [vars.classId]: { subject_id: '', teacher_id: '' } }));
      queryClient.invalidateQueries({ queryKey: ['class-subjects-expanded'] });
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Failed to assign subject'),
  });

  const deleteClassMutation = useMutation({
    mutationFn: (classId: string) => classesApi.remove(classId),
    onSuccess: () => {
      toast.success('Class deleted');
      queryClient.invalidateQueries({ queryKey: ['classes', selectedYear?.id] });
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Failed to delete class'),
  });

  // ── Data ───────────────────────────────────────────────────────────────────
  const classes = classesQuery.data ?? [];
  const subjects = subjectsQuery.data ?? [];
  const classDetailsMap = classDetailsQuery.data ?? {};
  const classSubjectsMap = classSubjectsQuery.data ?? {};

  return (
    <div>
      <PageHeader
        title="Classes & Sections"
        subtitle="Manage section presets, classes, and subject assignments"
      />

      {/* Academic Year Selector */}
      <div className="mb-4">
        <select
          value={selectedYear?.id ?? ''}
          onChange={(e) => {
            const y = (yearsQuery.data ?? []).find((yr: any) => yr.id === e.target.value);
            if (!y) return;
            setSelectedYear({ id: y.id, name: y.name, startDate: y.start_date, endDate: y.end_date, isCurrent: y.is_current });
          }}
          className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
        >
          <option value="">Select Academic Year</option>
          {(yearsQuery.data ?? []).map((y: any) => (
            <option key={y.id} value={y.id}>{y.name}</option>
          ))}
        </select>
      </div>

      {/* Tab bar */}
      <div className="mb-6 flex gap-1 rounded-xl border border-gray-200 bg-gray-50 p-1 dark:border-gray-700 dark:bg-gray-900/40 w-fit">
        <button
          onClick={() => setActiveTab('sections')}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
            activeTab === 'sections'
              ? 'bg-white text-indigo-700 shadow-sm dark:bg-gray-800 dark:text-indigo-400'
              : 'text-gray-600 hover:text-gray-900 dark:text-gray-400'
          }`}
        >
          <Tag size={15} /> Section Presets
        </button>
        <button
          onClick={() => setActiveTab('classes')}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
            activeTab === 'classes'
              ? 'bg-white text-indigo-700 shadow-sm dark:bg-gray-800 dark:text-indigo-400'
              : 'text-gray-600 hover:text-gray-900 dark:text-gray-400'
          }`}
        >
          <Layers size={15} /> Classes
        </button>
      </div>

      {/* ── SECTION PRESETS TAB ──────────────────────────────────────────────── */}
      {activeTab === 'sections' && (
        <div className="max-w-lg">
          <div className="mb-4 rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
            <strong>How it works:</strong> Create section presets (like A, B, C) here first. Then when
            you create a class, you can pick which sections to include — they'll be auto-created.
          </div>

          <div className="mb-4 flex gap-2">
            <input
              value={newPreset}
              onChange={(e) => setNewPreset(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && addPreset()}
              placeholder="Section name (e.g. A, B, Science)"
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
            />
            <button
              onClick={addPreset}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Plus size={14} />
              Add Preset
            </button>
          </div>

          {presets.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center dark:border-gray-700">
              <Tag className="mx-auto mb-2 text-gray-400" size={32} />
              <p className="text-sm text-gray-500">No section presets yet. Add A, B, C to get started.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {presets.map((preset) => (
                <div
                  key={preset}
                  className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm dark:border-gray-700 dark:bg-gray-800"
                >
                  <div className="flex items-center gap-3">
                    <GripVertical size={16} className="text-gray-400" />
                    <span className="font-medium text-gray-800 dark:text-white">Section {preset}</span>
                  </div>
                  <button
                    onClick={() => removePreset(preset)}
                    className="rounded p-1 text-red-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── CLASSES TAB ──────────────────────────────────────────────────────── */}
      {activeTab === 'classes' && (
        <>
          {/* Create Class Form */}
          <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
              Create New Class
            </h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Class Name
                </label>
                <input
                  value={newClass.name}
                  onChange={(e) => setNewClass({ name: e.target.value })}
                  placeholder="e.g. Class 1, Grade 5, Nursery"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Default Section Capacity
                </label>
                <input
                  type="number"
                  min={1}
                  value={sectionCapacity}
                  onChange={(e) => setSectionCapacity(Number(e.target.value) || 40)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
            </div>

            {/* Section preset picker */}
            {presets.length > 0 && (
              <div className="mt-3">
                <label className="mb-2 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Sections to include
                </label>
                <div className="flex flex-wrap gap-2">
                  {presets.map((preset) => {
                    const selected = selectedPresets.includes(preset);
                    return (
                      <button
                        key={preset}
                        onClick={() => togglePresetSelection(preset)}
                        className={`rounded-full border px-3 py-1 text-xs font-medium transition-all ${
                          selected
                            ? 'border-indigo-500 bg-indigo-600 text-white'
                            : 'border-gray-300 bg-white text-gray-600 hover:border-indigo-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {selected && <span className="mr-1">✓</span>}
                        Section {preset}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {presets.length === 0 && (
              <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                💡 Go to "Section Presets" tab to add sections (A, B, C) first, then select them here.
              </p>
            )}

            <div className="mt-4 flex items-center gap-3">
              <button
                onClick={() => createClassMutation.mutate()}
                disabled={createClassMutation.isPending || !selectedYear?.id}
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                <Plus size={14} />
                {createClassMutation.isPending ? 'Creating...' : 'Create Class'}
              </button>
              {selectedPresets.length > 0 && (
                <span className="text-xs text-gray-500">
                  Will create with sections: {selectedPresets.join(', ')}
                </span>
              )}
            </div>
          </div>

          {/* Classes Table */}
          {classesQuery.isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
            </div>
          ) : classes.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center dark:border-gray-700">
              <BookOpen className="mx-auto mb-3 text-gray-400" size={36} />
              <p className="text-sm text-gray-500">No classes yet. Create your first class above.</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-900/40">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Class</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Sections</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Students</th>
                    <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {classes.map((cls: any) => (
                    <React.Fragment key={cls.id}>
                      <tr className="border-t border-gray-100 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900/20">
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                          {cls.name}
                        </td>
                        <td className="px-4 py-3">
                          {(() => {
                            const secs = classDetailsMap[cls.id]?.sections ?? cls.sections ?? [];
                            return secs.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {secs.map((s: any) => (
                                  <Badge key={s.id} label={s.name} />
                                ))}
                              </div>
                            ) : (
                              <span className="text-xs text-gray-400">–</span>
                            );
                          })()}
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                          {cls.student_count ?? 0}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="inline-flex items-center gap-2">
                            <button
                              onClick={() =>
                                setExpanded((prev) => ({ ...prev, [cls.id]: !prev[cls.id] }))
                              }
                              className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-2 py-1 text-xs hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                            >
                              {expanded[cls.id] ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                              Manage
                            </button>
                            {isSuperAdmin && (
                              <button
                                onClick={() => {
                                  if (window.confirm(`Delete class "${cls.name}"? This cannot be undone.`)) {
                                    deleteClassMutation.mutate(cls.id);
                                  }
                                }}
                                title="Delete class (Super Admin only)"
                                className="rounded-lg border border-red-200 p-1 text-red-400 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20"
                              >
                                <Trash2 size={13} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>

                      {/* Expanded manage row */}
                      {expanded[cls.id] && (
                        <tr className="border-t border-gray-100 bg-gray-50/60 dark:border-gray-700 dark:bg-gray-900/10">
                          <td colSpan={4} className="px-4 py-4">
                            <div className="grid gap-5 md:grid-cols-2">
                              {/* Sections */}
                              <div>
                                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                                  Sections
                                </h4>
                                <div className="mb-3 flex flex-wrap gap-2">
                                  {(() => {
                                    const secs = classDetailsMap[cls.id]?.sections ?? cls.sections ?? [];
                                    return secs.length === 0 ? (
                                      <p className="text-xs text-gray-400">No sections yet.</p>
                                    ) : (
                                      secs.map((sec: any) => (
                                        <div
                                          key={sec.id}
                                          className="inline-flex items-center gap-1 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs dark:border-indigo-800 dark:bg-indigo-900/20"
                                        >
                                          <span className="font-medium text-indigo-700 dark:text-indigo-400">
                                            Section {sec.name}
                                          </span>
                                          <span className="text-indigo-400">· {sec.capacity} seats</span>
                                          {sec.room_number && (
                                            <span className="text-indigo-400">· Room {sec.room_number}</span>
                                          )}
                                        </div>
                                      ))
                                    );
                                  })()}
                                </div>

                                {/* Add section from presets or custom */}
                                <div className="space-y-2">
                                  {presets.length > 0 && (
                                    <div>
                                      <p className="mb-1 text-xs text-gray-500">Add from presets:</p>
                                      <div className="flex flex-wrap gap-1">
                                        {presets
                                          .filter(
                                            (p) => {
                                              const secs = classDetailsMap[cls.id]?.sections ?? cls.sections ?? [];
                                              return !secs.some((s: any) => s.name === p);
                                            }
                                          )
                                          .map((preset) => (
                                            <button
                                              key={preset}
                                              onClick={() =>
                                                addSectionMutation.mutate({ classId: cls.id, name: preset })
                                              }
                                              className="inline-flex items-center gap-1 rounded-full border border-dashed border-indigo-300 px-2 py-0.5 text-xs text-indigo-600 hover:border-indigo-500 hover:bg-indigo-50 dark:border-indigo-700 dark:text-indigo-400"
                                            >
                                              <Plus size={10} />
                                              {preset}
                                            </button>
                                          ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Subjects */}
                              <div>
                                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                                  Class Subjects
                                </h4>
                                <div className="mb-2 flex flex-wrap gap-1">
                                  {(classSubjectsMap[cls.id] ?? []).map((row: any) => (
                                    <Badge
                                      key={row.subject_id}
                                      label={`${row.subject_name}${row.subject_code ? ` (${row.subject_code})` : ''}`}
                                      color="bg-green-100 text-green-700"
                                    />
                                  ))}
                                </div>
                                <div className="flex gap-2">
                                  <select
                                    value={subjectDrafts[cls.id]?.subject_id ?? ''}
                                    onChange={(e) =>
                                      setSubjectDrafts((p) => ({
                                        ...p,
                                        [cls.id]: { ...(p[cls.id] ?? { subject_id: '', teacher_id: '' }), subject_id: e.target.value },
                                      }))
                                    }
                                    className="flex-1 rounded-lg border border-gray-300 px-2 py-1.5 text-xs dark:border-gray-600 dark:bg-gray-800"
                                  >
                                    <option value="">Select subject…</option>
                                    {subjects.map((s: any) => (
                                      <option key={s.id} value={s.id}>{s.name}</option>
                                    ))}
                                  </select>
                                  <button
                                    onClick={() => {
                                      const payload = subjectDrafts[cls.id];
                                      if (!payload?.subject_id) return toast.error('Select a subject');
                                      assignSubjectMutation.mutate({ classId: cls.id, payload: { subject_id: payload.subject_id } });
                                    }}
                                    className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white"
                                  >
                                    Assign
                                  </button>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
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

export default ClassesPage;
