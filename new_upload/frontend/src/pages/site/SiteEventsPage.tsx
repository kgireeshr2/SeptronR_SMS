import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { websiteApi } from '@api/website';
import { useSchoolSite } from '@hooks/useSchoolSite';

const SiteEventsPage: React.FC = () => {
  const { slug } = useSchoolSite();
  const { data, isLoading } = useQuery({
    queryKey: ['site-events', slug],
    enabled: !!slug,
    queryFn: () => websiteApi.listEvents(slug),
  });
  const events = (data as any[]) ?? [];

  return (
    <div className="mx-auto max-w-4xl px-4 py-14">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">Events</h1>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      {!isLoading && events.length === 0 && <p className="text-gray-500">No events yet.</p>}
      <div className="space-y-4">
        {events.map((e) => (
          <div key={e.id} className="flex gap-4 overflow-hidden rounded-lg border border-gray-200 bg-white">
            {e.image_url && (
              <img src={e.image_url} alt={e.title} className="h-32 w-40 shrink-0 object-cover" loading="lazy" />
            )}
            <div className="p-4">
              <div className="flex items-center gap-2">
                {e.is_featured && (
                  <span
                    className="rounded px-1.5 py-0.5 text-[10px] font-semibold text-white"
                    style={{ background: 'var(--site-primary)' }}
                  >
                    Featured
                  </span>
                )}
                <h3 className="font-semibold text-gray-900">{e.title}</h3>
              </div>
              {e.event_date && (
                <p className="mt-1 text-xs text-gray-500">
                  {new Date(e.event_date).toLocaleString()}
                  {e.location ? ` · ${e.location}` : ''}
                </p>
              )}
              {e.description && <p className="mt-2 text-sm text-gray-600">{e.description}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SiteEventsPage;
