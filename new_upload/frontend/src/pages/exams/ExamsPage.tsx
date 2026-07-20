import React from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import { toast } from 'sonner';
import { examsApi, Exam, ExamType, GradingScale, GradeRange, ExamMarkResponse, MarkEntryItem } from '@api/exams';
import { academicYearsApi } from '@api/academicYears';
import { classesApi } from '@api/classes';
import { useAcademicYearStore } from '@store/academicYearStore';

const unwrap = (res: any) => res?.data ?? res;

const TABS = ['Exams', 'Exam Types', 'Grading Scale', 'Report Cards', 'Admit Cards'] as const;
type Tab = typeof TABS[number];

const STATUS_COLORS: Record<string, string> = {
  scheduled: 'bg-blue-100 text-blue-700',
  ongoing: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
  results_published: 'bg-purple-100 text-purple-700',
};

const RESULT_COLORS: Record<string, string> = {
  Pass: 'text-green-600 font-semibold',
  Fail: 'text-red-600 font-semibold',
  Absent: 'text-yellow-600',
  Exempted: 'text-gray-500',
  Pending: 'text-gray-400',
};

const Page: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState<Tab>('Exams');

  // ── Common state ─────────────────────────────────────────────────
  const [years, setYears] = React.useState<any[]>([]);
  const [classes, setClasses] = React.useState<any[]>([]);
  const [exams, setExams] = React.useState<Exam[]>([]);
  const [examTypes, setExamTypes] = React.useState<ExamType[]>([]);
  const [gradingScale, setGradingScale] = React.useState<GradingScale | null>(null);

  const { selectedYear } = useAcademicYearStore();

  // ── Filters ───────────────────────────────────────────────────────
  const [yearId, setYearId] = React.useState('');
  const [classId, setClassId] = React.useState('');
  const [examTypeId, setExamTypeId] = React.useState('');

  // ── Create Exam ───────────────────────────────────────────────────
  const [showCreateExam, setShowCreateExam] = React.useState(false);
  const [newExam, setNewExam] = React.useState<Partial<Exam>>({
    full_marks: 100, pass_marks: 35,
  });

  // ── Marks entry ───────────────────────────────────────────────────
  const [selectedExam, setSelectedExam] = React.useState<Exam | null>(null);
  const [marks, setMarks] = React.useState<ExamMarkResponse[]>([]);
  const [markEntries, setMarkEntries] = React.useState<Record<string, number | undefined>>({});
  const [absentEntries, setAbsentEntries] = React.useState<Record<string, boolean>>({});
  const [loadingMarks, setLoadingMarks] = React.useState(false);

  // ── Exam Types ────────────────────────────────────────────────────
  const [newTypeName, setNewTypeName] = React.useState('');
  const [newTypeWeightage, setNewTypeWeightage] = React.useState(100);

  // ── Grading Scale ─────────────────────────────────────────────────
  const [editRanges, setEditRanges] = React.useState<GradeRange[]>([]);
  const [scaleName, setScaleName] = React.useState('Default');
  const [loading, setLoading] = React.useState(false);

  // ── Load data ─────────────────────────────────────────────────────
  React.useEffect(() => {
    Promise.all([
      academicYearsApi.list().then(unwrap),
      examsApi.listExamTypes().then(unwrap),
      examsApi.getGradingScale().then(unwrap),
    ]).then(([ys, et, gs]) => {
      setYears(ys ?? []);
      setExamTypes(et ?? []);
      if (gs) {
        setGradingScale(gs);
        setEditRanges(gs.ranges ?? []);
        setScaleName(gs.name ?? 'Default');
      }
      // Auto-select the active academic year — classes will load via the yearId useEffect
      const yearRows: any[] = ys ?? [];
      const defaultId = selectedYear?.id || yearRows.find((y: any) => y.is_current)?.id || yearRows[0]?.id;
      if (defaultId) {
        setYearId(defaultId);
        setNewExam((p) => ({ ...p, academic_year_id: p.academic_year_id || defaultId }));
      }
    }).catch(() => {});
  }, []);

  // Reload classes when year filter changes
  React.useEffect(() => {
    if (!yearId) return;
    classesApi.list(yearId).then(unwrap).then((r) => {
      setClasses(Array.isArray(r) ? r : (r?.items ?? []));
    }).catch(() => {});
  }, [yearId]);

  React.useEffect(() => {
    examsApi.listExams({
      year_id: yearId || undefined,
      class_id: classId || undefined,
      exam_type_id: examTypeId || undefined,
    }).then(unwrap).then(setExams).catch(() => {});
  }, [yearId, classId, examTypeId]);

  // ── Open marks panel ──────────────────────────────────────────────
  const openMarks = async (exam: Exam) => {
    setSelectedExam(exam);
    setLoadingMarks(true);
    try {
      const existing = unwrap(await examsApi.getMarks(exam.id));
      setMarks(existing ?? []);
      const ent: Record<string, number | undefined> = {};
      const abs: Record<string, boolean> = {};
      (existing ?? []).forEach((m: ExamMarkResponse) => {
        ent[m.student_id] = m.marks_obtained ?? undefined;
        abs[m.student_id] = m.is_absent;
      });
      setMarkEntries(ent);
      setAbsentEntries(abs);
    } finally {
      setLoadingMarks(false);
    }
  };

  // ── Save marks ────────────────────────────────────────────────────
  const saveMarks = async () => {
    if (!selectedExam) return;
    const entries: MarkEntryItem[] = marks.map((m) => ({
      student_id: m.student_id,
      marks_obtained: absentEntries[m.student_id] ? undefined : markEntries[m.student_id],
      is_absent: absentEntries[m.student_id] ?? false,
      is_exempted: m.is_exempted,
    }));
    setLoading(true);
    try {
      const updated = unwrap(await examsApi.enterMarks(selectedExam.id, entries));
      setMarks(updated ?? marks);
      toast.success('Marks saved');
    } catch {
      toast.error('Failed to save marks');
    } finally {
      setLoading(false);
    }
  };

  // ── Create exam ───────────────────────────────────────────────────
  const createExam = async () => {
    setLoading(true);
    try {
      const created = unwrap(await examsApi.createExam(newExam));
      setExams((prev) => [created, ...prev]);
      setShowCreateExam(false);
      setNewExam({ full_marks: 100, pass_marks: 35 });
      toast.success('Exam created');
    } catch {
      toast.error('Failed to create exam');
    } finally {
      setLoading(false);
    }
  };

  // ── Delete exam ───────────────────────────────────────────────────
  const deleteExam = async (id: string) => {
    if (!confirm('Delete this exam?')) return;
    await examsApi.deleteExam(id).then(() => {
      setExams((prev) => prev.filter((e) => e.id !== id));
      toast.success('Exam deleted');
    }).catch(() => toast.error('Failed'));
  };

  // ── Publish Results ───────────────────────────────────────────────
  const publishResults = async (exam: Exam) => {
    if (!confirm(`Publish results for "${exam.name}"? This will notify students/parents.`)) return;
    try {
      await examsApi.publishResults(exam.id);
      setExams(prev => prev.map(e => e.id === exam.id ? { ...e, status: 'results_published' as any } : e));
      toast.success('Results published successfully');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to publish results');
    }
  };

  // ── Exam Types CRUD ───────────────────────────────────────────────
  const addExamType = async () => {
    if (!newTypeName.trim()) return;
    setLoading(true);
    try {
      const created = unwrap(await examsApi.createExamType({ name: newTypeName, weightage: newTypeWeightage }));
      setExamTypes((prev) => [...prev, created]);
      setNewTypeName('');
      toast.success('Exam type added');
    } catch {
      toast.error('Failed');
    } finally {
      setLoading(false);
    }
  };

  const deleteExamType = async (id: string) => {
    if (!confirm('Delete exam type?')) return;
    await examsApi.deleteExamType(id).then(() => {
      setExamTypes((prev) => prev.filter((t) => t.id !== id));
      toast.success('Deleted');
    }).catch(() => toast.error('Failed'));
  };

  // ── Grading scale ─────────────────────────────────────────────────
  const saveScale = async () => {
    setLoading(true);
    try {
      const saved = unwrap(await examsApi.upsertGradingScale({ name: scaleName, ranges: editRanges }));
      setGradingScale(saved);
      toast.success('Grading scale saved');
    } catch {
      toast.error('Failed');
    } finally {
      setLoading(false);
    }
  };

  const addRange = () =>
    setEditRanges((prev) => [...prev, { grade: '', min_pct: 0, max_pct: 0, grade_point: 0 }]);

  const removeRange = (i: number) =>
    setEditRanges((prev) => prev.filter((_, idx) => idx !== i));

  const updateRange = (i: number, field: keyof GradeRange, value: string | number) =>
    setEditRanges((prev) => prev.map((r, idx) => idx === i ? { ...r, [field]: value } : r));

  // ── Load students into marks view on selection ────────────────────
  const loadStudentsForExam = async (exam: Exam) => {
    // If no marks yet, initialise with empty entries from server
    if (marks.length === 0 || selectedExam?.id !== exam.id) {
      await openMarks(exam);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Exam Management" />

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === t
                ? 'border-brand-500 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* ── Exams Tab ─────────────────────────────────────────────── */}
      {activeTab === 'Exams' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <select
              className="input w-48"
              value={yearId}
              onChange={(e) => setYearId(e.target.value)}
            >
              <option value="">All Academic Years</option>
              {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
            </select>
            <select
              className="input w-40"
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
            >
              <option value="">All Classes</option>
              {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <select
              className="input w-48"
              value={examTypeId}
              onChange={(e) => setExamTypeId(e.target.value)}
            >
              <option value="">All Exam Types</option>
              {examTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
            <button
              onClick={() => setShowCreateExam(true)}
              className="ml-auto btn-primary"
            >
              + Add Exam
            </button>
          </div>

          {/* Create Exam Modal */}
          {showCreateExam && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
              <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
                <h3 className="mb-4 text-lg font-semibold">Create Exam</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <label className="label">Exam Name</label>
                    <input
                      className="input w-full"
                      placeholder="e.g. Half Yearly – Mathematics – Class 10"
                      value={newExam.name ?? ''}
                      onChange={(e) => setNewExam({ ...newExam, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Academic Year</label>
                    <select
                      className="input w-full"
                      value={newExam.academic_year_id ?? ''}
                      onChange={(e) => setNewExam({ ...newExam, academic_year_id: e.target.value })}
                    >
                      <option value="">Select Year</option>
                      {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="label">Exam Type</label>
                    <select
                      className="input w-full"
                      value={newExam.exam_type_id ?? ''}
                      onChange={(e) => setNewExam({ ...newExam, exam_type_id: e.target.value })}
                    >
                      <option value="">Select Type</option>
                      {examTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="label">Class</label>
                    <select
                      className="input w-full"
                      value={newExam.class_id ?? ''}
                      onChange={(e) => setNewExam({ ...newExam, class_id: e.target.value })}
                    >
                      <option value="">Select Class</option>
                      {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="label">Exam Date</label>
                    <input
                      type="date"
                      className="input w-full"
                      value={newExam.exam_date ?? ''}
                      onChange={(e) => setNewExam({ ...newExam, exam_date: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Full Marks</label>
                    <input
                      type="number"
                      className="input w-full"
                      value={newExam.full_marks ?? 100}
                      onChange={(e) => setNewExam({ ...newExam, full_marks: +e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Pass Marks</label>
                    <input
                      type="number"
                      className="input w-full"
                      value={newExam.pass_marks ?? 35}
                      onChange={(e) => setNewExam({ ...newExam, pass_marks: +e.target.value })}
                    />
                  </div>
                </div>
                <div className="mt-4 flex justify-end gap-2">
                  <button onClick={() => setShowCreateExam(false)} className="btn-outline">Cancel</button>
                  <button onClick={createExam} disabled={loading} className="btn-primary">
                    {loading ? 'Creating...' : 'Create'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Exam list */}
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-100 bg-gray-50 dark:border-gray-700 dark:bg-gray-700/50">
                <tr>
                  {['Name', 'Type', 'Class', 'Date', 'Full Marks', 'Pass', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {exams.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-gray-400">No exams found. Create one above.</td>
                  </tr>
                )}
                {exams.map((exam) => (
                  <tr key={exam.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-4 py-3 font-medium text-gray-800 dark:text-gray-200">{exam.name}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {examTypes.find((t) => t.id === exam.exam_type_id)?.name ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {classes.find((c: any) => c.id === exam.class_id)?.name ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{exam.exam_date ?? '—'}</td>
                    <td className="px-4 py-3 text-center">{exam.full_marks}</td>
                    <td className="px-4 py-3 text-center">{exam.pass_marks}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[exam.status] ?? 'bg-gray-100 text-gray-600'}`}>
                        {exam.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2 flex-wrap">
                        <button
                          onClick={() => openMarks(exam)}
                          className="text-xs text-brand-600 hover:underline"
                        >
                          Marks
                        </button>
                        {exam.status === 'completed' && (
                          <button
                            onClick={() => publishResults(exam)}
                            className="text-xs text-green-600 hover:underline font-medium"
                          >
                            Publish
                          </button>
                        )}
                        {exam.status === 'results_published' && (
                          <span className="text-xs text-green-500">✓ Published</span>
                        )}
                        <button
                          onClick={() => deleteExam(exam.id)}
                          className="text-xs text-red-500 hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Marks Panel */}
          {selectedExam && (
            <div className="rounded-xl border border-brand-200 bg-white p-6 shadow-sm dark:border-brand-700 dark:bg-gray-800">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-base font-semibold">
                  Mark Entry — <span className="text-brand-600">{selectedExam.name}</span>
                  <span className="ml-2 text-sm text-gray-500">(Full: {selectedExam.full_marks} | Pass: {selectedExam.pass_marks})</span>
                </h3>
                <button onClick={() => setSelectedExam(null)} className="text-sm text-gray-400 hover:text-gray-600">✕ Close</button>
              </div>

              {loadingMarks ? (
                <p className="text-sm text-gray-400">Loading students…</p>
              ) : marks.length === 0 ? (
                <p className="text-sm text-gray-400">No students enrolled or marks not loaded yet.</p>
              ) : (
                <>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-500 dark:border-gray-700">
                        <th className="pb-2 pr-4">Student</th>
                        <th className="pb-2 pr-4">Admission No.</th>
                        <th className="pb-2 pr-4">Absent</th>
                        <th className="pb-2 pr-4">Marks (/{selectedExam.full_marks})</th>
                        <th className="pb-2 pr-4">Grade</th>
                        <th className="pb-2">Result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {marks.map((m) => {
                        const absent = absentEntries[m.student_id] ?? m.is_absent;
                        const marksVal = markEntries[m.student_id];
                        const pct = marksVal != null ? (marksVal / selectedExam.full_marks) * 100 : null;
                        const pass = marksVal != null && marksVal >= selectedExam.pass_marks;
                        return (
                          <tr key={m.student_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/20">
                            <td className="py-2 pr-4 font-medium text-gray-800 dark:text-gray-200">{m.student_name}</td>
                            <td className="py-2 pr-4 text-gray-500">{m.admission_number}</td>
                            <td className="py-2 pr-4">
                              <input
                                type="checkbox"
                                checked={absent}
                                onChange={(e) => setAbsentEntries((prev) => ({ ...prev, [m.student_id]: e.target.checked }))}
                                className="h-4 w-4 rounded"
                              />
                            </td>
                            <td className="py-2 pr-4">
                              <input
                                type="number"
                                disabled={absent}
                                min={0}
                                max={selectedExam.full_marks}
                                className="input w-24 disabled:opacity-50"
                                value={absent ? '' : (marksVal ?? '')}
                                onChange={(e) => setMarkEntries((prev) => ({ ...prev, [m.student_id]: +e.target.value }))}
                              />
                            </td>
                            <td className="py-2 pr-4 font-medium text-gray-700 dark:text-gray-300">
                              {absent ? '—' : m.grade ?? (pct != null ? `${pct.toFixed(0)}%` : '—')}
                            </td>
                            <td className={`py-2 ${absent ? 'text-yellow-600' : pass ? RESULT_COLORS['Pass'] : marksVal != null ? RESULT_COLORS['Fail'] : 'text-gray-400'}`}>
                              {absent ? 'Absent' : marksVal != null ? (pass ? 'Pass' : 'Fail') : '—'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <div className="mt-4 flex justify-end">
                    <button onClick={saveMarks} disabled={loading} className="btn-primary">
                      {loading ? 'Saving…' : 'Save Marks'}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Exam Types Tab ────────────────────────────────────────── */}
      {activeTab === 'Exam Types' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Add Exam Type</h3>
            <div className="flex gap-3">
              <input
                className="input flex-1"
                placeholder="Type name (e.g. Unit Test 1, Half Yearly)"
                value={newTypeName}
                onChange={(e) => setNewTypeName(e.target.value)}
              />
              <input
                type="number"
                className="input w-32"
                placeholder="Weightage %"
                value={newTypeWeightage}
                onChange={(e) => setNewTypeWeightage(+e.target.value)}
              />
              <button onClick={addExamType} disabled={loading} className="btn-primary">
                Add
              </button>
            </div>
          </div>

          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-100 bg-gray-50 dark:border-gray-700 dark:bg-gray-700/50">
                <tr>
                  {['Name', 'Weightage', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {examTypes.length === 0 && (
                  <tr><td colSpan={4} className="py-8 text-center text-gray-400">No exam types yet.</td></tr>
                )}
                {examTypes.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-4 py-3 font-medium text-gray-800 dark:text-gray-200">{t.name}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{t.weightage}%</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {t.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => deleteExamType(t.id)} className="text-xs text-red-500 hover:underline">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Grading Scale Tab ──────────────────────────────────────── */}
      {activeTab === 'Grading Scale' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Grading Scale</h3>
                <input
                  className="input w-48"
                  placeholder="Scale name"
                  value={scaleName}
                  onChange={(e) => setScaleName(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <button onClick={addRange} className="btn-outline text-sm">+ Add Range</button>
                <button onClick={saveScale} disabled={loading} className="btn-primary text-sm">
                  {loading ? 'Saving…' : 'Save Scale'}
                </button>
              </div>
            </div>

            {editRanges.length === 0 ? (
              <p className="text-sm text-gray-400">No grade ranges. Add one above.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-500 dark:border-gray-700">
                    <th className="pb-2 pr-3">Grade</th>
                    <th className="pb-2 pr-3">Min %</th>
                    <th className="pb-2 pr-3">Max %</th>
                    <th className="pb-2 pr-3">Grade Point</th>
                    <th className="pb-2 pr-3">Description</th>
                    <th className="pb-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {editRanges.map((r, i) => (
                    <tr key={i}>
                      <td className="py-1.5 pr-3">
                        <input className="input w-16" value={r.grade} onChange={(e) => updateRange(i, 'grade', e.target.value)} />
                      </td>
                      <td className="py-1.5 pr-3">
                        <input type="number" className="input w-20" value={r.min_pct} onChange={(e) => updateRange(i, 'min_pct', +e.target.value)} />
                      </td>
                      <td className="py-1.5 pr-3">
                        <input type="number" className="input w-20" value={r.max_pct} onChange={(e) => updateRange(i, 'max_pct', +e.target.value)} />
                      </td>
                      <td className="py-1.5 pr-3">
                        <input type="number" step="0.1" className="input w-20" value={r.grade_point} onChange={(e) => updateRange(i, 'grade_point', +e.target.value)} />
                      </td>
                      <td className="py-1.5 pr-3">
                        <input className="input w-36" value={r.description ?? ''} onChange={(e) => updateRange(i, 'description', e.target.value)} />
                      </td>
                      <td className="py-1.5">
                        <button onClick={() => removeRange(i)} className="text-red-400 hover:text-red-600">✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ── Report Cards Tab ──────────────────────────────────────── */}
      {activeTab === 'Report Cards' && (
        <ReportCardsTab
          exams={exams}
          examTypes={examTypes}
          years={years}
          classes={classes}
          yearId={yearId}
          classId={classId}
          examTypeId={examTypeId}
          setYearId={setYearId}
          setClassId={setClassId}
          setExamTypeId={setExamTypeId}
        />
      )}

      {/* ── Admit Cards Tab ───────────────────────────────────────── */}
      {activeTab === 'Admit Cards' && (
        <AdmitCardsTab
          examTypes={examTypes}
          years={years}
          classes={classes}
        />
      )}
    </div>
  );
};

// ── Report Cards Sub-Component ────────────────────────────────────────────────
const ReportCardsTab: React.FC<{
  exams: any[];
  examTypes: any[];
  years: any[];
  classes: any[];
  yearId: string;
  classId: string;
  examTypeId: string;
  setYearId: (v: string) => void;
  setClassId: (v: string) => void;
  setExamTypeId: (v: string) => void;
}> = ({ exams, examTypes, years, classes, yearId, classId, examTypeId, setYearId, setClassId, setExamTypeId }) => {
  const [studentId, setStudentId] = React.useState('');
  const [downloading, setDownloading] = React.useState(false);
  const [students, setStudents] = React.useState<any[]>([]);

  React.useEffect(() => {
    if (!classId || !yearId) { setStudents([]); return; }
    import('@api/students').then(({ studentsApi }) =>
      studentsApi.list({ class_id: classId, academic_year_id: yearId })
        .then((r: any) => setStudents((r?.data ?? r) ?? []))
        .catch(() => {})
    );
  }, [classId, yearId]);

  const selectedExam = exams.find((e) => e.exam_type_id === examTypeId);

  const handleDownload = async (sid: string) => {
    if (!selectedExam || !yearId) return;
    setDownloading(true);
    try {
      const api = (await import('@api/axios')).default;
      const res = await api.get(
        `/exams/${selectedExam.id}/report-card/${sid}/pdf`,
        { params: { year_id: yearId }, responseType: 'blob' }
      );
      const url = URL.createObjectURL(new Blob([res as any], { type: 'application/pdf' }));
      const a = document.createElement('a'); a.href = url; a.download = `report_card_${sid}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch {
      (await import('sonner')).toast.error('Failed to generate report card');
    } finally { setDownloading(false); }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h3 className="mb-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Generate Report Cards</h3>
        <div className="flex flex-wrap gap-3 mb-5">
          <select className="input w-48" value={yearId} onChange={(e) => setYearId(e.target.value)}>
            <option value="">Select Academic Year</option>
            {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
          </select>
          <select className="input w-40" value={classId} onChange={(e) => setClassId(e.target.value)}>
            <option value="">Select Class</option>
            {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select className="input w-48" value={examTypeId} onChange={(e) => setExamTypeId(e.target.value)}>
            <option value="">Select Exam Type</option>
            {examTypes.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </div>

        {students.length === 0 && classId && yearId ? (
          <p className="text-sm text-gray-400">No students found for selected class/year.</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-100 dark:border-gray-700">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  {['Student', 'Admission No.', 'Action'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {students.map((s: any) => (
                  <tr key={s.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-4 py-3 font-medium">{s.first_name} {s.last_name}</td>
                    <td className="px-4 py-3 text-gray-500">{s.admission_number}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleDownload(s.id)}
                        disabled={!examTypeId || !yearId || downloading}
                        className="text-xs text-brand-600 hover:underline disabled:text-gray-400 disabled:no-underline"
                      >
                        Download PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {(!classId || !yearId) && (
          <p className="text-sm text-gray-400">Select academic year and class to list students.</p>
        )}
      </div>
    </div>
  );
};

// ── Admit Cards Sub-Component ─────────────────────────────────────────────────
const AdmitCardsTab: React.FC<{
  examTypes: any[];
  years: any[];
  classes: any[];
}> = ({ examTypes, years, classes }) => {
  const [yearId, setYearId] = React.useState('');
  const [classId, setClassId] = React.useState('');
  const [examTypeId, setExamTypeId] = React.useState('');
  const [downloading, setDownloading] = React.useState(false);

  const handleDownload = async () => {
    if (!examTypeId || !classId || !yearId) {
      (await import('sonner')).toast.error('Please select exam type, class, and academic year');
      return;
    }
    setDownloading(true);
    try {
      const api = (await import('@api/axios')).default;
      const res = await api.get(
        `/admit-card-configs/${examTypeId}/admit-cards/pdf`,
        { params: { class_id: classId, year_id: yearId }, responseType: 'blob' }
      );
      const url = URL.createObjectURL(new Blob([res as any], { type: 'application/pdf' }));
      const a = document.createElement('a'); a.href = url; a.download = 'admit_cards.pdf'; a.click();
      URL.revokeObjectURL(url);
    } catch {
      (await import('sonner')).toast.error('Failed to generate admit cards');
    } finally { setDownloading(false); }
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <h3 className="mb-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Generate Admit Cards (Hall Tickets)</h3>
      <p className="mb-4 text-sm text-gray-500">Generate admit cards for all students in a class for a given exam.</p>
      <div className="flex flex-wrap gap-3 mb-5">
        <select className="input w-48" value={yearId} onChange={(e) => setYearId(e.target.value)}>
          <option value="">Select Academic Year</option>
          {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
        </select>
        <select className="input w-40" value={classId} onChange={(e) => setClassId(e.target.value)}>
          <option value="">Select Class</option>
          {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select className="input w-48" value={examTypeId} onChange={(e) => setExamTypeId(e.target.value)}>
          <option value="">Select Exam Type</option>
          {examTypes.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <button
          onClick={handleDownload}
          disabled={!examTypeId || !classId || !yearId || downloading}
          className="btn-primary"
        >
          {downloading ? 'Generating…' : 'Download Admit Cards PDF'}
        </button>
      </div>
      <div className="rounded-lg bg-blue-50 p-3 text-sm text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
        <strong>Note:</strong> This will generate one admit card per student in the selected class.
        Each card includes the exam schedule for all subjects in the selected exam type.
      </div>
    </div>
  );
};

export default Page;
