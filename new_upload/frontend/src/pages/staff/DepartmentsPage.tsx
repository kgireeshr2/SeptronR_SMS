import React, { useEffect, useState, useRef } from 'react';
import { staffApi, Department, Designation } from '../../api/staff';

const unwrap = (res: any) => res?.data ?? res;

// ── tiny modal ────────────────────────────────────────────────────────────────
interface ModalProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}
const Modal: React.FC<ModalProps> = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
    <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
      <div className="flex items-center justify-between px-6 py-4 border-b">
        <h3 className="text-base font-semibold text-gray-800">{title}</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
      </div>
      <div className="px-6 py-4">{children}</div>
    </div>
  </div>
);

// ── badge ─────────────────────────────────────────────────────────────────────
const Badge: React.FC<{ active: boolean }> = ({ active }) => (
  <span className={`px-2 py-0.5 rounded text-xs font-medium ${active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
    {active ? 'Active' : 'Inactive'}
  </span>
);

// ── confirm helper ────────────────────────────────────────────────────────────
const useConfirm = () => {
  const [state, setState] = useState<{ msg: string; resolve: (v: boolean) => void } | null>(null);
  const confirm = (msg: string) => new Promise<boolean>((res) => setState({ msg, resolve: res }));
  const dialog = state ? (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4">
        <p className="text-sm text-gray-700 mb-5">{state.msg}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={() => { state.resolve(false); setState(null); }} className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">Cancel</button>
          <button onClick={() => { state.resolve(true); setState(null); }} className="px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700">Delete</button>
        </div>
      </div>
    </div>
  ) : null;
  return { confirm, dialog };
};

// ═══════════════════════════════════════════════════════════════════════════════
// DEPARTMENTS TAB
// ═══════════════════════════════════════════════════════════════════════════════
const DepartmentsTab: React.FC = () => {
  const [list, setList] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  // add modal
  const [showAdd, setShowAdd] = useState(false);
  const [addName, setAddName] = useState('');
  const [addError, setAddError] = useState('');
  const [addLoading, setAddLoading] = useState(false);

  // edit modal
  const [editing, setEditing] = useState<Department | null>(null);
  const [editName, setEditName] = useState('');
  const [editActive, setEditActive] = useState(true);
  const [editError, setEditError] = useState('');
  const [editLoading, setEditLoading] = useState(false);

  const { confirm, dialog } = useConfirm();
  const addInputRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await staffApi.listDepartments();
      setList(unwrap(res) ?? []);
      setPageError(null);
    } catch (e: any) {
      setPageError(e?.detail || 'Failed to load departments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => { if (showAdd) setTimeout(() => addInputRef.current?.focus(), 50); }, [showAdd]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addName.trim()) { setAddError('Name is required'); return; }
    setAddLoading(true);
    try {
      await staffApi.createDepartment({ name: addName.trim() });
      setShowAdd(false);
      setAddName('');
      setAddError('');
      await load();
    } catch (e: any) {
      setAddError(e?.detail || 'Failed to create department');
    } finally {
      setAddLoading(false);
    }
  };

  const openEdit = (dept: Department) => {
    setEditing(dept);
    setEditName(dept.name);
    setEditActive(dept.is_active);
    setEditError('');
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    if (!editName.trim()) { setEditError('Name is required'); return; }
    setEditLoading(true);
    try {
      await staffApi.updateDepartment(editing.id, { name: editName.trim(), is_active: editActive });
      setEditing(null);
      await load();
    } catch (e: any) {
      setEditError(e?.detail || 'Failed to update department');
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async (dept: Department) => {
    const ok = await confirm(`Delete department "${dept.name}"? Staff assigned here will lose their department.`);
    if (!ok) return;
    try {
      await staffApi.deleteDepartment(dept.id);
      await load();
    } catch (e: any) {
      alert(e?.detail || 'Failed to delete department');
    }
  };

  return (
    <>
      {dialog}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">{list.length} department{list.length !== 1 ? 's' : ''}</p>
        <button
          onClick={() => { setShowAdd(true); setAddName(''); setAddError(''); }}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          + Add Department
        </button>
      </div>

      {pageError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 mb-4 text-sm">{pageError}</div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : list.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No departments yet. Add one to get started.</div>
      ) : (
        <div className="bg-white rounded shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Staff Count</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-800">{d.name}</td>
                  <td className="px-6 py-4 text-gray-600">{d.staff_count ?? 0}</td>
                  <td className="px-6 py-4"><Badge active={d.is_active} /></td>
                  <td className="px-6 py-4 text-sm flex gap-3">
                    <button onClick={() => openEdit(d)} className="text-blue-600 hover:underline">Edit</button>
                    <button onClick={() => handleDelete(d)} className="text-red-600 hover:underline">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Modal */}
      {showAdd && (
        <Modal title="Add Department" onClose={() => setShowAdd(false)}>
          <form onSubmit={handleAdd} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Department Name <span className="text-red-500">*</span>
              </label>
              <input
                ref={addInputRef}
                type="text"
                value={addName}
                onChange={(e) => { setAddName(e.target.value); setAddError(''); }}
                className={`w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${addError ? 'border-red-400' : 'border-gray-300'}`}
                placeholder="e.g. Mathematics"
              />
              {addError && <p className="mt-1 text-xs text-red-600">{addError}</p>}
            </div>
            <div className="flex gap-3 justify-end pt-2">
              <button type="button" onClick={() => setShowAdd(false)} className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={addLoading} className="px-5 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
                {addLoading ? 'Saving…' : 'Create'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Edit Modal */}
      {editing && (
        <Modal title="Edit Department" onClose={() => setEditing(null)}>
          <form onSubmit={handleEdit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Department Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={editName}
                onChange={(e) => { setEditName(e.target.value); setEditError(''); }}
                className={`w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${editError ? 'border-red-400' : 'border-gray-300'}`}
              />
              {editError && <p className="mt-1 text-xs text-red-600">{editError}</p>}
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input type="checkbox" checked={editActive} onChange={(e) => setEditActive(e.target.checked)} className="rounded" />
              Active
            </label>
            <div className="flex gap-3 justify-end pt-2">
              <button type="button" onClick={() => setEditing(null)} className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={editLoading} className="px-5 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
                {editLoading ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// DESIGNATIONS TAB
// ═══════════════════════════════════════════════════════════════════════════════
const DesignationsTab: React.FC = () => {
  const [list, setList] = useState<Designation[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  const [showAdd, setShowAdd] = useState(false);
  const [addName, setAddName] = useState('');
  const [addError, setAddError] = useState('');
  const [addLoading, setAddLoading] = useState(false);

  const [editing, setEditing] = useState<Designation | null>(null);
  const [editName, setEditName] = useState('');
  const [editActive, setEditActive] = useState(true);
  const [editError, setEditError] = useState('');
  const [editLoading, setEditLoading] = useState(false);

  const { confirm, dialog } = useConfirm();
  const addInputRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await staffApi.listDesignations();
      setList(unwrap(res) ?? []);
      setPageError(null);
    } catch (e: any) {
      setPageError(e?.detail || 'Failed to load designations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => { if (showAdd) setTimeout(() => addInputRef.current?.focus(), 50); }, [showAdd]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addName.trim()) { setAddError('Name is required'); return; }
    setAddLoading(true);
    try {
      await staffApi.createDesignation({ name: addName.trim() });
      setShowAdd(false);
      setAddName('');
      setAddError('');
      await load();
    } catch (e: any) {
      setAddError(e?.detail || 'Failed to create designation');
    } finally {
      setAddLoading(false);
    }
  };

  const openEdit = (desig: Designation) => {
    setEditing(desig);
    setEditName(desig.name);
    setEditActive(desig.is_active);
    setEditError('');
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    if (!editName.trim()) { setEditError('Name is required'); return; }
    setEditLoading(true);
    try {
      await staffApi.updateDesignation(editing.id, { name: editName.trim(), is_active: editActive });
      setEditing(null);
      await load();
    } catch (e: any) {
      setEditError(e?.detail || 'Failed to update designation');
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async (desig: Designation) => {
    const ok = await confirm(`Delete designation "${desig.name}"? Staff with this designation will be affected.`);
    if (!ok) return;
    try {
      await staffApi.deleteDesignation(desig.id);
      await load();
    } catch (e: any) {
      alert(e?.detail || 'Failed to delete designation');
    }
  };

  return (
    <>
      {dialog}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">{list.length} designation{list.length !== 1 ? 's' : ''}</p>
        <button
          onClick={() => { setShowAdd(true); setAddName(''); setAddError(''); }}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          + Add Designation
        </button>
      </div>

      {pageError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 mb-4 text-sm">{pageError}</div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : list.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No designations yet. Add one to get started.</div>
      ) : (
        <div className="bg-white rounded shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Staff Count</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-800">{d.name}</td>
                  <td className="px-6 py-4 text-gray-600">{d.staff_count ?? 0}</td>
                  <td className="px-6 py-4"><Badge active={d.is_active} /></td>
                  <td className="px-6 py-4 text-sm flex gap-3">
                    <button onClick={() => openEdit(d)} className="text-blue-600 hover:underline">Edit</button>
                    <button onClick={() => handleDelete(d)} className="text-red-600 hover:underline">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAdd && (
        <Modal title="Add Designation" onClose={() => setShowAdd(false)}>
          <form onSubmit={handleAdd} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Designation Name <span className="text-red-500">*</span>
              </label>
              <input
                ref={addInputRef}
                type="text"
                value={addName}
                onChange={(e) => { setAddName(e.target.value); setAddError(''); }}
                className={`w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${addError ? 'border-red-400' : 'border-gray-300'}`}
                placeholder="e.g. Teacher, Principal"
              />
              {addError && <p className="mt-1 text-xs text-red-600">{addError}</p>}
            </div>
            <div className="flex gap-3 justify-end pt-2">
              <button type="button" onClick={() => setShowAdd(false)} className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={addLoading} className="px-5 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
                {addLoading ? 'Saving…' : 'Create'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {editing && (
        <Modal title="Edit Designation" onClose={() => setEditing(null)}>
          <form onSubmit={handleEdit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Designation Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={editName}
                onChange={(e) => { setEditName(e.target.value); setEditError(''); }}
                className={`w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${editError ? 'border-red-400' : 'border-gray-300'}`}
              />
              {editError && <p className="mt-1 text-xs text-red-600">{editError}</p>}
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input type="checkbox" checked={editActive} onChange={(e) => setEditActive(e.target.checked)} className="rounded" />
              Active
            </label>
            <div className="flex gap-3 justify-end pt-2">
              <button type="button" onClick={() => setEditing(null)} className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={editLoading} className="px-5 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
                {editLoading ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════
type Tab = 'departments' | 'designations';

const DepartmentsPage: React.FC = () => {
  const [tab, setTab] = useState<Tab>('departments');

  const tabClass = (t: Tab) =>
    `px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
      tab === t
        ? 'border-blue-600 text-blue-600'
        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
    }`;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Departments & Designations</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6 flex">
        <button className={tabClass('departments')} onClick={() => setTab('departments')}>
          Departments
        </button>
        <button className={tabClass('designations')} onClick={() => setTab('designations')}>
          Designations
        </button>
      </div>

      {tab === 'departments' ? <DepartmentsTab /> : <DesignationsTab />}
    </div>
  );
};

export default DepartmentsPage;
