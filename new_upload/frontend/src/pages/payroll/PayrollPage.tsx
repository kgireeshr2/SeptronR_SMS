import React, { useState, useEffect } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';
import { toast } from 'sonner';
import { Download, CheckCircle, RefreshCw, Plus, X } from 'lucide-react';

interface PayrollRecord {
  id: string;
  staff_id: string;
  staff_name?: string;
  employee_id?: string;
  month: number;
  year: number;
  basic_salary: number;
  allowances: number;
  deductions: number;
  net_salary: number;
  is_paid: boolean;
  paid_at?: string;
  remarks?: string;
}

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const fmt = (n: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

const unwrap = (r: any): any[] => {
  if (Array.isArray(r)) return r;
  if (Array.isArray(r?.data)) return r.data;
  if (Array.isArray(r?.items)) return r.items;
  return [];
};

const PayrollPage: React.FC = () => {
  const [tab, setTab] = useState<'records' | 'generate' | 'my_history'>('records');
  const [records, setRecords] = useState<PayrollRecord[]>([]);
  const [myHistory, setMyHistory] = useState<PayrollRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [slipModal, setSlipModal] = useState<PayrollRecord | null>(null);
  const [slip, setSlip] = useState<any>(null);

  // Filters
  const [filterMonth, setFilterMonth] = useState('');
  const [filterYear, setFilterYear] = useState('');
  const [filterPaid, setFilterPaid] = useState('');

  // Generate form
  const [genMonth, setGenMonth] = useState(new Date().getMonth() + 1);
  const [genYear, setGenYear] = useState(new Date().getFullYear());
  const [genAcYear, setGenAcYear] = useState('');
  const [acYears, setAcYears] = useState<any[]>([]);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    api.get('/academic-years').then((r: any) => {
      const rows = unwrap(r);
      setAcYears(rows);
      const cur = rows.find((y: any) => y.is_current) ?? rows[0];
      if (cur?.id) setGenAcYear(cur.id);
    }).catch(() => {});
  }, []);

  useEffect(() => { if (tab === 'records') loadRecords(); }, [tab, filterMonth, filterYear, filterPaid]);
  useEffect(() => { if (tab === 'my_history') loadMyHistory(); }, [tab]);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filterMonth) params.month = filterMonth;
      if (filterYear) params.year = filterYear;
      if (filterPaid !== '') params.is_paid = filterPaid === 'true';
      const r = await api.get('/payroll', { params });
      setRecords(unwrap(r));
    } catch { toast.error('Failed to load payroll records'); }
    finally { setLoading(false); }
  };

  const loadMyHistory = async () => {
    setLoading(true);
    try {
      const r = await api.get('/payroll/my/history');
      setMyHistory(unwrap(r));
    } catch { toast.error('Failed to load payroll history'); }
    finally { setLoading(false); }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    try {
      await api.post('/payroll/generate', { month: genMonth, year: genYear, academic_year_id: genAcYear || undefined });
      toast.success(`Payroll generated for ${MONTHS[genMonth - 1]} ${genYear}`);
      setTab('records');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to generate payroll');
    } finally { setGenerating(false); }
  };

  const handleMarkPaid = async () => {
    if (selected.size === 0) { toast.error('Select records to mark as paid'); return; }
    try {
      await api.patch('/payroll/mark-paid', { payroll_ids: [...selected] });
      toast.success(`${selected.size} record(s) marked as paid`);
      setSelected(new Set());
      loadRecords();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to mark as paid');
    }
  };

  const openSlip = async (rec: PayrollRecord) => {
    setSlipModal(rec);
    try {
      const r: any = await api.get(`/payroll/${rec.id}/slip`);
      setSlip(r?.data ?? r);
    } catch { setSlip(null); }
  };

  const downloadPayslip = async (id: string) => {
    try {
      const r: any = await api.get(`/payroll/${id}/payslip/pdf`, { responseType: 'blob' });
      const blob = new Blob([r], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `payslip-${id}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch { toast.error('Failed to download payslip'); }
  };

  const toggleSelect = (id: string) => {
    setSelected(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });
  };

  const selectAll = () => {
    const unpaid = records.filter(r => !r.is_paid).map(r => r.id);
    setSelected(new Set(unpaid));
  };

  const years = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - 2 + i);

  const renderRecordsTable = (data: PayrollRecord[], showCheckbox = false) => (
    <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 dark:bg-gray-700/50">
          <tr>
            {showCheckbox && <th className="px-4 py-2.5 w-10"><input type="checkbox" onChange={e => e.target.checked ? selectAll() : setSelected(new Set())} checked={selected.size > 0 && selected.size === records.filter(r => !r.is_paid).length} className="rounded" /></th>}
            <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Staff</th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Emp ID</th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase text-gray-500">Period</th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase text-gray-500">Basic</th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase text-gray-500">Allowances</th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase text-gray-500">Deductions</th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase text-gray-500">Net</th>
            <th className="px-4 py-2.5 text-center text-xs font-semibold uppercase text-gray-500">Status</th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
          {data.length === 0 ? (
            <tr><td colSpan={showCheckbox ? 10 : 9} className="px-4 py-8 text-center text-gray-400">No records found.</td></tr>
          ) : data.map(rec => (
            <tr key={rec.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
              {showCheckbox && (
                <td className="px-4 py-3">
                  {!rec.is_paid && <input type="checkbox" checked={selected.has(rec.id)} onChange={() => toggleSelect(rec.id)} className="rounded" />}
                </td>
              )}
              <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{rec.staff_name ?? '—'}</td>
              <td className="px-4 py-3 font-mono text-xs text-gray-500">{rec.employee_id ?? '—'}</td>
              <td className="px-4 py-3 text-gray-600">{MONTHS[(rec.month ?? 1) - 1]} {rec.year}</td>
              <td className="px-4 py-3 text-right">{fmt(rec.basic_salary ?? 0)}</td>
              <td className="px-4 py-3 text-right text-green-600">+{fmt(rec.allowances ?? 0)}</td>
              <td className="px-4 py-3 text-right text-red-600">−{fmt(rec.deductions ?? 0)}</td>
              <td className="px-4 py-3 text-right font-bold text-indigo-600">{fmt(rec.net_salary ?? 0)}</td>
              <td className="px-4 py-3 text-center">
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${rec.is_paid ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  {rec.is_paid ? 'Paid' : 'Pending'}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex justify-end gap-1">
                  <button onClick={() => openSlip(rec)} className="rounded px-2 py-1 text-xs text-indigo-600 hover:bg-indigo-50">View Slip</button>
                  <button onClick={() => downloadPayslip(rec.id)} className="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100"><Download size={12} /></button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div>
      <PageHeader title="Payroll" subtitle="Manage staff salaries and payslips" />

      {/* Tabs */}
      <div className="mb-5 flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {([
          { key: 'records', label: '📋 Payroll Records' },
          { key: 'generate', label: '⚙️ Generate Payroll' },
          { key: 'my_history', label: '👤 My History' },
        ] as const).map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t.key ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Records Tab */}
      {tab === 'records' && (
        <div>
          {/* Filters */}
          <div className="mb-4 flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-xs text-gray-500">Month</label>
              <select value={filterMonth} onChange={e => setFilterMonth(e.target.value)} className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="">All Months</option>
                {MONTHS.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Year</label>
              <select value={filterYear} onChange={e => setFilterYear(e.target.value)} className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="">All Years</option>
                {years.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-500">Status</label>
              <select value={filterPaid} onChange={e => setFilterPaid(e.target.value)} className="rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                <option value="">All</option>
                <option value="false">Pending</option>
                <option value="true">Paid</option>
              </select>
            </div>
            <button onClick={loadRecords} className="flex items-center gap-2 rounded bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-700">
              <RefreshCw size={14} /> Refresh
            </button>
            {selected.size > 0 && (
              <button onClick={handleMarkPaid} className="flex items-center gap-2 rounded bg-green-600 px-3 py-2 text-sm text-white hover:bg-green-700">
                <CheckCircle size={14} /> Mark {selected.size} Paid
              </button>
            )}
          </div>

          {/* Summary Cards */}
          {records.length > 0 && (
            <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: 'Total Records', val: records.length, color: 'text-gray-700' },
                { label: 'Total Net Salary', val: fmt(records.reduce((s, r) => s + (r.net_salary ?? 0), 0)), color: 'text-indigo-600' },
                { label: 'Paid', val: records.filter(r => r.is_paid).length, color: 'text-green-600' },
                { label: 'Pending', val: records.filter(r => !r.is_paid).length, color: 'text-yellow-600' },
              ].map(c => (
                <div key={c.label} className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
                  <p className="text-xs text-gray-500">{c.label}</p>
                  <p className={`text-xl font-bold ${c.color}`}>{c.val}</p>
                </div>
              ))}
            </div>
          )}

          {loading ? <div className="py-10 text-center text-gray-400">Loading…</div> : renderRecordsTable(records, true)}
        </div>
      )}

      {/* Generate Tab */}
      {tab === 'generate' && (
        <div className="max-w-md">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-4 text-base font-semibold text-gray-900 dark:text-white">Generate Monthly Payroll</h3>
            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Month *</label>
                <select required value={genMonth} onChange={e => setGenMonth(+e.target.value)} className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                  {MONTHS.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Year *</label>
                <select required value={genYear} onChange={e => setGenYear(+e.target.value)} className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                  {years.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Academic Year</label>
                <select value={genAcYear} onChange={e => setGenAcYear(e.target.value)} className="w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                  <option value="">— Select —</option>
                  {acYears.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
                </select>
              </div>
              <p className="text-xs text-gray-500">This will generate payroll for all active staff with salary configured. Existing records for this period won't be duplicated.</p>
              <button type="submit" disabled={generating} className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60">
                {generating ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> : <Plus size={16} />}
                {generating ? 'Generating…' : 'Generate Payroll'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* My History Tab */}
      {tab === 'my_history' && (
        <div>
          <p className="mb-4 text-sm text-gray-500">Your personal payroll history</p>
          {loading ? <div className="py-10 text-center text-gray-400">Loading…</div> : renderRecordsTable(myHistory)}
        </div>
      )}

      {/* Payslip Modal */}
      {slipModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold dark:text-white">Payslip — {MONTHS[(slipModal.month ?? 1) - 1]} {slipModal.year}</h3>
              <button onClick={() => { setSlipModal(null); setSlip(null); }} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
            </div>

            <div className="space-y-3 text-sm">
              {slip ? (
                <>
                  <div className="rounded-lg bg-indigo-50 p-4 dark:bg-indigo-900/20">
                    <p className="font-semibold text-gray-700 dark:text-gray-200">{slip.staff_name ?? slipModal.staff_name}</p>
                    <p className="text-xs text-gray-500">{slip.employee_id ?? slipModal.employee_id}</p>
                    <p className="text-xs text-gray-500">{slip.designation ?? ''} {slip.department ? `• ${slip.department}` : ''}</p>
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between"><span className="text-gray-500">Basic Salary</span><span>{fmt(slip.basic_salary ?? slipModal.basic_salary)}</span></div>
                    <div className="flex justify-between text-green-600"><span>Allowances</span><span>+{fmt(slip.allowances ?? slipModal.allowances ?? 0)}</span></div>
                    <div className="flex justify-between text-red-600"><span>Deductions</span><span>−{fmt(slip.deductions ?? slipModal.deductions ?? 0)}</span></div>
                    <div className="mt-2 flex justify-between border-t pt-2 text-base font-bold text-indigo-600">
                      <span>Net Salary</span><span>{fmt(slip.net_salary ?? slipModal.net_salary)}</span>
                    </div>
                  </div>
                  {slip.remarks && <p className="text-xs text-gray-500">Remarks: {slip.remarks}</p>}
                </>
              ) : (
                <>
                  <div className="space-y-1.5">
                    <div className="flex justify-between"><span className="text-gray-500">Staff</span><span>{slipModal.staff_name}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Period</span><span>{MONTHS[(slipModal.month ?? 1) - 1]} {slipModal.year}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Basic Salary</span><span>{fmt(slipModal.basic_salary ?? 0)}</span></div>
                    <div className="flex justify-between text-green-600"><span>Allowances</span><span>+{fmt(slipModal.allowances ?? 0)}</span></div>
                    <div className="flex justify-between text-red-600"><span>Deductions</span><span>−{fmt(slipModal.deductions ?? 0)}</span></div>
                    <div className="mt-2 flex justify-between border-t pt-2 text-base font-bold text-indigo-600">
                      <span>Net Salary</span><span>{fmt(slipModal.net_salary ?? 0)}</span>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="mt-4 flex justify-end gap-2">
              <button onClick={() => downloadPayslip(slipModal.id)} className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">
                <Download size={14} /> Download PDF
              </button>
              <button onClick={() => { setSlipModal(null); setSlip(null); }} className="rounded-lg border px-4 py-2 text-sm dark:border-gray-600">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PayrollPage;
