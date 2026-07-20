import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { websiteApi } from '@api/website';
import { useSchoolSite } from '@hooks/useSchoolSite';

const SiteNoticeDetailPage: React.FC = () => {
  const { slug, siteHref } = useSchoolSite();
  const { noticeId = '' } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ['site-notice', slug, noticeId],
    enabled: !!slug && !!noticeId,
    queryFn: () => websiteApi.getNotice(slug, noticeId),
    retry: false,
  });
  const n = data as any;

  return (
    <div className="mx-auto max-w-3xl px-4 py-14">
      <Link to={siteHref('/notices')} className="text-sm text-gray-500 hover:underline">
        ← Back to notices
      </Link>
      {isLoading && <p className="mt-6 text-sm text-gray-400">Loading…</p>}
      {error && <p className="mt-6 text-gray-500">Notice not found.</p>}
      {n && (
        <article className="mt-4">
          <span
            className="rounded-full px-2 py-0.5 text-[11px] font-medium text-white"
            style={{ background: 'var(--site-primary)' }}
          >
            {n.category}
          </span>
          <h1 className="mt-3 text-2xl font-bold text-gray-900">{n.title}</h1>
          {n.publish_at && (
            <p className="mt-1 text-xs text-gray-400">{new Date(n.publish_at).toLocaleString()}</p>
          )}
          {n.body && <p className="mt-5 whitespace-pre-line leading-relaxed text-gray-700">{n.body}</p>}
          {n.attachment_url && (
            <a
              href={n.attachment_url}
              target="_blank"
              rel="noreferrer"
              className="mt-5 inline-block rounded-md px-4 py-2 text-sm font-semibold text-white"
              style={{ background: 'var(--site-primary)' }}
            >
              Download attachment
            </a>
          )}
        </article>
      )}
    </div>
  );
};

export default SiteNoticeDetailPage;
