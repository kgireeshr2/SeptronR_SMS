import React, { createContext, useContext, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { websiteApi, WebsiteConfig } from '@api/website';

interface SchoolSiteContextValue {
  slug: string;
  basePath: string; // '' on a custom domain, '/site/:slug' in path mode
  config: WebsiteConfig | null;
  isLoading: boolean;
  error: unknown;
  isSectionEnabled: (key: string) => boolean;
  siteHref: (path?: string) => string;
}

const SchoolSiteContext = createContext<SchoolSiteContextValue | null>(null);

function setMeta(name: string, content: string, attr: 'name' | 'property' = 'name') {
  if (!content) return;
  let el = document.head.querySelector(`meta[${attr}="${name}"]`) as HTMLMetaElement | null;
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, name);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

export const SchoolSiteProvider: React.FC<{
  slug: string;
  basePath: string;
  children: React.ReactNode;
}> = ({ slug, basePath, children }) => {
  const query = useQuery({
    queryKey: ['site-config', slug],
    enabled: !!slug,
    queryFn: () => websiteApi.getSite(slug),
    retry: false,
  });

  const config = (query.data as WebsiteConfig) ?? null;

  // SEO + theme color meta + favicon, applied imperatively (SPA, no SSR).
  useEffect(() => {
    if (!config) return;
    const name = config.school?.name ?? 'School';
    document.title = config.seo_title || name;
    setMeta('description', config.seo_description || config.hero_subtitle || `${name} — official website`);
    setMeta('og:title', config.seo_title || name, 'property');
    setMeta('og:description', config.seo_description || config.hero_subtitle || '', 'property');
    if (config.school?.logo_url) setMeta('og:image', config.school.logo_url, 'property');
    setMeta('theme-color', config.theme_color || '#1e40af');
    if (config.school?.logo_url) {
      let link = document.head.querySelector("link[rel='icon']") as HTMLLinkElement | null;
      if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
      }
      link.href = config.school.logo_url;
    }
  }, [config]);

  const value: SchoolSiteContextValue = {
    slug,
    basePath,
    config,
    isLoading: query.isLoading,
    error: query.error,
    isSectionEnabled: (key) => !!config?.sections?.[key],
    siteHref: (path = '') => {
      const clean = path.startsWith('/') ? path : `/${path}`;
      const joined = `${basePath}${clean === '/' ? '' : clean}`;
      return joined || '/';
    },
  };

  return (
    <SchoolSiteContext.Provider value={value}>
      {/* Theme scope: sections consume `bg-[var(--site-primary)]` etc. */}
      <div
        className="public-site min-h-screen bg-white text-gray-800"
        style={
          {
            '--site-primary': config?.theme_color || '#1e40af',
            '--site-secondary': config?.secondary_color || config?.theme_color || '#1e3a8a',
          } as React.CSSProperties
        }
      >
        {children}
      </div>
    </SchoolSiteContext.Provider>
  );
};

export function useSchoolSite(): SchoolSiteContextValue {
  const ctx = useContext(SchoolSiteContext);
  if (!ctx) throw new Error('useSchoolSite must be used within a SchoolSiteProvider');
  return ctx;
}
