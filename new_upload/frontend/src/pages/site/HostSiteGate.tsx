import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { websiteApi } from '@api/website';
import { SchoolSiteProvider } from '@hooks/useSchoolSite';
import { PublicSiteChrome } from '@components/public/PublicSiteLayout';
import SiteHomePage from './SiteHomePage';
import SiteAboutPage from './SiteAboutPage';
import SiteGalleryPage from './SiteGalleryPage';
import SiteNoticesPage from './SiteNoticesPage';
import SiteNoticeDetailPage from './SiteNoticeDetailPage';
import SiteEventsPage from './SiteEventsPage';
import SiteEnquiryPage from './SiteEnquiryPage';
import SiteContactPage from './SiteContactPage';
import SiteSectionPage from './SiteSectionPage';

/**
 * Entry point when the app is served on a recognized custom domain (host mode).
 * Resolves the school from window.location.hostname, then renders the public
 * site with un-prefixed section routes (basePath = '').
 */
const HostSiteGate: React.FC = () => {
  const host = window.location.hostname;
  const { data, isLoading, error } = useQuery({
    queryKey: ['resolve-host', host],
    queryFn: () => websiteApi.resolveByHost(host),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-gray-600" />
      </div>
    );
  }

  if (error || !data?.slug) {
    return (
      <div className="flex h-screen flex-col items-center justify-center px-4 text-center">
        <h1 className="text-2xl font-semibold text-gray-800">Site not found</h1>
        <p className="mt-2 text-gray-500">This domain is not linked to a published school website.</p>
      </div>
    );
  }

  return (
    <SchoolSiteProvider slug={data.slug} basePath="">
      <Routes>
        <Route
          element={
            <PublicSiteChrome />
          }
        >
          <Route index element={<SiteHomePage />} />
          <Route path="about" element={<SiteAboutPage />} />
          <Route path="academics" element={<SiteSectionPage />} />
          <Route path="faculty" element={<SiteSectionPage />} />
          <Route path="achievements" element={<SiteSectionPage />} />
          <Route path="facilities" element={<SiteSectionPage />} />
          <Route path="downloads" element={<SiteSectionPage />} />
          <Route path="testimonials" element={<SiteSectionPage />} />
          <Route path="gallery" element={<SiteGalleryPage />} />
          <Route path="notices" element={<SiteNoticesPage />} />
          <Route path="notices/:noticeId" element={<SiteNoticeDetailPage />} />
          <Route path="events" element={<SiteEventsPage />} />
          <Route path="enquiry" element={<SiteEnquiryPage />} />
          <Route path="contact" element={<SiteContactPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </SchoolSiteProvider>
  );
};

export default HostSiteGate;
