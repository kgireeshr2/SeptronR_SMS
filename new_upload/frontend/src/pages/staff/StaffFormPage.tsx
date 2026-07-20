import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { staffApi, StaffCreate, StaffUpdate, Department, Designation } from '../../api/staff';
import { rolesApi, RoleResponse } from '../../api/roles';

const unwrap = (res: any) => res?.data ?? res;

const Field = ({
  label,
  required,
  children,
  error,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
  error?: string;
}) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">
      {label} {required && <span className="text-red-500">*</span>}
    </label>
    {children}
    {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
  </div>
);

const inputClass = (err?: string) =>
  `w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
    err ? 'border-red-400' : 'border-gray-300'
  }`;

const EMPLOYMENT_TYPES = [
  { value: 'permanent', label: 'Permanent' },
  { value: 'contract', label: 'Contract' },
  { value: 'part_time', label: 'Part Time' },
  { value: 'probation', label: 'Probation' },
];

const SALARY_TYPES = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'hourly', label: 'Hourly' },
  { value: 'daily', label: 'Daily' },
];

const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
];

type FormData = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  gender: string;
  department_id: string;
  designation_id: string;
  date_of_joining: string;
  employment_type: string;
  salary_type: string;
  monthly_salary: string;
  bank_account_no: string;
  bank_name: string;
  ifsc_code: string;
  address: string;
  experience_years: string;
  aadhaar_number: string;
  pan_number: string;
  driving_licence: string;
  role_ids: string[];
};

const emptyForm: FormData = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  date_of_birth: '',
  gender: '',
  department_id: '',
  designation_id: '',
  date_of_joining: '',
  employment_type: 'permanent',
  salary_type: 'monthly',
  monthly_salary: '0',
  bank_account_no: '',
  bank_name: '',
  ifsc_code: '',
  address: '',
  experience_years: '',
  aadhaar_number: '',
  pan_number: '',
  driving_licence: '',
  role_ids: [],
};

const StaffFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { staffId } = useParams<{ staffId: string }>();
  const isEdit = !!staffId;

  const [form, setForm] = useState<FormData>(emptyForm);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [designations, setDesignations] = useState<Designation[]>([]);
  const [allRoles, setAllRoles] = useState<RoleResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchingStaff, setFetchingStaff] = useState(isEdit);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const loadDropdowns = async () => {
      try {
        const [deptsRes, desigRes, rolesRes] = await Promise.all([
          staffApi.listDepartments({ is_active: true }),
          staffApi.listDesignations({ is_active: true }),
          rolesApi.list(),
        ]);
        setDepartments(unwrap(deptsRes) ?? []);
        setDesignations(unwrap(desigRes) ?? []);
        setAllRoles(unwrap(rolesRes) ?? []);
      } catch {
        // non-fatal — dropdowns stay empty
      }
    };
    loadDropdowns();
  }, []);

  // Load existing staff data in edit mode
  useEffect(() => {
    if (!isEdit || !staffId) return;
    const load = async () => {
      try {
        const res = unwrap(await staffApi.getStaff(staffId));
        if (res) {
          setForm({
            first_name: res.first_name ?? '',
            last_name: res.last_name ?? '',
            email: res.email ?? '',
            phone: res.phone ?? '',
            date_of_birth: res.date_of_birth ?? '',
            gender: res.gender ?? '',
            department_id: res.department_id ?? '',
            designation_id: res.designation_id ?? '',
            date_of_joining: res.date_of_joining ?? '',
            employment_type: res.employment_type ?? 'permanent',
            salary_type: res.salary_type ?? 'monthly',
            monthly_salary: res.monthly_salary ? String(res.monthly_salary / 100) : '0',
            bank_account_no: res.bank_account_no ?? '',
            bank_name: res.bank_name ?? '',
            ifsc_code: res.ifsc_code ?? '',
            address: res.address ?? '',
            experience_years: res.experience_years != null ? String(res.experience_years) : '',
            aadhaar_number: (res as any).aadhaar_number ?? '',
            pan_number: (res as any).pan_number ?? '',
            driving_licence: (res as any).driving_licence ?? '',
            role_ids: [],
          });
          // Load current roles
          try {
            const rolesRes = unwrap(await staffApi.getStaffRoles(staffId!));
            if (Array.isArray(rolesRes)) setForm(prev => ({ ...prev, role_ids: rolesRes.map((r: any) => r.id) }));
          } catch { /* ignore */ }
        }
      } catch {
        setError('Failed to load staff data');
      } finally {
        setFetchingStaff(false);
      }
    };
    load();
  }, [staffId, isEdit]);

  const set = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setFieldErrors((prev) => ({ ...prev, [field]: '' }));
  };

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!form.first_name.trim()) errs.first_name = 'First name is required';
    if (!form.last_name.trim()) errs.last_name = 'Last name is required';
    if (!isEdit) {
      if (!form.email.trim()) errs.email = 'Email is required';
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Invalid email';
      if (!form.phone.trim()) errs.phone = 'Phone is required';
    }
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setError(null);

    try {
      if (isEdit && staffId) {
        const updatePayload: StaffUpdate = {
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim(),
          employment_type: form.employment_type as StaffUpdate['employment_type'],
          salary_type: form.salary_type as StaffUpdate['salary_type'],
          monthly_salary: form.monthly_salary ? Math.round(parseFloat(form.monthly_salary) * 100) : 0,
          is_active: true,
        };
        if (form.date_of_birth) updatePayload.date_of_birth = form.date_of_birth;
        if (form.gender) updatePayload.gender = form.gender;
        if (form.department_id) updatePayload.department_id = form.department_id;
        if (form.designation_id) updatePayload.designation_id = form.designation_id;
        if (form.date_of_joining) updatePayload.date_of_joining = form.date_of_joining;
        if (form.bank_account_no.trim()) updatePayload.bank_account_no = form.bank_account_no.trim();
        if (form.bank_name.trim()) updatePayload.bank_name = form.bank_name.trim();
        if (form.ifsc_code.trim()) updatePayload.ifsc_code = form.ifsc_code.trim();
        if (form.address.trim()) updatePayload.address = form.address.trim();
        if (form.experience_years) updatePayload.experience_years = parseFloat(form.experience_years);
        if (form.aadhaar_number.trim()) (updatePayload as any).aadhaar_number = form.aadhaar_number.trim();
        if (form.pan_number.trim()) (updatePayload as any).pan_number = form.pan_number.trim();
        if (form.driving_licence.trim()) (updatePayload as any).driving_licence = form.driving_licence.trim();
        await staffApi.updateStaff(staffId, updatePayload);
        // Update roles separately
        await staffApi.assignStaffRoles(staffId, form.role_ids);
        navigate(`/admin/staff/${staffId}`);
      } else {
        const payload: StaffCreate = {
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim(),
          email: form.email.trim(),
          phone: form.phone.trim(),
          role_ids: form.role_ids,
          employment_type: form.employment_type as StaffCreate['employment_type'],
          salary_type: form.salary_type as StaffCreate['salary_type'],
          monthly_salary: form.monthly_salary ? Math.round(parseFloat(form.monthly_salary) * 100) : 0,
        };
        if (form.date_of_birth) payload.date_of_birth = form.date_of_birth;
        if (form.gender) payload.gender = form.gender;
        if (form.department_id) payload.department_id = form.department_id;
        if (form.designation_id) payload.designation_id = form.designation_id;
        if (form.date_of_joining) payload.date_of_joining = form.date_of_joining;
        if (form.bank_account_no.trim()) payload.bank_account_no = form.bank_account_no.trim();
        if (form.bank_name.trim()) payload.bank_name = form.bank_name.trim();
        if (form.ifsc_code.trim()) payload.ifsc_code = form.ifsc_code.trim();
        if (form.address.trim()) payload.address = form.address.trim();
        if (form.experience_years) payload.experience_years = parseFloat(form.experience_years);
        if (form.aadhaar_number.trim()) (payload as any).aadhaar_number = form.aadhaar_number.trim();
        if (form.pan_number.trim()) (payload as any).pan_number = form.pan_number.trim();
        if (form.driving_licence.trim()) (payload as any).driving_licence = form.driving_licence.trim();
        await staffApi.createStaff(payload);
        navigate('/admin/staff');
      }
    } catch (err: any) {
      const detail = err?.detail || err?.response?.data?.detail || `Failed to ${isEdit ? 'update' : 'create'} staff member`;
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  if (fetchingStaff) {
    return <div className="flex h-64 items-center justify-center text-gray-400">Loading staff data…</div>;
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate(isEdit ? `/admin/staff/${staffId}` : '/admin/staff')}
          className="text-gray-500 hover:text-gray-700 text-sm"
        >
          ← Back
        </button>
        <h1 className="text-2xl font-bold">{isEdit ? 'Edit Staff Member' : 'Add New Staff Member'}</h1>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 mb-6 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* ── Personal Information ── */}
        <section className="bg-white rounded shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-800">Personal Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="First Name" required error={fieldErrors.first_name}>
              <input
                type="text"
                value={form.first_name}
                onChange={set('first_name')}
                className={inputClass(fieldErrors.first_name)}
                placeholder="e.g. John"
              />
            </Field>
            <Field label="Last Name" required error={fieldErrors.last_name}>
              <input
                type="text"
                value={form.last_name}
                onChange={set('last_name')}
                className={inputClass(fieldErrors.last_name)}
                placeholder="e.g. Doe"
              />
            </Field>
            {!isEdit && (
              <>
                <Field label="Email" required error={fieldErrors.email}>
                  <input
                    type="email"
                    value={form.email}
                    onChange={set('email')}
                    className={inputClass(fieldErrors.email)}
                    placeholder="john.doe@school.com"
                  />
                </Field>
                <Field label="Phone" required error={fieldErrors.phone}>
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={set('phone')}
                    className={inputClass(fieldErrors.phone)}
                    placeholder="e.g. 9876543210"
                  />
                </Field>
              </>
            )}
            {isEdit && form.email && (
              <Field label="Email">
                <input type="email" value={form.email} disabled className="w-full border border-gray-200 rounded px-3 py-2 text-sm bg-gray-50 text-gray-500 cursor-not-allowed" />
                <p className="mt-0.5 text-[11px] text-gray-400">Email cannot be changed here</p>
              </Field>
            )}
            <Field label="Date of Birth">
              <input
                type="date"
                value={form.date_of_birth}
                onChange={set('date_of_birth')}
                className={inputClass()}
              />
            </Field>
            <Field label="Gender">
              <select value={form.gender} onChange={set('gender')} className={inputClass()}>
                <option value="">— Select —</option>
                {GENDER_OPTIONS.map((g) => (
                  <option key={g.value} value={g.value}>{g.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Address" >
              <textarea
                value={form.address}
                onChange={set('address')}
                className={inputClass()}
                rows={2}
                placeholder="Street, City, State"
              />
            </Field>
            <Field label="Experience (years)">
              <input
                type="number"
                min="0"
                step="0.5"
                value={form.experience_years}
                onChange={set('experience_years')}
                className={inputClass()}
                placeholder="e.g. 3.5"
              />
            </Field>
          </div>
        </section>

        {/* ── Employment Details ── */}
        <section className="bg-white rounded shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-800">Employment Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Department">
              <select value={form.department_id} onChange={set('department_id')} className={inputClass()}>
                <option value="">— None —</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Designation">
              <select value={form.designation_id} onChange={set('designation_id')} className={inputClass()}>
                <option value="">— None —</option>
                {designations.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Date of Joining">
              <input
                type="date"
                value={form.date_of_joining}
                onChange={set('date_of_joining')}
                className={inputClass()}
              />
            </Field>
            <Field label="Employment Type">
              <select value={form.employment_type} onChange={set('employment_type')} className={inputClass()}>
                {EMPLOYMENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </Field>
          </div>
        </section>

        {/* ── Salary & Bank ── */}
        <section className="bg-white rounded shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-800">Salary & Bank Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Salary Type">
              <select value={form.salary_type} onChange={set('salary_type')} className={inputClass()}>
                {SALARY_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Monthly Salary (₹)">
              <input
                type="number"
                min="0"
                value={form.monthly_salary}
                onChange={set('monthly_salary')}
                className={inputClass()}
                placeholder="0"
              />
            </Field>
            <Field label="Bank Account No.">
              <input
                type="text"
                value={form.bank_account_no}
                onChange={set('bank_account_no')}
                className={inputClass()}
              />
            </Field>
            <Field label="Bank Name">
              <input
                type="text"
                value={form.bank_name}
                onChange={set('bank_name')}
                className={inputClass()}
              />
            </Field>
            <Field label="IFSC Code">
              <input
                type="text"
                value={form.ifsc_code}
                onChange={set('ifsc_code')}
                className={inputClass()}
              />
            </Field>
          </div>
        </section>

        {/* ── Government IDs ── */}
        <section>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500 border-b pb-2">
            Government IDs
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Field label="Aadhaar Number">
              <input
                type="text"
                value={form.aadhaar_number}
                onChange={set('aadhaar_number')}
                placeholder="XXXX XXXX XXXX"
                maxLength={14}
                className={inputClass()}
              />
            </Field>
            <Field label="PAN Number">
              <input
                type="text"
                value={form.pan_number}
                onChange={(e) => setForm((p) => ({ ...p, pan_number: e.target.value.toUpperCase() }))}
                placeholder="ABCDE1234F"
                maxLength={10}
                className={inputClass() + ' font-mono'}
              />
            </Field>
            <Field label="Driving Licence">
              <input
                type="text"
                value={form.driving_licence}
                onChange={set('driving_licence')}
                placeholder="DL number"
                className={inputClass()}
              />
            </Field>
          </div>
        </section>

        {/* ── System Roles ── */}
        {allRoles.length > 0 && (
          <section className="bg-white rounded shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">System Roles</h2>
            <p className="text-xs text-gray-500 mb-3">Select the roles this staff member should have in the system.</p>
            <div className="flex flex-wrap gap-3">
              {allRoles.map(role => (
                <label key={role.id} className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    checked={form.role_ids.includes(role.id)}
                    onChange={e => {
                      setForm(prev => ({
                        ...prev,
                        role_ids: e.target.checked
                          ? [...prev.role_ids, role.id]
                          : prev.role_ids.filter(id => id !== role.id),
                      }));
                    }}
                  />
                  <span className="text-sm text-gray-700">{role.name}</span>
                </label>
              ))}
            </div>
          </section>
        )}

        {/* ── Actions ── */}
        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={() => navigate(isEdit ? `/admin/staff/${staffId}` : '/admin/staff')}
            className="px-5 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? (isEdit ? 'Saving…' : 'Creating…') : (isEdit ? 'Save Changes' : 'Create Staff Member')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default StaffFormPage;
