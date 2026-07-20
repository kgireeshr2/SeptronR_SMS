import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';
import { formatDateTime } from '@utils/formatters';

interface ReportGroups {
  student: string[];
  staff: string[];
  finance: string[];
  attendance: string[];
  other: string[];
}

interface SelectOption { id: string; name: string; }

const REPORT_LABELS: Record<string, string> = {
  student_list: 'Student List',
  student_attendance: 'Student Attendance Summary',
  low_attendance: 'Low Attendance Students',
  birthday_report: 'Student Birthdays',
  fee_defaulters: 'Fee Defaulters',
  fee_collection: 'Fee Collection',
  class_fee_summary: 'Class Fee Summary',
  income_expense: 'Income & Expense',
  monthly_pl: 'Monthly P&L Summary',
  staff_list: 'Staff List',
  staff_attendance: 'Staff Attendance Summary',
  leave_report: 'Staff Leave Report',
  exam_results: 'Exam Results Summary',
};

const REPORT_FILTERS: Record<string, string[]> = {
  student_list: ['class_id', 'gender', 'status'],
  student_attendance: ['class_id', 'month', 'year'],
  low_attendance: ['class_id', 'month', 'year', 'threshold_pct'],
  birthday_report: ['class_id', 'month'],
  fee_defaulters: ['class_id'],
  fee_collection: ['date_from', 'date_to'],
  class_fee_summary: [],
  income_expense: ['month', 'year'],
  monthly_pl: ['month', 'year'],
  staff_list: ['department_id'],
  staff_attendance: ['month', 'year', 'department_id'],
  leave_report: ['department_id', 'status', 'date_from', 'date_to'],
  exam_results: ['class_id', 'exam_type_id'],
};

const GROUP_COLORS: Record<keyof ReportGroups, string> = {
  student: 'bg-blue-50 text-blue-700 border-blue-200',
  staff: 'bg-purple-50 text-purple-700 border-purple-200',
  finance: 'bg-green-50 text-green-700 border-green-200',
  attendance: 'bg-orange-50 text-orange-700 border-orange-200',
  other: 'bg-gray-50 text-gray-700 border-gray-200',
};

