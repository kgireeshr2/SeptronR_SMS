import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AcademicYear {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
}

interface AcademicYearState {
  selectedYear: AcademicYear | null;
  years: AcademicYear[];
  setSelectedYear: (year: AcademicYear) => void;
  setYears: (years: AcademicYear[]) => void;
  reset: () => void;
}

export const useAcademicYearStore = create<AcademicYearState>()(
  persist(
    (set) => ({
      selectedYear: null,
      years: [],
      setSelectedYear: (year) => set({ selectedYear: year }),
      setYears: (years) => set({ years }),
      // Cleared whenever the active school changes — the selected year belongs
      // to a specific school and must not carry over to another.
      reset: () => set({ selectedYear: null, years: [] }),
    }),
    { name: 'sms-academic-year' }
  )
);
