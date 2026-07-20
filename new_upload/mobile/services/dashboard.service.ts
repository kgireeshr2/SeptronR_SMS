import api from './api';
import { DashboardStats } from '@/types';

export const dashboardService = {
  /**
   * The backend has no single /dashboard endpoint.
   * Build stats from individual lightweight queries.
   */
  getStats: async (): Promise<DashboardStats> => {
    const results = await Promise.allSettled([
      api.get('/staff?page=1&page_size=1'),
      api.get('/fees/structures?page=1&page_size=1'),
    ]);

    // Each settled result: value is either raw array or unwrapped data
    const staffRes  = results[0].status === 'fulfilled' ? results[0].value.data : null;
    const feesRes   = results[1].status === 'fulfilled' ? results[1].value.data : null;

    // staff endpoint returns raw array
    const staffArray  = Array.isArray(staffRes)  ? staffRes  : (staffRes?.items ?? []);
    const feesArray   = Array.isArray(feesRes)   ? feesRes   : (feesRes?.items ?? []);

    return {
      total_staff: staffArray.length > 0 ? staffArray.length : undefined,
    };
  },
};