const Page: React.FC = () => {
  const [groups, setGroups] = useState<ReportGroups | null>(null);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{ total_rows: number; data: Record<string, unknown>[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Options for dropdowns
  const [classes, setClasses] = useState<SelectOption[]>([]);
  const [departments, setDepartments] = useState<SelectOption[]>([]);

  useEffect(() => {
    api.get('/reports/available').then((r: any) => setGroups(r?.data ?? r)).catch(() => { /* ignore */ });
    // Load classes for dropdown
    const unwrap = (r: any) => Array.isArray(r) ? r : (r?.data ?? []);
    api.get('/academic-years').then((r: any) => {
      const years = unwrap(r);
      const current = years.find((y: any) => y.is_current) ?? years[0];
      if (current?.id) {
        api.get(`/classes?academic_year_id=${current.id}&limit=200`).then((cr: any) => {
          setClasses(unwrap(cr).map((c: any) => ({ id: c.id, name: c.name })));
        }).catch(() => { /* ignore */ });
      }
    }).catch(() => { /* ignore */ });
    // Load departments
    api.get('/departments').then((r: any) => {
      setDepartments(unwrap(r).map((d: any) => ({ id: d.id, name: d.name })));
    }).catch(() => { /* ignore */ });
  }, []);

  const setFilter = (key: string, val: string) => setFilters(p => ({ ...p, [key]: val }));

  const selectedFilters = selectedReport ? (REPORT_FILTERS[selectedReport] ?? []) : [];

  const runReport = async () => {
    if (!selectedReport) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([k, v]) => { if (v) params.append(k, v); });
      const r: any = await api.get(`/reports/${selectedReport}?${params.toString()}`);
      // Backend returns {report_id, total_rows, data:[...]} directly (no outer envelope)
      // but axios interceptor may add one level; normalise here
      const payload = r?.report_id !== undefined ? r : (r?.data ?? r);
      setResult(payload);
    } catch (e: unknown) {
      const errBody = (e as any);
      setError(errBody?.response?.data?.detail ?? errBody?.detail ?? 'Failed to generate report.');
    } finally { setRunning(false); }
  };

  const exportCSV = () => {
    if (!result?.data.length) return;
    const keys = Object.keys(result.data[0]);
    const rows = [keys.join(','), ...result.data.map(row => keys.map(k => JSON.stringify(row[k] ?? '')).join(','))];
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${selectedReport}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  const printReport = () => {
    if (!result?.data?.length) return;
    const label = REPORT_LABELS[selectedReport!] ?? selectedReport!.replace(/_/g, ' ');
    const keys = Object.keys(result.data[0]);
    const formatVal = (v: unknown) =>
      v === null || v === undefined ? '' : typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v);
    const thead = keys.map(k =>
      `<th>${k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</th>`
    ).join('');
    const tbody = result.data.map(row =>
      `<tr>${keys.map(k => `<td>${formatVal((row as any)[k])}</td>`).join('')}</tr>`
    ).join('');
    const html = `<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<title>${label}</title>
<style>
  @page { size: A4 landscape; margin: 15mm 12mm; }
  * { box-sizing: border-box; }
  body { font-family: Arial, sans-serif; font-size: 10pt; color: #111; margin: 0; }
  h1 { font-size: 14pt; margin: 0 0 2mm; }
  .meta { font-size: 8pt; color: #555; margin-bottom: 4mm; }
  table { width: 100%; border-collapse: collapse; page-break-inside: auto; }
  thead { display: table-header-group; }
  tr { page-break-inside: avoid; }
  th { background: #1e40af; color: #fff; padding: 4px 6px; text-align: left; font-size: 8pt; white-space: nowrap; }
  td { padding: 3px 6px; font-size: 8.5pt; border-bottom: 1px solid #e5e7eb; }
  tr:nth-child(even) td { background: #f9fafb; }
  .footer { margin-top: 4mm; font-size: 7.5pt; color: #888; text-align: right; }
</style>
</head><body>
<h1>${label}</h1>
<div class="meta">Generated: ${formatDateTime(new Date())} &nbsp;|&nbsp; Total rows: ${result.total_rows}</div>
<table><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>
<div class="footer">SeptroSchool</div>
</body></html>`;
    const w = window.open('', '_blank', 'width=1000,height=700');
    if (!w) return;
    w.document.write(html);
    w.document.close();
    w.focus();
    setTimeout(() => { w.print(); }, 400);
  };

  const renderFilter = (f: string) => {
    const cls = 'w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-700';
    switch (f) {
      case 'class_id':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">Class</label>
            <select value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls}>
              <option value="">All Classes</option>
              {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        );
      case 'department_id':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">Department</label>
            <select value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls}>
              <option value="">All Departments</option>
              {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
        );
      case 'gender':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">Gender</label>
            <select value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls}>
              <option value="">All</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
        );
      case 'status': {
        const isLeave = selectedReport === 'leave_report';
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">Status</label>
            <select value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls}>
              <option value="">All</option>
              {isLeave ? (
                <>
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                </>
              ) : (
                <>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </>
              )}
            </select>
          </div>
        );
      }
      case 'month':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">Month</label>
            <select value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls}>
              <option value="">All Months</option>
              {['January','February','March','April','May','June','July','August','September','October','November','December'].map((m, i) => (
                <option key={i+1} value={String(i+1)}>{m}</option>
              ))}
            </select>
          </div>
        );
      case 'year':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">Year</label>
            <select value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls}>
              <option value="">All Years</option>
              {Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - 2 + i).map(y => (
                <option key={y} value={String(y)}>{y}</option>
              ))}
            </select>
          </div>
        );
      case 'date_from':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">From Date</label>
            <input type="date" value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls} />
          </div>
        );
      case 'date_to':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">To Date</label>
            <input type="date" value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls} />
          </div>
        );
      case 'threshold_pct':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">Min. Attendance % (below)</label>
            <input type="number" min="0" max="100" placeholder="75" value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls} />
          </div>
        );
      case 'exam_type_id':
        return (
          <div key={f}>
            <label className="mb-1 block text-xs text-gray-500">Exam Type ID</label>
            <input type="text" placeholder="Exam type UUID (optional)" value={filters[f] ?? ''} onChange={e => setFilter(f, e.target.value)} className={cls} />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div>
      <PageHeader title="Reports" />

      <div className="flex gap-6">
        {/* Report Picker */}
        <aside className="w-64 flex-shrink-0">
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Select Report</p>
            {!groups ? (
              <p className="text-sm text-gray-500">Loading...</p>
            ) : (
              <div className="space-y-4">
                {(Object.entries(groups) as [keyof ReportGroups, string[]][]).map(([group, reports]) =>
                  reports.length === 0 ? null : (
                    <div key={group}>
                      <p className="mb-1.5 text-xs font-semibold uppercase text-gray-400 capitalize">{group}</p>
                      <div className="space-y-1">
                        {reports.map(r => (
                          <button
                            key={r}
                            onClick={() => { setSelectedReport(r); setFilters({}); setResult(null); setError(null); }}
                            className={`w-full rounded-lg border px-3 py-2 text-left text-xs font-medium transition-colors ${
                              selectedReport === r
                                ? `${GROUP_COLORS[group]} border`
                                : 'border-transparent text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700'
                            }`}
                          >
                            {REPORT_LABELS[r] ?? r.replace(/_/g, ' ')}
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        </aside>

        {/* Report Area */}
        <div className="flex-1 min-w-0">
          {!selectedReport ? (
            <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white dark:border-gray-700 dark:bg-gray-800">
              <p className="text-gray-500">← Select a report to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Report Header */}
              <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h3 className="font-semibold text-gray-800 dark:text-gray-100">
                  {REPORT_LABELS[selectedReport] ?? selectedReport.replace(/_/g, ' ')}
                </h3>

                {/* Filters */}
                {selectedFilters.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
                    {selectedFilters.map(f => renderFilter(f))}
                  </div>
                )}

                {/* Run Button */}
                <div className="mt-4 flex items-center gap-3">
                  <button
                    onClick={runReport}
                    disabled={running}
                    className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
                  >
                    {running ? 'Generating…' : 'Generate Report'}
                  </button>
                  {result && (
                    <button
                      onClick={exportCSV}
                      className="rounded-lg border border-green-300 px-4 py-2 text-sm text-green-700 hover:bg-green-50"
                    >
                      Export CSV
                    </button>
                  )}
                  {result && (
                    <button
                      onClick={printReport}
                      className="rounded-lg border border-blue-300 px-4 py-2 text-sm text-blue-700 hover:bg-blue-50"
                    >
                      🖨️ Print / Save PDF
                    </button>
                  )}
                  {result && (
                    <span className="text-sm text-gray-500">{result.total_rows} row{result.total_rows !== 1 ? 's' : ''}</span>
                  )}
                </div>
              </div>

              {error && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
              )}

              {/* Results Table */}
              {result && result.data.length > 0 && (
                <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        {Object.keys(result.data[0]).map(k => (
                          <th key={k} className="px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400 whitespace-nowrap">
                            {k.replace(/_/g, ' ')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.data.map((row, i) => (
                        <tr key={i} className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          {Object.values(row).map((v, j) => (
                            <td key={j} className="px-4 py-2.5 text-gray-700 dark:text-gray-300 whitespace-nowrap">
                              {v === null || v === undefined ? '—' : typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {result && result.data.length === 0 && (
                <div className="rounded-xl border border-gray-200 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-800">
                  <p className="text-gray-500">No data found for the selected filters.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Page;
