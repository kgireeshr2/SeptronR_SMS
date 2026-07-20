import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  School, Plus, Power, PowerOff,
  Users, GraduationCap, CheckCircle, Circle, ArrowRight,
  Building2, Package, CreditCard, LogIn,
  Trash2,
} from 'lucide-react';
import api from '@/api/axios';
import { useAuthStore } from '@store/authStore';
import { toast } from 'sonner';

interface SchoolOverview {
  id: string;
  name: string;
  code: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  logo_url?: string | null;
  setup_progress: number; // 0–8 steps completed
}

interface Plan {
  id: string;
  name: string;
  max_students?: number;
  max_staff?: number;
  enabled_modules: string[];
  price_monthly_paise: number;
}

interface Subscription {
  id: string;
  school_id: string;
  school_name?: string;
  plan_id: string;
  plan_name?: string;
  start_date: string;
  end_date?: string | null;
  is_active: boolean;
  max_students?: number;
  max_staff?: number;
}

interface FeatureFlag {
  id: string;
  school_id?: string | null;
  flag_key: string;
  is_enabled: boolean;
  description?: string;
}

const fmt = (paise: number) =>
  paise === 0 ? 'Free' : `₹${(paise / 100).toFixed(0)}/mo`;

const SETUP_STEPS = [
  { key: 'academic_year', label: 'Academic Year' },
  { key: 'classes',       label: 'Classes & Sections' },
  { key: 'staff',         label: 'Staff Added' },
  { key: 'students',      label: 'Students Enrolled' },
  { key: 'fees',          label: 'Fee Structures' },
  { key: 'timetable',     label: 'Timetable' },
  { key: 'exams',         label: 'Exams Created' },
  { key: 'attendance',    label: 'Attendance Tracked' },
];

