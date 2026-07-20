import React from 'react';
import { useSchoolSite } from '@hooks/useSchoolSite';

const Block: React.FC<{ title: string; body?: string | null }> = ({ title, body }) =>
  body ? (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-2 text-lg font-semibold" style={{ color: 'var(--site-primary)' }}>
        {title}
      </h3>
      <p className="whitespace-pre-line text-sm leading-relaxed text-gray-600">{body}</p>
    </div>
  ) : null;

const SiteAboutPage: React.FC = () => {
  const { config } = useSchoolSite();
  return (
    <div className="mx-auto max-w-4xl px-4 py-14">
      <h1 className="mb-6 text-3xl font-bold text-gray-900">About {config?.school?.name}</h1>
      <div className="space-y-6">
        {config?.about_content ? (
          <p className="whitespace-pre-line text-base leading-relaxed text-gray-700">{config.about_content}</p>
        ) : (
          <p className="text-gray-500">Information about the school will be available soon.</p>
        )}
        <Block title="Our Mission" body={config?.mission} />
        <Block title="Our Vision" body={config?.vision} />
      </div>
    </div>
  );
};

export default SiteAboutPage;
