import React from 'react';
import EnquiryForm from '@components/public/EnquiryForm';
import { useSchoolSite } from '@hooks/useSchoolSite';

const SiteContactPage: React.FC = () => {
  const { config } = useSchoolSite();
  return (
    <div className="mx-auto max-w-5xl px-4 py-14">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">Contact Us</h1>
      <div className="grid gap-8 md:grid-cols-2">
        <div className="space-y-4">
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <h3 className="mb-3 text-lg font-semibold" style={{ color: 'var(--site-primary)' }}>
              Get in touch
            </h3>
            {config?.contact_phone && <p className="text-sm text-gray-700">📞 {config.contact_phone}</p>}
            {config?.contact_email && <p className="mt-1 text-sm text-gray-700">✉️ {config.contact_email}</p>}
            {config?.contact_address && (
              <p className="mt-2 whitespace-pre-line text-sm text-gray-600">📍 {config.contact_address}</p>
            )}
          </div>
          {config?.map_embed_url && (
            <iframe
              title="map"
              src={config.map_embed_url}
              className="h-64 w-full rounded-xl border border-gray-200"
              loading="lazy"
            />
          )}
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-3 text-lg font-semibold" style={{ color: 'var(--site-primary)' }}>
            Send a message
          </h3>
          <EnquiryForm />
        </div>
      </div>
    </div>
  );
};

export default SiteContactPage;
