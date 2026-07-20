import React from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import { toast } from 'sonner';
import api from '@/api/axios';

import { academicYearsApi } from '@api/academicYears';
import { classesApi } from '@api/classes';
import { studentsApi } from '@api/students';
import { attendanceApi, AttendanceStatus, SessionType, StaffAttendanceMarkRequest } from '@api/attendance';

const unwrap = (res: any) => res?.data ?? res;

const statusOptions: AttendanceStatus[] = ['present', 'absent', 'late', 'half_day', 'leave'];
const staffStatusOptions: StaffAttendanceMarkRequest['status'][] = [
  'present', 'absent', 'late', 'half_day', 'on_leave', 'holiday',
];

// ─── Student Attendance Tab ──────────────────────────────────────────────────

const StudentAttendanceTab: React.FC = () => {
  const [loading, setLoading] = React.useState(false);
  const [years, setYears] = React.useState<any[]>([]);
  const [classes, setClasses] = React.useState<any[]>([]);
  const [sections, setSections] = React.useState<any[]>([]);
  const [students, setStudents] = React.useState<any[]>([]);
  const [summary, setSummary] = React.useState<any>(null);

  const [academicYearId, setAcademicYearId] = React.useState('');
  const [classId, setClassId] = React.useState('');
  const [sectionId, setSectionId] = React.useState('');
  const [sessionType, setSessionType] = React.useState<SessionType>('full_day');
  const [dateValue, setDateValue] = React.useState<string>(new Date().toISOString().slice(0, 10));
  const [statusMap, setStatusMap] = React.useState<Record<string, AttendanceStatus>>({});

  React.useEffect(() => {
    (async () => {
      try {
        const data = unwrap(await academicYearsApi.list());
        const rows = Array.isArray(data) ? data : (data?.items ?? []);
        setYears(rows);
        const current = rows.find((x: any) => x.is_current) ?? rows[0];
        if (current?.id) setAcademicYearId(current.id);
      } catch { toast.error('Failed to load academic years'); }
    })();
  }, []);

  React.useEffect(() => {
    if (!academicYearId) return;
    (async () => {
      try {
        const data = unwrap(await classesApi.list(academicYearId));
        setClasses(Array.isArray(data) ? data : (data?.items ?? []));
      } catch { toast.error('Failed to load classes'); }
    })();
  }, [academicYearId]);

  React.useEffect(() => {
    if (!classId) { setSections([]); setSectionId(''); return; }
    (async () => {
      try {
        const data = unwrap(await classesApi.listSections(classId));
        setSections(Array.isArray(data) ? data : (data?.items ?? []));
      } catch { toast.error('Failed to load sections'); }
    })();
  }, [classId]);

  const loadStudentsAndExisting = async () => {
    if (!sectionId || !academicYearId) return;
    setLoading(true);
    try {
      const studentsRes = unwrap(await studentsApi.listStudents({ section_id: sectionId, academic_year_id: academicYearId, is_active: true, limit: 500 }));
      const studentRows = Array.isArray(studentsRes) ? studentsRes : (studentsRes?.items ?? []);
      setStudents(studentRows);

      const attendanceRes = unwrap(await attendanceApi.getSectionForDate(sectionId, dateValue, sessionType));
      setSummary(attendanceRes);

      const nextMap: Record<string, AttendanceStatus> = {};
      for (const student of studentRows) nextMap[student.id] = 'present';
      for (const entry of attendanceRes?.entries ?? []) nextMap[entry.student_id] = entry.status;
      setStatusMap(nextMap);
    } catch (e: any) {
      setSummary(null);
      toast.error(e?.detail || e?.message || 'Failed to load attendance data');
    } finally { setLoading(false); }
  };

  const markAllPresent = () => {
    const nextMap: Record<string, AttendanceStatus> = {};
    for (const student of students) nextMap[student.id] = 'present';
    setStatusMap(nextMap);
  };

  const submitAttendance = async () => {
    if (!sectionId || !academicYearId) { toast.error('Select academic year, class, and section first'); return; }
    try {
      setLoading(true);
      const payload = {
        section_id: sectionId, academic_year_id: academicYearId, date: dateValue, session_type: sessionType,
        entries: students.map((student: any) => ({ student_id: student.id, status: statusMap[student.id] ?? 'present' })),
      };
      const res = unwrap(await attendanceApi.markAttendance(sectionId, payload));
      setSummary(res);
      toast.success('Attendance saved');
    } catch (e: any) {
      toast.error(e?.detail || e?.message || 'Failed to save attendance');
    } finally { setLoading(false); }
  };

  return (
    <div>
      <div className="mb-4 grid gap-3 md:grid-cols-5">
        <select className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" value={academicYearId} onChange={e => setAcademicYearId(e.target.value)}>
          <option value="">Select Academic Year</option>
          {years.map((year: any) => <option key={year.id} value={year.id}>{year.name}</option>)}
        </select>
        <select className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" value={classId} onChange={e => setClassId(e.target.value)}>
          <option value="">Select Class</option>
          {classes.map((cls: any) => <option key={cls.id} value={cls.id}>{cls.name}</option>)}
        </select>
        <select className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" value={sectionId} onChange={e => setSectionId(e.target.value)}>
          <option value="">Select Section</option>
          {sections.map((sec: any) => <option key={sec.id} value={sec.id}>{sec.name}</option>)}
        </select>
        <input type="date" className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" value={dateValue} onChange={e => setDateValue(e.target.value)} />
        <select className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" value={sessionType} onChange={e => setSessionType(e.target.value as SessionType)}>
          <option value="full_day">Full Day</option>
          <option value="morning">Morning</option>
          <option value="afternoon">Afternoon</option>
        </select>
      </div>

      <div className="mb-4 flex gap-2">
        <button onClick={loadStudentsAndExisting} className="rounded bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700">Load</button>
        <button onClick={markAllPresent} className="rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700">Mark All Present</button>
        <button onClick={submitAttendance} disabled={loading || students.length === 0} className="rounded bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60">
          {loading ? 'Saving…' : 'Save Attendance'}
        </button>
      </div>

      {summary && (
        <div className="mb-4 flex flex-wrap gap-4 rounded-xl border border-gray-200 bg-white p-3 text-sm shadow-sm dark:border-gray-700 dark:bg-gray-800">
          {[
            { label: 'Total', val: summary.total },
            { label: 'Present', val: summary.present, cls: 'text-green-600' },
            { label: 'Absent', val: summary.absent, cls: 'text-red-600' },
            { label: 'Late', val: summary.late, cls: 'text-yellow-600' },
            { label: 'Half Day', val: summary.half_day },
            { label: 'Leave', val: summary.leave },
            { label: '%', val: `${summary.attendance_pct}%`, cls: 'font-bold text-indigo-600' },
          ].map(item => (
            <span key={item.label} className={item.cls}><span className="text-gray-500">{item.label}: </span>{item.val}</span>
          ))}
        </div>
      )}

      <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Admission No</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Student</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody>
            {students.length === 0 ? (
              <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-500">Load a section to mark attendance.</td></tr>
            ) : students.map((student: any) => (
              <tr key={student.id} className="border-b border-gray-100 dark:border-gray-800">
                <td className="px-4 py-2">{student.admission_number}</td>
                <td className="px-4 py-2">{student.full_name || `${student.first_name} ${student.last_name}`}</td>
                <td className="px-4 py-2">
                  <select
                    className="rounded border border-gray-300 px-2 py-1 text-sm dark:border-gray-600 dark:bg-gray-700"
                    value={statusMap[student.id] ?? 'present'}
                    onChange={e => setStatusMap(prev => ({ ...prev, [student.id]: e.target.value as AttendanceStatus }))}
                  >
                    {statusOptions.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── Staff Attendance Tab ────────────────────────────────────────────────────

const STATUS_COLOR: Record<string, string> = {
  present:  'bg-green-100 text-green-700',
  absent:   'bg-red-100 text-red-700',
  late:     'bg-yellow-100 text-yellow-700',
  half_day: 'bg-blue-100 text-blue-700',
  on_leave: 'bg-purple-100 text-purple-700',
  holiday:  'bg-gray-100 text-gray-600',
};

const StaffAttendanceTab: React.FC = () => {
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [staffList, setStaffList] = React.useState<any[]>([]);
  const [statusMap, setStatusMap] = React.useState<Record<string, StaffAttendanceMarkRequest['status']>>({});
  const [checkinMap, setCheckinMap] = React.useState<Record<string, string>>({});
  const [dateValue, setDateValue] = React.useState(new Date().toISOString().slice(0, 10));
  const [departmentFilter, setDepartmentFilter] = React.useState('');
  const [departments, setDepartments] = React.useState<any[]>([]);

  // Load departments for filter
  React.useEffect(() => {
    api.get('/departments').then((r: any) => {
      const rows = Array.isArray(r) ? r : (r?.data ?? []);
      setDepartments(rows);
    }).catch(() => {});
  }, []);

  const loadStaff = React.useCallback(async () => {
    setLoading(true);
    try {
      // Load staff list
      const staffRes: any = await api.get('/staff', {
        params: { is_active: true, limit: 500, ...(departmentFilter ? { department_id: departmentFilter } : {}) }
      });
      const rows: any[] = Array.isArray(staffRes) ? staffRes : (staffRes?.data ?? staffRes?.items ?? []);
      setStaffList(rows);

      // Load existing attendance for the selected date
      const attRes: any = await attendanceApi.listStaffAttendance(dateValue);
      const existing: any[] = Array.isArray(attRes) ? attRes : (attRes?.data ?? []);

      // Build initial status map: default "present", override with any saved record
      const sm: Record<string, StaffAttendanceMarkRequest['status']> = {};
      const cm: Record<string, string> = {};
      for (const s of rows) sm[s.id] = 'present';
      for (const rec of existing) {
        sm[rec.staff_id] = rec.status;
        if (rec.check_in) cm[rec.staff_id] = rec.check_in.slice(0, 5); // HH:MM
      }
      setStatusMap(sm);
      setCheckinMap(cm);
    } catch (e: any) {
      toast.error(e?.detail || e?.message || 'Failed to load staff');
    } finally { setLoading(false); }
  }, [dateValue, departmentFilter]);

  const markAll = (status: StaffAttendanceMarkRequest['status']) => {
    const sm: Record<string, StaffAttendanceMarkRequest['status']> = {};
    for (const s of staffList) sm[s.id] = status;
    setStatusMap(sm);
  };

  const saveAttendance = async () => {
    if (staffList.length === 0) { toast.error('Load staff first'); return; }
    setSaving(true);
    try {
      const payload: StaffAttendanceMarkRequest[] = staffList.map(s => ({
        staff_id: s.id,
        date: dateValue,
        status: statusMap[s.id] ?? 'present',
        check_in: checkinMap[s.id] || undefined,
        source: 'manual' as const,
      }));
      await attendanceApi.markStaffAttendance(payload);
      toast.success(`Attendance saved for ${staffList.length} staff members`);
    } catch (e: any) {
      toast.error(e?.detail || e?.message || 'Failed to save staff attendance');
    } finally { setSaving(false); }
  };

  const presentCount = Object.values(statusMap).filter(s => s === 'present').length;
  const absentCount  = Object.values(statusMap).filter(s => s === 'absent').length;
  const lateCount    = Object.values(statusMap).filter(s => s === 'late').length;

  return (
    <div>
      {/* Controls */}
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">Date</label>
          <input
            type="date"
            value={dateValue}
            onChange={e => setDateValue(e.target.value)}
            className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">Department</label>
          <select
            value={departmentFilter}
            onChange={e => setDepartmentFilter(e.target.value)}
            className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
          >
            <option value="">All Departments</option>
            {departments.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <button
          onClick={loadStaff}
          disabled={loading}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {loading ? 'Loading…' : 'Load Staff'}
        </button>
      </div>

      {staffList.length > 0 && (
        <>
          {/* Summary bar */}
          <div className="mb-4 flex flex-wrap items-center gap-4 rounded-xl border bg-white p-3 text-sm shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <span className="font-medium text-gray-600 dark:text-gray-300">Total: {staffList.length}</span>
            <span className="text-green-600">Present: {presentCount}</span>
            <span className="text-red-600">Absent: {absentCount}</span>
            <span className="text-yellow-600">Late: {lateCount}</span>
            <div className="ml-auto flex gap-2">
              <button onClick={() => markAll('present')} className="rounded border border-green-300 px-3 py-1 text-xs font-medium text-green-700 hover:bg-green-50">Mark All Present</button>
              <button onClick={() => markAll('absent')}  className="rounded border border-red-300 px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-50">Mark All Absent</button>
              <button
                onClick={saveAttendance}
                disabled={saving}
                className="rounded bg-green-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
              >
                {saving ? 'Saving…' : 'Save Attendance'}
              </button>
            </div>
          </div>

          {/* Staff table */}
          <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  {['#', 'Name', 'Designation', 'Department', 'Status', 'Check-in'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {staffList.map((staff: any, idx: number) => (
                  <tr key={staff.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-4 py-2.5 text-gray-400">{idx + 1}</td>
                    <td className="px-4 py-2.5 font-medium text-gray-900 dark:text-white">
                      {staff.full_name || `${staff.first_name ?? ''} ${staff.last_name ?? ''}`.trim() || staff.employee_id}
                    </td>
                    <td className="px-4 py-2.5 text-gray-500">{staff.designation_name ?? staff.designation ?? '—'}</td>
                    <td className="px-4 py-2.5 text-gray-500">{staff.department_name ?? staff.department ?? '—'}</td>
                    <td className="px-4 py-2.5">
                      <select
                        value={statusMap[staff.id] ?? 'present'}
                        onChange={e => setStatusMap(prev => ({ ...prev, [staff.id]: e.target.value as StaffAttendanceMarkRequest['status'] }))}
                        className={`rounded border px-2 py-1 text-xs font-medium ${STATUS_COLOR[statusMap[staff.id] ?? 'present']} border-transparent`}
                      >
                        {staffStatusOptions.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-2.5">
                      <input
                        type="time"
                        value={checkinMap[staff.id] ?? ''}
                        onChange={e => setCheckinMap(prev => ({ ...prev, [staff.id]: e.target.value }))}
                        className="rounded border border-gray-300 px-2 py-1 text-xs dark:border-gray-600 dark:bg-gray-700"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!loading && staffList.length === 0 && (
        <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white text-gray-500 dark:border-gray-700 dark:bg-gray-800">
          Select a date and click "Load Staff" to begin marking attendance
        </div>
      )}
    </div>
  );
};

// ─── Reports Tab ─────────────────────────────────────────────────────────────

const AttendanceReportsTab: React.FC = () => {
  const [years, setYears] = React.useState<any[]>([]);
  const [classes, setClasses] = React.useState<any[]>([]);
  const [sections, setSections] = React.useState<any[]>([]);
  const [yearId, setYearId] = React.useState('');
  const [classId, setClassId] = React.useState('');
  const [sectionId, setSectionId] = React.useState('');
  const [month, setMonth] = React.useState(new Date().toISOString().slice(0, 7));
  const [report, setReport] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    (async () => {
      try {
        const [ys, cs] = await Promise.all([
          academicYearsApi.list().then(unwrap),
          classesApi.getClasses().then(unwrap),
        ]);
        setYears(Array.isArray(ys) ? ys : []);
        setClasses(Array.isArray(cs) ? cs : []);
      } catch {}
    })();
  }, []);

  React.useEffect(() => {
    if (!classId) return;
    classesApi.getSections(classId).then(r => setSections(Array.isArray(unwrap(r)) ? unwrap(r) : [])).catch(() => {});
  }, [classId]);

  const generate = async () => {
    if (!sectionId || !month) return;
    setLoading(true);
    try {
      const [y, m] = month.split('-');
      const res = await api.get('/attendance/monthly-report', {
        params: { section_id: sectionId, year: y, month: m },
      });
      setReport(Array.isArray(res) ? res : (res as any)?.data ?? []);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const summary = report.reduce(
    (acc, s) => {
      acc.present += s.present_days ?? 0;
      acc.absent += s.absent_days ?? 0;
      acc.total += s.total_working_days ?? 0;
      return acc;
    },
    { present: 0, absent: 0, total: 0 }
  );

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Academic Year</label>
          <select value={yearId} onChange={e => setYearId(e.target.value)}
            className="border rounded px-3 py-2 text-sm min-w-[140px]">
            <option value="">Select year</option>
            {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Class</label>
          <select value={classId} onChange={e => { setClassId(e.target.value); setSectionId(''); }}
            className="border rounded px-3 py-2 text-sm min-w-[120px]">
            <option value="">Select class</option>
            {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Section</label>
          <select value={sectionId} onChange={e => setSectionId(e.target.value)}
            className="border rounded px-3 py-2 text-sm min-w-[120px]">
            <option value="">Select section</option>
            {sections.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Month</label>
          <input type="month" value={month} onChange={e => setMonth(e.target.value)}
            className="border rounded px-3 py-2 text-sm" />
        </div>
        <button onClick={generate} disabled={loading || !sectionId}
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50">
          {loading ? 'Loading…' : 'Generate Report'}
        </button>
      </div>

      {report.length > 0 && (
        <>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Total Students', value: report.length, color: 'blue' },
              { label: 'Avg Present Days', value: report.length ? (summary.present / report.length).toFixed(1) : 0, color: 'green' },
              { label: 'Avg Absent Days', value: report.length ? (summary.absent / report.length).toFixed(1) : 0, color: 'red' },
            ].map(s => (
              <div key={s.label} className="bg-white rounded-xl border p-4 text-center">
                <p className="text-2xl font-bold text-gray-800">{s.value}</p>
                <p className="text-xs text-gray-500 mt-1">{s.label}</p>
              </div>
            ))}
          </div>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {['Student', 'Admission No', 'Present', 'Absent', 'Late', 'Working Days', 'Attendance %'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {report.map((r: any) => {
                  const pct = r.total_working_days ? ((r.present_days / r.total_working_days) * 100).toFixed(1) : '—';
                  const low = Number(pct) < 75;
                  return (
                    <tr key={r.student_id} className="border-t hover:bg-gray-50">
                      <td className="px-4 py-2 font-medium">{r.student_name}</td>
                      <td className="px-4 py-2 text-gray-500">{r.admission_number || '—'}</td>
                      <td className="px-4 py-2 text-green-600 font-semibold">{r.present_days}</td>
                      <td className="px-4 py-2 text-red-600 font-semibold">{r.absent_days}</td>
                      <td className="px-4 py-2 text-yellow-600">{r.late_days ?? 0}</td>
                      <td className="px-4 py-2">{r.total_working_days}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${low ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                          {pct}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

      {report.length === 0 && !loading && (
        <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white text-gray-500">
          Select section and month, then click Generate Report
        </div>
      )}
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const AttendancePage: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState<'student' | 'staff' | 'reports'>('student');

  return (
    <div>
      <PageHeader title="Attendance" subtitle="Mark and track daily attendance" />

      {/* Tab switcher */}
      <div className="mb-5 flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {([
          { key: 'student', label: '🎓 Student Attendance' },
          { key: 'staff',   label: '👩‍🏫 Staff Attendance' },
          { key: 'reports', label: '📊 Monthly Reports' },
        ] as const).map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
              activeTab === tab.key
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'student' && <StudentAttendanceTab />}
      {activeTab === 'staff' && <StaffAttendanceTab />}
      {activeTab === 'reports' && <AttendanceReportsTab />}
    </div>
  );
};

export default AttendancePage;