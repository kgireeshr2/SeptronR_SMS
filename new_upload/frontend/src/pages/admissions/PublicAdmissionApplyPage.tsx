import React from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { admissionsApi } from '@api/admissions';

const unwrap = (res: any) => res?.data ?? res;

const PublicAdmissionApplyPage: React.FC = () => {
  const { slug } = useParams();
  const [reference, setReference] = React.useState<string | null>(null);
  const [form, setForm] = React.useState({
    academic_year_id: '',
    applicant_name: '',
    date_of_birth: '',
    gender: '',
    parent_name: '',
    parent_phone: '',
    parent_email: '',
    address: '',
    previous_school: '',
  });
  const [files, setFiles] = React.useState<FileList | null>(null);

  const publicConfigQuery = useQuery({
    queryKey: ['public-admission-config', slug],
    enabled: !!slug,
    queryFn: async () => unwrap(await admissionsApi.getPublicConfig(slug || '')),
  });

  React.useEffect(() => {
    if (publicConfigQuery.data?.academic_year_id && !form.academic_year_id) {
      setForm((p) => ({ ...p, academic_year_id: publicConfigQuery.data.academic_year_id }));
    }
  }, [publicConfigQuery.data]);

  const submitMutation = useMutation({
    mutationFn: async () => {
      const body = new FormData();
      body.append('school_slug', slug || '');
      body.append('academic_year_id', form.academic_year_id);
      body.append('applicant_name', form.applicant_name);
      body.append('date_of_birth', form.date_of_birth);
      body.append('gender', form.gender);
      body.append('parent_name', form.parent_name);
      body.append('parent_phone', form.parent_phone);
      body.append('parent_email', form.parent_email);
      body.append('address', form.address);
      body.append('previous_school', form.previous_school);
      if (files) {
        Array.from(files).forEach((file) => body.append('files', file));
      }
      return unwrap(await admissionsApi.submitApplication(body));
    },
    onSuccess: (data: any) => {
      setReference(data?.reference_number ?? null);
      toast.success('Application submitted successfully');
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Submission failed'),
  });

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="mx-auto max-w-3xl rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="mb-1 text-2xl font-semibold">Online Admission Form</h1>
        <p className="mb-6 text-sm text-gray-500">School: {slug}</p>

        {publicConfigQuery.isLoading && (
          <p className="mb-4 text-sm text-gray-500">Loading admission configuration...</p>
        )}

        {reference ? (
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <p className="text-sm text-green-700">Application submitted.</p>
            <p className="mt-1 text-lg font-semibold text-green-800">Reference: {reference}</p>
            <p className="mt-1 text-xs text-green-700">Save this reference for tracking your application status.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {!form.academic_year_id && (
              <input className="w-full rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Academic Year ID (UUID)" value={form.academic_year_id} onChange={(e) => setForm((p) => ({ ...p, academic_year_id: e.target.value }))} />
            )}
            <div className="grid gap-3 md:grid-cols-2">
              <input className="rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Applicant Name" value={form.applicant_name} onChange={(e) => setForm((p) => ({ ...p, applicant_name: e.target.value }))} />
              <input type="date" className="rounded border border-gray-300 px-3 py-2 text-sm" value={form.date_of_birth} onChange={(e) => setForm((p) => ({ ...p, date_of_birth: e.target.value }))} />
              <input className="rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Gender" value={form.gender} onChange={(e) => setForm((p) => ({ ...p, gender: e.target.value }))} />
              <input className="rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Parent Name" value={form.parent_name} onChange={(e) => setForm((p) => ({ ...p, parent_name: e.target.value }))} />
              <input className="rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Parent Phone" value={form.parent_phone} onChange={(e) => setForm((p) => ({ ...p, parent_phone: e.target.value }))} />
              <input className="rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Parent Email" value={form.parent_email} onChange={(e) => setForm((p) => ({ ...p, parent_email: e.target.value }))} />
            </div>
            <textarea className="w-full rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Address" value={form.address} onChange={(e) => setForm((p) => ({ ...p, address: e.target.value }))} />
            <input className="w-full rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Previous School" value={form.previous_school} onChange={(e) => setForm((p) => ({ ...p, previous_school: e.target.value }))} />
            <input type="file" multiple onChange={(e) => setFiles(e.target.files)} className="text-sm" />

            <button
              onClick={() => {
                if (!slug || !form.academic_year_id || !form.applicant_name || !form.date_of_birth || !form.parent_name || !form.parent_phone) {
                  toast.error('Please fill required fields');
                  return;
                }
                submitMutation.mutate();
              }}
              className="rounded bg-brand-600 px-4 py-2 text-sm font-semibold text-white"
            >
              Submit Application
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PublicAdmissionApplyPage;
