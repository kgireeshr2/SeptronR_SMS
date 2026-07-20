import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import { homeworkApi } from '@/api/homework';
import api from '@/api/axios';
import { toast } from 'sonner';
import { formatDate } from '@utils/formatters';
import { X } from 'lucide-react';

type Tab = 'homework' | 'lesson-plans' | 'ptm';

interface Homework {
  id: string;
  title: string;
  class_id: string;
  subject_id: string;
  due_date: string;
  description: string;
  max_marks?: number;
}

interface LessonPlan {
  id: string;
  class_id: string;
  subject_id: string;
  plan_date: string;
  period_number: number;
  topic: string;
  objectives?: string;
  status: string;
}

interface PTMEvent {
  id: string;
  title: string;
  ptm_date: string;
  venue?: string;
  description?: string;
}

const statusColor: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  published: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
};

const Page: React.FC = () => {
  const [tab, setTab] = useState<Tab>('homework');

  // Homework
  const [homeworks, setHomeworks] = useState<Homework[]>([]);
  const [hwLoading, setHwLoading] = useState(false);
  const [showHwModal, setShowHwModal] = useState(false);
  const [hwForm, setHwForm] = useState({ title: '', class_id: '', subject_id: '', due_date: '', max_marks: '', description: '' });

  // Lesson Plans
  const [plans, setPlans] = useState<LessonPlan[]>([]);
  const [planLoading, setPlanLoading] = useState(false);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [planForm, setPlanForm] = useState({ class_id: '', subject_id: '', plan_date: '', period_number: '1', topic: '', objectives: '' });

  // PTM
  const [ptmEvents, setPtmEvents] = useState<PTMEvent[]>([]);
  const [ptmLoading, setPtmLoading] = useState(false);
  const [showPtmModal, setShowPtmModal] = useState(false);
  const [ptmForm, setPtmForm] = useState({ title: '', ptm_date: '', venue: '', description: '' });

  useEffect(() => {
    if (tab === 'homework') loadHomeworks();
    if (tab === 'lesson-plans') loadPlans();
    if (tab === 'ptm') loadPTM();
  }, [tab]);

  // Submissions modal
  const [subModal, setSubModal] = useState<Homework | null>(null);
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [subLoading, setSubLoading] = useState(false);

  const openSubmissions = async (hw: Homework) => {
    setSubModal(hw);
    setSubLoading(true);
    try {
      const r: any = await api.get(`/homework/${hw.id}/submissions`);
      setSubmissions(Array.isArray(r) ? r : (r?.data ?? []));
    } catch { setSubmissions([]); } finally { setSubLoading(false); }
  };

  const reviewSubmission = async (subId: string, marks: number, feedback: string) => {
    try {
      await api.put(`/homework/submissions/${subId}/review`, { marks_obtained: marks, feedback, status: 'graded' });
      toast.success('Submission graded');
      if (subModal) openSubmissions(subModal);
    } catch { toast.error('Failed to grade'); }
  };

  const loadHomeworks = async () => {
    setHwLoading(true);
    try { const r: any = await homeworkApi.list(); setHomeworks(Array.isArray(r) ? r : (r?.data ?? [])); } catch { /* ignore */ } finally { setHwLoading(false); }
  };
  const loadPlans = async () => {
    setPlanLoading(true);
    try { const r: any = await homeworkApi.listLessonPlans(); setPlans(Array.isArray(r) ? r : (r?.data ?? [])); } catch { /* ignore */ } finally { setPlanLoading(false); }
  };
  const loadPTM = async () => {
    setPtmLoading(true);
    try { const r: any = await homeworkApi.listPTMEvents(); setPtmEvents(Array.isArray(r) ? r : (r?.data ?? [])); } catch { /* ignore */ } finally { setPtmLoading(false); }
  };

  const saveHomework = async (e: React.FormEvent) => {
    e.preventDefault();
    await homeworkApi.create({ ...hwForm, max_marks: hwForm.max_marks ? +hwForm.max_marks : undefined });
    setShowHwModal(false); setHwForm({ title: '', class_id: '', subject_id: '', due_date: '', max_marks: '', description: '' });
    loadHomeworks();
  };
  const savePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    await homeworkApi.createLessonPlan({ ...planForm, period_number: +planForm.period_number });
    setShowPlanModal(false); setPlanForm({ class_id: '', subject_id: '', plan_date: '', period_number: '1', topic: '', objectives: '' });
    loadPlans();
  };
  const savePTM = async (e: React.FormEvent) => {
    e.preventDefault();
    await homeworkApi.createPTMEvent(ptmForm);
    setShowPtmModal(false); setPtmForm({ title: '', ptm_date: '', venue: '', description: '' });
    loadPTM();
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'homework', label: 'Homework' },
    { key: 'lesson-plans', label: 'Lesson Plans' },
    { key: 'ptm', label: 'Parent-Teacher Meetings' },
  ];

  return (
    <div>
      <PageHeader title="Homework & PTM" />

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-gray-200 dark:border-gray-700">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Homework Tab */}
      {tab === 'homework' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => setShowHwModal(true)} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              + Assign Homework
            </button>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  {['Title', 'Class', 'Subject', 'Due Date', 'Max Marks', 'Actions'].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {hwLoading ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
                ) : homeworks.length === 0 ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No homework assigned yet.</td></tr>
                ) : homeworks.map(hw => (
                  <tr key={hw.id} className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3 font-medium">{hw.title}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{hw.class_id}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{hw.subject_id}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{hw.due_date}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{hw.max_marks ?? '-'}</td>                      <td className="px-4 py-3"><button onClick={() => openSubmissions(hw)} className="rounded px-2 py-1 text-xs text-indigo-600 hover:bg-indigo-50">Submissions</button></td>                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {showHwModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
              <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
                <h3 className="mb-4 text-lg font-semibold">Assign Homework</h3>
                <form onSubmit={saveHomework} className="space-y-3">
                  {[
                    { label: 'Title', key: 'title', type: 'text' },
                    { label: 'Class ID', key: 'class_id', type: 'text' },
                    { label: 'Subject ID', key: 'subject_id', type: 'text' },
                    { label: 'Due Date', key: 'due_date', type: 'date' },
                    { label: 'Max Marks', key: 'max_marks', type: 'number' },
                  ].map(f => (
                    <div key={f.key}>
                      <label className="mb-1 block text-sm font-medium">{f.label}</label>
                      <input
                        type={f.type}
                        value={(hwForm as Record<string, string>)[f.key]}
                        onChange={e => setHwForm(p => ({ ...p, [f.key]: e.target.value }))}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                        required={['title', 'class_id', 'subject_id', 'due_date'].includes(f.key)}
                      />
                    </div>
                  ))}
                  <div>
                    <label className="mb-1 block text-sm font-medium">Description</label>
                    <textarea
                      value={hwForm.description}
                      onChange={e => setHwForm(p => ({ ...p, description: e.target.value }))}
                      rows={3}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                    />
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button type="button" onClick={() => setShowHwModal(false)} className="rounded-lg border px-4 py-2 text-sm">Cancel</button>
                    <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">Save</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Lesson Plans Tab */}
      {tab === 'lesson-plans' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => setShowPlanModal(true)} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              + Create Lesson Plan
            </button>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  {['Date', 'Class', 'Subject', 'Period', 'Topic', 'Status'].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {planLoading ? (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
                ) : plans.length === 0 ? (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No lesson plans yet.</td></tr>
                ) : plans.map(p => (
                  <tr key={p.id} className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">{p.plan_date}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{p.class_id}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{p.subject_id}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{p.period_number}</td>
                    <td className="px-4 py-3 font-medium">{p.topic}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-1 text-xs font-medium ${statusColor[p.status] ?? 'bg-gray-100 text-gray-600'}`}>
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {showPlanModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
              <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
                <h3 className="mb-4 text-lg font-semibold">Create Lesson Plan</h3>
                <form onSubmit={savePlan} className="space-y-3">
                  {[
                    { label: 'Class ID', key: 'class_id', type: 'text' },
                    { label: 'Subject ID', key: 'subject_id', type: 'text' },
                    { label: 'Plan Date', key: 'plan_date', type: 'date' },
                    { label: 'Period Number', key: 'period_number', type: 'number' },
                    { label: 'Topic', key: 'topic', type: 'text' },
                    { label: 'Objectives', key: 'objectives', type: 'text' },
                  ].map(f => (
                    <div key={f.key}>
                      <label className="mb-1 block text-sm font-medium">{f.label}</label>
                      <input
                        type={f.type}
                        value={(planForm as Record<string, string>)[f.key]}
                        onChange={e => setPlanForm(p => ({ ...p, [f.key]: e.target.value }))}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                        required={['class_id', 'subject_id', 'plan_date', 'period_number', 'topic'].includes(f.key)}
                      />
                    </div>
                  ))}
                  <div className="flex justify-end gap-2 pt-2">
                    <button type="button" onClick={() => setShowPlanModal(false)} className="rounded-lg border px-4 py-2 text-sm">Cancel</button>
                    <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">Save</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* PTM Tab */}
      {tab === 'ptm' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => setShowPtmModal(true)} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              + Schedule PTM
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {ptmLoading ? (
              <p className="col-span-3 text-center text-gray-500">Loading...</p>
            ) : ptmEvents.length === 0 ? (
              <p className="col-span-3 text-center text-gray-500">No PTM events scheduled.</p>
            ) : ptmEvents.map(ev => (
              <div key={ev.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h4 className="font-semibold text-gray-900 dark:text-white">{ev.title}</h4>
                <p className="mt-1 text-sm text-gray-500">{ev.ptm_date}</p>
                {ev.venue && <p className="text-sm text-gray-500">Venue: {ev.venue}</p>}
                {ev.description && <p className="mt-2 text-xs text-gray-400">{ev.description}</p>}
              </div>
            ))}
          </div>

          {showPtmModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
              <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
                <h3 className="mb-4 text-lg font-semibold">Schedule PTM Event</h3>
                <form onSubmit={savePTM} className="space-y-3">
                  {[
                    { label: 'Title', key: 'title', type: 'text' },
                    { label: 'Date', key: 'ptm_date', type: 'date' },
                    { label: 'Venue', key: 'venue', type: 'text' },
                    { label: 'Description', key: 'description', type: 'text' },
                  ].map(f => (
                    <div key={f.key}>
                      <label className="mb-1 block text-sm font-medium">{f.label}</label>
                      <input
                        type={f.type}
                        value={(ptmForm as Record<string, string>)[f.key]}
                        onChange={e => setPtmForm(p => ({ ...p, [f.key]: e.target.value }))}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                        required={['title', 'ptm_date'].includes(f.key)}
                      />
                    </div>
                  ))}
                  <div className="flex justify-end gap-2 pt-2">
                    <button type="button" onClick={() => setShowPtmModal(false)} className="rounded-lg border px-4 py-2 text-sm">Cancel</button>
                    <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">Save</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
      {/* Submissions Modal */}
      {subModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800 max-h-[90vh] flex flex-col">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold dark:text-white">Submissions — {subModal.title}</h3>
              <button onClick={() => setSubModal(null)}><X size={18} className="text-gray-400" /></button>
            </div>
            {subLoading ? <p className="py-8 text-center text-gray-400">Loading…</p> : (
              <div className="overflow-y-auto flex-1">
                {submissions.length === 0 ? <p className="py-8 text-center text-gray-400">No submissions yet.</p> : (
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-700/50">
                      <tr>{['Student','Submitted At','Status','Marks','Feedback','Action'].map(h=><th key={h} className="px-3 py-2 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {submissions.map((s: any) => (
                        <SubmissionRow key={s.id} s={s} maxMarks={subModal.max_marks} onGrade={reviewSubmission} />
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const SubmissionRow: React.FC<{ s: any; maxMarks?: number; onGrade: (id: string, marks: number, feedback: string) => void }> = ({ s, maxMarks, onGrade }) => {
  const [marks, setMarks] = React.useState(s.marks_obtained ?? '');
  const [feedback, setFeedback] = React.useState(s.feedback ?? '');
  return (
    <tr>
      <td className="px-3 py-2">{s.student_name ?? s.student_id}</td>
      <td className="px-3 py-2 text-xs text-gray-500">{formatDate(s.submitted_at)}</td>
      <td className="px-3 py-2 capitalize">{s.status}</td>
      <td className="px-3 py-2 w-20"><input type="number" value={marks} onChange={e => setMarks(e.target.value)} className="w-full rounded border px-2 py-1 text-xs" placeholder={`/${maxMarks ?? '—'}`} /></td>
      <td className="px-3 py-2"><input value={feedback} onChange={e => setFeedback(e.target.value)} className="w-full rounded border px-2 py-1 text-xs" placeholder="Feedback…" /></td>
      <td className="px-3 py-2"><button onClick={() => onGrade(s.id, Number(marks), feedback)} className="rounded bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700">Grade</button></td>
    </tr>
  );
};

export default Page;
