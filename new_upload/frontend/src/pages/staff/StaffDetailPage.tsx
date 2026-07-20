import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { staffApi, Staff, StaffDocument } from '../../api/staff';
import { rolesApi, RoleResponse } from '../../api/roles';
import api from '@/api/axios';
import { toast } from 'sonner';

type Tab = 'profile' | 'documents' | 'payroll' | 'leaves';

const unwrap = (res: any) => res?.data ?? res;
const unwrapArr = (r: any): any[] => Array.isArray(r) ? r : (Array.isArray(r?.data) ? r.data : (Array.isArray(r?.items) ? r.items : []));
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const fmt = (n: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

const LEAVE_STATUS_CLS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700', approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700', cancelled: 'bg-gray-100 text-gray-600',
};

const Badge: React.FC<{ children: React.ReactNode; color?: string }> = ({ children, color = 'gray' }) => {
  const colors: Record<string, string> = {
    green: 'bg-green-100 text-green-800', red: 'bg-red-100 text-red-800',
    blue: 'bg-blue-100 text-blue-800', gray: 'bg-gray-100 text-gray-700', amber: 'bg-amber-100 text-amber-800',
  };
  return <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${colors[color] ?? colors.gray}`}>{children}</span>;
};

const Row: React.FC<{ label: string; value?: React.ReactNode }> = ({ label, value }) => (
  <div className="flex items-start py-2 border-b border-gray-50 last:border-0">
    <span className="w-40 flex-shrink-0 text-xs font-medium text-gray-500">{label}</span>
    <span className="text-sm text-gray-800">{value ?? <span className="text-gray-300">—</span>}</span>
  </div>
);

const StaffDetailPage: React.FC = () => {
  const { staffId } = useParams<{ staffId: string }>();
  const navigate = useNavigate();
  const [staff, setStaff] = useState<Staff | null>(null);
  const [docs, setDocs] = useState<StaffDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [payrolls, setPayrolls] = useState<any[]>([]);
  const [payrollLoading, setPayrollLoading] = useState(false);
  const [leaves, setLeaves] = useState<any[]>([]);
  const [leavesLoading, setLeavesLoading] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [staffRoles, setStaffRoles] = useState<{ id: string; name: string; slug: string }[]>([]);
  const [allRoles, setAllRoles] = useState<RoleResponse[]>([]);
  const [showRolesModal, setShowRolesModal] = useState(false);
  const [editRoleIds, setEditRoleIds] = useState<string[]>([]);
  const [savingRoles, setSavingRoles] = useState(false);

  useEffect(() => {
    if (!staffId) return;
    const load = async () => {
      try {
        const [staffRes, docsRes] = await Promise.allSettled([
          staffApi.getStaff(staffId),
          staffApi.listStaffDocuments(staffId),
        ]);
        if (staffRes.status === 'fulfilled') setStaff(unwrap(staffRes.value));
        else throw new Error('Staff not found');
        if (docsRes.status === 'fulfilled') setDocs(unwrap(docsRes.value) ?? []);
        // Load roles
        try {
          const [rolesRes, allRolesRes] = await Promise.all([
            staffApi.getStaffRoles(staffId!),
            rolesApi.list(),
          ]);
          setStaffRoles(unwrap(rolesRes) ?? []);
          setAllRoles(unwrap(allRolesRes) ?? []);
        } catch { /* non-fatal */ }
      } catch (err: any) {
        setError(err?.response?.data?.detail ?? err?.message ?? 'Failed to load staff');
      } finally { setLoading(false); }
    };
    load();
  }, [staffId]);

  useEffect(() => {
    if (activeTab === 'payroll' && staffId) loadPayroll();
    if (activeTab === 'leaves' && staffId) loadLeaves();
  }, [activeTab]);

  const loadPayroll = async () => {
    setPayrollLoading(true);
    try { setPayrolls(unwrapArr(await api.get(`/payroll/staff/${staffId}`))); }
    catch { setPayrolls([]); } finally { setPayrollLoading(false); }
  };

  const loadLeaves = async () => {
    setLeavesLoading(true);
    try { setLeaves(unwrapArr(await api.get('/leaves/applications', { params: { staff_id: staffId } }))); }
    catch { setLeaves([]); } finally { setLeavesLoading(false); }
  };

  const handleDelete = async () => {
    if (!staffId || !confirm('Delete this staff member? This cannot be undone.')) return;
    try { await staffApi.deleteStaff(staffId); navigate('/admin/staff'); }
    catch (err: any) { alert(err?.response?.data?.detail ?? 'Failed to delete'); }
  };

  const handleToggleActive = async () => {
    if (!staffId || !staff) return;
    try { setStaff(unwrap(await staffApi.updateStaff(staffId, { is_active: !staff.is_active }))); }
    catch { alert('Failed to update status'); }
  };

  const handleDocUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !staffId) return;
    const docType = prompt('Document type (e.g. id_proof, certificate, resume):');
    if (!docType) return;
    setUploadingDoc(true);
    try {
      const fd = new FormData(); fd.append('file', file); fd.append('doc_type', docType);
      await api.post(`/staff/${staffId}/documents`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Document uploaded');
      setDocs(unwrap(await staffApi.listStaffDocuments(staffId)) ?? []);
    } catch { toast.error('Failed to upload document'); }
    finally { setUploadingDoc(false); }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!staffId || !confirm('Delete this document?')) return;
    try {
      await api.delete(`/staff/${staffId}/documents/${docId}`);
      setDocs(prev => prev.filter(d => d.id !== docId));
      toast.success('Document deleted');
    } catch { toast.error('Failed to delete document'); }
  };

  const openRolesModal = () => {
    setEditRoleIds(staffRoles.map(r => r.id));
    setShowRolesModal(true);
  };

  const saveRoles = async () => {
    if (!staffId) return;
    setSavingRoles(true);
    try {
      const updated = unwrap(await staffApi.assignStaffRoles(staffId, editRoleIds));
      setStaffRoles(Array.isArray(updated) ? updated : []);
      setShowRolesModal(false);
      toast.success('Roles updated');
    } catch { toast.error('Failed to update roles'); }
    finally { setSavingRoles(false); }
  };

  if (loading) return <div className="flex h-64 items-center justify-center text-gray-400 text-sm">Loading…</div>;
  if (error || !staff) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 text-center">
        <p className="text-red-500 mb-4">{error ?? 'Staff not found'}</p>
        <Link to="/admin/staff" className="text-blue-600 hover:underline text-sm">← Back to Staff List</Link>
      </div>
    );
  }

  return (
    <><div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button onClick={() => navigate('/admin/staff')} className="text-gray-500 hover:text-gray-700 text-sm">← Staff</button>
        <span className="text-gray-300">/</span>
        <span className="text-sm text-gray-700 font-medium">{staff.full_name}</span>
        <div className="ml-auto flex items-center gap-2">
          <button onClick={handleToggleActive} className={`text-xs px-3 py-1.5 rounded border font-medium transition ${staff.is_active ? 'border-amber-200 text-amber-700 hover:bg-amber-50' : 'border-green-200 text-green-700 hover:bg-green-50'}`}>
            {staff.is_active ? 'Deactivate' : 'Activate'}
          </button>
          <Link to={`/admin/staff/${staffId}/edit`} className="text-xs px-3 py-1.5 rounded border border-blue-200 text-blue-700 hover:bg-blue-50 font-medium">Edit</Link>
          <button onClick={handleDelete} className="text-xs px-3 py-1.5 rounded border border-red-200 text-red-600 hover:bg-red-50 font-medium">Delete</button>
        </div>
      </div>

      {/* Avatar card */}
      <div className="mb-4 flex items-center gap-5 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        {staff.photo_url ? (
          <img src={staff.photo_url} alt={staff.full_name} className="w-16 h-16 rounded-full object-cover ring-2 ring-blue-100" />
        ) : (
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white text-2xl font-bold">
            {staff.first_name?.[0]?.toUpperCase()}{staff.last_name?.[0]?.toUpperCase()}
          </div>
        )}
        <div className="flex-1">
          <h2 className="text-lg font-bold text-gray-800 dark:text-white">{staff.full_name}</h2>
          <p className="text-sm text-gray-500">{staff.designation_name ?? '—'}{staff.department_name ? ` • ${staff.department_name}` : ''}</p>
          <div className="mt-2 flex gap-2">
            <Badge color={staff.is_active ? 'green' : 'red'}>{staff.is_active ? 'Active' : 'Inactive'}</Badge>
            <Badge color="blue">{staff.employment_type?.replace('_', ' ')}</Badge>
          </div>
        </div>
        <div className="text-right text-xs text-gray-500 space-y-0.5">
          {staff.email && <p>{staff.email}</p>}
          {staff.phone && <p>{staff.phone}</p>}
          {staff.employee_id && <p className="font-mono">{staff.employee_id}</p>}
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-5 flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {(['profile','documents','payroll','leaves'] as Tab[]).map(t => (
          <button key={t} onClick={() => setActiveTab(t)} className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px capitalize transition-colors ${activeTab === t ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Profile */}
      {activeTab === 'profile' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Personal Information</h3>
            <Row label="Employee ID" value={<span className="font-mono font-semibold">{staff.employee_id}</span>} />
            <Row label="Date of Birth" value={staff.date_of_birth} />
            <Row label="Gender" value={staff.gender ? staff.gender.charAt(0).toUpperCase() + staff.gender.slice(1) : undefined} />
            <Row label="Experience" value={staff.experience_years != null ? `${staff.experience_years} years` : undefined} />
            <Row label="Address" value={staff.address} />
          </div>
          <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">System Roles</h3>
              <button onClick={openRolesModal} className="text-xs px-2.5 py-1 rounded border border-blue-200 text-blue-600 hover:bg-blue-50 font-medium">Edit Roles</button>
            </div>
            {staffRoles.length === 0 ? (
              <p className="text-sm text-gray-400">No roles assigned.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {staffRoles.map(r => <Badge key={r.id} color="blue">{r.name}</Badge>)}
              </div>
            )}
          </div>
          <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Employment</h3>
            <Row label="Date of Joining" value={staff.date_of_joining} />
            <Row label="Salary Type" value={staff.salary_type} />
            <Row label="Monthly Salary" value={staff.monthly_salary ? fmt(staff.monthly_salary / 100) : undefined} />
          </div>
          {(staff.bank_account_no || staff.bank_name) && (
            <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Bank Details</h3>
              <Row label="Account No." value={staff.bank_account_no} />
              <Row label="Bank" value={staff.bank_name} />
              <Row label="IFSC" value={staff.ifsc_code} />
            </div>
          )}
        </div>
      )}

      {/* Documents */}
      {activeTab === 'documents' && (
        <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Documents</h3>
            <label className={`cursor-pointer rounded-lg bg-indigo-600 px-3 py-1.5 text-xs text-white hover:bg-indigo-700 ${uploadingDoc ? 'opacity-60 pointer-events-none' : ''}`}>
              {uploadingDoc ? 'Uploading…' : '+ Upload Doc'}
              <input type="file" className="hidden" onChange={handleDocUpload} disabled={uploadingDoc} />
            </label>
          </div>
          {docs.length === 0 ? (
            <p className="text-sm text-gray-400">No documents uploaded.</p>
          ) : docs.map(doc => (
            <div key={doc.id} className="flex items-center justify-between rounded-lg border border-gray-100 px-4 py-2.5 dark:border-gray-700">
              <span className="text-sm font-medium capitalize">{doc.doc_type?.replace(/_/g, ' ')}</span>
              <div className="flex gap-3">
                <a href={doc.file_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline">View →</a>
                <button onClick={() => handleDeleteDoc(doc.id)} className="text-xs text-red-500 hover:underline">Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Payroll */}
      {activeTab === 'payroll' && (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>{['Period','Basic','Allowances','Deductions','Net','Status'].map(h => <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {payrollLoading ? <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
                : payrolls.length === 0 ? <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No payroll records found.</td></tr>
                  : payrolls.map(p => (
                    <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3">{MONTHS[(p.month ?? 1) - 1]} {p.year}</td>
                      <td className="px-4 py-3">{fmt(p.basic_salary ?? 0)}</td>
                      <td className="px-4 py-3 text-green-600">+{fmt(p.allowances ?? 0)}</td>
                      <td className="px-4 py-3 text-red-600">−{fmt(p.deductions ?? 0)}</td>
                      <td className="px-4 py-3 font-bold text-indigo-600">{fmt(p.net_salary ?? 0)}</td>
                      <td className="px-4 py-3"><span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${p.is_paid ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{p.is_paid ? 'Paid' : 'Pending'}</span></td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Leaves */}
      {activeTab === 'leaves' && (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>{['Leave Type','From','To','Days','Reason','Status','Remarks'].map(h => <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {leavesLoading ? <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
                : leaves.length === 0 ? <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No leave applications found.</td></tr>
                  : leaves.map(l => (
                    <tr key={l.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-4 py-3">{l.leave_type_name ?? '—'}</td>
                      <td className="px-4 py-3">{l.from_date}</td>
                      <td className="px-4 py-3">{l.to_date}</td>
                      <td className="px-4 py-3 text-center">{l.total_days}</td>
                      <td className="px-4 py-3 max-w-[180px] truncate text-gray-500">{l.reason}</td>
                      <td className="px-4 py-3"><span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${LEAVE_STATUS_CLS[l.status] ?? 'bg-gray-100 text-gray-600'}`}>{l.status}</span></td>
                      <td className="px-4 py-3 text-xs text-gray-400">{l.remarks ?? '—'}</td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      )}
    </div>

    {/* Edit Roles Modal */}
    {showRolesModal && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
          <h3 className="text-base font-semibold mb-4">Assign Roles</h3>
          {allRoles.length === 0 ? (
            <p className="text-sm text-gray-400">No roles available.</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {allRoles.map(role => (
                <label key={role.id} className="flex items-center gap-3 cursor-pointer select-none rounded-lg border border-gray-100 px-3 py-2 hover:bg-gray-50">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    checked={editRoleIds.includes(role.id)}
                    onChange={e => setEditRoleIds(prev =>
                      e.target.checked ? [...prev, role.id] : prev.filter(id => id !== role.id)
                    )}
                  />
                  <span className="text-sm text-gray-700">{role.name}</span>
                </label>
              ))}
            </div>
          )}
          <div className="mt-5 flex justify-end gap-2">
            <button onClick={() => setShowRolesModal(false)} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50">Cancel</button>
            <button onClick={saveRoles} disabled={savingRoles} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {savingRoles ? 'Saving…' : 'Save Roles'}
            </button>
          </div>
        </div>
      </div>
    )}
  </>
  );
};

export default StaffDetailPage;