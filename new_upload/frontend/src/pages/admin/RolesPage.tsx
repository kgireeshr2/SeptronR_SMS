import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Plus, Pencil, Trash2, Copy, Shield, CheckSquare, Square,
  Loader2, X, Check,
} from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { PermissionGuard } from '@components/shared/PermissionGuard';
import { rolesApi, RoleResponse, RoleCreate, RoleUpdate, PermissionResponse } from '@api/roles';

// ─── Unique module list derived from permissions ───────────────────────────
const MODULE_LABELS: Record<string, string> = {
  users: 'Users', roles: 'Roles', academic_years: 'Academic Years',
  admissions: 'Admissions', classes: 'Classes', sections: 'Sections',
  subjects: 'Subjects', timetable: 'Timetable', students: 'Students',
  staff: 'Staff', attendance: 'Attendance', fees: 'Fees', exams: 'Exams',
  library: 'Library', transport: 'Transport', inventory: 'Inventory',
  accounting: 'Accounting', communication: 'Communication', calendar: 'Calendar',
  homework: 'Homework', ptm: 'PTM', reports: 'Reports',
  audit_logs: 'Audit Logs', settings: 'Settings', dashboard: 'Dashboard',
};

const ACTION_LABELS: Record<string, string> = {
  view: 'View', create: 'Create', update: 'Update', delete: 'Delete',
  approve: 'Approve', export: 'Export', manage: 'Manage',
};

type ModalMode = 'create' | 'edit' | 'permissions' | null;

// ─── Permission Matrix ─────────────────────────────────────────────────────
interface PermissionMatrixProps {
  role: RoleResponse;
  allPermissions: PermissionResponse[];
  onClose: () => void;
}

