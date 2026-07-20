import React from 'react';
import { Outlet, useParams, Link, NavLink } from 'react-router-dom';
import { SchoolSiteProvider, useSchoolSite } from '@hooks/useSchoolSite';

/**
 * Public per-school website shell. Themed with the school's own colors/logo —
 * deliberately does NOT use the admin AppLayout/Sidebar/Navbar/ChatWidget.
 *
 * Used in path mode (/site/:slug). For custom domains, HostSiteGate renders the
 * same provider + chrome with basePath = ''.
 */

const NAV: Array<{ label: string; path: string; section?: string }> = [
  { label: 'Home', path: '/' },
  { label: 'About', path: '/about', section: 'about' },
  { label: 'Academics', path: '/academics', section: 'academics' },
  { label: 'Faculty', path: '/faculty', section: 'faculty' },
  { label: 'Gallery', path: '/gallery', section: 'gallery' },
  { label: 'Notices', path: '/notices', section: 'notices' },
  { label: 'Events', path: '/events', section: 'events' },
  { label: 'Contact', path: '/contact', section: 'contact' },
];

const SiteHeader: React.FC = () => {
  const { config, siteHref, isSectionEnabled } = useSchoolSite();
  const [open, setOpen] = React.useState(false);
  const school = config?.school;
  const items = NAV.filter((n) => !n.section || isSectionEnabled(n.section));

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to={siteHref('/')} className="flex items-center gap-3">
          {school?.logo_url ? (
            <img src={school.logo_url} alt={school.name} className="h-10 w-10 rounded object-contain" />
          ) : (
            <div
              className="flex h-10 w-10 items-center justify-center rounded font-bold text-white"
              style={{ background: 'var(--site-primary)' }}
            >
              {school?.name?.[0] ?? 'S'}
            </div>
          )}
          <div className="leading-tight">
            <p className="text-sm font-semibold text-gray-900">{school?.name ?? 'School'}</p>
            {school?.tagline && <p className="text-[11px] text-gray-500">{school.tagline}</p>}
          </div>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {items.map((item) => (
            <NavLink
              key={item.path}
              to={siteHref(item.path)}
              end={item.path === '/'}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? 'text-[color:var(--site-primary)]' : 'text-gray-600 hover:text-gray-900'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
          {isSectionEnabled('admissions') && school && (
            <Link
              to={`/admissions/apply/${school.slug}`}
              className="ml-2 rounded-md px-4 py-2 text-sm font-semibold text-white shadow-sm"
              style={{ background: 'var(--site-primary)' }}
            >
              Apply Now
            </Link>
          )}
        </nav>

        <button
          className="rounded p-2 text-gray-600 md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          <span className="block h-0.5 w-6 bg-current" />
          <span className="mt-1 block h-0.5 w-6 bg-current" />
          <span className="mt-1 block h-0.5 w-6 bg-current" />
        </button>
      </div>

      {open && (
        <div className="border-t border-gray-100 bg-white md:hidden">
          {items.map((item) => (
            <NavLink
              key={item.path}
              to={siteHref(item.path)}
              end={item.path === '/'}
              onClick={() => setOpen(false)}
              className="block px-4 py-3 text-sm text-gray-700 hover:bg-gray-50"
            >
              {item.label}
            </NavLink>
          ))}
          {isSectionEnabled('admissions') && school && (
            <Link
              to={`/admissions/apply/${school.slug}`}
              onClick={() => setOpen(false)}
              className="block px-4 py-3 text-sm font-semibold"
              style={{ color: 'var(--site-primary)' }}
            >
              Apply Now →
            </Link>
          )}
        </div>
      )}
    </header>
  );
};

const SiteFooter: React.FC = () => {
  const { config, siteHref, isSectionEnabled } = useSchoolSite();
  const school = config?.school;
  const social = config?.social_links ?? {};
  return (
    <footer className="mt-16 bg-gray-900 text-gray-300">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 md:grid-cols-3">
        <div>
          <p className="text-lg font-semibold text-white">{school?.name}</p>
          {school?.tagline && <p className="mt-1 text-sm text-gray-400">{school.tagline}</p>}
          {school?.affiliation_board && (
            <p className="mt-2 text-xs text-gray-500">Affiliated to {school.affiliation_board}</p>
          )}
        </div>
        <div>
          <p className="mb-2 text-sm font-semibold text-white">Quick Links</p>
          <ul className="space-y-1 text-sm">
            {NAV.filter((n) => !n.section || isSectionEnabled(n.section)).map((n) => (
              <li key={n.path}>
                <Link to={siteHref(n.path)} className="hover:text-white">
                  {n.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 text-sm font-semibold text-white">Contact</p>
          {config?.contact_phone && <p className="text-sm">📞 {config.contact_phone}</p>}
          {config?.contact_email && <p className="text-sm">✉️ {config.contact_email}</p>}
          {config?.contact_address && <p className="mt-1 text-sm text-gray-400">{config.contact_address}</p>}
          <div className="mt-3 flex gap-3 text-sm">
            {Object.entries(social).map(([k, v]) =>
              v ? (
                <a key={k} href={v} target="_blank" rel="noreferrer" className="capitalize hover:text-white">
                  {k}
                </a>
              ) : null
            )}
          </div>
        </div>
      </div>
      <div className="border-t border-gray-800 py-4 text-center text-xs text-gray-500">
        © {new Date().getFullYear()} {school?.name}. All rights reserved.
      </div>
    </footer>
  );
};

/** Inner chrome shared by path mode and host mode. */
export const PublicSiteChrome: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const { isLoading, error, config } = useSchoolSite();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-[color:var(--site-primary)]" />
      </div>
    );
  }

  if (error || !config) {
    return (
      <div className="flex h-screen flex-col items-center justify-center px-4 text-center">
        <h1 className="text-2xl font-semibold text-gray-800">Website not available</h1>
        <p className="mt-2 text-gray-500">
          This school website is not published yet, or the address is incorrect.
        </p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">{children ?? <Outlet />}</main>
      <SiteFooter />
    </div>
  );
};

/** Path-mode layout: /site/:slug/* */
const PublicSiteLayout: React.FC = () => {
  const { slug = '' } = useParams();
  return (
    <SchoolSiteProvider slug={slug} basePath={`/site/${slug}`}>
      <PublicSiteChrome />
    </SchoolSiteProvider>
  );
};

export default PublicSiteLayout;