const SuperAdminPage: React.FC = () => {
  const navigate = useNavigate();
  const { setSchool } = useAuthStore();

  const [schools, setSchools] = useState<SchoolOverview[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [featureFlags, setFeatureFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'schools' | 'plans' | 'subscriptions' | 'feature_flags' | 'impersonation'>('schools');

  // Impersonation
  const [impLogs, setImpLogs] = useState<any[]>([]);
  const [impLoading, setImpLoading] = useState(false);
  const [impSchoolId, setImpSchoolId] = useState('');
  const [impUserId, setImpUserId] = useState('');
  const [impSchoolUsers, setImpSchoolUsers] = useState<any[]>([]);

  // Create school modal
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '', code: '', slug: '', address: '', phone: '', email: '',
    admin_email: '', admin_password: '',
    admin_first_name: '', admin_last_name: '',
  });

  // Plan modal
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [planForm, setPlanForm] = useState({
    name: '', max_students: '', max_staff: '',
    price_monthly_paise: '0', enabled_modules: '',
  });

  // Subscription modal
  const [showSubModal, setShowSubModal] = useState(false);
  const [subForm, setSubForm] = useState({
    school_id: '', plan_id: '', start_date: new Date().toISOString().slice(0, 10),
    end_date: '', max_students: '', max_staff: '',
  });

  // Feature flag modal
  const [showFlagModal, setShowFlagModal] = useState(false);
  const [flagForm, setFlagForm] = useState({ school_id: '', flag_key: '', is_enabled: true, description: '' });

  // Impersonate
  const [impersonating, setImpersonating] = useState<string | null>(null);

  useEffect(() => { loadSchools(); }, []);
  useEffect(() => {
    if (tab === 'plans') loadPlans();
    if (tab === 'subscriptions') loadSubscriptions();
    if (tab === 'feature_flags') loadFeatureFlags();
    if (tab === 'impersonation') loadImpLogs();
  }, [tab]);

  const loadSchools = async () => {
    setLoading(true);
    try {
      const res = await api.get('/superadmin/schools') as any;
      const list = Array.isArray(res) ? res : (res?.data ?? res?.items ?? []);
      setSchools(list);
    } catch (err: any) {
      const detail =
        err?.detail ??
        err?.message ??
        (typeof err === 'string' ? err : 'Failed to load schools');
      toast.error(`Failed to load schools: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  const loadPlans = async () => {
    try {
      const res = await api.get('/superadmin/plans') as any;
      setPlans(Array.isArray(res) ? res : (res?.data ?? []));
    } catch { /* ignore */ }
  };

  const loadSubscriptions = async () => {
    try {
      const res = await api.get('/superadmin/subscriptions') as any;
      const rows: Subscription[] = Array.isArray(res) ? res : (res?.data ?? []);
      // Enrich with school/plan names
      setSubscriptions(rows.map(s => ({
        ...s,
        school_name: schools.find(sc => sc.id === s.school_id)?.name ?? s.school_id,
        plan_name: plans.find(p => p.id === s.plan_id)?.name ?? s.plan_id,
      })));
    } catch { /* ignore */ }
  };

  const loadFeatureFlags = async () => {
    try {
      const res = await api.get('/superadmin/feature-flags') as any;
      setFeatureFlags(Array.isArray(res) ? res : (res?.data ?? []));
    } catch { /* ignore */ }
  };

  const loadImpLogs = async () => {
    setImpLoading(true);
    try {
      const r: any = await api.get('/superadmin/impersonate');
      setImpLogs(Array.isArray(r) ? r : (r?.data ?? []));
    } catch { /* ignore */ } finally { setImpLoading(false); }
  };

  const loadSchoolUsers = async (schoolId: string) => {
    setImpSchoolId(schoolId);
    setImpUserId('');
    try {
      const r: any = await api.get(`/superadmin/schools/${schoolId}/users`);
      setImpSchoolUsers(Array.isArray(r) ? r : (r?.data ?? []));
    } catch { setImpSchoolUsers([]); }
  };

  const handleStartImpersonation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!impSchoolId || !impUserId) { toast.error('Select school and user'); return; }
    try {
      const r: any = await api.post('/superadmin/impersonate', { school_id: impSchoolId, user_id: impUserId });
      toast.success(`Impersonation started. Log ID: ${r?.id ?? '—'}`);
      loadImpLogs();
    } catch (err: any) { toast.error(err?.response?.data?.detail ?? 'Failed to start impersonation'); }
  };

  const handleEndImpersonation = async (logId: string) => {
    try {
      await api.patch(`/superadmin/impersonate/${logId}/end`);
      toast.success('Impersonation ended');
      loadImpLogs();
    } catch { toast.error('Failed to end impersonation'); }
  };

  const handleManageSchool = (school: SchoolOverview) => {
    // Atomic switch: updates schoolInfo (→ X-School-Id), syncs localStorage,
    // resets the academic year, and clears the React Query cache.
    setSchool({ id: school.id, name: school.name, slug: school.slug, logo_url: school.logo_url });
    toast.success(`Managing: ${school.name}`);
    navigate('/dashboard');
  };

  const handleImpersonate = async (school: SchoolOverview) => {
    setImpersonating(school.id);
    try {
      // Records the impersonation on the backend (audit log). The active-school
      // switch below is what actually scopes every subsequent request.
      await api.post(`/superadmin/impersonate/${school.id}`).catch(() => undefined);
      setSchool({ id: school.id, name: school.name, slug: school.slug, logo_url: school.logo_url });
      toast.success(`Impersonating admin of: ${school.name}`);
      navigate('/dashboard');
    } finally {
      setImpersonating(null);
    }
  };

  const handleToggleSchool = async (school: SchoolOverview) => {
    try {
      await api.patch(`/superadmin/schools/${school.id}/toggle-active?is_active=${!school.is_active}`);
      toast.success(`School ${school.is_active ? 'deactivated' : 'activated'}`);
      loadSchools();
    } catch {
      toast.error('Failed to update school status');
    }
  };

  const handleCreateSchool = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post('/schools/bootstrap', {
        school_name: createForm.name,
        address: createForm.address || undefined,
        phone: createForm.phone || undefined,
        email: createForm.email || undefined,
        admin_email: createForm.admin_email || undefined,
        admin_password: createForm.admin_password || undefined,
        admin_first_name: createForm.admin_first_name || undefined,
        admin_last_name: createForm.admin_last_name || undefined,
      });
      toast.success('School created successfully!');
      setShowCreate(false);
      setCreateForm({
        name: '', code: '', slug: '', address: '', phone: '', email: '',
        admin_email: '', admin_password: '',
        admin_first_name: '', admin_last_name: '',
      });
      loadSchools();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err?.message ?? 'Failed to create school';
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setCreating(false);
    }
  };

  const handleSavePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/superadmin/plans', {
        ...planForm,
        max_students: planForm.max_students ? +planForm.max_students : null,
        max_staff: planForm.max_staff ? +planForm.max_staff : null,
        price_monthly_paise: +planForm.price_monthly_paise,
        enabled_modules: planForm.enabled_modules.split(',').map(s => s.trim()).filter(Boolean),
      });
      toast.success('Plan created');
      setShowPlanModal(false);
      setPlanForm({ name: '', max_students: '', max_staff: '', price_monthly_paise: '0', enabled_modules: '' });
      loadPlans();
    } catch {
      toast.error('Failed to create plan');
    }
  };

  const handleSaveSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/superadmin/subscriptions', {
        school_id: subForm.school_id,
        plan_id: subForm.plan_id,
        start_date: subForm.start_date,
        end_date: subForm.end_date || null,
        max_students: subForm.max_students ? +subForm.max_students : null,
        max_staff: subForm.max_staff ? +subForm.max_staff : null,
      });
      toast.success('Subscription created');
      setShowSubModal(false);
      setSubForm({ school_id: '', plan_id: '', start_date: new Date().toISOString().slice(0, 10), end_date: '', max_students: '', max_staff: '' });
      loadSubscriptions();
    } catch {
      toast.error('Failed to create subscription');
    }
  };

  const handleDeactivateSubscription = async (id: string) => {
    if (!confirm('Deactivate this subscription?')) return;
    try {
      await api.patch(`/superadmin/subscriptions/${id}/deactivate`);
      toast.success('Subscription deactivated');
      loadSubscriptions();
    } catch {
      toast.error('Failed to deactivate subscription');
    }
  };

  const handleSaveFeatureFlag = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/superadmin/feature-flags', {
        school_id: flagForm.school_id || null,
        flag_key: flagForm.flag_key,
        is_enabled: flagForm.is_enabled,
        description: flagForm.description || null,
      });
      toast.success('Feature flag saved');
      setShowFlagModal(false);
      setFlagForm({ school_id: '', flag_key: '', is_enabled: true, description: '' });
      loadFeatureFlags();
    } catch {
      toast.error('Failed to save feature flag');
    }
  };

  const handleToggleFlag = async (flag: FeatureFlag) => {
    try {
      await api.patch(`/superadmin/feature-flags/${flag.id}`, { is_enabled: !flag.is_enabled });
      setFeatureFlags(prev => prev.map(f => f.id === flag.id ? { ...f, is_enabled: !f.is_enabled } : f));
    } catch {
      toast.error('Failed to toggle flag');
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Super Admin Dashboard</h1>
          <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
            Manage schools, subscription plans, and system settings
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 shadow-sm"
        >
          <Plus size={16} />
          Create School
        </button>
      </div>

      {/* Stats */}
      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: 'Total Schools', value: schools.length, icon: <Building2 size={18} />, color: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400' },
          { label: 'Active Schools', value: schools.filter(s => s.is_active).length, icon: <CheckCircle size={18} />, color: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
          { label: 'Plans Available', value: plans.length, icon: <CreditCard size={18} />, color: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
          { label: 'Inactive', value: schools.filter(s => !s.is_active).length, icon: <Circle size={18} />, color: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400' },
        ].map(stat => (
          <div key={stat.label} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className={`mb-2 flex h-8 w-8 items-center justify-center rounded-lg ${stat.color}`}>
              {stat.icon}
            </div>
            <p className="text-xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="mb-4 flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {([
          { key: 'schools', label: `Schools (${schools.length})` },
          { key: 'plans', label: 'Subscription Plans' },
          { key: 'subscriptions', label: 'Subscriptions' },
          { key: 'feature_flags', label: 'Feature Flags' },
          { key: 'impersonation', label: '🕵️ Impersonation' },
        ] as const).map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 capitalize transition-colors -mb-px ${
              tab === t.key
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Schools Tab */}
      {tab === 'schools' && (
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
            </div>
          ) : schools.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <School size={48} className="mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300">No Schools Yet</h3>
              <p className="mt-1 text-sm text-gray-500">Create your first school to get started</p>
              <button
                onClick={() => setShowCreate(true)}
                className="mt-4 flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
              >
                <Plus size={16} />
                Create Your First School
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">School</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Code</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Setup Progress</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Status</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Created</th>
                    <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {schools.map(school => (
                    <tr key={school.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                            <School size={16} className="text-indigo-600 dark:text-indigo-400" />
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 dark:text-white">{school.name}</p>
                            <p className="text-xs text-gray-400">{school.slug}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="rounded bg-gray-100 px-2 py-0.5 font-mono text-xs dark:bg-gray-700">{school.code}</span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1">
                          {SETUP_STEPS.map((step, i) => (
                            <div
                              key={step.key}
                              title={`${step.label}: ${i < school.setup_progress ? '✓ Done' : 'Pending'}`}
                              className={`h-2.5 w-2.5 rounded-full transition-colors ${
                                i < school.setup_progress
                                  ? 'bg-green-500'
                                  : 'bg-gray-200 dark:bg-gray-600'
                              }`}
                            />
                          ))}
                          <span className="ml-1 text-xs text-gray-400">
                            {school.setup_progress}/{SETUP_STEPS.length}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          school.is_active
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        }`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${school.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                          {school.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-xs text-gray-400">
                        {new Date(school.created_at).toLocaleDateString('en-IN')}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleManageSchool(school)}
                            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
                          >
                            Manage
                            <ArrowRight size={12} />
                          </button>
                          <button
                            onClick={() => handleImpersonate(school)}
                            disabled={impersonating === school.id}
                            title="Impersonate School Admin"
                            className="flex items-center gap-1 rounded-lg border border-purple-200 px-2 py-1.5 text-xs font-medium text-purple-600 hover:bg-purple-50 dark:border-purple-800 dark:hover:bg-purple-900/20 disabled:opacity-50"
                          >
                            {impersonating === school.id
                              ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
                              : <LogIn size={12} />}
                          </button>
                          <button
                            onClick={() => handleToggleSchool(school)}
                            title={school.is_active ? 'Deactivate' : 'Activate'}
                            className={`rounded-lg border p-1.5 ${
                              school.is_active
                                ? 'border-red-200 text-red-500 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20'
                                : 'border-green-200 text-green-500 hover:bg-green-50 dark:border-green-800 dark:hover:bg-green-900/20'
                            }`}
                          >
                            {school.is_active ? <PowerOff size={14} /> : <Power size={14} />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Plans Tab */}
      {tab === 'plans' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button
              onClick={() => setShowPlanModal(true)}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Plus size={16} />
              Add Plan
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {plans.length === 0 ? (
              <p className="col-span-3 rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center text-gray-500 dark:border-gray-600 dark:bg-gray-800">
                No plans yet. Create your first subscription plan.
              </p>
            ) : plans.map(p => (
              <div key={p.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-base font-bold text-gray-900 dark:text-white">{p.name}</h4>
                    <p className="mt-0.5 text-xl font-bold text-indigo-600">{fmt(p.price_monthly_paise)}</p>
                  </div>
                  <Package size={20} className="text-gray-400" />
                </div>
                <div className="mt-3 space-y-1 text-xs text-gray-500">
                  <p><Users size={12} className="mr-1 inline" /> Students: {p.max_students ?? 'Unlimited'}</p>
                  <p><GraduationCap size={12} className="mr-1 inline" /> Staff: {p.max_staff ?? 'Unlimited'}</p>
                </div>
                {p.enabled_modules.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {p.enabled_modules.map(m => (
                      <span key={m} className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs capitalize text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
                        {m}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Subscriptions Tab ── */}
      {tab === 'subscriptions' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button
              onClick={() => setShowSubModal(true)}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Plus size={16} />
              Add Subscription
            </button>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-hidden">
            {subscriptions.length === 0 ? (
              <p className="p-8 text-center text-gray-500">No subscriptions yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    {['School', 'Plan', 'Start Date', 'End Date', 'Status', 'Actions'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {subscriptions.map(s => (
                    <tr key={s.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3 font-medium">{s.school_name ?? s.school_id}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{s.plan_name ?? s.plan_id}</td>
                      <td className="px-4 py-3 text-xs text-gray-500">{s.start_date}</td>
                      <td className="px-4 py-3 text-xs text-gray-500">{s.end_date ?? '—'}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                          s.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {s.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {s.is_active && (
                          <button
                            onClick={() => handleDeactivateSubscription(s.id)}
                            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                          >
                            <Trash2 size={12} /> Deactivate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ── Feature Flags Tab ── */}
      {tab === 'feature_flags' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button
              onClick={() => setShowFlagModal(true)}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Plus size={16} />
              Add Flag
            </button>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-hidden">
            {featureFlags.length === 0 ? (
              <p className="p-8 text-center text-gray-500">No feature flags configured yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    {['Flag Key', 'Scope', 'Description', 'Status'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {featureFlags.map(f => (
                    <tr key={f.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3 font-mono text-xs font-semibold text-indigo-700 dark:text-indigo-400">{f.flag_key}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          f.school_id ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {f.school_id ? schools.find(sc => sc.id === f.school_id)?.name ?? f.school_id : 'Global'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">{f.description ?? '—'}</td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleToggleFlag(f)}
                          className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none ${
                            f.is_enabled ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-600'
                          }`}
                          title={f.is_enabled ? 'Disable' : 'Enable'}
                        >
                          <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition-transform ${
                            f.is_enabled ? 'translate-x-4' : 'translate-x-0'
                          }`} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ── Add Subscription Modal ── */}
      {showSubModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
            <h3 className="mb-4 text-lg font-semibold dark:text-white">Add Subscription</h3>
            <form onSubmit={handleSaveSubscription} className="space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium dark:text-gray-300">School *</label>
                <select
                  required
                  value={subForm.school_id}
                  onChange={e => setSubForm(f => ({ ...f, school_id: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">Select school...</option>
                  {schools.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium dark:text-gray-300">Plan *</label>
                <select
                  required
                  value={subForm.plan_id}
                  onChange={e => setSubForm(f => ({ ...f, plan_id: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">Select plan...</option>
                  {plans.map(p => <option key={p.id} value={p.id}>{p.name} — {fmt(p.price_monthly_paise)}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium dark:text-gray-300">Start Date *</label>
                  <input type="date" required value={subForm.start_date}
                    onChange={e => setSubForm(f => ({ ...f, start_date: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white" />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium dark:text-gray-300">End Date</label>
                  <input type="date" value={subForm.end_date}
                    onChange={e => setSubForm(f => ({ ...f, end_date: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white" />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium dark:text-gray-300">Max Students</label>
                  <input type="number" value={subForm.max_students} placeholder="Unlimited"
                    onChange={e => setSubForm(f => ({ ...f, max_students: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white" />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium dark:text-gray-300">Max Staff</label>
                  <input type="number" value={subForm.max_staff} placeholder="Unlimited"
                    onChange={e => setSubForm(f => ({ ...f, max_staff: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowSubModal(false)} className="rounded-lg border px-4 py-2 text-sm dark:border-gray-600">Cancel</button>
                <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Add Feature Flag Modal ── */}
      {showFlagModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
            <h3 className="mb-4 text-lg font-semibold dark:text-white">Add Feature Flag</h3>
            <form onSubmit={handleSaveFeatureFlag} className="space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium dark:text-gray-300">School (leave blank for global)</label>
                <select
                  value={flagForm.school_id}
                  onChange={e => setFlagForm(f => ({ ...f, school_id: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">— Global —</option>
                  {schools.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium dark:text-gray-300">Flag Key *</label>
                <input required value={flagForm.flag_key} placeholder="e.g. enable_library_module"
                  onChange={e => setFlagForm(f => ({ ...f, flag_key: e.target.value.toLowerCase().replace(/\s+/g, '_') }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-700 dark:text-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium dark:text-gray-300">Description</label>
                <input value={flagForm.description} placeholder="Optional description"
                  onChange={e => setFlagForm(f => ({ ...f, description: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white" />
              </div>
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium dark:text-gray-300">Enabled by default</label>
                <button type="button" onClick={() => setFlagForm(f => ({ ...f, is_enabled: !f.is_enabled }))}
                  className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                    flagForm.is_enabled ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-600'
                  }`}>
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    flagForm.is_enabled ? 'translate-x-4' : 'translate-x-0'
                  }`} />
                </button>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowFlagModal(false)} className="rounded-lg border px-4 py-2 text-sm dark:border-gray-600">Cancel</button>
                <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Impersonation Tab ── */}
      {tab === 'impersonation' && (
        <div className="space-y-6">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-4 text-base font-semibold dark:text-white">Start Impersonation</h3>
            <form onSubmit={handleStartImpersonation} className="flex flex-wrap items-end gap-3">
              <div>
                <label className="mb-1 block text-xs text-gray-500">School</label>
                <select value={impSchoolId} onChange={e => loadSchoolUsers(e.target.value)}
                  className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white">
                  <option value="">— Select school —</option>
                  {schools.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-500">User</label>
                <select value={impUserId} onChange={e => setImpUserId(e.target.value)}
                  className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white min-w-[200px]">
                  <option value="">— Select user —</option>
                  {impSchoolUsers.map((u: any) => <option key={u.id} value={u.id}>{u.username} ({u.email})</option>)}
                </select>
              </div>
              <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
                Start Impersonation
              </button>
            </form>
            {impSchoolId && impSchoolUsers.length === 0 && (
              <p className="mt-2 text-xs text-gray-400">No users found for this school, or endpoint not available.</p>
            )}
          </div>

          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700">
              <h3 className="font-semibold dark:text-white">Impersonation Logs</h3>
              <button onClick={loadImpLogs} className="text-xs text-indigo-600 hover:underline">Refresh</button>
            </div>
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>{['School', 'User', 'Started At', 'Ended At', 'Actions'].map(h => <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {impLoading ? <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
                  : impLogs.length === 0 ? <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No impersonation logs.</td></tr>
                    : impLogs.map((log: any) => (
                      <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <td className="px-4 py-3">{log.school_name ?? log.school_id}</td>
                        <td className="px-4 py-3 text-gray-600">{log.target_username ?? log.user_id}</td>
                        <td className="px-4 py-3 text-gray-500 text-xs">{log.started_at ? new Date(log.started_at).toLocaleString() : '—'}</td>
                        <td className="px-4 py-3 text-xs">{log.ended_at ? new Date(log.ended_at).toLocaleString() : <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-yellow-700">Active</span>}</td>
                        <td className="px-4 py-3">
                          {!log.ended_at && (
                            <button onClick={() => handleEndImpersonation(log.id)} className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50">End</button>
                          )}
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Create School Modal ── */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl dark:bg-gray-800 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700 flex-shrink-0">
              <div className="flex items-center gap-2">
                <School size={18} className="text-indigo-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Create New School</h3>
              </div>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
            </div>
            <form onSubmit={handleCreateSchool} className="overflow-y-auto p-6 space-y-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">School Details</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">School Name *</label>
                  <input
                    required
                    value={createForm.name}
                    onChange={e => {
                      const name = e.target.value;
                      const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
                      const code = name.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
                      setCreateForm(f => ({ ...f, name, slug, code }));
                    }}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="e.g. St. Mary's High School"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Code *</label>
                  <input
                    required
                    value={createForm.code}
                    onChange={e => setCreateForm(f => ({ ...f, code: e.target.value.toUpperCase().slice(0, 8) }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="SMHS"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Slug *</label>
                  <input
                    required
                    value={createForm.slug}
                    onChange={e => setCreateForm(f => ({ ...f, slug: e.target.value.toLowerCase() }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="st-marys"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Phone</label>
                  <input
                    value={createForm.phone}
                    onChange={e => setCreateForm(f => ({ ...f, phone: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="9876543210"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
                  <input
                    type="email"
                    value={createForm.email}
                    onChange={e => setCreateForm(f => ({ ...f, email: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="admin@school.com"
                  />
                </div>
                <div className="col-span-2">
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Address</label>
                  <input
                    value={createForm.address}
                    onChange={e => setCreateForm(f => ({ ...f, address: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="123 School Road, City"
                  />
                </div>
              </div>

              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-gray-400">School Admin Account</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">First Name</label>
                  <input
                    value={createForm.admin_first_name}
                    onChange={e => setCreateForm(f => ({ ...f, admin_first_name: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="John"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Last Name</label>
                  <input
                    value={createForm.admin_last_name}
                    onChange={e => setCreateForm(f => ({ ...f, admin_last_name: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="Doe"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Admin Email *</label>
                  <input
                    required
                    type="email"
                    value={createForm.admin_email}
                    onChange={e => setCreateForm(f => ({ ...f, admin_email: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="admin@school.com"
                  />
                </div>
                <div className="col-span-2">
                  <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Admin Password *</label>
                  <input
                    required
                    type="password"
                    minLength={8}
                    value={createForm.admin_password}
                    onChange={e => setCreateForm(f => ({ ...f, admin_password: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="Min 8 characters"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
                >
                  {creating ? (
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  ) : (
                    <Plus size={16} />
                  )}
                  {creating ? 'Creating...' : 'Create School'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Create Plan Modal ── */}
      {showPlanModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
            <h3 className="mb-4 text-lg font-semibold dark:text-white">Add Subscription Plan</h3>
            <form onSubmit={handleSavePlan} className="space-y-3">
              {[
                { label: 'Plan Name *', key: 'name', type: 'text', required: true },
                { label: 'Price (paise/month, 0 = free)', key: 'price_monthly_paise', type: 'number', required: true },
                { label: 'Max Students (empty = unlimited)', key: 'max_students', type: 'number', required: false },
                { label: 'Max Staff (empty = unlimited)', key: 'max_staff', type: 'number', required: false },
                { label: 'Modules (comma-separated)', key: 'enabled_modules', type: 'text', required: false },
              ].map(f => (
                <div key={f.key}>
                  <label className="mb-1 block text-sm font-medium dark:text-gray-300">{f.label}</label>
                  <input
                    type={f.type}
                    required={f.required}
                    value={(planForm as Record<string, string>)[f.key]}
                    onChange={e => setPlanForm(p => ({ ...p, [f.key]: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              ))}
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowPlanModal(false)} className="rounded-lg border px-4 py-2 text-sm dark:border-gray-600">Cancel</button>
                <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">Save Plan</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuperAdminPage;
