import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import { calendarApi } from '@/api/calendar';
import api from '@/api/axios';
import { toast } from 'sonner';
import { formatDateTime } from '@utils/formatters';

type MainTab = 'events' | 'holidays';
type EventType = 'holiday' | 'exam' | 'meeting' | 'sports' | 'cultural' | 'trip' | 'other';

interface Holiday { id: string; date: string; name: string; description?: string; is_recurring?: boolean; }

interface CalendarEvent {
  id: string;
  title: string;
  event_type: EventType;
  start_datetime: string;
  end_datetime: string;
  venue?: string;
  description?: string;
  color_tag?: string;
  is_public: boolean;
}

const EVENT_COLORS: Record<EventType, string> = {
  holiday:  'bg-red-100 text-red-700',
  exam:     'bg-purple-100 text-purple-700',
  meeting:  'bg-blue-100 text-blue-700',
  sports:   'bg-green-100 text-green-700',
  cultural: 'bg-yellow-100 text-yellow-700',
  trip:     'bg-orange-100 text-orange-700',
  other:    'bg-gray-100 text-gray-700',
};

const EVENT_TYPES: EventType[] = ['holiday', 'exam', 'meeting', 'sports', 'cultural', 'trip', 'other'];

const fmt = (dt: string) => formatDateTime(dt);

