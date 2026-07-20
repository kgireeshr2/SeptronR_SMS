import axios from 'axios';
import api from './axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// ── Public (anonymous) client ─────────────────────────────────────────────────
// The shared `api` instance attaches the auth token + X-School-Id and, on a 401,
// force-redirects to /login — all wrong for the unauthenticated public site.
// This bare instance only unwraps the response envelope.
const pub = axios.create({ baseURL: BASE_URL, headers: { 'Content-Type': 'application/json' } });
pub.interceptors.response.use((res) => res.data);

const unwrap = (res: any) => res?.data ?? res;

// ── Types ─────────────────────────────────────────────────────────────────────
export interface WebsiteConfig {
  id: string;
  school_id: string;
  is_published: boolean;
  sections: Record<string, boolean>;
  theme_color: string;
  secondary_color?: string | null;
  hero_title?: string | null;
  hero_subtitle?: string | null;
  hero_image_url?: string | null;
  about_content?: string | null;
  mission?: string | null;
  vision?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  contact_address?: string | null;
  map_embed_url?: string | null;
  social_links?: Record<string, string>;
  seo_title?: string | null;
  seo_description?: string | null;
  school: {
    id: string;
    name: string;
    slug: string;
    logo_url?: string | null;
    tagline?: string | null;
    established_year?: number | null;
    affiliation_board?: string | null;
    city?: string | null;
    state?: string | null;
  };
}

export const websiteApi = {
  // ── Public ──
  resolveByHost: (host: string) => pub.get('/public/resolve', { params: { host } }).then(unwrap),
  resolveBySlug: (slug: string) => pub.get('/public/resolve', { params: { slug } }).then(unwrap),
  getSite: (slug: string): Promise<WebsiteConfig> => pub.get(`/public/site/${slug}`).then(unwrap),
  listNotices: (slug: string) => pub.get(`/public/site/${slug}/notices`).then(unwrap),
  getNotice: (slug: string, id: string) => pub.get(`/public/site/${slug}/notices/${id}`).then(unwrap),
  listGallery: (slug: string) => pub.get(`/public/site/${slug}/gallery`).then(unwrap),
  listEvents: (slug: string) => pub.get(`/public/site/${slug}/events`).then(unwrap),
  listContent: (slug: string, section: string) =>
    pub.get(`/public/site/${slug}/content/${section}`).then(unwrap),
  submitEnquiry: (slug: string, body: Record<string, any>) =>
    pub.post(`/public/site/${slug}/enquiry`, body).then(unwrap),

  // ── Admin (authenticated) ──
  getConfig: () => api.get('/website/config'),
  updateConfig: (data: Record<string, any>) => api.put('/website/config', data),
  setPublish: (is_published: boolean) => api.put('/website/publish', { is_published }),
  setSections: (sections: Record<string, boolean>) => api.put('/website/sections', { sections }),
  uploadHero: (file: File) => uploadFile('/website/hero-image', file),

  listAlbums: () => api.get('/website/gallery/albums'),
  createAlbum: (data: Record<string, any>) => api.post('/website/gallery/albums', data),
  updateAlbum: (id: string, data: Record<string, any>) => api.put(`/website/gallery/albums/${id}`, data),
  deleteAlbum: (id: string) => api.delete(`/website/gallery/albums/${id}`),
  listImages: (albumId?: string) =>
    api.get('/website/gallery/images', { params: albumId ? { album_id: albumId } : {} }),
  uploadImage: (file: File, albumId?: string, caption?: string) =>
    uploadFile('/website/gallery/images', file, { album_id: albumId, caption }),
  deleteImage: (id: string) => api.delete(`/website/gallery/images/${id}`),

  listAdminNotices: () => api.get('/website/notices'),
  createNotice: (data: Record<string, any>) => api.post('/website/notices', data),
  updateNotice: (id: string, data: Record<string, any>) => api.put(`/website/notices/${id}`, data),
  deleteNotice: (id: string) => api.delete(`/website/notices/${id}`),
  uploadNoticeAttachment: (file: File) => uploadFile('/website/notices/attachment', file),

  listAdminEvents: () => api.get('/website/events'),
  createEvent: (data: Record<string, any>) => api.post('/website/events', data),
  updateEvent: (id: string, data: Record<string, any>) => api.put(`/website/events/${id}`, data),
  deleteEvent: (id: string) => api.delete(`/website/events/${id}`),

  listAdminContent: (section: string) => api.get(`/website/content/${section}`),
  createContent: (section: string, data: Record<string, any>) => api.post(`/website/content/${section}`, data),
  updateContent: (section: string, id: string, data: Record<string, any>) =>
    api.put(`/website/content/${section}/${id}`, data),
  deleteContent: (section: string, id: string) => api.delete(`/website/content/${section}/${id}`),
  uploadContentImage: (file: File) => uploadFile('/website/content-image', file),

  listEnquiries: (params?: Record<string, any>) => api.get('/website/enquiries', { params }),
  enquiryStats: () => api.get('/website/enquiries/stats'),
  updateEnquiryStatus: (id: string, status: string) =>
    api.put(`/website/enquiries/${id}/status`, { status }),

  listDomains: () => api.get('/website/domains'),
  addDomain: (hostname: string) => api.post('/website/domains', { hostname }),
  verifyDomain: (id: string) => api.post(`/website/domains/${id}/verify`),
  setPrimaryDomain: (id: string) => api.put(`/website/domains/${id}/primary`),
  deleteDomain: (id: string) => api.delete(`/website/domains/${id}`),
};

function uploadFile(url: string, file: File, params?: Record<string, any>) {
  const form = new FormData();
  form.append('file', file);
  return api.post(url, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params,
  });
}
