import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ExternalLink, Trash2, Plus, CheckCircle } from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { websiteApi } from '@api/website';
import { useAuthStore } from '@store/authStore';
import { formatDateTime } from '@utils/formatters';

const unwrap = (res: any) => res?.data ?? res;
const SECTION_KEYS = [
  'home', 'about', 'gallery', 'notices', 'events', 'admissions',
  'enquiry', 'contact', 'faculty', 'academics', 'achievements',
  'facilities', 'downloads', 'testimonials',
];
const CONTENT_SECTIONS = ['faculty', 'academics', 'achievements', 'facilities', 'downloads', 'testimonials'];
const TABS = ['Settings', 'Gallery', 'Notices', 'Events', 'Content', 'Enquiries', 'Domains'] as const;
type Tab = (typeof TABS)[number];

const input = 'w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500';
const btn = 'rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60';

const WebsiteAdminPage: React.FC = () => {
  const [tab, setTab] = React.useState<Tab>('Settings');
  const slug = useAuthStore((s) => s.schoolInfo?.slug);

  return (
    <div>
      <PageHeader
        title="Website"
        subtitle="Manage your school's public website"
        actions={
          slug ? (
            <a href={`/site/${slug}`} target="_blank" rel="noreferrer" className={`${btn} inline-flex items-center gap-2`}>
              <ExternalLink size={14} /> View live site
            </a>
          ) : undefined
        }
      />
      <div className="mb-6 flex flex-wrap gap-1 border-b border-gray-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
              tab === t ? 'border-brand-600 text-brand-700' : 'border-transparent text-gray-500 hover:text-gray-800'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Settings' && <SettingsTab />}
      {tab === 'Gallery' && <GalleryTab />}
      {tab === 'Notices' && <NoticesTab />}
      {tab === 'Events' && <EventsTab />}
      {tab === 'Content' && <ContentTab />}
      {tab === 'Enquiries' && <EnquiriesTab />}
      {tab === 'Domains' && <DomainsTab />}
    </div>
  );
};