const Page: React.FC = () => {
  const [mainTab, setMainTab] = useState<MainTab>('events');
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<EventType | ''>('');
  const [showModal, setShowModal] = useState(false);
  const [editTarget, setEditTarget] = useState<CalendarEvent | null>(null);
  const [form, setForm] = useState({
    title: '', event_type: 'other' as EventType,
    start_datetime: '', end_datetime: '',
    venue: '', description: '', color_tag: '#3B82F6', is_public: true,
  });

  // Holidays state
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [holLoading, setHolLoading] = useState(false);
  const [showHolModal, setShowHolModal] = useState(false);
  const [editHol, setEditHol] = useState<Holiday | null>(null);
  const [holForm, setHolForm] = useState({ date: '', name: '', description: '', is_recurring: false });

  useEffect(() => { if (mainTab === 'events') loadEvents(); else loadHolidays(); }, [filterType, mainTab]);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const r: any = await calendarApi.list({ event_type: filterType || undefined });
      setEvents(Array.isArray(r) ? r : (r?.data ?? []));
    } catch { /* ignore */ } finally { setLoading(false); }
  };

  const loadHolidays = async () => {
    setHolLoading(true);
    try {
      const r: any = await api.get('/holidays');
      setHolidays(Array.isArray(r) ? r : (r?.data ?? []));
    } catch { /* ignore */ } finally { setHolLoading(false); }
  };

  const saveHoliday = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editHol) {
        await api.put(`/holidays/${editHol.id}`, holForm);
        toast.success('Holiday updated');
      } else {
        await api.post('/holidays', holForm);
        toast.success('Holiday added');
      }
      setShowHolModal(false); setEditHol(null);
      setHolForm({ date: '', name: '', description: '', is_recurring: false });
      loadHolidays();
    } catch (err: any) { toast.error(err?.response?.data?.detail ?? 'Failed to save holiday'); }
  };

  const deleteHoliday = async (id: string) => {
    if (!confirm('Delete this holiday?')) return;
    try { await api.delete(`/holidays/${id}`); toast.success('Deleted'); loadHolidays(); }
    catch { toast.error('Failed to delete'); }
  };

  const openEditHol = (h: Holiday) => {
    setEditHol(h);
    setHolForm({ date: h.date, name: h.name, description: h.description ?? '', is_recurring: h.is_recurring ?? false });
    setShowHolModal(true);
  };

  const openCreate = () => {
    setEditTarget(null);
    setForm({ title: '', event_type: 'other', start_datetime: '', end_datetime: '', venue: '', description: '', color_tag: '#3B82F6', is_public: true });
    setShowModal(true);
  };

  const openEdit = (ev: CalendarEvent) => {
    setEditTarget(ev);
    setForm({
      title: ev.title, event_type: ev.event_type,
      start_datetime: ev.start_datetime.slice(0, 16),
      end_datetime: ev.end_datetime.slice(0, 16),
      venue: ev.venue ?? '', description: ev.description ?? '',
      color_tag: ev.color_tag ?? '#3B82F6', is_public: ev.is_public,
    });
    setShowModal(true);
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editTarget) {
      await calendarApi.update(editTarget.id, form);
    } else {
      await calendarApi.create(form);
    }
    setShowModal(false);
    loadEvents();
  };

  const remove = async (id: string) => {
    if (!confirm('Delete this event?')) return;
    await calendarApi.delete(id);
    loadEvents();
  };

  return (
    <div>
      <PageHeader title="School Calendar" />

      {/* Main Tabs */}
      <div className="mb-5 flex gap-1 border-b border-gray-200 dark:border-gray-700">
        <button onClick={() => setMainTab('events')} className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${mainTab === 'events' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>📅 Calendar Events</button>
        <button onClick={() => setMainTab('holidays')} className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${mainTab === 'holidays' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>🏖️ Holidays</button>
      </div>

      {/* ── Holidays Tab ─────────────────────────────────────── */}
      {mainTab === 'holidays' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => { setEditHol(null); setHolForm({ date: '', name: '', description: '', is_recurring: false }); setShowHolModal(true); }}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">+ Add Holiday</button>
          </div>
          {holLoading ? <p className="py-10 text-center text-gray-400">Loading…</p> : (
            <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>{['Date', 'Name', 'Description', 'Recurring', 'Actions'].map(h => <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {holidays.length === 0 ? <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No holidays found.</td></tr>
                    : holidays.map(h => (
                      <tr key={h.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                        <td className="px-4 py-3 font-mono text-gray-700">{h.date}</td>
                        <td className="px-4 py-3 font-medium">{h.name}</td>
                        <td className="px-4 py-3 text-gray-500">{h.description ?? '—'}</td>
                        <td className="px-4 py-3">{h.is_recurring ? <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">Yes</span> : '—'}</td>
                        <td className="px-4 py-3 flex gap-2">
                          <button onClick={() => openEditHol(h)} className="text-xs text-indigo-600 hover:underline">Edit</button>
                          <button onClick={() => deleteHoliday(h.id)} className="text-xs text-red-500 hover:underline">Delete</button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}

          {showHolModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
              <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
                <h3 className="mb-4 text-lg font-semibold dark:text-white">{editHol ? 'Edit Holiday' : 'Add Holiday'}</h3>
                <form onSubmit={saveHoliday} className="space-y-4">
                  <div><label className="mb-1 block text-sm font-medium">Date *</label><input required type="date" value={holForm.date} onChange={e => setHolForm(f => ({ ...f, date: e.target.value }))} className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" /></div>
                  <div><label className="mb-1 block text-sm font-medium">Name *</label><input required value={holForm.name} onChange={e => setHolForm(f => ({ ...f, name: e.target.value }))} className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" /></div>
                  <div><label className="mb-1 block text-sm font-medium">Description</label><input value={holForm.description} onChange={e => setHolForm(f => ({ ...f, description: e.target.value }))} className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" /></div>
                  <div className="flex items-center gap-2"><input type="checkbox" id="is_rec" checked={holForm.is_recurring} onChange={e => setHolForm(f => ({ ...f, is_recurring: e.target.checked }))} className="rounded" /><label htmlFor="is_rec" className="text-sm">Recurring yearly</label></div>
                  <div className="flex justify-end gap-2"><button type="button" onClick={() => setShowHolModal(false)} className="rounded-lg border px-4 py-2 text-sm dark:border-gray-600">Cancel</button><button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">Save</button></div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Events Tab ─────────────────────────────────────── */}
      {mainTab === 'events' && (
      <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setFilterType('')}
            className={`rounded-full px-3 py-1 text-xs font-medium border ${filterType === '' ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-300 text-gray-600 hover:bg-gray-50'}`}
          >
            All
          </button>
          {EVENT_TYPES.map(t => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`rounded-full px-3 py-1 text-xs font-medium border capitalize ${filterType === t ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-300 text-gray-600 hover:bg-gray-50'}`}
            >
              {t}
            </button>
          ))}
        </div>
        <button onClick={openCreate} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          + Add Event
        </button>
      </div>

      {/* Event Cards */}
      {loading ? (
        <p className="text-center text-gray-500 py-12">Loading...</p>
      ) : events.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-800">
          <p className="text-gray-500">No events found. Add the first one!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {events.map(ev => (
            <div
              key={ev.id}
              className="flex items-start justify-between rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
              style={{ borderLeft: `4px solid ${ev.color_tag ?? '#3B82F6'}` }}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${EVENT_COLORS[ev.event_type]}`}>
                    {ev.event_type}
                  </span>
                  {!ev.is_public && (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">Private</span>
                  )}
                </div>
                <h4 className="mt-1 font-semibold text-gray-900 dark:text-white">{ev.title}</h4>
                <p className="text-sm text-gray-500">
                  {fmt(ev.start_datetime)} → {fmt(ev.end_datetime)}
                </p>
                {ev.venue && <p className="text-xs text-gray-400 mt-0.5">📍 {ev.venue}</p>}
                {ev.description && <p className="mt-1 text-xs text-gray-400">{ev.description}</p>}
              </div>
              <div className="flex gap-2 ml-4">
                <button onClick={() => openEdit(ev)} className="rounded-lg border border-gray-200 px-3 py-1 text-xs hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700">
                  Edit
                </button>
                <button onClick={() => remove(ev.id)} className="rounded-lg border border-red-200 px-3 py-1 text-xs text-red-600 hover:bg-red-50">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800 max-h-[90vh] overflow-y-auto">
            <h3 className="mb-4 text-lg font-semibold">{editTarget ? 'Edit Event' : 'Add Calendar Event'}</h3>
            <form onSubmit={save} className="space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium">Title</label>
                <input
                  type="text" value={form.title} required
                  onChange={e => setForm(p => ({ ...p, title: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Event Type</label>
                <select
                  value={form.event_type}
                  onChange={e => setForm(p => ({ ...p, event_type: e.target.value as EventType }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                >
                  {EVENT_TYPES.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium">Start</label>
                  <input
                    type="datetime-local" value={form.start_datetime} required
                    onChange={e => setForm(p => ({ ...p, start_datetime: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">End</label>
                  <input
                    type="datetime-local" value={form.end_datetime} required
                    onChange={e => setForm(p => ({ ...p, end_datetime: e.target.value }))}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Venue</label>
                <input
                  type="text" value={form.venue}
                  onChange={e => setForm(p => ({ ...p, venue: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Description</label>
                <textarea
                  value={form.description} rows={2}
                  onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <label className="mb-1 block text-sm font-medium">Color Tag</label>
                  <input
                    type="color" value={form.color_tag}
                    onChange={e => setForm(p => ({ ...p, color_tag: e.target.value }))}
                    className="h-9 w-full rounded-lg border border-gray-300 cursor-pointer"
                  />
                </div>
                <label className="flex items-center gap-2 cursor-pointer mt-5">
                  <input
                    type="checkbox" checked={form.is_public}
                    onChange={e => setForm(p => ({ ...p, is_public: e.target.checked }))}
                    className="rounded"
                  />
                  <span className="text-sm">Public</span>
                </label>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="rounded-lg border px-4 py-2 text-sm">Cancel</button>
                <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>
    )}
    </div>
  );
};

export default Page;
