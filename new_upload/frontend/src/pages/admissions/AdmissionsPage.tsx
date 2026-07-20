import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ClipboardList, Plus, X } from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { admissionsApi } from '@api/admissions';
import { academicYearsApi } from '@api/academicYears';
import { formatDate } from '@utils/formatters';
import { classesApi } from '@api/classes';
import { useAcademicYearStore } from '@store/academicYearStore';
import { useAuthStore } from '@store/authStore';

const unwrap = (res: any) => res?.data ?? res;

const STATUS_COLORS: Record<string, string> = {
  draft:        'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  submitted:    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  under_review: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved:     'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  rejected:     'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  waitlisted:   'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
};

// ─── Front Desk Submission Modal ──────────────────────────────────────────────

interface FrontDeskForm {
  applicant_name: string;
  date_of_birth: string;
  gender: string;
  applying_for_class_id: string;
  parent_name: string;
  parent_phone: string;
  parent_email: string;
  address: string;
  previous_school: string;
  academic_year_id: string;
  // Government IDs — student
  student_aadhaar: string;
  student_pan: string;
  student_apaar: string;
  // Government IDs — parent/guardian
  parent_aadhaar: string;
  parent_pan: string;
  parent_ration_card: string;
  // Father
  father_name: string;
  father_aadhaar: string;
  father_pan: string;
  father_ration_card: string;
  // Mother
  mother_name: string;
  mother_aadhaar: string;
  mother_pan: string;
  mother_ration_card: string;
  // Guardian (if different)
  guardian_name: string;
  guardian_aadhaar: string;
  guardian_pan: string;
  guardian_ration_card: string;
}

const emptyFrontDeskForm = (): FrontDeskForm => ({
  applicant_name: '',
  date_of_birth: '',
  gender: 'male',
  applying_for_class_id: '',
  parent_name: '',
  parent_phone: '',
  parent_email: '',
  address: '',
  previous_school: '',
  academic_year_id: '',
  student_aadhaar: '',
  student_pan: '',
  student_apaar: '',
  parent_aadhaar: '',
  parent_pan: '',
  parent_ration_card: '',
  father_name: '',
  father_aadhaar: '',
  father_pan: '',
  father_ration_card: '',
  mother_name: '',
  mother_aadhaar: '',
  mother_pan: '',
  mother_ration_card: '',
  guardian_name: '',
  guardian_aadhaar: '',
  guardian_pan: '',
  guardian_ration_card: '',
});

const FrontDeskModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({
  onClose,
  onSuccess,
}) => {
  const [form, setForm] = React.useState<FrontDeskForm>(emptyFrontDeskForm);
  const [saving, setSaving] = React.useState(false);

  const schoolInfo = useAuthStore((s) => s.schoolInfo);
  const { selectedYear } = useAcademicYearStore();

  // Pre-populate academic year from global store
  React.useEffect(() => {
    if (selectedYear?.id) {
      setForm((p) => ({ ...p, academic_year_id: p.academic_year_id || selectedYear.id }));
    }
  }, [selectedYear?.id]);

  const set = (field: keyof FrontDeskForm, value: string) =>
    setForm((p) => ({ ...p, [field]: value }));

  // Academic years
  const yearsQuery = useQuery({
    queryKey: ['academic-years-select'],
    queryFn: async () => {
      const data = unwrap(await academicYearsApi.list());
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  // Classes for selected year
  const effectiveYearId = form.academic_year_id || selectedYear?.id;
  const classesQuery = useQuery({
    queryKey: ['classes-for-admission', effectiveYearId],
    enabled: !!effectiveYearId,
    queryFn: async () => {
      const data = unwrap(await classesApi.list(effectiveYearId!));
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  const handleSubmit = async () => {
    if (!form.applicant_name.trim()) return toast.error('Applicant name is required');
    if (!form.date_of_birth) return toast.error('Date of birth is required');
    if (!form.parent_name.trim()) return toast.error('Parent name is required');
    if (!form.parent_phone.trim()) return toast.error('Parent phone is required');
    if (!schoolInfo?.slug) return toast.error('School context missing — please select a school');

    const yearId = form.academic_year_id || selectedYear?.id;
    if (!yearId) return toast.error('Select an academic year');

    setSaving(true);
    try {
      await admissionsApi.frontdeskSubmit({
        school_slug: schoolInfo.slug,
        academic_year_id: yearId,
        applicant_name: form.applicant_name.trim(),
        date_of_birth: form.date_of_birth,
        gender: form.gender || undefined,
        applying_for_class_id: form.applying_for_class_id || undefined,
        parent_name: form.parent_name.trim(),
        parent_phone: form.parent_phone.trim(),
        parent_email: form.parent_email || undefined,
        address: form.address || undefined,
        previous_school: form.previous_school || undefined,
        student_aadhaar: form.student_aadhaar || undefined,
        student_pan: form.student_pan || undefined,
        student_apaar: form.student_apaar || undefined,
        parent_aadhaar: form.parent_aadhaar || undefined,
        parent_pan: form.parent_pan || undefined,
        parent_ration_card: form.parent_ration_card || undefined,
        father_name: form.father_name || undefined,
        father_aadhaar: form.father_aadhaar || undefined,
        father_pan: form.father_pan || undefined,
        father_ration_card: form.father_ration_card || undefined,
        mother_name: form.mother_name || undefined,
        mother_aadhaar: form.mother_aadhaar || undefined,
        mother_pan: form.mother_pan || undefined,
        mother_ration_card: form.mother_ration_card || undefined,
        guardian_name: form.guardian_name || undefined,
        guardian_aadhaar: form.guardian_aadhaar || undefined,
        guardian_pan: form.guardian_pan || undefined,
        guardian_ration_card: form.guardian_ration_card || undefined,
      });
      toast.success('Application submitted for review');
      onSuccess();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err?.detail ?? 'Failed to submit application';
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  };

  const years = yearsQuery.data ?? [];
  const classes = classesQuery.data ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 pt-10">
      <div className="w-full max-w-2xl rounded-2xl bg-white shadow-xl dark:bg-gray-900">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900/30">
              <ClipboardList size={18} className="text-indigo-600" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">
                New Admission Application
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Front-desk entry — will be submitted for admin review
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X size={18} />
          </button>
        </div>

        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {/* Year + Class */}
          <div className="grid grid-cols-2 gap-3 px-6 py-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                Academic Year <span className="text-red-500">*</span>
              </label>
              <select
                value={form.academic_year_id}
                onChange={(e) => set('academic_year_id', e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
              >
                {years.length === 0 && <option value="">Loading years…</option>}
                {years.map((y: any) => (
                  <option key={y.id} value={y.id}>
                    {y.name}{y.is_current ? ' (✓ Active)' : ''}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                Applying for Class
              </label>
              <select
                value={form.applying_for_class_id}
                onChange={(e) => set('applying_for_class_id', e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
              >
                <option value="">Select class</option>
                {classes.map((c: any) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Applicant */}
          <div className="px-6 py-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
              Applicant (Student)
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2 md:col-span-1">
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  value={form.applicant_name}
                  onChange={(e) => set('applicant_name', e.target.value)}
                  placeholder="Student's full name"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Date of Birth <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={form.date_of_birth}
                  onChange={(e) => set('date_of_birth', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Gender</label>
                <select
                  value={form.gender}
                  onChange={(e) => set('gender', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Previous School
                </label>
                <input
                  value={form.previous_school}
                  onChange={(e) => set('previous_school', e.target.value)}
                  placeholder="Name of previous school"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
            </div>
            {/* Student Government IDs */}
            <div className="mt-3 grid grid-cols-3 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Student Aadhaar</label>
                <input value={form.student_aadhaar} onChange={(e) => set('student_aadhaar', e.target.value)} placeholder="XXXX XXXX XXXX" maxLength={14} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Student PAN</label>
                <input value={form.student_pan} onChange={(e) => set('student_pan', e.target.value.toUpperCase())} placeholder="ABCDE1234F" maxLength={10} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">APAAR / PEN No.</label>
                <input value={form.student_apaar} onChange={(e) => set('student_apaar', e.target.value)} placeholder="APAAR/PEN number" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
            </div>
          </div>

          {/* Parent / Guardian */}
          <div className="px-6 py-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
              Parent / Guardian
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  value={form.parent_name}
                  onChange={(e) => set('parent_name', e.target.value)}
                  placeholder="Parent's full name"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Phone <span className="text-red-500">*</span>
                </label>
                <input
                  type="tel"
                  value={form.parent_phone}
                  onChange={(e) => set('parent_phone', e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Email</label>
                <input
                  type="email"
                  value={form.parent_email}
                  onChange={(e) => set('parent_email', e.target.value)}
                  placeholder="parent@example.com"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Address</label>
                <input
                  value={form.address}
                  onChange={(e) => set('address', e.target.value)}
                  placeholder="Residential address"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
            </div>
            {/* Parent Government IDs */}
            <div className="mt-3 grid grid-cols-3 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Parent Aadhaar</label>
                <input value={form.parent_aadhaar} onChange={(e) => set('parent_aadhaar', e.target.value)} placeholder="XXXX XXXX XXXX" maxLength={14} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Parent PAN</label>
                <input value={form.parent_pan} onChange={(e) => set('parent_pan', e.target.value.toUpperCase())} placeholder="ABCDE1234F" maxLength={10} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Ration Card No.</label>
                <input value={form.parent_ration_card} onChange={(e) => set('parent_ration_card', e.target.value)} placeholder="Ration card number" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
            </div>
          </div>

          {/* Father / Mother / Guardian Details */}
          <div className="px-6 py-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Father Details</h3>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div className="md:col-span-1">
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Father Name</label>
                <input value={form.father_name} onChange={(e) => set('father_name', e.target.value)} placeholder="Full name" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Aadhaar</label>
                <input value={form.father_aadhaar} onChange={(e) => set('father_aadhaar', e.target.value)} placeholder="XXXX XXXX XXXX" maxLength={14} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">PAN</label>
                <input value={form.father_pan} onChange={(e) => set('father_pan', e.target.value.toUpperCase())} placeholder="ABCDE1234F" maxLength={10} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Ration Card</label>
                <input value={form.father_ration_card} onChange={(e) => set('father_ration_card', e.target.value)} placeholder="Ration card number" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
            </div>
            <h3 className="mb-3 mt-4 text-xs font-semibold uppercase tracking-wide text-gray-500">Mother Details</h3>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div className="md:col-span-1">
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Mother Name</label>
                <input value={form.mother_name} onChange={(e) => set('mother_name', e.target.value)} placeholder="Full name" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Aadhaar</label>
                <input value={form.mother_aadhaar} onChange={(e) => set('mother_aadhaar', e.target.value)} placeholder="XXXX XXXX XXXX" maxLength={14} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">PAN</label>
                <input value={form.mother_pan} onChange={(e) => set('mother_pan', e.target.value.toUpperCase())} placeholder="ABCDE1234F" maxLength={10} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Ration Card</label>
                <input value={form.mother_ration_card} onChange={(e) => set('mother_ration_card', e.target.value)} placeholder="Ration card number" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
            </div>
            <h3 className="mb-3 mt-4 text-xs font-semibold uppercase tracking-wide text-gray-500">Guardian Details <span className="text-gray-400 font-normal normal-case">(if different from parents)</span></h3>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div className="md:col-span-1">
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Guardian Name</label>
                <input value={form.guardian_name} onChange={(e) => set('guardian_name', e.target.value)} placeholder="Full name" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Aadhaar</label>
                <input value={form.guardian_aadhaar} onChange={(e) => set('guardian_aadhaar', e.target.value)} placeholder="XXXX XXXX XXXX" maxLength={14} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">PAN</label>
                <input value={form.guardian_pan} onChange={(e) => set('guardian_pan', e.target.value.toUpperCase())} placeholder="ABCDE1234F" maxLength={10} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-800" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Ration Card</label>
                <input value={form.guardian_ration_card} onChange={(e) => set('guardian_ration_card', e.target.value)} placeholder="Ration card number" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
              </div>
            </div>
          </div>

          {/* Note */}
          <div className="px-6 py-3">
            <div className="rounded-lg bg-amber-50 px-4 py-3 text-xs text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
              📋 This application will be submitted in <strong>Under Review</strong> status so that
              higher authorities (Principal / Admission Officer) can review and approve or reject it.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 border-t border-gray-200 px-6 py-4 dark:border-gray-700">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            <ClipboardList size={14} />
            {saving ? 'Submitting…' : 'Submit for Review'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const AdmissionsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const selectedYear = useAcademicYearStore((s) => s.selectedYear);

  const [status, setStatus] = React.useState('');
  const [search, setSearch] = React.useState('');
  const [page, setPage] = React.useState(1);
  const [selected, setSelected] = React.useState<any | null>(null);
  const [review, setReview] = React.useState({
    status: 'under_review',
    remarks: '',
    assigned_admission_number: '',
  });
  const [showFrontDesk, setShowFrontDesk] = React.useState(false);
  const [bulkSelected, setBulkSelected] = React.useState<Set<string>>(new Set());
  const [bulkApproving, setBulkApproving] = React.useState(false);

  const listQuery = useQuery({
    queryKey: ['admissions', selectedYear?.id, status, search, page],
    queryFn: async () =>
      unwrap(
        await admissionsApi.list({
          academic_year_id: selectedYear?.id,
          status: status || undefined,
          search: search || undefined,
          page,
          page_size: 20,
        })
      ),
  });

  const statsQuery = useQuery({
    queryKey: ['admission-stats', selectedYear?.id],
    enabled: !!selectedYear?.id,
    queryFn: async () => unwrap(await admissionsApi.stats(selectedYear!.id)),
  });

  const reviewMutation = useMutation({
    mutationFn: () => admissionsApi.review(selected.id, review as any),
    onSuccess: () => {
      toast.success('Admission updated');
      setSelected(null);
      queryClient.invalidateQueries({ queryKey: ['admissions'] });
      queryClient.invalidateQueries({ queryKey: ['admission-stats'] });
    },
    onError: (err: any) => toast.error(err?.detail ?? 'Failed to update admission'),
  });

  const items = listQuery.data?.items ?? [];
  const stats = statsQuery.data ?? {};

  const approvableItems = items.filter((r: any) => ['submitted', 'under_review'].includes(r.status));

  const handleBulkApprove = async () => {
    if (bulkSelected.size === 0) { toast.error('Select applications to approve'); return; }
    if (!confirm(`Approve ${bulkSelected.size} application(s)?`)) return;
    setBulkApproving(true);
    let ok = 0, fail = 0;
    for (const id of bulkSelected) {
      try {
        await admissionsApi.review(id, { status: 'approved', remarks: 'Bulk approved' } as any);
        ok++;
      } catch { fail++; }
    }
    setBulkSelected(new Set());
    queryClient.invalidateQueries({ queryKey: ['admissions'] });
    queryClient.invalidateQueries({ queryKey: ['admission-stats'] });
    setBulkApproving(false);
    if (ok > 0) toast.success(`${ok} application(s) approved`);
    if (fail > 0) toast.error(`${fail} failed`);
  };

  return (
    <div>
      <PageHeader
        title="Admissions"
        subtitle="Review and process applications"
        actions={
          <button
            onClick={() => setShowFrontDesk(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            <Plus size={14} />
            New Application (Front Desk)
          </button>
        }
      />

      {/* Stats Row */}
      <div className="mb-4 grid gap-3 md:grid-cols-6">
        {['draft', 'submitted', 'under_review', 'approved', 'rejected', 'waitlisted'].map((k) => (
          <button
            key={k}
            onClick={() => setStatus(status === k ? '' : k)}
            className={`rounded-xl border p-3 text-center text-xs shadow-sm transition-all hover:shadow-md ${
              status === k
                ? 'border-indigo-400 bg-indigo-50 dark:border-indigo-700 dark:bg-indigo-900/30'
                : 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'
            }`}
          >
            <div className="uppercase text-gray-500 dark:text-gray-400">{k.replace('_', ' ')}</div>
            <div className="mt-1 text-lg font-bold text-gray-900 dark:text-white">{stats[k] ?? 0}</div>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
        >
          <option value="">All statuses</option>
          <option value="submitted">Submitted</option>
          <option value="under_review">Under Review</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="waitlisted">Waitlisted</option>
        </select>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search name or phone…"
          className="flex-1 min-w-[180px] rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
        />
        <button
          onClick={() => {
            setPage(1);
            queryClient.invalidateQueries({ queryKey: ['admissions'] });
          }}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Search
        </button>
      </div>

      {/* Bulk Actions */}
      {bulkSelected.size > 0 && (
        <div className="mb-3 flex items-center gap-3 rounded-lg bg-indigo-50 border border-indigo-200 px-4 py-2">
          <span className="text-sm text-indigo-700 font-medium">{bulkSelected.size} selected</span>
          <button
            disabled={bulkApproving}
            onClick={handleBulkApprove}
            className="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 font-medium"
          >
            {bulkApproving ? 'Approving…' : '✓ Bulk Approve'}
          </button>
          <button onClick={() => setBulkSelected(new Set())} className="text-xs text-gray-500 hover:text-gray-700">
            Clear
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-900/40">
            <tr>
              <th className="px-4 py-3 w-10">
                <input type="checkbox" className="rounded"
                  checked={bulkSelected.size > 0 && bulkSelected.size === approvableItems.length}
                  onChange={e => setBulkSelected(e.target.checked ? new Set(approvableItems.map((r: any) => r.id)) : new Set())}
                />
              </th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Ref</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Applicant</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">D.O.B</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Parent Phone</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Status</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-600 dark:text-gray-400">Submitted</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-600 dark:text-gray-400">Actions</th>
            </tr>
          </thead>
          <tbody>
            {listQuery.isLoading ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-gray-400">Loading…</td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-10 text-center text-gray-400">No applications found.</td>
              </tr>
            ) : (
              items.map((row: any) => (
                <tr key={row.id} className="border-t border-gray-100 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900/20">
                  <td className="px-4 py-3">
                    {['submitted', 'under_review'].includes(row.status) && (
                      <input type="checkbox" className="rounded"
                        checked={bulkSelected.has(row.id)}
                        onChange={() => setBulkSelected(prev => {
                          const next = new Set(prev);
                          next.has(row.id) ? next.delete(row.id) : next.add(row.id);
                          return next;
                        })}
                      />
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{row.reference_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{row.applicant_name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{formatDate(row.date_of_birth)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{row.parent_phone}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[row.status] ?? 'bg-gray-100 text-gray-600'}`}
                    >
                      {String(row.status).replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                    {formatDate(row.submitted_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => {
                        setSelected(row);
                        setReview({
                          status: 'under_review',
                          remarks: row.remarks ?? '',
                          assigned_admission_number: row.assigned_admission_number ?? '',
                        });
                      }}
                      className="rounded-lg border border-indigo-200 px-2 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-50 dark:border-indigo-800 dark:text-indigo-400"
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-end gap-2">
        <button
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
          className="rounded-lg border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        >
          Prev
        </button>
        <span className="text-sm text-gray-600">Page {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          className="rounded-lg border border-gray-300 px-3 py-1 text-sm"
        >
          Next
        </button>
      </div>

      {/* Review Modal */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-900">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">Review Application</h3>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>
            <div className="mb-4 rounded-lg bg-gray-50 px-4 py-2 text-sm text-gray-600 dark:bg-gray-800 dark:text-gray-400">
              <span className="font-mono">{selected.reference_number}</span> — {selected.applicant_name}
            </div>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Update Status
                </label>
                <select
                  value={review.status}
                  onChange={(e) => setReview((p) => ({ ...p, status: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="under_review">Under Review</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="waitlisted">Waitlisted</option>
                </select>
              </div>
              {review.status === 'approved' && (
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                    Assigned Admission Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    value={review.assigned_admission_number}
                    onChange={(e) => setReview((p) => ({ ...p, assigned_admission_number: e.target.value }))}
                    placeholder="e.g. ADM-2025-001"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  />
                </div>
              )}
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Remarks / Notes
                </label>
                <textarea
                  value={review.remarks}
                  onChange={(e) => setReview((p) => ({ ...p, remarks: e.target.value }))}
                  rows={3}
                  placeholder="Optional remarks for this decision"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setSelected(null)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (review.status === 'approved' && !review.assigned_admission_number) {
                    toast.error('Admission number is required for approval');
                    return;
                  }
                  reviewMutation.mutate();
                }}
                disabled={reviewMutation.isPending}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {reviewMutation.isPending ? 'Saving…' : 'Save Decision'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Front Desk Modal */}
      {showFrontDesk && (
        <FrontDeskModal
          onClose={() => setShowFrontDesk(false)}
          onSuccess={() => {
            setShowFrontDesk(false);
            queryClient.invalidateQueries({ queryKey: ['admissions'] });
            queryClient.invalidateQueries({ queryKey: ['admission-stats'] });
          }}
        />
      )}
    </div>
  );
};

export default AdmissionsPage;
