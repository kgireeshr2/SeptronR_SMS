import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Download, Trash2, BookOpen, Settings, PlusCircle, X, ChevronDown, ChevronUp } from 'lucide-react';
import { PageHeader } from '@components/shared/PageHeader';
import { academicYearsApi } from '@api/academicYears';
import { classesApi, subjectsApi, timetableApi } from '@api/classes';
import { staffApi } from '@api/staff';
import { useAcademicYearStore } from '@store/academicYearStore';

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

// Strip seconds from "HH:MM:SS" → "HH:MM"
function fmtTime(t: string | null | undefined): string {
  if (!t) return '';
  return String(t).slice(0, 5);
}

const COLORS = [
  'bg-blue-50 border-blue-200 text-blue-800',
  'bg-violet-50 border-violet-200 text-violet-800',
  'bg-emerald-50 border-emerald-200 text-emerald-800',
  'bg-amber-50 border-amber-200 text-amber-800',
  'bg-pink-50 border-pink-200 text-pink-800',
  'bg-cyan-50 border-cyan-200 text-cyan-800',
  'bg-orange-50 border-orange-200 text-orange-800',
  'bg-rose-50 border-rose-200 text-rose-800',
];

const getSubjectColor = (subjectId: string, subjectIds: string[]) => {
  const idx = subjectIds.indexOf(subjectId);
  return COLORS[idx % COLORS.length] ?? COLORS[0];
};

// ── Period configuration ─────────────────────────────────────────────────────

interface PeriodDef {
  number: number;
  label: string;
  start_time: string;
  end_time: string;
}

const DEFAULT_PERIODS: PeriodDef[] = [
  { number: 1, label: 'Period 1', start_time: '09:00', end_time: '09:40' },
  { number: 2, label: 'Period 2', start_time: '09:45', end_time: '10:25' },
  { number: 3, label: 'Period 3', start_time: '10:30', end_time: '11:10' },
  { number: 4, label: 'Period 4', start_time: '11:15', end_time: '11:55' },
  { number: 5, label: 'Period 5', start_time: '12:30', end_time: '13:10' },
  { number: 6, label: 'Period 6', start_time: '13:15', end_time: '13:55' },
  { number: 7, label: 'Period 7', start_time: '14:00', end_time: '14:40' },
  { number: 8, label: 'Period 8', start_time: '14:45', end_time: '15:25' },
];

function loadPeriodConfig(sectionId: string): PeriodDef[] {
  try {
    const raw = localStorage.getItem(`tt_periods_${sectionId}`);
    if (raw) return JSON.parse(raw) as PeriodDef[];
  } catch {}
  return DEFAULT_PERIODS;
}

function savePeriodConfig(sectionId: string, periods: PeriodDef[]) {
  localStorage.setItem(`tt_periods_${sectionId}`, JSON.stringify(periods));
}

const EMPTY_SLOT = {
  subject_id: '',
  teacher_id: '',
  day_of_week: 1,
  period_number: 1,
  start_time: '09:00',
  end_time: '09:40',
};

const unwrap = (res: any) => res?.data ?? res;

const TimetablePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { selectedYear, setSelectedYear, setYears } = useAcademicYearStore();

  const [selectedClassId, setSelectedClassId] = React.useState('');
  const [selectedSectionId, setSelectedSectionId] = React.useState('');
  const [slot, setSlot] = React.useState(EMPTY_SLOT);
  const [highlightDay, setHighlightDay] = React.useState<number | null>(null);
  const [highlightPeriod, setHighlightPeriod] = React.useState<number | null>(null);
  const [periodConfig, setPeriodConfig] = React.useState<PeriodDef[]>(DEFAULT_PERIODS);
  const [showPeriodConfig, setShowPeriodConfig] = React.useState(false);
  const [draftPeriods, setDraftPeriods] = React.useState<PeriodDef[]>(DEFAULT_PERIODS);

  // Load period config from localStorage when section changes
  React.useEffect(() => {
    if (selectedSectionId) {
      const cfg = loadPeriodConfig(selectedSectionId);
      setPeriodConfig(cfg);
      setDraftPeriods(cfg);
    }
  }, [selectedSectionId]);

  const yearsQuery = useQuery({
    queryKey: ['academic-years-select-timetable'],
    queryFn: async () => {
      const data = unwrap(await academicYearsApi.list());
      const items = Array.isArray(data) ? data : (data?.items ?? []);
      setYears(
        items.map((y: any) => ({
          id: y.id,
          name: y.name,
          startDate: y.start_date,
          endDate: y.end_date,
          isCurrent: y.is_current,
        }))
      );
      if (!selectedYear && items.length > 0) {
        const current = items.find((y: any) => y.is_current) || items[0];
        setSelectedYear({
          id: current.id,
          name: current.name,
          startDate: current.start_date,
          endDate: current.end_date,
          isCurrent: current.is_current,
        });
      }
      return items;
    },
  });

  const classesQuery = useQuery({
    queryKey: ['tt-classes', selectedYear?.id],
    enabled: !!selectedYear?.id,
    queryFn: async () => {
      const data = unwrap(await classesApi.list(selectedYear!.id));
      const items = Array.isArray(data) ? data : (data?.items ?? []);
      if (!selectedClassId && items.length > 0) setSelectedClassId(items[0].id);
      return items;
    },
  });

  const classDetailQuery = useQuery({
    queryKey: ['tt-class-detail', selectedClassId],
    enabled: !!selectedClassId,
    queryFn: async () => {
      const detail = unwrap(await classesApi.get(selectedClassId));
      const sections = detail?.sections ?? [];
      if (!selectedSectionId && sections.length > 0) setSelectedSectionId(sections[0].id);
      return detail;
    },
  });

  const subjectsQuery = useQuery({
    queryKey: ['tt-subjects'],
    queryFn: async () => {
      const data = unwrap(await subjectsApi.list());
      return (Array.isArray(data) ? data : (data?.items ?? [])).filter((x: any) => x.is_active !== false);
    },
  });

  const staffQuery = useQuery({
    queryKey: ['tt-staff'],
    queryFn: async () => {
      const data = unwrap(await staffApi.listStaff({ is_active: true, limit: 200 }));
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  const gridQuery = useQuery({
    queryKey: ['tt-grid', selectedSectionId, selectedYear?.id],
    enabled: !!selectedSectionId && !!selectedYear?.id,
    queryFn: async () => unwrap(await timetableApi.getSection(selectedSectionId, selectedYear!.id)),
  });

  const upsertMutation = useMutation({
    mutationFn: () =>
      timetableApi.upsertSlot(selectedSectionId, selectedYear!.id, {
        ...slot,
        teacher_id: slot.teacher_id || null,
      }),
    onSuccess: () => {
      toast.success('Timetable slot saved');
      queryClient.invalidateQueries({ queryKey: ['tt-grid', selectedSectionId, selectedYear?.id] });
      setSlot(EMPTY_SLOT);
      setHighlightDay(null);
      setHighlightPeriod(null);
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? err?.detail ?? err?.message ?? 'Failed to save slot';
      toast.error(msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => timetableApi.removeSlot(id),
    onSuccess: () => {
      toast.success('Slot deleted');
      queryClient.invalidateQueries({ queryKey: ['tt-grid', selectedSectionId, selectedYear?.id] });
    },
    onError: () => toast.error('Failed to delete slot'),
  });

  const sections = classDetailQuery.data?.sections ?? [];
  const classes = classesQuery.data ?? [];
  const subjects = subjectsQuery.data ?? [];
  const staff = staffQuery.data ?? [];
  const grid = gridQuery.data?.grid ?? {};
  // Grid always shows ALL configured periods (not just those with data)
  const allPeriods: number[] = periodConfig.map((p) => p.number);

  const allSubjectIds = React.useMemo(() => {
    const ids: string[] = [];
    Object.values(grid).forEach((daySlots: any) => {
      Object.values(daySlots).forEach((s: any) => {
        if (s?.subject_id && !ids.includes(s.subject_id)) ids.push(s.subject_id);
      });
    });
    return ids;
  }, [grid]);

  const handleCellClick = (dayIndex: number, period: number) => {
    const existing = grid?.[dayIndex]?.[period];
    if (existing) return;
    const pDef = periodConfig.find((p) => p.number === period);
    setSlot((p) => ({
      ...p,
      day_of_week: dayIndex,
      period_number: period,
      start_time: pDef?.start_time ?? p.start_time,
      end_time: pDef?.end_time ?? p.end_time,
    }));
    setHighlightDay(dayIndex);
    setHighlightPeriod(period);
  };

  // When period select changes, auto-fill time from period config
  const handlePeriodSelect = (num: number) => {
    const pDef = periodConfig.find((p) => p.number === num);
    setSlot((p) => ({
      ...p,
      period_number: num,
      start_time: pDef?.start_time ?? p.start_time,
      end_time: pDef?.end_time ?? p.end_time,
    }));
  };

  const savePeriodDraft = () => {
    if (draftPeriods.length === 0) return toast.error('Need at least one period');
    for (const p of draftPeriods) {
      if (!p.start_time || !p.end_time) return toast.error(`Period ${p.number}: set both start and end time`);
      if (p.start_time >= p.end_time) return toast.error(`Period ${p.number}: start must be before end`);
    }
    setPeriodConfig(draftPeriods);
    if (selectedSectionId) savePeriodConfig(selectedSectionId, draftPeriods);
    setShowPeriodConfig(false);
    toast.success('Period configuration saved');
  };

  const addDraftPeriod = () => {
    const last = draftPeriods[draftPeriods.length - 1];
    const nextNum = last ? last.number + 1 : 1;
    // Auto-calculate next start/end by adding 45 min to last end
    let nextStart = '09:00';
    let nextEnd = '09:40';
    if (last?.end_time) {
      const [h, m] = last.end_time.split(':').map(Number);
      const startMin = h * 60 + m + 5;
      const endMin = startMin + 40;
      nextStart = `${String(Math.floor(startMin / 60)).padStart(2, '0')}:${String(startMin % 60).padStart(2, '0')}`;
      nextEnd = `${String(Math.floor(endMin / 60)).padStart(2, '0')}:${String(endMin % 60).padStart(2, '0')}`;
    }
    setDraftPeriods((prev) => [
      ...prev,
      { number: nextNum, label: `Period ${nextNum}`, start_time: nextStart, end_time: nextEnd },
    ]);
  };

  const handleSave = () => {
    if (!selectedSectionId || !selectedYear?.id) return toast.error('Select year and section first');
    if (!slot.subject_id) return toast.error('Select a subject');
    if (!slot.start_time || !slot.end_time) return toast.error('Set start and end time');
    upsertMutation.mutate();
  };

  return (
    <div>
      <PageHeader title="Timetable" subtitle="Build weekly timetable per section and detect conflicts" />

      {/* ── Selection bar ─────────────────────────────────────────────── */}
      <div className="mb-4 grid gap-3 md:grid-cols-4">
        <select
          value={selectedYear?.id ?? ''}
          onChange={(e) => {
            const selected = (yearsQuery.data ?? []).find((y: any) => y.id === e.target.value);
            if (!selected) return;
            setSelectedYear({
              id: selected.id,
              name: selected.name,
              startDate: selected.start_date,
              endDate: selected.end_date,
              isCurrent: selected.is_current,
            });
            setSelectedClassId('');
            setSelectedSectionId('');
          }}
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        >
          {(yearsQuery.data ?? []).map((year: any) => (
            <option key={year.id} value={year.id}>{year.name}</option>
          ))}
        </select>

        <select
          value={selectedClassId}
          onChange={(e) => { setSelectedClassId(e.target.value); setSelectedSectionId(''); }}
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">-- Select Class --</option>
          {classes.map((c: any) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <select
          value={selectedSectionId}
          onChange={(e) => setSelectedSectionId(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">-- Select Section --</option>
          {sections.map((s: any) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        <button
          onClick={() => {
            if (!selectedSectionId || !selectedYear?.id) return toast.error('Select section first');
            window.open(timetableApi.exportPdfUrl(selectedSectionId, selectedYear.id), '_blank');
          }}
          disabled={!selectedSectionId}
          className="inline-flex items-center justify-center gap-2 rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 disabled:opacity-40"
        >
          <Download size={14} />
          Export PDF
        </button>
      </div>

      {/* ── Period configuration panel ───────────────────────────────── */}
      <div className="mb-4 rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <button
          onClick={() => { setShowPeriodConfig((v) => !v); setDraftPeriods(periodConfig); }}
          className="w-full flex items-center gap-2 px-4 py-3 text-sm font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/40 transition rounded-xl"
        >
          <Settings size={15} />
          Configure Periods
          <span className="ml-1 text-xs font-normal text-gray-400">{periodConfig.length} period{periodConfig.length !== 1 ? 's' : ''} configured</span>
          <span className="ml-auto">{showPeriodConfig ? <ChevronUp size={15} /> : <ChevronDown size={15} />}</span>
        </button>

        {showPeriodConfig && (
          <div className="border-t dark:border-gray-700 px-4 pb-4 pt-3">
            <p className="text-[11px] text-gray-400 mb-3">
              Define how many periods the school day has and their time ranges.
              Changes are saved per section in your browser.
            </p>

            <div className="space-y-2 mb-3">
              <div className="grid grid-cols-12 gap-1.5 text-[10px] font-semibold text-gray-500 uppercase px-1">
                <span className="col-span-1">#</span>
                <span className="col-span-3">Label</span>
                <span className="col-span-3">Start</span>
                <span className="col-span-3">End</span>
                <span className="col-span-2"></span>
              </div>
              {draftPeriods.map((p, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-1.5 items-center">
                  <span className="col-span-1 text-xs font-bold text-gray-500 text-center">{p.number}</span>
                  <input
                    value={p.label}
                    onChange={(e) => setDraftPeriods((prev) =>
                      prev.map((x, i) => i === idx ? { ...x, label: e.target.value } : x)
                    )}
                    className="col-span-3 rounded border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-300"
                    placeholder="Label"
                  />
                  <input
                    type="time"
                    value={p.start_time}
                    onChange={(e) => setDraftPeriods((prev) =>
                      prev.map((x, i) => i === idx ? { ...x, start_time: e.target.value } : x)
                    )}
                    className="col-span-3 rounded border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-300"
                  />
                  <input
                    type="time"
                    value={p.end_time}
                    onChange={(e) => setDraftPeriods((prev) =>
                      prev.map((x, i) => i === idx ? { ...x, end_time: e.target.value } : x)
                    )}
                    className="col-span-3 rounded border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-300"
                  />
                  <button
                    onClick={() => setDraftPeriods((prev) =>
                      prev.filter((_, i) => i !== idx).map((x, i) => ({ ...x, number: i + 1, label: x.label.startsWith('Period') ? `Period ${i + 1}` : x.label }))
                    )}
                    className="col-span-2 flex items-center justify-center gap-0.5 rounded border border-red-100 text-red-400 hover:bg-red-50 text-[10px] py-1 transition"
                  >
                    <X size={11} /> Remove
                  </button>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={addDraftPeriod}
                className="inline-flex items-center gap-1 rounded border border-dashed border-blue-300 text-blue-600 text-xs px-3 py-1.5 hover:bg-blue-50 transition"
              >
                <PlusCircle size={13} /> Add Period
              </button>
              <button
                onClick={() => setDraftPeriods(DEFAULT_PERIODS)}
                className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1.5 transition"
              >
                Reset to default
              </button>
              <button
                onClick={savePeriodDraft}
                className="ml-auto rounded bg-brand-600 text-white text-xs px-4 py-1.5 font-semibold hover:bg-brand-700 transition"
              >
                Save
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Add slot form ──────────────────────────────────────────────── */}
      <div className="mb-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
          <BookOpen size={15} />
          {highlightDay !== null
            ? `Add slot — ${DAY_NAMES[highlightDay - 1]} · Period ${highlightPeriod}`
            : 'Add / Update Slot'}
          {highlightDay !== null && (
            <button
              onClick={() => { setSlot(EMPTY_SLOT); setHighlightDay(null); setHighlightPeriod(null); }}
              className="ml-auto text-xs text-gray-400 hover:text-gray-600"
            >
              ✕ Clear
            </button>
          )}
        </div>
        <div className="grid gap-2 md:grid-cols-7">
          {/* Subject */}
          <select
            value={slot.subject_id}
            onChange={(e) => setSlot((p) => ({ ...p, subject_id: e.target.value }))}
            className="rounded border border-gray-300 px-2 py-2 text-xs col-span-2"
          >
            <option value="">— Subject —</option>
            {subjects.map((s: any) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>

          {/* Teacher */}
          <select
            value={slot.teacher_id}
            onChange={(e) => setSlot((p) => ({ ...p, teacher_id: e.target.value }))}
            className="rounded border border-gray-300 px-2 py-2 text-xs col-span-2"
          >
            <option value="">— Teacher (optional) —</option>
            {staff.map((t: any) => (
              <option key={t.id} value={t.user_id ?? t.id}>
                {t.full_name ?? `${t.first_name} ${t.last_name}`}
              </option>
            ))}
          </select>

          {/* Day */}
          <select
            value={slot.day_of_week}
            onChange={(e) => setSlot((p) => ({ ...p, day_of_week: Number(e.target.value) }))}
            className="rounded border border-gray-300 px-2 py-2 text-xs"
          >
            {DAY_NAMES.map((d, i) => (
              <option key={i + 1} value={i + 1}>{d}</option>
            ))}
          </select>

          {/* Period */}
          <select
            value={slot.period_number}
            onChange={(e) => handlePeriodSelect(Number(e.target.value))}
            className="rounded border border-gray-300 px-2 py-2 text-xs"
          >
            {periodConfig.map((p) => (
              <option key={p.number} value={p.number}>
                {p.label} ({fmtTime(p.start_time)}–{fmtTime(p.end_time)})
              </option>
            ))}
          </select>
        </div>

        <div className="mt-2 grid gap-2 md:grid-cols-7 items-end">
          <div className="col-span-2 flex flex-col gap-0.5">
            <label className="text-[10px] text-gray-500">Start Time</label>
            <input
              type="time"
              value={slot.start_time}
              onChange={(e) => setSlot((p) => ({ ...p, start_time: e.target.value }))}
              className="rounded border border-gray-300 px-2 py-1.5 text-xs"
            />
          </div>
          <div className="col-span-2 flex flex-col gap-0.5">
            <label className="text-[10px] text-gray-500">End Time</label>
            <input
              type="time"
              value={slot.end_time}
              onChange={(e) => setSlot((p) => ({ ...p, end_time: e.target.value }))}
              className="rounded border border-gray-300 px-2 py-1.5 text-xs"
            />
          </div>
          <div className="col-span-3 flex items-end">
            <button
              onClick={handleSave}
              disabled={upsertMutation.isPending || !selectedSectionId}
              className="w-full rounded bg-brand-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50 hover:bg-brand-700 transition"
            >
              {upsertMutation.isPending ? 'Saving…' : 'Save Slot'}
            </button>
          </div>
        </div>
        <p className="mt-1.5 text-[11px] text-gray-400">
          💡 Tip: Click any empty cell in the grid below to pre-fill day &amp; period.
        </p>
      </div>

      {/* ── Grid ──────────────────────────────────────────────────────── */}
      {!selectedSectionId ? (
        <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 py-16 text-center text-sm text-gray-400">
          Select a class and section to view the timetable
        </div>
      ) : gridQuery.isLoading ? (
        <div className="rounded-xl border border-gray-200 bg-white py-16 text-center text-sm text-gray-400">
          Loading timetable…
        </div>
      ) : (
        <div className="overflow-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="border-b px-4 py-2.5 font-semibold text-sm text-gray-700 dark:text-gray-200 flex items-center gap-2">
            {gridQuery.data?.class_name} — {gridQuery.data?.section_name}
            <span className="ml-auto text-xs font-normal text-gray-400">
              {allPeriods.length} period{allPeriods.length !== 1 ? 's' : ''}
            </span>
          </div>
          <table className="min-w-full text-xs">
            <thead className="bg-gray-50 dark:bg-gray-900/40">
              <tr>
                <th className="px-3 py-2.5 text-left font-medium text-gray-500 w-24">Day</th>
                {allPeriods.map((period: number) => {
                  const pDef = periodConfig.find((p) => p.number === period);
                  return (
                    <th key={period} className="px-3 py-2.5 text-center font-medium text-gray-500 min-w-[110px]">
                      <div>{pDef?.label ?? `P${period}`}</div>
                      {pDef && (
                        <div className="text-[10px] font-normal text-gray-400">
                          {fmtTime(pDef.start_time)}–{fmtTime(pDef.end_time)}
                        </div>
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {DAY_NAMES.map((dayName: string, index: number) => {
                const dayIndex = index + 1;
                return (
                  <tr key={dayName} className="border-t border-gray-100 dark:border-gray-700">
                    <td className="px-3 py-2 font-semibold text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-900/20 whitespace-nowrap">
                      {dayName.slice(0, 3)}
                    </td>
                    {allPeriods.map((period: number) => {
                      const slotData = grid?.[dayIndex]?.[period];
                      const isHighlighted = highlightDay === dayIndex && highlightPeriod === period;
                      const colorClass = slotData ? getSubjectColor(slotData.subject_id, allSubjectIds) : '';
                      return (
                        <td
                          key={`${dayIndex}-${period}`}
                          className={`px-1.5 py-1.5 align-top cursor-pointer transition-colors ${
                            isHighlighted
                              ? 'bg-yellow-50 ring-2 ring-inset ring-yellow-400'
                              : slotData
                              ? ''
                              : 'hover:bg-blue-50/50'
                          }`}
                          onClick={() => handleCellClick(dayIndex, period)}
                        >
                          {slotData ? (
                            <div className={`rounded border px-2 py-1.5 text-center ${colorClass}`}>
                              <div className="font-semibold leading-tight truncate max-w-[100px]">
                                {slotData.subject_name}
                              </div>
                              <div className="text-[10px] mt-0.5 opacity-75">
                                {fmtTime(slotData.start_time)}–{fmtTime(slotData.end_time)}
                              </div>
                              {slotData.teacher_name && (
                                <div className="text-[10px] opacity-70 truncate max-w-[100px]">
                                  {slotData.teacher_name}
                                </div>
                              )}
                              <button
                                onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(slotData.id); }}
                                disabled={deleteMutation.isPending}
                                className="mt-1 inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] bg-white/60 hover:bg-red-50 text-red-500 border border-red-100 transition"
                              >
                                <Trash2 size={9} /> Remove
                              </button>
                            </div>
                          ) : (
                            <div className={`h-14 flex items-center justify-center rounded border border-dashed text-[10px] text-gray-300 transition-colors ${
                              isHighlighted
                                ? 'border-yellow-400 text-yellow-500'
                                : 'border-gray-200 hover:border-blue-300 hover:text-blue-400'
                            }`}>
                              {isHighlighted ? 'Selected' : '+'}
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Subject colour legend */}
          {allSubjectIds.length > 0 && (
            <div className="flex flex-wrap gap-2 px-4 py-3 border-t bg-gray-50 dark:bg-gray-900/20">
              {allSubjectIds.map((sid) => {
                const sub = subjects.find((s: any) => s.id === sid);
                if (!sub) return null;
                return (
                  <span
                    key={sid}
                    className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${getSubjectColor(sid, allSubjectIds)}`}
                  >
                    {sub.name}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TimetablePage;
