import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Key, Search, Eye, EyeOff, User, Users, Shield, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';

const unwrap = (res: any) => res?.data ?? res;

type UserType = 'all' | 'student' | 'parent' | 'staff';

interface CredentialUser {
  id: string | null;
  user_type: 'student' | 'parent' | 'staff';
  display_name: string;
  email: string | null;
  phone: string | null;
  username: string | null;
  is_active: boolean;
  linked_id: string;
  linked_ref: string | null;
}

const USER_TYPE_COLORS: Record<string, string> = {
  student: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  parent:  'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  staff:   'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
};

const USER_TYPE_ICON: Record<string, React.ReactNode> = {
  student: <User size={13} />,
  parent:  <Users size={13} />,
  staff:   <Shield size={13} />,
};

// ─── Set Password Modal ───────────────────────────────────────────────────────
const PasswordModal: React.FC<{ user: CredentialUser; onClose: () => void }> = ({ user, onClose }) => {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [show, setShow] = useState(false);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      api.post('/credentials/set-password', { user_id: user.id, new_password: password }),
    onSuccess: () => {
      toast.success('Password updated successfully');
      queryClient.invalidateQueries({ queryKey: ['credentials-users'] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? 'Failed to update password');
    },
  });

  const submit = () => {
    if (!user.id) return toast.error('This user has no portal account yet');
    if (password.length < 6) return toast.error('Password must be at least 6 characters');
    if (password !== confirm) return toast.error('Passwords do not match');
    mutation.mutate();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <div className="mb-4 flex items-center gap-3">
          <Key size={20} className="text-blue-600" />
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">Set Password</h3>
            <p className="text-xs text-gray-500">{user.display_name}</p>
          </div>
        </div>
        {!user.id && (
          <div className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
            ⚠️ This person has no portal account yet — they cannot log in. Contact system support to create their account.
          </div>
        )}
        <div className="space-y-3">
          <div className="relative">
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">New Password</label>
            <input
              type={show ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 6 characters"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm dark:border-gray-600 dark:bg-gray-700"
            />
            <button onClick={() => setShow((p) => !p)} className="absolute right-3 top-7 text-gray-400 hover:text-gray-600">
              {show ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Confirm Password</label>
            <input
              type={show ? 'text' : 'password'}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
              placeholder="Re-enter password"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
            />
          </div>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700">
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={mutation.isPending || !user.id}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {mutation.isPending ? 'Updating…' : 'Set Password'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Set Username / Phone Modal ───────────────────────────────────────────────
const IdentityModal: React.FC<{ user: CredentialUser; onClose: () => void }> = ({ user, onClose }) => {
  const [username, setUsername] = useState(user.username ?? '');
  const [phone, setPhone] = useState(user.phone ?? '');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      api.post('/credentials/set-username', {
        user_id: user.id,
        username: username || null,
        phone: phone || null,
      }),
    onSuccess: () => {
      toast.success('Login identity updated');
      queryClient.invalidateQueries({ queryKey: ['credentials-users'] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? 'Failed to update identity');
    },
  });

  const HINT: Record<string, string> = {
    student: 'Set username to admission number so the student can log in using their admission number.',
    parent:  'Set phone number so the parent can log in using their mobile number.',
    staff:   'Set username to employee ID so the staff can log in using their employee ID.',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <div className="mb-4 flex items-center gap-3">
          <User size={20} className="text-purple-600" />
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">Edit Login Identity</h3>
            <p className="text-xs text-gray-500">{user.display_name}</p>
          </div>
        </div>
        <div className="mb-4 rounded-lg bg-blue-50 px-3 py-2 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-400">
          💡 {HINT[user.user_type]}
        </div>
        {!user.id && (
          <div className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
            ⚠️ No portal account found — changes cannot be saved.
          </div>
        )}
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
              Username / Alias
              {user.user_type === 'student' && <span className="ml-1 text-gray-400">(admission number or custom)</span>}
              {user.user_type === 'staff' && <span className="ml-1 text-gray-400">(employee ID or custom)</span>}
            </label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={user.linked_ref ?? 'Enter username'}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
            />
            {user.user_type === 'student' && user.linked_ref && (
              <button
                onClick={() => setUsername(user.linked_ref!)}
                className="mt-1 text-xs text-blue-600 hover:underline"
              >
                Use admission number ({user.linked_ref})
              </button>
            )}
            {user.user_type === 'staff' && user.linked_ref && (
              <button
                onClick={() => setUsername(user.linked_ref!)}
                className="mt-1 text-xs text-blue-600 hover:underline"
              >
                Use employee ID ({user.linked_ref})
              </button>
            )}
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
              Phone Number {user.user_type === 'parent' && <span className="text-purple-600">(primary login for parents)</span>}
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 98765 43210"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
            />
          </div>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700">
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !user.id}
            className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-700 disabled:opacity-60"
          >
            {mutation.isPending ? 'Saving…' : 'Save Identity'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────
const CredentialsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [userType, setUserType] = useState<UserType>('all');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [passwordModal, setPasswordModal] = useState<CredentialUser | null>(null);
  const [identityModal, setIdentityModal] = useState<CredentialUser | null>(null);

  // Simple debounce
  const handleSearch = useCallback((val: string) => {
    setSearch(val);
    clearTimeout((window as any)._cred_search_timer);
    (window as any)._cred_search_timer = setTimeout(() => setDebouncedSearch(val), 350);
  }, []);

  const { data, isLoading } = useQuery({
    queryKey: ['credentials-users', userType, debouncedSearch],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (userType !== 'all') params.set('user_type', userType);
      if (debouncedSearch) params.set('search', debouncedSearch);
      params.set('limit', '100');
      const res = unwrap(await api.get(`/credentials/users?${params.toString()}`));
      return (res?.items ?? res ?? []) as CredentialUser[];
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
      api.post(`/credentials/toggle-active?user_id=${userId}&is_active=${isActive}`),
    onSuccess: () => {
      toast.success('Account status updated');
      queryClient.invalidateQueries({ queryKey: ['credentials-users'] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail ?? 'Failed to update'),
  });

  const users = data ?? [];

  return (
    <div>
      <PageHeader
        title="Credential Management"
        subtitle="Manage login passwords and alternate usernames for students, parents, and staff"
      />

      {/* Info Banner */}
      <div className="mb-5 rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800 dark:border-blue-900/40 dark:bg-blue-900/20 dark:text-blue-300">
        <p className="font-medium mb-1">Login Identity Rules</p>
        <ul className="ml-4 list-disc space-y-0.5 text-xs">
          <li><strong>Students</strong> can log in with their email <em>or</em> Admission Number (set username below)</li>
          <li><strong>Parents</strong> can log in with their email <em>or</em> Phone Number (set phone below)</li>
          <li><strong>Staff</strong> can log in with their email <em>or</em> Employee ID (set username below)</li>
        </ul>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search by name, email, admission no…"
            className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
          />
        </div>
        {(['all', 'student', 'parent', 'staff'] as UserType[]).map((t) => (
          <button
            key={t}
            onClick={() => setUserType(t)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium capitalize ${
              userType === t
                ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                : 'border border-gray-300 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900/50">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Type</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Name</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Reference</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Email / Phone</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Username / Alias</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                  <RefreshCw size={20} className="mx-auto mb-2 animate-spin" />
                  Loading…
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-gray-400">No users found</td>
              </tr>
            ) : (
              users.map((u, idx) => (
                <tr key={u.linked_id ?? idx} className="border-b border-gray-100 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800/50">
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${USER_TYPE_COLORS[u.user_type]}`}>
                      {USER_TYPE_ICON[u.user_type]}
                      {u.user_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{u.display_name}</td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono">{u.linked_ref ?? '—'}</td>
                  <td className="px-4 py-3 text-xs text-gray-600 dark:text-gray-400">
                    <div>{u.email ?? <span className="text-gray-400">—</span>}</div>
                    {u.phone && <div className="text-purple-600 dark:text-purple-400">{u.phone}</div>}
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-gray-600 dark:text-gray-400">{u.username ?? <span className="text-gray-400 font-sans">not set</span>}</td>
                  <td className="px-4 py-3">
                    {u.id ? (
                      u.is_active ? (
                        <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                          <CheckCircle size={12} /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-red-500">
                          <XCircle size={12} /> Disabled
                        </span>
                      )
                    ) : (
                      <span className="text-xs text-gray-400">No account</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setPasswordModal(u)}
                        title="Set Password"
                        className="rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                      >
                        <Key size={12} className="inline mr-1" />
                        Password
                      </button>
                      <button
                        onClick={() => setIdentityModal(u)}
                        title="Edit Login Identity"
                        className="rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                      >
                        <User size={12} className="inline mr-1" />
                        Identity
                      </button>
                      {u.id && (
                        <button
                          onClick={() => toggleActiveMutation.mutate({ userId: u.id!, isActive: !u.is_active })}
                          title={u.is_active ? 'Disable account' : 'Enable account'}
                          className={`rounded-lg border px-2.5 py-1.5 text-xs ${
                            u.is_active
                              ? 'border-red-200 text-red-600 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20'
                              : 'border-green-200 text-green-600 hover:bg-green-50 dark:border-green-800 dark:hover:bg-green-900/20'
                          }`}
                        >
                          {u.is_active ? 'Disable' : 'Enable'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        {users.length > 0 && (
          <div className="px-4 py-2.5 text-xs text-gray-400 border-t border-gray-100 dark:border-gray-700">
            Showing {users.length} user{users.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Modals */}
      {passwordModal && <PasswordModal user={passwordModal} onClose={() => setPasswordModal(null)} />}
      {identityModal && <IdentityModal user={identityModal} onClose={() => setIdentityModal(null)} />}
    </div>
  );
};

export default CredentialsPage;
