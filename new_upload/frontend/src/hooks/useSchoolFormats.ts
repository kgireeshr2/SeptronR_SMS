import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { schoolsApi } from '@api/schools';
import { useAuthStore } from '@store/authStore';
import { setActiveDateFormat } from '@utils/formatters';

const unwrap = (res: any) => res?.data ?? res;

/**
 * Loads the active school's general settings once (date format, etc.) and
 * publishes the configured date format app-wide via setActiveDateFormat, so
 * formatDate()/formatDateTime() everywhere render in the school's chosen format.
 *
 * Shares the React Query cache key with the Settings page (`['school-settings']`),
 * which is cleared on school switch/logout — so switching schools re-derives the
 * format for the newly active school.
 */
export const useSchoolFormats = (): void => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const schoolId = useAuthStore((s) => s.schoolInfo?.id);

  const { data } = useQuery({
    queryKey: ['school-settings'],
    queryFn: async () => unwrap(await schoolsApi.getSettings()),
    enabled: isAuthenticated && !!schoolId,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    const fmt = (data as any)?.general?.date_format;
    if (fmt) setActiveDateFormat(fmt);
  }, [data]);
};