// ── Settings ───────────────────────────────────────────────────────────────
const SettingsTab: React.FC = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['admin-website-config'], queryFn: () => websiteApi.getConfig().then(unwrap) });
  const [form, setForm] = React.useState<any>(null);

  React.useEffect(() => {
    if (data && !form) setForm(data);
  }, [data]);

  const save = useMutation({
    mutationFn: (payload: any) => websiteApi.updateConfig(payload),
    onSuccess: () => {
      toast.success('Saved');
      qc.invalidateQueries({ queryKey: ['admin-website-config'] });
    },
    onError: (e: any) => toast.error(e?.detail ?? 'Save failed'),
  });
  const publish = useMutation({
    mutationFn: (v: boolean) => websiteApi.setPublish(v),
    onSuccess: (_, v) => {
      toast.success(v ? 'Website published' : 'Website unpublished');
      qc.invalidateQueries({ queryKey: ['admin-website-config'] });
    },
  });

  if (isLoading || !form) return <p className="text-sm text-gray-400">Loading…</p>;

  const set = (k: string, v: any) => setForm((p: any) => ({ ...p, [k]: v }));
  const toggleSection = (k: string) =>
    setForm((p: any) => ({ ...p, sections: { ...(p.sections ?? {}), [k]: !p.sections?.[k] } }));

  return (
    <div className="max-w-3xl space-y-6">
      {/* Publish */}
      <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-5">
        <div>
          <p className="font-semibold text-gray-900">Site published</p>
          <p className="text-sm text-gray-500">When off, the public site shows a "not available" message.</p>
        </div>
        <button
          onClick={() => publish.mutate(!form.is_published)}
          className={`relative h-6 w-11 rounded-full transition-colors ${form.is_published ? 'bg-green-500' : 'bg-gray-300'}`}
        >
          <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${form.is_published ? 'left-[22px]' : 'left-0.5'}`} />
        </button>
      </div>

      {/* Sections */}
      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <p className="mb-3 font-semibold text-gray-900">Sections</p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {SECTION_KEYS.map((k) => (
            <label key={k} className="flex items-center gap-2 text-sm capitalize text-gray-700">
              <input type="checkbox" checked={!!form.sections?.[k]} onChange={() => toggleSection(k)} />
              {k}
            </label>
          ))}
        </div>
      </div>

      {/* Branding + content */}
      <div className="space-y-3 rounded-xl border border-gray-200 bg-white p-5">
        <p className="font-semibold text-gray-900">Appearance &amp; Content</p>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600">Theme color</label>
          <input type="color" value={form.theme_color ?? '#1e40af'} onChange={(e) => set('theme_color', e.target.value)} className="h-9 w-16 rounded border" />
        </div>
        <input className={input} placeholder="Hero title" value={form.hero_title ?? ''} onChange={(e) => set('hero_title', e.target.value)} />
        <input className={input} placeholder="Hero subtitle" value={form.hero_subtitle ?? ''} onChange={(e) => set('hero_subtitle', e.target.value)} />
        <HeroUpload onDone={() => qc.invalidateQueries({ queryKey: ['admin-website-config'] })} current={form.hero_image_url} />
        <textarea className={input} rows={5} placeholder="About content" value={form.about_content ?? ''} onChange={(e) => set('about_content', e.target.value)} />
        <div className="grid gap-3 md:grid-cols-2">
          <textarea className={input} rows={3} placeholder="Mission" value={form.mission ?? ''} onChange={(e) => set('mission', e.target.value)} />
          <textarea className={input} rows={3} placeholder="Vision" value={form.vision ?? ''} onChange={(e) => set('vision', e.target.value)} />
        </div>
      </div>

      {/* Contact + social */}
      <div className="space-y-3 rounded-xl border border-gray-200 bg-white p-5">
        <p className="font-semibold text-gray-900">Contact</p>
        <div className="grid gap-3 md:grid-cols-2">
          <input className={input} placeholder="Contact phone" value={form.contact_phone ?? ''} onChange={(e) => set('contact_phone', e.target.value)} />
          <input className={input} placeholder="Contact email" value={form.contact_email ?? ''} onChange={(e) => set('contact_email', e.target.value)} />
        </div>
        <textarea className={input} rows={2} placeholder="Contact address" value={form.contact_address ?? ''} onChange={(e) => set('contact_address', e.target.value)} />
        <input className={input} placeholder="Google Maps embed URL" value={form.map_embed_url ?? ''} onChange={(e) => set('map_embed_url', e.target.value)} />
        <div className="grid gap-3 md:grid-cols-2">
          {['facebook', 'instagram', 'youtube', 'twitter'].map((s) => (
            <input
              key={s}
              className={input}
              placeholder={`${s} URL`}
              value={form.social_links?.[s] ?? ''}
              onChange={(e) => set('social_links', { ...(form.social_links ?? {}), [s]: e.target.value })}
            />
          ))}
        </div>
      </div>

      <button
        className={btn}
        disabled={save.isPending}
        onClick={() => {
          const { school, id, school_id, ...payload } = form;
          save.mutate(payload);
        }}
      >
        {save.isPending ? 'Saving…' : 'Save changes'}
      </button>
    </div>
  );
};

const HeroUpload: React.FC<{ current?: string | null; onDone: () => void }> = ({ current, onDone }) => {
  const up = useMutation({
    mutationFn: (f: File) => websiteApi.uploadHero(f),
    onSuccess: () => {
      toast.success('Hero image uploaded');
      onDone();
    },
    onError: () => toast.error('Upload failed'),
  });
  return (
    <div className="flex items-center gap-3">
      {current && <img src={current} alt="hero" className="h-12 w-20 rounded object-cover" />}
      <input type="file" accept="image/*" className="text-sm" onChange={(e) => e.target.files?.[0] && up.mutate(e.target.files[0])} />
    </div>
  );
};

// ── Gallery ────────────────────────────────────────────────────────────────
const GalleryTab: React.FC = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['admin-gallery'], queryFn: () => websiteApi.listImages().then(unwrap) });
  const images = (data as any[]) ?? [];
  const upload = useMutation({
    mutationFn: (f: File) => websiteApi.uploadImage(f),
    onSuccess: () => {
      toast.success('Image uploaded');
      qc.invalidateQueries({ queryKey: ['admin-gallery'] });
    },
    onError: () => toast.error('Upload failed'),
  });
  const del = useMutation({
    mutationFn: (id: string) => websiteApi.deleteImage(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-gallery'] }),
  });

  return (
    <div>
      <label className={`${btn} mb-5 inline-flex cursor-pointer items-center gap-2`}>
        <Plus size={14} /> Upload image
        <input type="file" accept="image/*" hidden onChange={(e) => e.target.files?.[0] && upload.mutate(e.target.files[0])} />
      </label>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {images.map((img) => (
          <div key={img.id} className="group relative aspect-square overflow-hidden rounded-lg bg-gray-100">
            <img src={img.image_url} alt={img.caption ?? ''} className="h-full w-full object-cover" />
            <button
              onClick={() => del.mutate(img.id)}
              className="absolute right-1 top-1 rounded bg-red-600 p-1 text-white opacity-0 transition-opacity group-hover:opacity-100"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
      {!isLoading && images.length === 0 && <p className="text-sm text-gray-400">No images yet.</p>}
    </div>
  );
};

// ── Notices ────────────────────────────────────────────────────────────────
const NoticesTab: React.FC = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['admin-notices'], queryFn: () => websiteApi.listAdminNotices().then(unwrap) });
  const [editing, setEditing] = React.useState<any | null>(null);
  const notices = (data as any[]) ?? [];
  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin-notices'] });
  const del = useMutation({ mutationFn: (id: string) => websiteApi.deleteNotice(id), onSuccess: invalidate });

  return (
    <div>
      <button className={`${btn} mb-4 inline-flex items-center gap-2`} onClick={() => setEditing({})}>
        <Plus size={14} /> New notice
      </button>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      <ul className="space-y-2">
        {notices.map((n) => (
          <li key={n.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3">
            <div>
              <p className="font-medium text-gray-900">{n.is_pinned && '📌 '}{n.title}</p>
              <p className="text-xs text-gray-400">{n.category} · {n.is_published ? 'Published' : 'Draft'}</p>
            </div>
            <div className="flex gap-2">
              <button className="text-sm text-brand-600" onClick={() => setEditing(n)}>Edit</button>
              <button className="text-sm text-red-600" onClick={() => del.mutate(n.id)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
      {editing && <NoticeModal notice={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); invalidate(); }} />}
    </div>
  );
};

const NoticeModal: React.FC<{ notice: any; onClose: () => void; onSaved: () => void }> = ({ notice, onClose, onSaved }) => {
  const [form, setForm] = React.useState<any>({ category: 'notice', is_published: true, is_pinned: false, ...notice });
  const save = useMutation({
    mutationFn: () => (notice.id ? websiteApi.updateNotice(notice.id, form) : websiteApi.createNotice(form)),
    onSuccess: () => { toast.success('Saved'); onSaved(); },
    onError: (e: any) => toast.error(e?.detail ?? 'Save failed'),
  });
  const set = (k: string, v: any) => setForm((p: any) => ({ ...p, [k]: v }));
  return (
    <Modal onClose={onClose} title={notice.id ? 'Edit notice' : 'New notice'}>
      <input className={input} placeholder="Title" value={form.title ?? ''} onChange={(e) => set('title', e.target.value)} />
      <textarea className={input} rows={5} placeholder="Body" value={form.body ?? ''} onChange={(e) => set('body', e.target.value)} />
      <div className="grid grid-cols-2 gap-3">
        <select className={input} value={form.category} onChange={(e) => set('category', e.target.value)}>
          {['notice', 'update', 'circular', 'announcement'].map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <div className="flex items-center gap-4 text-sm">
          <label className="flex items-center gap-1"><input type="checkbox" checked={form.is_published} onChange={(e) => set('is_published', e.target.checked)} /> Published</label>
          <label className="flex items-center gap-1"><input type="checkbox" checked={form.is_pinned} onChange={(e) => set('is_pinned', e.target.checked)} /> Pinned</label>
        </div>
      </div>
      <button className={btn} disabled={save.isPending} onClick={() => form.title ? save.mutate() : toast.error('Title required')}>Save</button>
    </Modal>
  );
};

// ── Events ─────────────────────────────────────────────────────────────────
const EventsTab: React.FC = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['admin-events'], queryFn: () => websiteApi.listAdminEvents().then(unwrap) });
  const [editing, setEditing] = React.useState<any | null>(null);
  const events = (data as any[]) ?? [];
  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin-events'] });
  const del = useMutation({ mutationFn: (id: string) => websiteApi.deleteEvent(id), onSuccess: invalidate });

  return (
    <div>
      <button className={`${btn} mb-4 inline-flex items-center gap-2`} onClick={() => setEditing({})}><Plus size={14} /> New event</button>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      <ul className="space-y-2">
        {events.map((e) => (
          <li key={e.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3">
            <div>
              <p className="font-medium text-gray-900">{e.is_featured && '⭐ '}{e.title}</p>
              <p className="text-xs text-gray-400">{e.event_date ? formatDateTime(e.event_date) : 'No date'} · {e.is_published ? 'Published' : 'Draft'}</p>
            </div>
            <div className="flex gap-2">
              <button className="text-sm text-brand-600" onClick={() => setEditing(e)}>Edit</button>
              <button className="text-sm text-red-600" onClick={() => del.mutate(e.id)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
      {editing && <EventModal event={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); invalidate(); }} />}
    </div>
  );
};

const EventModal: React.FC<{ event: any; onClose: () => void; onSaved: () => void }> = ({ event, onClose, onSaved }) => {
  const [form, setForm] = React.useState<any>({ is_published: true, is_featured: false, ...event });
  const save = useMutation({
    mutationFn: () => (event.id ? websiteApi.updateEvent(event.id, form) : websiteApi.createEvent(form)),
    onSuccess: () => { toast.success('Saved'); onSaved(); },
    onError: (e: any) => toast.error(e?.detail ?? 'Save failed'),
  });
  const set = (k: string, v: any) => setForm((p: any) => ({ ...p, [k]: v }));
  return (
    <Modal onClose={onClose} title={event.id ? 'Edit event' : 'New event'}>
      <input className={input} placeholder="Title" value={form.title ?? ''} onChange={(e) => set('title', e.target.value)} />
      <textarea className={input} rows={3} placeholder="Description" value={form.description ?? ''} onChange={(e) => set('description', e.target.value)} />
      <div className="grid grid-cols-2 gap-3">
        <input type="datetime-local" className={input} value={form.event_date ?? ''} onChange={(e) => set('event_date', e.target.value)} />
        <input className={input} placeholder="Location" value={form.location ?? ''} onChange={(e) => set('location', e.target.value)} />
      </div>
      <div className="flex items-center gap-4 text-sm">
        <label className="flex items-center gap-1"><input type="checkbox" checked={form.is_published} onChange={(e) => set('is_published', e.target.checked)} /> Published</label>
        <label className="flex items-center gap-1"><input type="checkbox" checked={form.is_featured} onChange={(e) => set('is_featured', e.target.checked)} /> Featured</label>
      </div>
      <button className={btn} disabled={save.isPending} onClick={() => form.title ? save.mutate() : toast.error('Title required')}>Save</button>
    </Modal>
  );
};

// ── Content (faculty/academics/...) ──────────────────────────────────────────
const ContentTab: React.FC = () => {
  const qc = useQueryClient();
  const [section, setSection] = React.useState(CONTENT_SECTIONS[0]);
  const [editing, setEditing] = React.useState<any | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ['admin-content', section],
    queryFn: () => websiteApi.listAdminContent(section).then(unwrap),
  });
  const items = (data as any[]) ?? [];
  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin-content', section] });
  const del = useMutation({ mutationFn: (id: string) => websiteApi.deleteContent(section, id), onSuccess: invalidate });

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <select className={`${input} max-w-xs`} value={section} onChange={(e) => setSection(e.target.value)}>
          {CONTENT_SECTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button className={`${btn} inline-flex items-center gap-2`} onClick={() => setEditing({})}><Plus size={14} /> Add</button>
      </div>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      <ul className="space-y-2">
        {items.map((it) => (
          <li key={it.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3">
            <div className="flex items-center gap-3">
              {it.image_url && <img src={it.image_url} alt="" className="h-10 w-10 rounded object-cover" />}
              <div>
                <p className="font-medium text-gray-900">{it.title}</p>
                {it.subtitle && <p className="text-xs text-gray-400">{it.subtitle}</p>}
              </div>
            </div>
            <div className="flex gap-2">
              <button className="text-sm text-brand-600" onClick={() => setEditing(it)}>Edit</button>
              <button className="text-sm text-red-600" onClick={() => del.mutate(it.id)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
      {editing && <ContentModal section={section} item={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); invalidate(); }} />}
    </div>
  );
};

const ContentModal: React.FC<{ section: string; item: any; onClose: () => void; onSaved: () => void }> = ({ section, item, onClose, onSaved }) => {
  const [form, setForm] = React.useState<any>({ is_published: true, ...item });
  const upload = useMutation({
    mutationFn: (f: File) => websiteApi.uploadContentImage(f).then(unwrap),
    onSuccess: (res: any) => { setForm((p: any) => ({ ...p, image_url: res.path ?? res.image_url })); toast.success('Image uploaded'); },
    onError: () => toast.error('Upload failed'),
  });
  const save = useMutation({
    mutationFn: () => (item.id ? websiteApi.updateContent(section, item.id, form) : websiteApi.createContent(section, form)),
    onSuccess: () => { toast.success('Saved'); onSaved(); },
    onError: (e: any) => toast.error(e?.detail ?? 'Save failed'),
  });
  const set = (k: string, v: any) => setForm((p: any) => ({ ...p, [k]: v }));
  return (
    <Modal onClose={onClose} title={`${item.id ? 'Edit' : 'Add'} ${section}`}>
      <input className={input} placeholder="Title / Name" value={form.title ?? ''} onChange={(e) => set('title', e.target.value)} />
      <input className={input} placeholder="Subtitle (e.g. designation / level / author role)" value={form.subtitle ?? ''} onChange={(e) => set('subtitle', e.target.value)} />
      <textarea className={input} rows={4} placeholder="Description" value={form.description ?? ''} onChange={(e) => set('description', e.target.value)} />
      <input className={input} placeholder="Link URL (optional, e.g. download file)" value={form.link_url ?? ''} onChange={(e) => set('link_url', e.target.value)} />
      <div className="flex items-center gap-3">
        {form.image_url && <img src={form.image_url.startsWith('/') || form.image_url.startsWith('http') ? form.image_url : `/uploads/${form.image_url}`} alt="" className="h-12 w-12 rounded object-cover" />}
        <input type="file" className="text-sm" onChange={(e) => e.target.files?.[0] && upload.mutate(e.target.files[0])} />
      </div>
      <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={form.is_published} onChange={(e) => set('is_published', e.target.checked)} /> Published</label>
      <button className={btn} disabled={save.isPending} onClick={() => form.title ? save.mutate() : toast.error('Title required')}>Save</button>
    </Modal>
  );
};

// ── Enquiries ────────────────────────────────────────────────────────────────
const EnquiriesTab: React.FC = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['admin-enquiries'], queryFn: () => websiteApi.listEnquiries().then(unwrap) });
  const items = (data?.items as any[]) ?? [];
  const upd = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => websiteApi.updateEnquiryStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-enquiries'] }),
  });
  const badge: Record<string, string> = { new: 'bg-blue-100 text-blue-700', read: 'bg-gray-100 text-gray-600', responded: 'bg-green-100 text-green-700', closed: 'bg-gray-200 text-gray-500' };

  return (
    <div>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      {!isLoading && items.length === 0 && <p className="text-sm text-gray-400">No enquiries yet.</p>}
      <div className="space-y-3">
        {items.map((e) => (
          <div key={e.id} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-gray-900">{e.name} {e.subject ? `· ${e.subject}` : ''}</p>
                <p className="text-xs text-gray-400">{[e.phone, e.email].filter(Boolean).join(' · ')} · {formatDateTime(e.created_at)}</p>
              </div>
              <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${badge[e.status] ?? 'bg-gray-100'}`}>{e.status}</span>
            </div>
            <p className="mt-2 whitespace-pre-line text-sm text-gray-700">{e.message}</p>
            <div className="mt-3 flex gap-2">
              {['read', 'responded', 'closed'].map((s) => (
                <button key={s} onClick={() => upd.mutate({ id: e.id, status: s })} className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50 capitalize">
                  Mark {s}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── Domains ──────────────────────────────────────────────────────────────────
const DomainsTab: React.FC = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['admin-domains'], queryFn: () => websiteApi.listDomains().then(unwrap) });
  const [host, setHost] = React.useState('');
  const [dns, setDns] = React.useState<any>(null);
  const domains = (data as any[]) ?? [];
  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin-domains'] });
  const add = useMutation({
    mutationFn: () => websiteApi.addDomain(host.trim()).then(unwrap),
    onSuccess: (res: any) => { setDns(res.dns_instructions); setHost(''); invalidate(); toast.success('Domain added'); },
    onError: (e: any) => toast.error(e?.detail ?? 'Failed'),
  });
  const verify = useMutation({ mutationFn: (id: string) => websiteApi.verifyDomain(id), onSuccess: () => { toast.success('Verified'); invalidate(); }, onError: (e: any) => toast.error(e?.detail ?? 'Verification failed') });
  const primary = useMutation({ mutationFn: (id: string) => websiteApi.setPrimaryDomain(id), onSuccess: invalidate });
  const del = useMutation({ mutationFn: (id: string) => websiteApi.deleteDomain(id), onSuccess: invalidate });

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex gap-2">
        <input className={input} placeholder="www.yourschool.edu" value={host} onChange={(e) => setHost(e.target.value)} />
        <button className={btn} disabled={!host.trim() || add.isPending} onClick={() => add.mutate()}>Add domain</button>
      </div>
      {dns && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
          <p className="font-semibold text-amber-800">Create these DNS records, then click Verify:</p>
          <p className="mt-2 font-mono text-xs">TXT {dns.txt_record.host} = {dns.txt_record.value}</p>
          <p className="font-mono text-xs">CNAME {dns.cname_record.host} → {dns.cname_record.value}</p>
        </div>
      )}
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      <ul className="space-y-2">
        {domains.map((d) => (
          <li key={d.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3">
            <div>
              <p className="font-medium text-gray-900">{d.hostname} {d.is_primary && <span className="text-xs text-green-600">(primary)</span>}</p>
              <p className="text-xs text-gray-400">{d.is_verified ? `Verified · SSL ${d.ssl_status ?? 'pending'}` : 'Unverified'}</p>
            </div>
            <div className="flex items-center gap-2">
              {!d.is_verified && <button className="text-sm text-brand-600" onClick={() => verify.mutate(d.id)}>Verify</button>}
              {d.is_verified && !d.is_primary && <button className="inline-flex items-center gap-1 text-sm text-green-600" onClick={() => primary.mutate(d.id)}><CheckCircle size={14} /> Set primary</button>}
              <button className="text-sm text-red-600" onClick={() => del.mutate(d.id)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

// ── Shared modal ─────────────────────────────────────────────────────────────
const Modal: React.FC<{ title: string; onClose: () => void; children: React.ReactNode }> = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
    <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <button onClick={onClose} className="text-2xl text-gray-400 hover:text-gray-700">×</button>
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  </div>
);

export default WebsiteAdminPage;
