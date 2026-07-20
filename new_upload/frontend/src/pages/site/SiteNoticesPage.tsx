import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { websiteApi } from '@api/website';
import { useSchoolSite } from '@hooks/useSchoolSite';

const SiteNoticesPage: React.FC = () => {
  const { slug, siteHref } = useSchoolSite();
  const { data, isLoading } = useQuery({
    queryKey: ['site-notices', slug],
    enabled: !!slug,
    queryFn: () => websiteApi.listNotices(slug),
  });
  const notices = (data as any[]) ?? [];

  return (
    <div className="mx-auto max-w-4xl px-4 py-14">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">Notices &amp; Updates</h1>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      {!isLoading && notices.length === 0 && <p className="text-gray-500">No notices yet.</p>}
      <ul className="space-y-3">
        {notices.map((n) => (
          <li key={n.id} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <Link to={siteHref(`/notices/${n.id}`)} className="font-medium text-gray-900 hover:underline">
                {n.is_pinned && '📌 '}
                {n.title}
              </Link>
              <span
                className="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium text-white"
                style={{ background: 'var(--site-primary)' }}
              >
                {n.category}
              </span>
            </div>
            {n.body && <p className="mt-1 line-clamp-2 text-sm text-gray-600">{n.body}</p>}
            {n.publish_at && (
              <p className="mt-1 text-xs text-gray-400">{new Date(n.publish_at).toLocaleDateString()}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SiteNoticesPage;
