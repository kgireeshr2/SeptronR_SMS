import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { websiteApi } from '@api/website';
import { useSchoolSite } from '@hooks/useSchoolSite';

const Section: React.FC<{ title?: string; subtitle?: string; children: React.ReactNode; className?: string }> = ({
  title,
  subtitle,
  children,
  className = '',
}) => (
  <section className={`mx-auto max-w-6xl px-4 py-14 ${className}`}>
    {title && (
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-gray-900 md:text-3xl">{title}</h2>
        {subtitle && <p className="mx-auto mt-2 max-w-2xl text-sm text-gray-500">{subtitle}</p>}
        <div className="mx-auto mt-3 h-1 w-16 rounded" style={{ background: 'var(--site-primary)' }} />
      </div>
    )}
    {children}
  </section>
);

const SiteHomePage: React.FC = () => {
  const { config, slug, siteHref, isSectionEnabled } = useSchoolSite();
  const school = config?.school;

  const q = (key: string, section: string, fn: () => Promise<any>) =>
    useQuery({ queryKey: [key, slug], enabled: !!slug && isSectionEnabled(section), queryFn: fn });

  const notices = (q('site-notices', 'notices', () => websiteApi.listNotices(slug)).data as any[]) ?? [];
  const events = (q('site-events', 'events', () => websiteApi.listEvents(slug)).data as any[]) ?? [];
  const academics = (q('site-academics', 'academics', () => websiteApi.listContent(slug, 'academics')).data as any[]) ?? [];
  const faculty = (q('site-faculty', 'faculty', () => websiteApi.listContent(slug, 'faculty')).data as any[]) ?? [];
  const testimonials = (q('site-testimonials', 'testimonials', () => websiteApi.listContent(slug, 'testimonials')).data as any[]) ?? [];
  const gallery = (q('site-gallery', 'gallery', () => websiteApi.listGallery(slug)).data as any[]) ?? [];
  const galleryImages = gallery.flatMap((a: any) => a.images ?? []).slice(0, 8);

  const facts = [
    ['Established', school?.established_year],
    ['Board', school?.affiliation_board],
    ['City', school?.city],
    ['State', school?.state],
  ].filter(([, v]) => v) as [string, string][];

  return (
    <div>
      {/* Hero */}
      <section
        className="relative bg-cover bg-center"
        style={{
          backgroundImage: config?.hero_image_url
            ? `linear-gradient(rgba(0,0,0,0.55),rgba(0,0,0,0.55)), url(${config.hero_image_url})`
            : 'linear-gradient(135deg, var(--site-primary), var(--site-secondary))',
        }}
      >
        <div className="mx-auto flex max-w-4xl flex-col items-center px-4 py-24 text-center text-white md:py-32">
          <h1 className="text-3xl font-bold leading-tight md:text-5xl">{config?.hero_title || school?.name}</h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-white/90 md:text-lg">
            {config?.hero_subtitle || school?.tagline || 'Welcome to our school'}
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            {isSectionEnabled('admissions') && school && (
              <Link to={`/admissions/apply/${school.slug}`} className="rounded-md bg-white px-6 py-3 text-sm font-semibold text-gray-900 shadow transition hover:bg-gray-100">
                Apply for Admission
              </Link>
            )}
            {isSectionEnabled('enquiry') && (
              <Link to={siteHref('/enquiry')} className="rounded-md border border-white/70 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10">
                Make an Enquiry
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Stats strip */}
      {facts.length > 0 && (
        <div style={{ background: 'var(--site-primary)' }}>
          <div className="mx-auto grid max-w-5xl grid-cols-2 gap-6 px-4 py-8 md:grid-cols-4">
            {facts.map(([label, v]) => (
              <div key={label} className="text-center text-white">
                <p className="text-xl font-bold">{v}</p>
                <p className="text-xs uppercase tracking-wide text-white/70">{label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* About teaser */}
      {isSectionEnabled('about') && config?.about_content && (
        <Section title={`About ${school?.name ?? ''}`}>
          <p className="mx-auto max-w-3xl text-center leading-relaxed text-gray-600">
            {config.about_content.slice(0, 360)}
            {config.about_content.length > 360 ? '…' : ''}
          </p>
          <div className="mt-6 text-center">
            <Link to={siteHref('/about')} className="text-sm font-semibold" style={{ color: 'var(--site-primary)' }}>
              Read more →
            </Link>
          </div>
        </Section>
      )}

      {/* Academics */}
      {isSectionEnabled('academics') && academics.length > 0 && (
        <div className="bg-gray-50">
          <Section title="Academic Programs" subtitle="A continuous learning journey at every stage.">
            <div className="grid gap-6 md:grid-cols-3">
              {academics.slice(0, 3).map((p) => (
                <div key={p.id} className="overflow-hidden rounded-xl border border-gray-200 bg-white">
                  {p.image_url && <img src={p.image_url} alt={p.title} className="h-40 w-full object-cover" loading="lazy" />}
                  <div className="p-5">
                    <h3 className="font-semibold text-gray-900">{p.title}</h3>
                    {p.subtitle && <p className="text-sm font-medium" style={{ color: 'var(--site-primary)' }}>{p.subtitle}</p>}
                    {p.description && <p className="mt-2 text-sm text-gray-600">{p.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          </Section>
        </div>
      )}

      {/* Notices + Events */}
      {(isSectionEnabled('notices') || isSectionEnabled('events')) && (
        <Section>
          <div className="grid gap-10 md:grid-cols-2">
            {isSectionEnabled('notices') && (
              <div>
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900">Latest Notices</h2>
                  <Link to={siteHref('/notices')} className="text-sm" style={{ color: 'var(--site-primary)' }}>View all →</Link>
                </div>
                <ul className="space-y-3">
                  {notices.slice(0, 5).map((n) => (
                    <li key={n.id} className="rounded-lg border border-gray-200 p-3 transition hover:shadow-sm">
                      <Link to={siteHref(`/notices/${n.id}`)} className="font-medium text-gray-800 hover:underline">
                        {n.is_pinned && '📌 '}{n.title}
                      </Link>
                      <p className="mt-0.5 text-xs uppercase tracking-wide text-gray-400">{n.category}</p>
                    </li>
                  ))}
                  {notices.length === 0 && <p className="text-sm text-gray-400">No notices yet.</p>}
                </ul>
              </div>
            )}
            {isSectionEnabled('events') && (
              <div>
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900">Upcoming Events</h2>
                  <Link to={siteHref('/events')} className="text-sm" style={{ color: 'var(--site-primary)' }}>View all →</Link>
                </div>
                <ul className="space-y-3">
                  {events.slice(0, 5).map((e) => (
                    <li key={e.id} className="flex gap-3 rounded-lg border border-gray-200 p-3">
                      {e.image_url && <img src={e.image_url} alt="" className="h-14 w-14 shrink-0 rounded object-cover" loading="lazy" />}
                      <div>
                        <p className="font-medium text-gray-800">{e.title}</p>
                        {e.event_date && (
                          <p className="mt-0.5 text-xs text-gray-400">
                            {new Date(e.event_date).toLocaleDateString()} {e.location ? `· ${e.location}` : ''}
                          </p>
                        )}
                      </div>
                    </li>
                  ))}
                  {events.length === 0 && <p className="text-sm text-gray-400">No events yet.</p>}
                </ul>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Gallery preview */}
      {isSectionEnabled('gallery') && galleryImages.length > 0 && (
        <div className="bg-gray-50">
          <Section title="Gallery" subtitle="A glimpse of life at our school.">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {galleryImages.map((img: any) => (
                <div key={img.id} className="aspect-square overflow-hidden rounded-lg bg-gray-100">
                  <img src={img.image_url} alt={img.caption ?? ''} loading="lazy" className="h-full w-full object-cover transition hover:scale-105" />
                </div>
              ))}
            </div>
            <div className="mt-6 text-center">
              <Link to={siteHref('/gallery')} className="text-sm font-semibold" style={{ color: 'var(--site-primary)' }}>
                View full gallery →
              </Link>
            </div>
          </Section>
        </div>
      )}

      {/* Faculty preview */}
      {isSectionEnabled('faculty') && faculty.length > 0 && (
        <Section title="Our Faculty" subtitle="Experienced educators dedicated to your child.">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {faculty.slice(0, 4).map((f) => (
              <div key={f.id} className="rounded-xl border border-gray-200 bg-white p-5 text-center">
                {f.image_url ? (
                  <img src={f.image_url} alt={f.title} className="mx-auto h-24 w-24 rounded-full object-cover" loading="lazy" />
                ) : (
                  <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full text-2xl font-bold text-white" style={{ background: 'var(--site-primary)' }}>
                    {f.title?.[0]}
                  </div>
                )}
                <h3 className="mt-3 font-semibold text-gray-900">{f.title}</h3>
                {f.subtitle && <p className="text-sm" style={{ color: 'var(--site-primary)' }}>{f.subtitle}</p>}
                {f.description && <p className="mt-1 text-xs text-gray-500">{f.description}</p>}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Testimonials */}
      {isSectionEnabled('testimonials') && testimonials.length > 0 && (
        <div className="bg-gray-50">
          <Section title="What Parents & Students Say">
            <div className="grid gap-5 md:grid-cols-3">
              {testimonials.slice(0, 3).map((t) => (
                <blockquote key={t.id} className="rounded-xl border border-gray-200 bg-white p-6">
                  <p className="text-sm italic leading-relaxed text-gray-700">“{t.description}”</p>
                  <div className="mt-4 flex items-center gap-3">
                    {t.image_url && <img src={t.image_url} alt={t.title} className="h-10 w-10 rounded-full object-cover" />}
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{t.title}</p>
                      {t.subtitle && <p className="text-xs text-gray-500">{t.subtitle}</p>}
                    </div>
                  </div>
                </blockquote>
              ))}
            </div>
          </Section>
        </div>
      )}

      {/* CTA band */}
      {isSectionEnabled('admissions') && school && (
        <div style={{ background: 'var(--site-primary)' }}>
          <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 px-4 py-12 text-center md:flex-row md:text-left">
            <div className="text-white">
              <h2 className="text-2xl font-bold">Admissions Open</h2>
              <p className="mt-1 text-white/85">Join the Greenwood family. Applications are now being accepted.</p>
            </div>
            <Link to={`/admissions/apply/${school.slug}`} className="rounded-md bg-white px-6 py-3 text-sm font-semibold text-gray-900 shadow">
              Apply Now
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default SiteHomePage;
