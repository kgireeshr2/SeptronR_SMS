import { QueryClient } from '@tanstack/react-query';

/**
 * The single app-wide React Query client.
 *
 * Exported from its own module (rather than created inline in main.tsx) so that
 * non-component code — the auth store, school-switch handlers — can clear the
 * cache when the active school changes. This is critical for multi-tenant
 * isolation: cached data from one school must never survive a switch to another.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      onError: (error: unknown) => {
        const msg = (error as { message?: string })?.message || 'An error occurred';
        console.error('[Mutation Error]', msg);
      },
    },
  },
});
