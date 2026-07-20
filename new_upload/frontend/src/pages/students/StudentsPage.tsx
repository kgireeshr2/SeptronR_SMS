import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Plus, X, UserPlus } from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { studentsApi, Student, StudentDetail, StudentStats } from '@api/students';
import { formatDate } from '@utils/formatters';
import EditStudentModal from './EditStudentModal';
import { classesApi } from '@api/classes';
import { academicYearsApi } from '@api/academicYears';
import { useAcademicYearStore } from '@store/academicYearStore';
import { feesV2Api } from '@api/feesV2';
import api from '@/api/axios';

const unwrap = (r: any) => r?.data ?? r;

// ─── Add Student Modal ────────────────────────────────────────────────────────

interface ParentEntry {
  include: boolean;
  name: string;
  phone: string;
  email: string;
  occupation: string;
  aadhaar_number: string;
  pan_number: string;
  ration_card_number: string;
  is_primary_contact: boolean;
}

const emptyParent = (): ParentEntry => ({
  include: false,
  name: '',
  phone: '',
  email: '',
  occupation: '',
  aadhaar_number: '',
  pan_number: '',
  ration_card_number: '',
  is_primary_contact: false,
});

interface AddStudentForm {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  nationality: string;
  admission_date: string;
  admission_number: string;
  blood_group: string;
  religion: string;
  category: string;
  // Government IDs
  aadhaar_number: string;
  pan_number: string;
  apaar_number: string;
  // Enrollment
  academic_year_id: string;
  class_id: string;
  section_id: string;
  roll_number: string;
  // Fee
  fee_master_id: string;
}

const emptyForm = (): AddStudentForm => ({
  first_name: '',
  last_name: '',
  date_of_birth: '',
  gender: 'male',
  nationality: 'Indian',
  admission_date: new Date().toISOString().slice(0, 10),
  admission_number: '',
  blood_group: '',
  religion: '',
  category: '',
  aadhaar_number: '',
  pan_number: '',
  apaar_number: '',
  academic_year_id: '',
  class_id: '',
  section_id: '',
  roll_number: '',
  fee_master_id: '',
});

const AddStudentModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({
  onClose,
  onSuccess,
}) => {
  const [form, setForm] = useState<AddStudentForm>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [father, setFather] = useState<ParentEntry>(emptyParent);
  const [mother, setMother] = useState<ParentEntry>(emptyParent);
  const [guardian, setGuardian] = useState<ParentEntry>(emptyParent);
  const { selectedYear } = useAcademicYearStore();

  const setParent = (setter: React.Dispatch<React.SetStateAction<ParentEntry>>) =>
    (field: keyof ParentEntry, value: string | boolean) =>
      setter(prev => ({ ...prev, [field]: value }));

  // Pre-populate academic year from global store
  React.useEffect(() => {
    if (selectedYear?.id) {
      setForm((p) => ({ ...p, academic_year_id: p.academic_year_id || selectedYear.id }));
    }
  }, [selectedYear?.id]);

  const set = (field: keyof AddStudentForm, value: string) =>
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
  const classesQuery = useQuery({
    queryKey: ['classes-for-enroll', form.academic_year_id || selectedYear?.id],
    enabled: !!(form.academic_year_id || selectedYear?.id),
    queryFn: async () => {
      const yearId = form.academic_year_id || selectedYear?.id;
      if (!yearId) return [];
      const data = unwrap(await classesApi.list(yearId));
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  // Sections derived from already-loaded class list (each class has sections[])
  const sections = React.useMemo(() => {
    if (!form.class_id) return [];
    const cls = (classesQuery.data ?? []).find((c: any) => c.id === form.class_id);
    return (cls as any)?.sections ?? [];
  }, [form.class_id, classesQuery.data]);

  // Fee masters for selected class/year (optional fee assignment at admission)
  const feeMastersQuery = useQuery({
    queryKey: ['fee-masters-for-admit', form.class_id, form.academic_year_id || selectedYear?.id],
    enabled: !!form.class_id,
    queryFn: async () => {
      const yearId = form.academic_year_id || selectedYear?.id;
      const d = unwrap(
        await feesV2Api.listFeeMasters(
          yearId ? { class_id: form.class_id, academic_year_id: yearId } : { class_id: form.class_id },
        ),
      );
      return Array.isArray(d) ? d : (d?.items ?? []);
    },
  });

  const handleSubmit = async () => {
    if (!form.first_name.trim()) return toast.error('First name is required');
    if (!form.last_name.trim()) return toast.error('Last name is required');
    if (!form.date_of_birth) return toast.error('Date of birth is required');
    if (!form.admission_date) return toast.error('Admission date is required');

    setSaving(true);
    try {
      const payload: any = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        date_of_birth: form.date_of_birth,
        gender: form.gender,
        nationality: form.nationality || 'Indian',
        admission_date: form.admission_date,
        is_active: true,
      };
      if (form.admission_number) payload.admission_number = form.admission_number;
      if (form.blood_group) payload.blood_group = form.blood_group;
      if (form.religion) payload.religion = form.religion;
      if (form.category) payload.category = form.category;
      if (form.aadhaar_number) payload.aadhaar_number = form.aadhaar_number;
      if (form.pan_number) payload.pan_number = form.pan_number;
      if (form.apaar_number) payload.apaar_number = form.apaar_number;

      // Enrollment (optional if class is selected)
      if (form.class_id) {
        payload.enrollment = {
          academic_year_id: form.academic_year_id || selectedYear?.id,
          class_id: form.class_id,
          section_id: form.section_id || undefined,
          roll_number: form.roll_number || undefined,
          is_current: true,
        };
      }

      // Build parents array
      const parentsPayload: any[] = [];
      if (father.include && father.name.trim()) {
        parentsPayload.push({
          relation: 'father', name: father.name.trim(),
          phone: father.phone || undefined, email: father.email || undefined,
          occupation: father.occupation || undefined,
          aadhaar_number: father.aadhaar_number || undefined,
          pan_number: father.pan_number || undefined,
          ration_card_number: father.ration_card_number || undefined,
          is_primary_contact: father.is_primary_contact,
          can_access_portal: true,
        });
      }
      if (mother.include && mother.name.trim()) {
        parentsPayload.push({
          relation: 'mother', name: mother.name.trim(),
          phone: mother.phone || undefined, email: mother.email || undefined,
          occupation: mother.occupation || undefined,
          aadhaar_number: mother.aadhaar_number || undefined,
          pan_number: mother.pan_number || undefined,
          ration_card_number: mother.ration_card_number || undefined,
          is_primary_contact: mother.is_primary_contact,
          can_access_portal: true,
        });
      }
      if (guardian.include && guardian.name.trim()) {
        parentsPayload.push({
          relation: 'guardian', name: guardian.name.trim(),
          phone: guardian.phone || undefined, email: guardian.email || undefined,
          occupation: guardian.occupation || undefined,
          aadhaar_number: guardian.aadhaar_number || undefined,
          pan_number: guardian.pan_number || undefined,
          ration_card_number: guardian.ration_card_number || undefined,
          is_primary_contact: guardian.is_primary_contact,
          can_access_portal: true,
        });
      }
      if (parentsPayload.length > 0) payload.parents = parentsPayload;

      const created = unwrap(await studentsApi.createStudent(payload));
      const newStudentId: string | undefined = created?.id;

      // Optionally assign fee master at admission
      if (newStudentId && form.fee_master_id) {
        const yearId = form.academic_year_id || selectedYear?.id;
        try {
          await feesV2Api.assignFeeMaster({
            student_ids: [newStudentId],
            fee_master_id: form.fee_master_id,
            academic_year_id: yearId!,
          });
        } catch {
          toast.warning('Student added but fee master assignment failed — assign later from Advanced Fees.');
        }
      }

      toast.success(`${form.first_name} ${form.last_name} added successfully`);
      onSuccess();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err?.detail ?? 'Failed to add student';
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  };

  const years = yearsQuery.data ?? [];
  const classes = classesQuery.data ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 pt-12">
      <div className="w-full max-w-2xl rounded-2xl bg-white shadow-xl dark:bg-gray-900">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
              <UserPlus size={18} className="text-blue-600" />
            </div>
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">Add New Student</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700"
          >
            <X size={18} />
          </button>
        </div>

        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {/* Basic Info */}
          <div className="px-6 py-5">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
              Basic Info
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  First Name <span className="text-red-500">*</span>
                </label>
                <input
                  value={form.first_name}
                  onChange={(e) => set('first_name', e.target.value)}
                  placeholder="First name"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Last Name <span className="text-red-500">*</span>
                </label>
                <input
                  value={form.last_name}
                  onChange={(e) => set('last_name', e.target.value)}
                  placeholder="Last name"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
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
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Gender <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.gender}
                  onChange={(e) => set('gender', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Admission Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={form.admission_date}
                  onChange={(e) => set('admission_date', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Admission Number <span className="text-gray-400">(auto if blank)</span>
                </label>
                <input
                  value={form.admission_number}
                  onChange={(e) => set('admission_number', e.target.value)}
                  placeholder="Leave blank to auto-generate"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
            </div>
          </div>

          {/* Additional Details */}
          <div className="px-6 py-5">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
              Additional Details
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Nationality</label>
                <input
                  value={form.nationality}
                  onChange={(e) => set('nationality', e.target.value)}
                  placeholder="Indian"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Blood Group</label>
                <select
                  value={form.blood_group}
                  onChange={(e) => set('blood_group', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="">Select</option>
                  {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((bg) => (
                    <option key={bg} value={bg}>{bg}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Category</label>
                <select
                  value={form.category}
                  onChange={(e) => set('category', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="">Select</option>
                  {['General', 'OBC', 'SC', 'ST', 'EWS', 'Other'].map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>
            {/* Government IDs */}
            <div className="mt-3 grid grid-cols-3 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Aadhaar No.</label>
                <input
                  value={form.aadhaar_number}
                  onChange={(e) => set('aadhaar_number', e.target.value)}
                  placeholder="XXXX XXXX XXXX"
                  maxLength={14}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">PAN No.</label>
                <input
                  value={form.pan_number}
                  onChange={(e) => set('pan_number', e.target.value.toUpperCase())}
                  placeholder="ABCDE1234F"
                  maxLength={10}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">APAAR / PEN No.</label>
                <input
                  value={form.apaar_number}
                  onChange={(e) => set('apaar_number', e.target.value)}
                  placeholder="APAAR / PEN number"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
            </div>
          </div>

          {/* Parents */}
          <div className="px-6 py-5">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Parents / Guardians</h3>
            {(
              [['Father', father, setFather], ['Mother', mother, setMother], ['Guardian', guardian, setGuardian]] as
              [string, ParentEntry, React.Dispatch<React.SetStateAction<ParentEntry>>][]
            ).map(([label, entry, setter]) => {
              const sp = setParent(setter);
              return (
                <div key={label} className="mb-3 rounded-xl border border-gray-200 dark:border-gray-700">
                  <button
                    type="button"
                    onClick={() => sp('include', !entry.include)}
                    className="flex w-full items-center justify-between rounded-xl px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    <span className="flex items-center gap-2">
                      <span className={`inline-block h-2 w-2 rounded-full ${entry.include ? 'bg-blue-500' : 'bg-gray-300'}`} />
                      {label} Details
                    </span>
                    <span className="text-xs text-gray-400">{entry.include ? '▲ Collapse' : '▼ Add'}</span>
                  </button>
                  {entry.include && (
                    <div className="border-t border-gray-100 px-4 pb-4 pt-3 dark:border-gray-700">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="col-span-2 md:col-span-1">
                          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                            Name <span className="text-red-500">*</span>
                          </label>
                          <input value={entry.name} onChange={(e) => sp('name', e.target.value)}
                            placeholder={`${label}'s full name`}
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Phone</label>
                          <input type="tel" value={entry.phone} onChange={(e) => sp('phone', e.target.value)}
                            placeholder="+91 98765 43210"
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Email</label>
                          <input type="email" value={entry.email} onChange={(e) => sp('email', e.target.value)}
                            placeholder="email@example.com"
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Occupation</label>
                          <input value={entry.occupation} onChange={(e) => sp('occupation', e.target.value)}
                            placeholder="e.g. Engineer, Teacher"
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
                        </div>
                      </div>
                      <div className="mt-3 grid grid-cols-3 gap-3">
                        <div>
                          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Aadhaar No.</label>
                          <input value={entry.aadhaar_number} onChange={(e) => sp('aadhaar_number', e.target.value)}
                            placeholder="XXXX XXXX XXXX" maxLength={14}
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">PAN No.</label>
                          <input value={entry.pan_number} onChange={(e) => sp('pan_number', e.target.value.toUpperCase())}
                            placeholder="ABCDE1234F" maxLength={10}
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-800" />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Ration Card No.</label>
                          <input value={entry.ration_card_number} onChange={(e) => sp('ration_card_number', e.target.value)}
                            placeholder="Ration card number"
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800" />
                        </div>
                      </div>
                      <label className="mt-3 flex items-center gap-2 cursor-pointer select-none">
                        <input type="checkbox" checked={entry.is_primary_contact}
                          onChange={(e) => sp('is_primary_contact', e.target.checked)}
                          className="h-4 w-4 rounded border-gray-300 text-blue-600" />
                        <span className="text-xs text-gray-600 dark:text-gray-400">Primary contact</span>
                      </label>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Enrollment */}
          <div className="px-6 py-5">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
              Class Enrollment <span className="text-gray-400 normal-case font-normal">(optional — can be done later)</span>
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Academic Year</label>
                <select
                  value={form.academic_year_id}
                  onChange={(e) => {
                    set('academic_year_id', e.target.value);
                    set('class_id', '');
                    set('section_id', '');
                  }}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                >
                  {years.map((y: any) => (
                    <option key={y.id} value={y.id}>{y.name}{y.is_current ? ' (✓ Active)' : ''}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Class</label>
                <select
                  value={form.class_id}
                  onChange={(e) => { set('class_id', e.target.value); set('section_id', ''); }}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="">Select class</option>
                  {classes.map((c: any) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Section</label>
                <select
                  value={form.section_id}
                  onChange={(e) => set('section_id', e.target.value)}
                  disabled={!form.class_id}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:opacity-60 dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="">Select section</option>
                  {sections.map((s: any) => (
                    <option key={s.id} value={s.id}>Section {s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Roll Number</label>
                <input
                  value={form.roll_number}
                  onChange={(e) => set('roll_number', e.target.value)}
                  placeholder="Optional"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div className="col-span-2">
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                  Assign Fee Master <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <select
                  value={form.fee_master_id}
                  onChange={(e) => set('fee_master_id', e.target.value)}
                  disabled={!form.class_id}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:opacity-60 dark:border-gray-600 dark:bg-gray-800"
                >
                  <option value="">No fee master (assign later)</option>
                  {(feeMastersQuery.data ?? []).map((fm: any) => (
                    <option key={fm.id} value={fm.id}>{fm.name}</option>
                  ))}
                </select>
              </div>
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
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            <UserPlus size={14} />
            {saving ? 'Adding…' : 'Add Student'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Students Page ────────────────────────────────────────────────────────────

const Page: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { selectedYear } = useAcademicYearStore();

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [classFilter, setClassFilter] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined);
  const [showAddModal, setShowAddModal] = useState(false);

  // Debounce search so we don't fire an API call on every keystroke
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 350);
    return () => clearTimeout(t);
  }, [search]);
  const [bulkSelected, setBulkSelected] = useState<Set<string>>(new Set());
  const [editStudent, setEditStudent] = useState<StudentDetail | null>(null);
  const [loadingEditStudent, setLoadingEditStudent] = useState(false);
  const [showPromoteModal, setShowPromoteModal] = useState(false);
  const [promoteTargetYearId, setPromoteTargetYearId] = useState('');
  const [promoteTargetClassId, setPromoteTargetClassId] = useState('');
  const [promoteTargetSectionId, setPromoteTargetSectionId] = useState('');
  const [promoteLoading, setPromoteLoading] = useState(false);
  const [promoteSections, setPromoteSections] = useState<any[]>([]);

  // Students list
  const { data: students = [], isLoading } = useQuery({
    queryKey: ['students', { search: debouncedSearch, class_id: classFilter, academic_year_id: yearFilter, is_active: activeFilter }],
    queryFn: async () => {
      const params: any = {};
      if (debouncedSearch) params.search = debouncedSearch;
      if (classFilter) params.class_id = classFilter;
      if (yearFilter) params.academic_year_id = yearFilter;
      if (activeFilter !== undefined) params.is_active = activeFilter;
      const response = await studentsApi.listStudents(params);
      const list = unwrap(response);
      return Array.isArray(list) ? list : (list?.items ?? []);
    },
  });

  // Stats
  const { data: stats } = useQuery<StudentStats>({
    queryKey: ['students-stats'],
    queryFn: async () => {
      const response = await studentsApi.getStudentStats();
      return unwrap(response);
    },
  });

  // Classes for filter (using selectedYear)
  const { data: classes = [] } = useQuery({
    queryKey: ['classes-filter', selectedYear?.id],
    enabled: !!selectedYear?.id,
    queryFn: async () => {
      if (!selectedYear?.id) return [];
      const data = unwrap(await classesApi.list(selectedYear.id));
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  // Academic years for filter
  const { data: academicYears = [] } = useQuery({
    queryKey: ['academic-years-filter'],
    queryFn: async () => {
      const data = unwrap(await academicYearsApi.list());
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (studentId: string) => studentsApi.deleteStudent(studentId),
    onSuccess: () => {
      toast.success('Student deleted');
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete student');
    },
  });

  const handleDelete = (studentId: string, admissionNumber: string) => {
    if (window.confirm(`Delete student ${admissionNumber}? This cannot be undone.`)) {
      deleteMutation.mutate(studentId);
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await studentsApi.exportCSV();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'students.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Export started');
    } catch {
      toast.error('Failed to export students');
    }
  };

  const handleBulkPromote = async () => {
    if (!promoteTargetYearId || !promoteTargetClassId || !promoteTargetSectionId) {
      toast.error('Select target year, class and section');
      return;
    }
    setPromoteLoading(true);
    try {
      const promotions = [...bulkSelected].map(studentId => ({
        student_id: studentId,
        to_class_id: promoteTargetClassId,
        to_section_id: promoteTargetSectionId,
      }));
      const res = await studentsApi.promoteStudents({
        academic_year_id: promoteTargetYearId,
        promotions,
      } as any);
      const data = (res as any)?.data ?? res;
      const promoted = data?.promoted ?? promotions.length;
      toast.success(`${promoted} student(s) promoted successfully`);
      if (data?.errors?.length) toast.error(`${data.errors.length} failed`);
      setBulkSelected(new Set());
      setShowPromoteModal(false);
      queryClient.invalidateQueries({ queryKey: ['students'] });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Promotion failed');
    } finally {
      setPromoteLoading(false);
    }
  };


  return (
    <div>
      <PageHeader
        title="Students"
        subtitle="Manage student records, enrollments, and details"
        actions={
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            <Plus size={14} />
            Add Student
          </button>
        }
      />

      {/* Stats */}
      {stats && (
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {[
            { label: 'Total', value: stats.total_students, color: 'text-gray-900 dark:text-white' },
            { label: 'Active', value: stats.active_students, color: 'text-green-600' },
            { label: 'Inactive', value: stats.inactive_students, color: 'text-red-600' },
            { label: 'Male', value: stats.male_students, color: 'text-blue-600' },
            { label: 'Female', value: stats.female_students, color: 'text-pink-600' },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400">{label}</div>
              <div className={`mt-1 text-2xl font-bold ${color}`}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="mb-5 rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Search by name or admission no…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="min-w-[200px] flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700"
          />
          <select
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
          >
            <option value="">All Classes</option>
            {classes.map((cls: any) => (
              <option key={cls.id} value={cls.id}>{cls.name}</option>
            ))}
          </select>
          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
          >
            <option value="">All Years</option>
            {academicYears.map((year: any) => (
              <option key={year.id} value={year.id}>{year.name}</option>
            ))}
          </select>
          <select
            value={activeFilter === undefined ? '' : String(activeFilter)}
            onChange={(e) => setActiveFilter(e.target.value === '' ? undefined : e.target.value === 'true')}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
          >
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
          <button
            onClick={handleExportCSV}
            className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Bulk Actions */}
      {bulkSelected.size > 0 && (
        <div className="mb-3 flex items-center gap-3 rounded-lg bg-blue-50 border border-blue-200 px-4 py-2">
          <span className="text-sm text-blue-700 font-medium">{bulkSelected.size} selected</span>
          <button
            onClick={() => setShowPromoteModal(true)}
            className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 font-medium"
          >
            🎓 Bulk Promote
          </button>
          <button onClick={() => setBulkSelected(new Set())} className="text-xs text-gray-500 hover:text-gray-700">
            Clear
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        {isLoading ? (
          <div className="flex h-32 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        ) : (students as Student[]).length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-500">No students found.</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-3 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus size={14} /> Add First Student
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 w-10">
                    <input type="checkbox" className="rounded"
                      checked={bulkSelected.size > 0 && bulkSelected.size === (students as Student[]).length}
                      onChange={e => setBulkSelected(e.target.checked ? new Set((students as Student[]).map(s => s.id)) : new Set())}
                    />
                  </th>
                  {['Admission No', 'Name', 'Gender', 'Age', 'Admission Date', 'Status', ''].map((h) => (
                    <th
                      key={h}
                      className={`px-4 py-3 text-xs font-semibold uppercase text-gray-500 ${h === '' ? 'text-right' : 'text-left'}`}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {(students as Student[]).map((student) => (
                  <tr key={student.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-4 py-3">
                      <input type="checkbox" className="rounded"
                        checked={bulkSelected.has(student.id)}
                        onChange={() => setBulkSelected(prev => {
                          const next = new Set(prev);
                          next.has(student.id) ? next.delete(student.id) : next.add(student.id);
                          return next;
                        })}
                      />
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                      {student.admission_number}
                    </td>
                    <td className="px-4 py-3 text-gray-900 dark:text-white">{student.full_name}</td>
                    <td className="px-4 py-3 capitalize text-gray-600 dark:text-gray-300">{student.gender}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{student.age}y</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                      {formatDate(student.admission_date)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                          student.is_active
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        }`}
                      >
                        {student.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => navigate(`/students/${student.id}`)}
                        className="mr-3 text-blue-600 hover:text-blue-800 dark:text-blue-400"
                      >
                        View
                      </button>
                      <button
                        onClick={async () => {
                          setLoadingEditStudent(true);
                          try {
                            const detail = unwrap(await studentsApi.getStudent(student.id));
                            setEditStudent(detail);
                          } catch {
                            toast.error('Failed to load student details');
                          } finally {
                            setLoadingEditStudent(false);
                          }
                        }}
                        disabled={loadingEditStudent}
                        className="mr-3 text-green-600 hover:text-green-800 dark:text-green-400 disabled:opacity-50"
                      >
                        {loadingEditStudent ? 'Loading…' : 'Edit'}
                      </button>
                      <button
                        onClick={() => handleDelete(student.id, student.admission_number)}
                        className="text-red-500 hover:text-red-700"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Student Modal */}
      {editStudent && (
        <EditStudentModal
          key={editStudent.id}
          student={editStudent}
          onClose={() => setEditStudent(null)}
          onSaved={() => {
            setEditStudent(null);
            queryClient.invalidateQueries({ queryKey: ['students'] });
            queryClient.invalidateQueries({ queryKey: ['students-stats'] });
          }}
        />
      )}

      {/* Add Student Modal */}
      {showAddModal && (
        <AddStudentModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            queryClient.invalidateQueries({ queryKey: ['students'] });
            queryClient.invalidateQueries({ queryKey: ['students-stats'] });
          }}
        />
      )}

      {/* Bulk Promote Modal */}
      {showPromoteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-900">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Bulk Promote {bulkSelected.size} Students</h3>
              <button onClick={() => setShowPromoteModal(false)} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
            </div>
            <p className="text-sm text-gray-500 mb-4">Promote selected students to a new academic year, class and section.</p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Target Academic Year *</label>
                <select value={promoteTargetYearId} onChange={e => setPromoteTargetYearId(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm">
                  <option value="">Select year</option>
                  {academicYears.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Target Class *</label>
                <select value={promoteTargetClassId} onChange={async e => {
                  setPromoteTargetClassId(e.target.value);
                  setPromoteTargetSectionId('');
                  if (e.target.value) {
                    try {
                      const r = await classesApi.getSections(e.target.value);
                      const s = unwrap(r);
                      setPromoteSections(Array.isArray(s) ? s : []);
                    } catch { setPromoteSections([]); }
                  }
                }}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm">
                  <option value="">Select class</option>
                  {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Target Section *</label>
                <select value={promoteTargetSectionId} onChange={e => setPromoteTargetSectionId(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm">
                  <option value="">Select section</option>
                  {promoteSections.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowPromoteModal(false)} className="rounded border border-gray-300 px-4 py-2 text-sm">Cancel</button>
              <button onClick={handleBulkPromote} disabled={promoteLoading}
                className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
                {promoteLoading ? 'Promoting…' : `Promote ${bulkSelected.size} Students`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Page;
