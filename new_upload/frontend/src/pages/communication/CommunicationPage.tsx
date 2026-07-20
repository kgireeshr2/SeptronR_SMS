import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Send, Megaphone, ListChecks, Smartphone } from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { communicationsApi } from '@api/communications';
import { formatDateTime } from '@utils/formatters';

const unwrap = (res: any) => res?.data ?? res;

const CHANNELS = ['in_app', 'sms', 'whatsapp', 'email', 'push'];
const AUDIENCES = ['all', 'parents', 'students', 'staff'];

type Tab = 'compose' | 'announcements' | 'reports';

const CommunicationPage: React.FC = () => {
  const qc = useQueryClient();
  const [tab, setTab] = React.useState<Tab>('compose');

  // ── Compose / Bulk ──────────────────────────────────────────────────────
  const [bulk, setBulk] = React.useState({
    title: '', body: '', audience: 'parents',
    channels: ['in_app', 'sms'] as string[], scheduled_at: '',
  });
  const toggleChannel = (c: string) =>
    setBulk((p) => ({ ...p, channels: p.channels.includes(c) ? p.channels.filter((x) => x !== c) : [...p.channels, c] }));

  const sendBulk = useMutation({
    mutationFn: () => communicationsApi.createBulkMessage({
      title: bulk.title,
      body: bulk.body,
      channel: bulk.channels.join(','),
      audience: bulk.audience,
      scheduled_at: bulk.scheduled_at || null,
    }),
    onSuccess: () => {
      toast.success(bulk.scheduled_at ? 'Message scheduled' : 'Message queued for sending');
      setBulk({ title: '', body: '', audience: 'parents', channels: ['in_app', 'sms'], scheduled_at: '' });
      qc.invalidateQueries({ queryKey: ['bulk-messages'] });
    },
    onError: () => toast.error('Failed to send message'),
  });

  // ── Announcements ───────────────────────────────────────────────────────
  const [ann, setAnn] = React.useState({ title: '', body: '', audience: 'all' });
  const { data: announcements } = useQuery({
    queryKey: ['announcements-admin'],
    queryFn: async () => unwrap(await communicationsApi.listAnnouncements({ active_only: false })) || [],
  });
  const createAnn = useMutation({
    mutationFn: () => communicationsApi.createAnnouncement({ title: ann.title, body: ann.body, audience: ann.audience }),
    onSuccess: () => {
      toast.success('Announcement published');
      setAnn({ title: '', body: '', audience: 'all' });
      qc.invalidateQueries({ queryKey: ['announcements-admin'] });
    },
    onError: () => toast.error('Failed to publish'),
  });
  const deleteAnn = useMutation({
    mutationFn: (id: string) => communicationsApi.deleteAnnouncement(id),
    onSuccess: () => { toast.success('Removed'); qc.invalidateQueries({ queryKey: ['announcements-admin'] }); },
  });

  // ── Reports ─────────────────────────────────────────────────────────────
  const { data: bulkMsgs } = useQuery({
    queryKey: ['bulk-messages'],
    queryFn: async () => unwrap(await communicationsApi.listBulkMessages()) || [],
    enabled: tab === 'reports',
  });
  const { data: logs } = useQuery({
    queryKey: ['message-logs'],
    queryFn: async () => unwrap(await communicationsApi.listMessageLogs({ limit: 100 })) || [],
    enabled: tab === 'reports',
  });

  const tabBtn = (t: Tab, label: string, Icon: any) => (
    <button
      onClick={() => setTab(t)}
      className={`flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium ${
        tab === t ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'
      }`}
    >
      <Icon size={15} /> {label}
    </button>
  );

  const input = 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800';
  const statusColor: Record<string, string> = {
    sent: 'text-green-600', delivered: 'text-green-600', queued: 'text-yellow-600',
    failed: 'text-red-600', sending: 'text-blue-600',
  };

  return (
    <div>
      <PageHeader title="Communications" subtitle="Send announcements & messages across SMS, WhatsApp, Email & Push" />

      <div className="mb-4 flex items-center gap-1 border-b border-gray-200 dark:border-gray-700">
        {tabBtn('compose', 'Compose', Send)}
        {tabBtn('announcements', 'Announcements', Megaphone)}
        {tabBtn('reports', 'Delivery Reports', ListChecks)}
        <Link to="/admin/whatsapp-test" className="ml-auto flex items-center gap-2 px-4 py-2 text-sm text-gray-500 hover:text-brand-600">
          <Smartphone size={15} /> WA Simulator
        </Link>
      </div>

      {tab === 'compose' && (
        <div className="max-w-2xl space-y-4 rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">Title</label>
            <input className={input} value={bulk.title} onChange={(e) => setBulk((p) => ({ ...p, title: e.target.value }))} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">Message</label>
            <textarea className={input} rows={4} value={bulk.body} onChange={(e) => setBulk((p) => ({ ...p, body: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Audience</label>
              <select className={input} value={bulk.audience} onChange={(e) => setBulk((p) => ({ ...p, audience: e.target.value }))}>
                {AUDIENCES.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Schedule (optional)</label>
              <input type="datetime-local" className={input} value={bulk.scheduled_at} onChange={(e) => setBulk((p) => ({ ...p, scheduled_at: e.target.value }))} />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">Channels</label>
            <div className="flex flex-wrap gap-3">
              {CHANNELS.map((c) => (
                <label key={c} className="flex items-center gap-1.5 text-sm">
                  <input type="checkbox" checked={bulk.channels.includes(c)} onChange={() => toggleChannel(c)} />
                  {c}
                </label>
              ))}
            </div>
          </div>
          <button
            disabled={!bulk.title || !bulk.body || !bulk.channels.length || sendBulk.isPending}
            onClick={() => sendBulk.mutate()}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {bulk.scheduled_at ? 'Schedule Message' : 'Send Now'}
          </button>
        </div>
      )}

      {tab === 'announcements' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="font-semibold text-gray-900 dark:text-white">New Announcement</h3>
            <input className={input} placeholder="Title" value={ann.title} onChange={(e) => setAnn((p) => ({ ...p, title: e.target.value }))} />
            <textarea className={input} rows={4} placeholder="Content" value={ann.body} onChange={(e) => setAnn((p) => ({ ...p, body: e.target.value }))} />
            <select className={input} value={ann.audience} onChange={(e) => setAnn((p) => ({ ...p, audience: e.target.value }))}>
              {['all', 'parents', 'students', 'staff'].map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
            <button
              disabled={!ann.title || createAnn.isPending}
              onClick={() => createAnn.mutate()}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
            >
              Publish
            </button>
          </div>
          <div className="space-y-2">
            {(announcements || []).map((a: any) => (
              <div key={a.id} className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{a.title}</p>
                    <p className="text-sm text-gray-500">{a.body}</p>
                    <p className="mt-1 text-[10px] text-gray-400">{a.audience} · {formatDateTime(a.created_at)}</p>
                  </div>
                  <button onClick={() => deleteAnn.mutate(a.id)} className="text-xs text-red-500 hover:underline">Remove</button>
                </div>
              </div>
            ))}
            {(announcements || []).length === 0 && <p className="text-sm text-gray-500">No announcements yet.</p>}
          </div>
        </div>
      )}

      {tab === 'reports' && (
        <div className="space-y-6">
          <div>
            <h3 className="mb-2 font-semibold text-gray-900 dark:text-white">Bulk Messages</h3>
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-900/40">
                  <tr className="text-left text-xs text-gray-500">
                    <th className="px-3 py-2">Title</th><th className="px-3 py-2">Audience</th>
                    <th className="px-3 py-2">Status</th><th className="px-3 py-2">Sent</th><th className="px-3 py-2">When</th>
                  </tr>
                </thead>
                <tbody>
                  {(bulkMsgs || []).map((m: any) => (
                    <tr key={m.id} className="border-t border-gray-100 dark:border-gray-700">
                      <td className="px-3 py-2">{m.title}</td>
                      <td className="px-3 py-2">{m.target_type || m.audience}</td>
                      <td className={`px-3 py-2 font-medium ${statusColor[m.status] || ''}`}>{m.status}</td>
                      <td className="px-3 py-2">{m.sent_count}/{m.total_recipients}</td>
                      <td className="px-3 py-2 text-xs text-gray-400">{formatDateTime(m.created_at)}</td>
                    </tr>
                  ))}
                  {(bulkMsgs || []).length === 0 && <tr><td colSpan={5} className="px-3 py-4 text-center text-gray-500">No bulk messages.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
          <div>
            <h3 className="mb-2 font-semibold text-gray-900 dark:text-white">Recent Deliveries</h3>
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-900/40">
                  <tr className="text-left text-xs text-gray-500">
                    <th className="px-3 py-2">Channel</th><th className="px-3 py-2">Recipient</th>
                    <th className="px-3 py-2">Event</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">When</th>
                  </tr>
                </thead>
                <tbody>
                  {(logs || []).map((l: any) => (
                    <tr key={l.id} className="border-t border-gray-100 dark:border-gray-700">
                      <td className="px-3 py-2">{l.channel}</td>
                      <td className="px-3 py-2">{l.recipient_phone || l.recipient_email || '—'}</td>
                      <td className="px-3 py-2 text-xs">{l.event_trigger || '—'}</td>
                      <td className={`px-3 py-2 font-medium ${statusColor[l.status] || ''}`}>{l.status}{l.error_message ? ` (${l.error_message})` : ''}</td>
                      <td className="px-3 py-2 text-xs text-gray-400">{formatDateTime(l.created_at)}</td>
                    </tr>
                  ))}
                  {(logs || []).length === 0 && <tr><td colSpan={5} className="px-3 py-4 text-center text-gray-500">No deliveries yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommunicationPage;
