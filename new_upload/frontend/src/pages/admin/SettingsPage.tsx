import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';
import { PageHeader } from '@components/shared/PageHeader';
import { schoolsApi } from '@api/schools';
import { academicYearsApi, AcademicYear } from '@api/academicYears';
import { useAcademicYearStore } from '@store/academicYearStore';
import { setActiveDateFormat } from '@utils/formatters';
import { Calendar, Plus, CheckCircle2 } from 'lucide-react';

const unwrap = (res: any) => res?.data ?? res;

const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [profile, setProfile] = React.useState<any>({});
  const [general, setGeneral] = React.useState({ timezone: 'Asia/Kolkata', currency: 'INR', date_format: 'DD/MM/YYYY' });
  const [needsBootstrap, setNeedsBootstrap] = React.useState(false);
  const [activeYearId, setActiveYearId] = React.useState<string>('');
  const [showCreateYear, setShowCreateYear] = React.useState(false);
  const [newYear, setNewYear] = React.useState({ name: '', start_date: '', end_date: '', set_as_active: true });
  const { setSelectedYear, setYears } = useAcademicYearStore();

  const isMissingSchoolContextError = (err: any) => {
    const detail = err?.detail ?? err?.response?.data?.detail ?? '';
    return typeof detail === 'string' && detail.includes('SuperAdmin must provide X-School-Id header');
  };

  useQuery({
    queryKey: ['school-profile'],
    queryFn: async () => {
      try {
        const data = unwrap(await schoolsApi.getProfile());
        setProfile(data ?? {});
        setNeedsBootstrap(false);
        return data;
      } catch (err: any) {
        if (isMissingSchoolContextError(err)) {
          setNeedsBootstrap(true);
          return {};
        }
        throw err;
      }
    },
  });

  useQuery({
    queryKey: ['school-settings'],
    queryFn: async () => {
      try {
        const data = unwrap(await schoolsApi.getSettings());
        const g = data?.general ?? {};
        setGeneral((prev) => ({ ...prev, ...g }));
        return data;
      } catch (err: any) {
        if (isMissingSchoolContextError(err)) {
          setNeedsBootstrap(true);
          return {};
        }
        throw err;
      }
    },
  });

  const { data: academicYearsRaw } = useQuery({
    queryKey: ['academic-years'],
    queryFn: async () => {
      const r = await academicYearsApi.list();
      return unwrap(r) as AcademicYear[];
    },
  });
  const academicYears: AcademicYear[] = Array.isArray(academicYearsRaw) ? academicYearsRaw : [];

  // Set active year id when years load
  React.useEffect(() => {
    const current = academicYears.find(y => y.is_current);
    if (current && !activeYearId) setActiveYearId(current.id);
  }, [academicYears]);

  const setCurrentYearMutation = useMutation({
    mutationFn: (yearId: string) => academicYearsApi.setCurrent(yearId),
    onSuccess: () => {
      toast.success('Active academic year updated');
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
      queryClient.invalidateQueries({ queryKey: ['navbar-academic-years'] });
      const year = academicYears.find((y) => y.id === activeYearId);
      if (year) {
        const mapped = academicYears.map((y) => ({
          id: y.id, name: y.name, startDate: y.start_date, endDate: y.end_date, isCurrent: y.id === activeYearId,
        }));
        setYears(mapped as any);
        setSelectedYear({ id: year.id, name: year.name, startDate: year.start_date, endDate: year.end_date, isCurrent: true } as any);
      }
    },
    onError: () => toast.error('Failed to update academic year'),
  });

  const createYearMutation = useMutation({
    mutationFn: () => academicYearsApi.create({ name: newYear.name, start_date: newYear.start_date, end_date: newYear.end_date }),
    onSuccess: async (res: any) => {
      const created = res?.data ?? res;
      toast.success('Academic year created');
      setNewYear({ name: '', start_date: '', end_date: '', set_as_active: true });
      setShowCreateYear(false);
      if (newYear.set_as_active && created?.id) {
        try {
          await academicYearsApi.setCurrent(created.id);
          setActiveYearId(created.id);
          queryClient.invalidateQueries({ queryKey: ['navbar-academic-years'] });
          const mapped = [{ id: created.id, name: created.name, startDate: created.start_date, endDate: created.end_date, isCurrent: true }];
          setYears(mapped as any);
          setSelectedYear(mapped[0] as any);
        } catch { /* year created, set-active failed */ }
      }
      queryClient.invalidateQueries({ queryKey: ['academic-years'] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail ?? 'Failed to create academic year'),
  });

  const saveProfileMutation = useMutation({
    mutationFn: async () => {
      if (needsBootstrap) {
        const created = unwrap(
          await schoolsApi.bootstrapSchool({
            school_name: profile.school_name || 'My School',
            phone: profile.phone,
            email: profile.email,
            website: profile.website,
            address: profile.address,
            city: profile.city,
            state: profile.state,
            country: profile.country,
            pincode: profile.pincode,
          })
        );
        const schoolId = created?.id;
        if (schoolId) {
          localStorage.setItem('sms-school-id', schoolId);
        }
        return created;
      }
      return schoolsApi.updateProfile(profile);
    },
    onSuccess: () => {
      toast.success(needsBootstrap ? 'School created successfully' : 'Profile updated');
      setNeedsBootstrap(false);
      queryClient.invalidateQueries({ queryKey: ['school-profile'] });
      queryClient.invalidateQueries({ queryKey: ['school-settings'] });
    },
    onError: () => toast.error(needsBootstrap ? 'Failed to create school' : 'Failed to update profile'),
  });

  const saveSettingsMutation = useMutation({
    mutationFn: () => schoolsApi.updateSettings(general as any),
    onSuccess: () => {
      toast.success('General settings updated');
      // Apply the new date format app-wide immediately (no reload needed).
      setActiveDateFormat(general.date_format);
      queryClient.invalidateQueries({ queryKey: ['school-settings'] });
    },
    onError: () => toast.error('Failed to update settings'),
  });

  const logoMutation = useMutation({
    mutationFn: (file: File) => schoolsApi.uploadLogo(file),
    onSuccess: () => {
      toast.success('Logo uploaded');
      queryClient.invalidateQueries({ queryKey: ['school-profile'] });
    },
    onError: () => toast.error('Logo upload failed'),
  });

  return (
    <div>
      <PageHeader title="Settings" subtitle="School configuration and preferences" />

      {needsBootstrap && (
        <div className="mb-4 rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          No school exists yet for this SuperAdmin session. Fill School Profile and click Save Profile to create the first school.
        </div>
      )}

      {/* ─── Active Academic Year (full width, top) ──────────────────────── */}
      <div className="mb-6 rounded-xl border border-blue-200 bg-white p-5 shadow-sm dark:border-blue-900/40 dark:bg-gray-800">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-blue-600 dark:text-blue-400" />
            <h3 className="font-semibold text-gray-900 dark:text-white">Active Academic Year</h3>
          </div>
          <button
            onClick={() => setShowCreateYear((p) => !p)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <Plus size={12} />
            New Year
          </button>
        </div>
        <p className="mb-3 text-xs text-gray-500 dark:text-gray-400">
          The active academic year is used as default across all modules — attendance, fees, exams, and reports.
          All forms pre-populate with this year automatically.
        </p>
        {academicYears.find((y) => y.is_current) && (
          <div className="mb-3 flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 dark:bg-green-900/20">
            <CheckCircle2 size={14} className="text-green-600 dark:text-green-400" />
            <span className="text-sm font-medium text-green-700 dark:text-green-400">
              Currently active: <strong>{academicYears.find((y) => y.is_current)?.name}</strong>
              {' '}({academicYears.find((y) => y.is_current)?.start_date?.slice(0, 10)} → {academicYears.find((y) => y.is_current)?.end_date?.slice(0, 10)})
            </span>
          </div>
        )}
        {academicYears.length === 0 && !showCreateYear ? (
          <p className="text-sm text-amber-600 dark:text-amber-400">No academic years yet — click <strong>New Year</strong> to create one.</p>
        ) : academicYears.length > 0 ? (
          <div className="flex flex-wrap items-center gap-3">
            <select
              className="flex-1 min-w-[200px] rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
              value={activeYearId}
              onChange={(e) => setActiveYearId(e.target.value)}
            >
              {academicYears.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.name} ({y.start_date?.slice(0, 10)} → {y.end_date?.slice(0, 10)}){y.is_current ? ' ✓ Active' : ''}
                </option>
              ))}
            </select>
            <button
              onClick={() => activeYearId && setCurrentYearMutation.mutate(activeYearId)}
              disabled={setCurrentYearMutation.isPending || !activeYearId || !!academicYears.find((y) => y.id === activeYearId)?.is_current}
              className="whitespace-nowrap rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 hover:bg-blue-700"
            >
              {setCurrentYearMutation.isPending ? 'Setting…' : 'Set Active'}
            </button>
          </div>
        ) : null}
        {/* Inline Create Year Form */}
        {showCreateYear && (
          <div className="mt-4 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-900/30">
            <h4 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">Create New Academic Year</h4>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="lg:col-span-1">
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Year Name</label>
                <input
                  placeholder="e.g. 2025-2026"
                  value={newYear.name}
                  onChange={(e) => setNewYear((p) => ({ ...p, name: e.target.value }))}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Start Date</label>
                <input
                  type="date"
                  value={newYear.start_date}
                  onChange={(e) => setNewYear((p) => ({ ...p, start_date: e.target.value }))}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">End Date</label>
                <input
                  type="date"
                  value={newYear.end_date}
                  onChange={(e) => setNewYear((p) => ({ ...p, end_date: e.target.value }))}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <div className="flex flex-col justify-end gap-2">
                <label className="flex cursor-pointer items-center gap-2 text-xs">
                  <input
                    type="checkbox"
                    checked={newYear.set_as_active}
                    onChange={(e) => setNewYear((p) => ({ ...p, set_as_active: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="font-medium text-gray-700 dark:text-gray-300">Set as active year</span>
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      if (!newYear.name || !newYear.start_date || !newYear.end_date) return toast.error('All fields are required');
                      if (new Date(newYear.end_date) <= new Date(newYear.start_date)) return toast.error('End date must be after start date');
                      createYearMutation.mutate();
                    }}
                    disabled={createYearMutation.isPending}
                    className="flex-1 rounded bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
                  >
                    {createYearMutation.isPending ? 'Creating…' : 'Create'}
                  </button>
                  <button
                    onClick={() => setShowCreateYear(false)}
                    className="rounded border border-gray-300 px-3 py-2 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* School Profile */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <h3 className="mb-3 font-semibold">School Profile</h3>
          <div className="space-y-3">
            {[
              { key: 'school_name', placeholder: 'School Name' },
              { key: 'phone', placeholder: 'Phone' },
              { key: 'email', placeholder: 'Email' },
              { key: 'website', placeholder: 'Website' },
            ].map(f => (
              <input
                key={f.key}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                placeholder={f.placeholder}
                value={profile[f.key] ?? ''}
                onChange={(e) => setProfile((p: any) => ({ ...p, [f.key]: e.target.value }))}
              />
            ))}
            <textarea
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
              placeholder="Address"
              value={profile.address ?? ''}
              onChange={(e) => setProfile((p: any) => ({ ...p, address: e.target.value }))}
            />
            <div className="grid grid-cols-3 gap-2">
              {[
                { key: 'city', placeholder: 'City' },
                { key: 'state', placeholder: 'State' },
                { key: 'pincode', placeholder: 'Pincode' },
              ].map(f => (
                <input
                  key={f.key}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                  placeholder={f.placeholder}
                  value={profile[f.key] ?? ''}
                  onChange={(e) => setProfile((p: any) => ({ ...p, [f.key]: e.target.value }))}
                />
              ))}
            </div>
            <div className="flex items-center gap-3">
              <label className="text-xs text-gray-500">Logo:</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) logoMutation.mutate(file);
                }}
                className="text-sm"
              />
            </div>
            <button
              onClick={() => saveProfileMutation.mutate()}
              disabled={saveProfileMutation.isPending}
              className="rounded bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 hover:opacity-90"
            >
              {saveProfileMutation.isPending ? 'Saving�' : 'Save Profile'}
            </button>
          </div>
        </div>

        {/* General Settings */}
        <div className="space-y-6">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-3 font-semibold">General Settings</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-500">Timezone</label>
                <select
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                  value={general.timezone}
                  onChange={(e) => setGeneral((p) => ({ ...p, timezone: e.target.value }))}
                >
                  {['Asia/Kolkata', 'Asia/Dubai', 'UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Singapore', 'Asia/Tokyo'].map(tz => (
                    <option key={tz} value={tz}>{tz}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-500">Currency</label>
                <select
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                  value={general.currency}
                  onChange={(e) => setGeneral((p) => ({ ...p, currency: e.target.value }))}
                >
                  {['INR', 'USD', 'EUR', 'GBP', 'AED', 'SGD', 'JPY', 'CAD', 'AUD'].map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-500">Date Format</label>
                <select
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                  value={general.date_format}
                  onChange={(e) => setGeneral((p) => ({ ...p, date_format: e.target.value }))}
                >
                  {['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD', 'DD-MM-YYYY', 'DD.MM.YYYY'].map(f => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => saveSettingsMutation.mutate()}
                disabled={saveSettingsMutation.isPending}
                className="rounded bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 hover:opacity-90"
              >
                {saveSettingsMutation.isPending ? 'Saving�' : 'Save General Settings'}
              </button>
            </div>
          </div>

        </div>
      </div>

      {/* Link to Advanced Settings */}
      <div className="mt-6 rounded-xl border border-dashed border-gray-300 bg-gray-50 p-4 text-center dark:border-gray-700 dark:bg-gray-800/50">
        <p className="mb-2 text-sm text-gray-600 dark:text-gray-400">
          Need more advanced configuration? (Fees, Attendance, Exam, Library, Security settings)
        </p>
        <Link
          to="/admin/settings/advanced"
          className="inline-flex items-center rounded-lg bg-gray-700 px-4 py-2 text-sm font-medium text-white hover:bg-gray-600 dark:bg-gray-600 dark:hover:bg-gray-500"
        >
          Advanced Settings ?
        </Link>
      </div>
    </div>
  );
};

export default SettingsPage;