const PermissionMatrix: React.FC<PermissionMatrixProps> = ({ role, allPermissions, onClose }) => {
  const queryClient = useQueryClient();
  const modules = [...new Set(allPermissions.map((p) => p.module))].sort();
  const actions = [...new Set(allPermissions.map((p) => p.action))].sort();

  // Normalize permissions: backend may return array of strings or a single space-joined string
  const normalizePerms = (p: string | string[]): string[] => {
    if (Array.isArray(p)) {
      // Each element might itself be space-joined if backend joins them
      return p.flatMap((s) => (typeof s === 'string' ? s.split(' ').filter(Boolean) : []));
    }
    return typeof p === 'string' ? p.split(' ').filter(Boolean) : [];
  };

  const [selected, setSelected] = useState<Set<string>>(new Set(normalizePerms(role.permissions as any)));

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleRow = (module: string) => {
    const rowPerms = allPermissions.filter((p) => p.module === module);
    const allChecked = rowPerms.every((p) => selected.has(`${p.module}:${p.action}`));
    setSelected((prev) => {
      const next = new Set(prev);
      rowPerms.forEach((p) => {
        const key = `${p.module}:${p.action}`;
        allChecked ? next.delete(key) : next.add(key);
      });
      return next;
    });
  };

  const toggleCol = (action: string) => {
    const colPerms = allPermissions.filter((p) => p.action === action);
    const allChecked = colPerms.every((p) => selected.has(`${p.module}:${p.action}`));
    setSelected((prev) => {
      const next = new Set(prev);
      colPerms.forEach((p) => {
        const key = `${p.module}:${p.action}`;
        allChecked ? next.delete(key) : next.add(key);
      });
      return next;
    });
  };

  const saveMutation = useMutation({
    mutationFn: () => {
      const permIds = allPermissions
        .filter((p) => selected.has(`${p.module}:${p.action}`))
        .map((p) => p.id);
      return rolesApi.assignPermissions(role.id, permIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      toast.success('Permissions saved!');
      onClose();
    },
    onError: () => toast.error('Failed to save permissions'),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="flex max-h-[90vh] w-full max-w-5xl flex-col rounded-2xl bg-white shadow-2xl dark:bg-gray-900">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Permissions — {role.name}
            </h2>
            <p className="text-sm text-gray-500">{selected.size} permissions selected</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-800">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-4">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="sticky left-0 bg-white py-2 pr-4 text-left font-medium text-gray-600 dark:bg-gray-900 dark:text-gray-400">
                  Module
                </th>
                {actions.map((action) => (
                  <th
                    key={action}
                    className="cursor-pointer px-3 py-2 text-center font-medium text-gray-600 hover:text-brand-600 dark:text-gray-400"
                    onClick={() => toggleCol(action)}
                    title={`Toggle all ${action}`}
                  >
                    {ACTION_LABELS[action] ?? action}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {modules.map((module) => {
                const rowPerms = allPermissions.filter((p) => p.module === module);
                const rowAllChecked = rowPerms.every((p) => selected.has(`${p.module}:${p.action}`));
                const rowSomeChecked = rowPerms.some((p) => selected.has(`${p.module}:${p.action}`));
                return (
                  <tr key={module} className="border-t border-gray-100 dark:border-gray-800">
                    <td
                      className="sticky left-0 cursor-pointer bg-white py-2 pr-4 font-medium text-gray-700 hover:text-brand-600 dark:bg-gray-900 dark:text-gray-300"
                      onClick={() => toggleRow(module)}
                    >
                      <div className="flex items-center gap-2">
                        {rowAllChecked ? (
                          <CheckSquare size={15} className="text-brand-600" />
                        ) : rowSomeChecked ? (
                          <div className="h-3.5 w-3.5 rounded border-2 border-brand-400 bg-brand-200" />
                        ) : (
                          <Square size={15} className="text-gray-400" />
                        )}
                        {MODULE_LABELS[module] ?? module}
                      </div>
                    </td>
                    {actions.map((action) => {
                      const perm = allPermissions.find(
                        (p) => p.module === module && p.action === action
                      );
                      const key = `${module}:${action}`;
                      if (!perm) {
                        return <td key={action} className="px-3 py-2 text-center text-gray-200 dark:text-gray-700">—</td>;
                      }
                      return (
                        <td key={action} className="px-3 py-2 text-center">
                          <button
                            type="button"
                            onClick={() => toggle(key)}
                            className={`inline-flex h-5 w-5 items-center justify-center rounded transition-colors ${
                              selected.has(key)
                                ? 'bg-brand-600 text-white'
                                : 'border border-gray-300 text-transparent hover:border-brand-400'
                            }`}
                          >
                            <Check size={12} />
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 dark:border-gray-700">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {saveMutation.isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Check size={14} />
            )}
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Role Form Modal ───────────────────────────────────────────────────────
interface RoleFormProps {
  role?: RoleResponse;
  onClose: () => void;
  onSubmit: (data: RoleCreate | RoleUpdate) => Promise<void>;
  loading: boolean;
}

const RoleFormModal: React.FC<RoleFormProps> = ({ role, onClose, onSubmit, loading }) => {
  const [name, setName] = useState(role?.name ?? '');
  const [slug, setSlug] = useState(role?.slug ?? '');
  const [description, setDescription] = useState(role?.description ?? '');

  const autoSlug = (v: string) =>
    v.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-900">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          {role ? 'Edit Role' : 'Create Role'}
        </h2>
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Name
            </label>
            <input
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (!role) setSlug(autoSlug(e.target.value));
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              placeholder="e.g. Head Teacher"
            />
          </div>
          {!role && (
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Slug
              </label>
              <input
                value={slug}
                onChange={(e) => setSlug(autoSlug(e.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:border-brand-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                placeholder="head_teacher"
              />
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              placeholder="Optional description"
            />
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm dark:border-gray-600 dark:text-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={() => onSubmit(role ? { name, description } : { name, slug, description })}
            disabled={!name || (!role && !slug) || loading}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {loading && <Loader2 size={14} className="animate-spin" />}
            {role ? 'Save' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Main Page ─────────────────────────────────────────────────────────────
const RolesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [modal, setModal] = useState<ModalMode>(null);
  const [selectedRole, setSelectedRole] = useState<RoleResponse | null>(null);

  const unwrapArr = (r: any): any[] => {
    if (Array.isArray(r)) return r;
    if (Array.isArray(r?.data)) return r.data;
    return [];
  };

  const { data: rolesRaw, isLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => rolesApi.list(),
  });
  const roles: RoleResponse[] = unwrapArr(rolesRaw);

  const { data: permsRaw } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => rolesApi.allPermissions(),
  });
  const allPermissions: PermissionResponse[] = unwrapArr(permsRaw);

  const createMutation = useMutation({
    mutationFn: (data: RoleCreate) => rolesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      toast.success('Role created!');
      setModal(null);
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail ?? 'Failed to create role'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: RoleUpdate }) =>
      rolesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      toast.success('Role updated!');
      setModal(null);
    },
    onError: () => toast.error('Failed to update role'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => rolesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      toast.success('Role deleted');
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail ?? 'Cannot delete this role'),
  });

  const cloneMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      rolesApi.clone(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      toast.success('Role cloned!');
    },
    onError: () => toast.error('Failed to clone role'),
  });

  const handleDelete = (role: RoleResponse) => {
    if (role.is_system) {
      toast.error('System roles cannot be deleted');
      return;
    }
    if (confirm(`Delete role "${role.name}"? This cannot be undone.`)) {
      deleteMutation.mutate(role.id);
    }
  };

  const handleClone = (role: RoleResponse) => {
    const name = prompt(`New name for cloned role (based on "${role.name}"):`);
    if (name) cloneMutation.mutate({ id: role.id, name });
  };

  return (
    <div>
      <PageHeader
        title="Roles & Permissions"
        subtitle="Manage roles and their permission sets for your school"
        actions={
          <PermissionGuard module="roles" action="create">
            <button
              onClick={() => { setSelectedRole(null); setModal('create'); }}
              className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
            >
              <Plus size={16} /> Create Role
            </button>
          </PermissionGuard>
        }
      />

      <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">Name</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">Slug</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">Type</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">Status</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-400">Permissions</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-gray-400">
                  <Loader2 className="mx-auto animate-spin" size={24} />
                </td>
              </tr>
            ) : roles.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-gray-400">
                  No roles found. Create your first role.
                </td>
              </tr>
            ) : (
              roles.map((role) => (
                <tr key={role.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Shield size={16} className="text-brand-500" />
                      <span className="font-medium text-gray-900 dark:text-white">{role.name}</span>
                    </div>
                    {role.description && (
                      <p className="ml-6 text-xs text-gray-400">{role.description}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{role.slug}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        role.is_system
                          ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {role.is_system ? 'System' : 'Custom'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        role.is_active
                          ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      }`}
                    >
                      {role.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => { setSelectedRole(role); setModal('permissions'); }}
                      className="text-xs text-brand-600 hover:underline"
                    >
                      {Array.isArray(role.permissions) ? role.permissions.length : role.permissions?.toString().split(' ').filter(Boolean).length ?? 0} permissions
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <PermissionGuard module="roles" action="update">
                        <button
                          onClick={() => { setSelectedRole(role); setModal('edit'); }}
                          className="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700"
                          title="Edit"
                        >
                          <Pencil size={14} />
                        </button>
                      </PermissionGuard>
                      <PermissionGuard module="roles" action="create">
                        <button
                          onClick={() => handleClone(role)}
                          className="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700"
                          title="Clone"
                        >
                          <Copy size={14} />
                        </button>
                      </PermissionGuard>
                      <PermissionGuard module="roles" action="delete">
                        <button
                          onClick={() => handleDelete(role)}
                          disabled={role.is_system}
                          className="rounded p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-30 dark:hover:bg-red-900/30"
                          title={role.is_system ? 'System role — cannot delete' : 'Delete'}
                        >
                          <Trash2 size={14} />
                        </button>
                      </PermissionGuard>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {(modal === 'create' || modal === 'edit') && (
        <RoleFormModal
          role={modal === 'edit' ? selectedRole ?? undefined : undefined}
          onClose={() => setModal(null)}
          loading={createMutation.isPending || updateMutation.isPending}
          onSubmit={async (data) => {
            if (modal === 'create') {
              await createMutation.mutateAsync(data as RoleCreate);
            } else if (selectedRole) {
              await updateMutation.mutateAsync({ id: selectedRole.id, data: data as RoleUpdate });
            }
          }}
        />
      )}

      {modal === 'permissions' && selectedRole && (
        <PermissionMatrix
          role={selectedRole}
          allPermissions={allPermissions as PermissionResponse[]}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
};

export default RolesPage;
