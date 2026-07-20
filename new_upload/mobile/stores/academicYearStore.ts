import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '@/services/api';

interface AcademicYear {
  id: string;       // UUID
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  is_locked?: boolean;
  school_id?: string;
}

interface AcademicYearState {
  currentYear:    AcademicYear | null;
  allYears:       AcademicYear[];
  selectedYearId: string | null;

  fetchYears:  () => Promise<void>;
  selectYear:  (id: string) => void;
}

export const useAcademicYearStore = create<AcademicYearState>()(
  persist(
    (set, get) => ({
      currentYear:    null,
      allYears:       [],
      selectedYearId: null,

      fetchYears: async () => {
        try {
          // Envelope interceptor unwraps {success, data} → data (array)
          const { data } = await api.get<AcademicYear[]>('/academic-years');
          const years: AcademicYear[] = Array.isArray(data) ? data : [];
          const current = years.find((y) => y.is_current) ?? years[0] ?? null;
          set({
            allYears:       years,
            currentYear:    current,
            selectedYearId: get().selectedYearId ?? current?.id ?? null,
          });
        } catch (_) {}
      },

      selectYear: (id) => set({ selectedYearId: id }),
    }),
    {
      name:    'academic-year-store',
      storage: createJSONStorage(() => AsyncStorage),
    },
  ),
);
