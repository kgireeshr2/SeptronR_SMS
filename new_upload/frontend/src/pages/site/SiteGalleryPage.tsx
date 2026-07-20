import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { websiteApi } from '@api/website';
import { useSchoolSite } from '@hooks/useSchoolSite';

interface Img {
  id: string;
  image_url: string;
  caption?: string | null;
}
interface Album {
  id: string | null;
  title: string;
  description?: string | null;
  images: Img[];
}

const SiteGalleryPage: React.FC = () => {
  const { slug } = useSchoolSite();
  const [lightbox, setLightbox] = React.useState<Img | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ['site-gallery', slug],
    enabled: !!slug,
    queryFn: () => websiteApi.listGallery(slug),
  });
  const albums = (data as Album[]) ?? [];

  return (
    <div className="mx-auto max-w-6xl px-4 py-14">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">Gallery</h1>
      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
      {!isLoading && albums.length === 0 && <p className="text-gray-500">No photos yet.</p>}

      {albums.map((album) => (
        <section key={album.id ?? album.title} className="mb-12">
          <h2 className="mb-1 text-xl font-semibold text-gray-800">{album.title}</h2>
          {album.description && <p className="mb-4 text-sm text-gray-500">{album.description}</p>}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {album.images.map((img) => (
              <button
                key={img.id}
                onClick={() => setLightbox(img)}
                className="group relative aspect-square overflow-hidden rounded-lg bg-gray-100"
              >
                <img
                  src={img.image_url}
                  alt={img.caption ?? ''}
                  loading="lazy"
                  className="h-full w-full object-cover transition-transform group-hover:scale-105"
                />
              </button>
            ))}
          </div>
        </section>
      ))}

      {lightbox && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={() => setLightbox(null)}
        >
          <div className="max-h-full max-w-4xl" onClick={(e) => e.stopPropagation()}>
            <img src={lightbox.image_url} alt={lightbox.caption ?? ''} className="max-h-[80vh] rounded-lg" />
            {lightbox.caption && <p className="mt-2 text-center text-sm text-white/90">{lightbox.caption}</p>}
          </div>
          <button className="absolute right-4 top-4 text-3xl text-white" onClick={() => setLightbox(null)}>
            ×
          </button>
        </div>
      )}
    </div>
  );
};

export default SiteGalleryPage;
