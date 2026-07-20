import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Plus, Trash2 } from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { subjectsApi } from '@api/classes';

const unwrap = (res: any) => res?.data ?? res;

const SubjectsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [draft, setDraft] = React.useState({ name: '', code: '', full_marks: 100, pass_marks: 35, is_elective: false });

  const subjectsQuery = useQuery({
    queryKey: ['subjects-full'],
    queryFn: async () => {
      const data = unwrap(await subjectsApi.list());
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  const createMutation = useMutation({
    mutationFn: () => subjectsApi.create(draft),
    onSuccess: () => {
      toast.success('Subject created');
      setDraft({ name: '', code: '', full_marks: 100, pass_marks: 35, is_elective: false });
      queryClient.invalidateQueries({ queryKey: ['subjects-full'] });
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Failed to create subject'),
  });

  const deleteMutation = useMutation({
    mutationFn: (subjectId: string) => subjectsApi.remove(subjectId),
    onSuccess: () => {
      toast.success('Subject deleted');
      queryClient.invalidateQueries({ queryKey: ['subjects-full'] });
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Failed to delete subject'),
  });

  const subjects = subjectsQuery.data ?? [];

  return (
    <div>
      <PageHeader title="Subjects" subtitle="Create and maintain school subjects" />

      <div className="mb-4 grid gap-3 md:grid-cols-6">
        <input
          value={draft.name}
          onChange={(e) => setDraft((p) => ({ ...p, name: e.target.value }))}
          placeholder="Name"
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <input
          value={draft.code}
          onChange={(e) => setDraft((p) => ({ ...p, code: e.target.value }))}
          placeholder="Code"
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <input
          type="number"
          min={1}
          value={draft.full_marks}
          onChange={(e) => setDraft((p) => ({ ...p, full_marks: Number(e.target.value || 100) }))}
          placeholder="Full marks"
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <input
          type="number"
          min={1}
          value={draft.pass_marks}
          onChange={(e) => setDraft((p) => ({ ...p, pass_marks: Number(e.target.value || 35) }))}
          placeholder="Pass marks"
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <label className="inline-flex items-center gap-2 rounded border border-gray-300 px-3 py-2 text-sm">
          <input
            type="checkbox"
            checked={draft.is_elective}
            onChange={(e) => setDraft((p) => ({ ...p, is_elective: e.target.checked }))}
          />
          Elective
        </label>
        <button
          onClick={() => {
            if (!draft.name) return toast.error('Subject name is required');
            if (draft.pass_marks > draft.full_marks) return toast.error('Pass marks cannot exceed full marks');
            createMutation.mutate();
          }}
          className="inline-flex items-center justify-center gap-2 rounded bg-brand-600 px-3 py-2 text-sm font-semibold text-white"
        >
          <Plus size={14} />
          Add Subject
        </button>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-900/40">
            <tr>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Code</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Marks</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {subjects.map((subject: any) => (
              <tr key={subject.id} className="border-t border-gray-100 dark:border-gray-700">
                <td className="px-4 py-3 font-medium">{subject.name}</td>
                <td className="px-4 py-3">{subject.code || '-'}</td>
                <td className="px-4 py-3">{subject.is_elective ? 'Elective' : 'Core'}</td>
                <td className="px-4 py-3">{subject.pass_marks}/{subject.full_marks}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => deleteMutation.mutate(subject.id)}
                    className="inline-flex items-center gap-1 rounded border border-red-200 px-2 py-1 text-xs text-red-700"
                  >
                    <Trash2 size={13} />
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SubjectsPage;
