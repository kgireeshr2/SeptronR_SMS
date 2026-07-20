import React from 'react';
import { useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { websiteApi } from '@api/website';
import { useSchoolSite } from '@hooks/useSchoolSite';

const TITLES: Record<string, string> = {
  faculty: 'Our Faculty',
  academics: 'Academics & Programs',
  achievements: 'Achievements',
  facilities: 'Facilities',
  downloads: 'Downloads',
  testimonials: 'Testimonials',
};

/** Renders a generic content section. Section derived from the trailing URL segment. */
const SiteSectionPage: React.FC = () => {
  const { slug } = useSchoolSite();
  const { pathname } = useLocation();
  const section = pathname.split('/').filter(Boolean).pop() || '';

  const { data, isLoading } = useQuery({
    queryKey: ['site-content', slug, section],
    enabled: !!slug && !!section,
    queryFn: () => websiteApi.listContent(slug, section),
  });
  const items = (data as any[]) ?? [];
  const isDownloads = section === 'downloads';
  const isTestimonials = section === 'testimonials';

  return (
    <div className="mx-auto max-w-6xl px-4 py-14">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">{TITLES[section] ?? 'Content'}</h1>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      {!isLoading && items.length === 0 && <p className="text-gray-500">Coming soon.</p>}

      {isDownloads ? (
        <ul className="space-y-3">
          {items.map((it) => (
            <li key={it.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
              <div>
                <p className="font-medium text-gray-900">{it.title}</p>
                {it.subtitle && <p className="text-sm text-gray-500">{it.subtitle}</p>}
              </div>
              {(it.link_url || it.image_url) && (
                <a
                  href={it.link_url || it.image_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-md px-4 py-2 text-sm font-semibold text-white"
                  style={{ background: 'var(--site-primary)' }}
                >
                  Download
                </a>
              )}
            </li>
          ))}
        </ul>
      ) : isTestimonials ? (
        <div className="grid gap-5 md:grid-cols-2">
          {items.map((it) => (
            <blockquote key={it.id} className="rounded-xl border border-gray-200 bg-white p-6">
              <p className="text-sm italic leading-relaxed text-gray-700">“{it.description}”</p>
              <div className="mt-4 flex items-center gap-3">
                {it.image_url && <img src={it.image_url} alt={it.title} className="h-10 w-10 rounded-full object-cover" />}
                <div>
                  <p className="text-sm font-semibold text-gray-900">{it.title}</p>
                  {it.subtitle && <p className="text-xs text-gray-500">{it.subtitle}</p>}
                </div>
              </div>
            </blockquote>
          ))}
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((it) => (
            <div key={it.id} className="overflow-hidden rounded-xl border border-gray-200 bg-white">
              {it.image_url && (
                <img src={it.image_url} alt={it.title} className="h-44 w-full object-cover" loading="lazy" />
              )}
              <div className="p-5">
                <h3 className="font-semibold text-gray-900">{it.title}</h3>
                {it.subtitle && (
                  <p className="text-sm font-medium" style={{ color: 'var(--site-primary)' }}>
                    {it.subtitle}
                  </p>
                )}
                {it.description && <p className="mt-2 text-sm text-gray-600">{it.description}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SiteSectionPage;
