import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { personalExpensesApi, PersonalExpense, PersonalExpenseCategory } from '@api/personalExpenses';
import { classesApi } from '@api/classes';
import { academicYearsApi } from '@api/academicYears';
import { studentsApi } from '@api/students';
import { useAuthStore } from '@store/authStore';
import { toast } from 'sonner';
import {
  Plus, Trash2, CheckCircle, XCircle, Printer, Filter, Users,
  RefreshCw, Tag, Search,
} from 'lucide-react';

const unwrap = (r: any) => r?.data?.data ?? r?.data ?? r;
const PAYMENT_METHODS = ['cash', 'online', 'upi', 'card', 'cheque', 'neft'];
const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  partial: 'bg-orange-100 text-orange-700',
  paid: 'bg-green-100 text-green-800',
  waived: 'bg-gray-100 text-gray-600',
};

// ── Receipt Printer ───────────────────────────────────────────────────────────
function printExpenseReceipt(params: {
  schoolName: string;
  receiptNo: string;
  studentName: string;
  admissionNo?: string;
  expenseTitle: string;
  categoryName: string;
  amount: number;
  paymentMethod: string;
  paidAt: string;
  collectedBy?: string;
}) {
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>Personal Expense Receipt</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; font-size: 13px; }
    .receipt { width: 80mm; margin: 0 auto; padding: 8mm; }
    .center { text-align: center; }
    .school-name { font-size: 15px; font-weight: bold; }
    .sub { font-size: 11px; color: #555; }
    .divider { border-top: 1px dashed #999; margin: 6px 0; }
    .double { border-top: 3px double #000; margin: 6px 0; }
    table { width: 100%; border-collapse: collapse; }
    td { padding: 3px 0; vertical-align: top; }
    td:last-child { text-align: right; font-weight: 500; }
    .label { color: #555; }
    .total-row td { font-weight: bold; font-size: 14px; border-top: 1px solid #000; padding-top: 4px; }
    .stamp { margin-top: 12px; text-align: center; font-size: 11px; color: #555; }
    @media print {
      body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
    }
  </style>
</head>
<body onload="window.print(); window.close();">
  <div class="receipt">
    <div class="center">
      <p class="sub">Personal Expense Receipt</p>
    </div>
    <div class="double"></div>
    <table>
      <tr><td class="label">Receipt No</td><td>${params.receiptNo}</td></tr>
      <tr><td class="label">Date</td><td>${params.paidAt}</td></tr>
    </table>
    <div class="divider"></div>
    <table>
      <tr><td class="label">Student</td><td>${params.studentName}</td></tr>
      ${params.admissionNo ? `<tr><td class="label">Adm. No</td><td>${params.admissionNo}</td></tr>` : ''}
    </table>
    <div class="divider"></div>
    <table>
      <tr><td class="label">Description</td><td>${params.expenseTitle}</td></tr>
      <tr><td class="label">Category</td><td>${params.categoryName}</td></tr>
      <tr><td class="label">Method</td><td>${params.paymentMethod.toUpperCase()}</td></tr>
    </table>
    <div class="divider"></div>
    <table>
      <tr class="total-row"><td>Amount Paid</td><td>&#8377;${params.amount.toFixed(2)}</td></tr>
    </table>
    <div class="stamp">
      <p>Thank you!</p>
      ${params.collectedBy ? `<p>Collected by: ${params.collectedBy}</p>` : ''}
      <p style="margin-top:16px; border-top:1px solid #ccc; padding-top:6px;">
        Authorised Signatory
      </p>
    </div>
  </div>
</body>
</html>`;
  const w = window.open('', '_blank', 'width=400,height=600');
  if (w) { w.document.write(html); w.document.close(); }
}

// ── Collect Modal ─────────────────────────────────────────────────────────────
function CollectModal({
  expense, categories, schoolName, onClose, onSuccess,
}: {
  expense: PersonalExpense;
  categories: PersonalExpenseCategory[];
  schoolName: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [method, setMethod] = useState('cash');
  const [paidAt, setPaidAt] = useState(new Date().toISOString().split('T')[0]);
  const [amountPaid, setAmountPaid] = useState(String(Number(expense.balance ?? expense.amount).toFixed(2)));
  const [loading, setLoading] = useState(false);
  const catName = categories.find(c => c.id === expense.category_id)?.name ?? '—';
  const parsedAmount = parseFloat(amountPaid) || 0;
  const billedAmt = Number(expense.amount);
  const alreadyPaid = Number(expense.paid_amount ?? 0);
  const balanceDue = Number(expense.balance ?? (billedAmt - alreadyPaid));

  const collect = async () => {
    setLoading(true);
    try {
      await personalExpensesApi.markPaid(expense.id, {
        payment_method: method,
        paid_at: paidAt,
        ...(parsedAmount !== Number(expense.amount) ? { amount_paid: parsedAmount } : {}),
      });
      toast.success('Payment collected');
      printExpenseReceipt({
        schoolName,
        receiptNo: `PE-${expense.id.slice(-6).toUpperCase()}`,
        studentName: expense.student_name || expense.student_id,
        admissionNo: expense.admission_number,
        expenseTitle: expense.title,
        categoryName: catName,
        amount: parsedAmount,
        paymentMethod: method,
        paidAt,
      });
      onSuccess();
    } catch {
      toast.error('Failed to collect payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-sm shadow-xl">
        <h3 className="font-semibold text-gray-800 dark:text-white mb-1">Collect Payment</h3>
        <p className="text-xs text-gray-500 mb-4">
          <strong>{expense.student_name || 'Student'}</strong> · {expense.title}
        </p>
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 mb-4 space-y-1 text-sm">
          <div className="flex justify-between"><span className="text-gray-500">Billed</span><span className="font-medium">₹{billedAmt.toFixed(2)}</span></div>
          {alreadyPaid > 0 && <div className="flex justify-between"><span className="text-gray-500">Already Paid</span><span className="text-green-600 font-medium">₹{alreadyPaid.toFixed(2)}</span></div>}
          <div className="flex justify-between border-t border-gray-200 dark:border-gray-600 pt-1 mt-1">
            <span className="font-semibold text-red-600">Balance Due</span>
            <span className="font-bold text-red-600">₹{balanceDue.toFixed(2)}</span>
          </div>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Amount to Collect (₹) *</label>
            <input
              type="number" min="0.01" step="0.01"
              className="input-field w-full mt-1 text-lg font-bold"
              value={amountPaid}
              onChange={e => setAmountPaid(e.target.value)}
            />
            {parsedAmount > 0 && parsedAmount !== balanceDue && (
              <p className="text-xs text-amber-600 mt-1">⚠ Partial — ₹{(balanceDue - parsedAmount).toFixed(2)} will remain outstanding</p>
            )}
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Payment Method</label>
            <select className="input-field w-full mt-1" value={method} onChange={e => setMethod(e.target.value)}>
              {PAYMENT_METHODS.map(m => <option key={m} value={m}>{m.toUpperCase()}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Payment Date</label>
            <input type="date" className="input-field w-full mt-1" value={paidAt} onChange={e => setPaidAt(e.target.value)} />
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <button className="btn-primary flex-1 flex items-center justify-center gap-2"
            onClick={collect} disabled={loading || parsedAmount <= 0}>
            <CheckCircle size={15} /> {loading ? 'Processing…' : 'Collect & Print Receipt'}
          </button>
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
const PersonalExpensesPage: React.FC = () => {
  const qc = useQueryClient();
  const { schoolInfo } = useAuthStore();
  const schoolName = schoolInfo?.name ?? 'School';

  // Filters
  const [academicYearId, setAcademicYearId] = useState('');
  const [classId, setClassId] = useState('');
  const [sectionId, setSectionId] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [page, setPage] = useState(0);
  const limit = 50;

  // UI state
  const [showBulkForm, setShowBulkForm] = useState(false);
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [collectingExpense, setCollectingExpense] = useState<PersonalExpense | null>(null);

  // Bulk form state
  const [bulkForm, setBulkForm] = useState({
    title: '', amount: '', category_id: '', expense_date: new Date().toISOString().split('T')[0], notes: '',
  });
  const [bulkTargetClassId, setBulkTargetClassId] = useState('');
  const [bulkTargetSectionId, setBulkTargetSectionId] = useState('');
  const [bulkStudents, setBulkStudents] = useState<any[]>([]);
  const [bulkStudentsLoading, setBulkStudentsLoading] = useState(false);
  const [bulkStudentSearch, setBulkStudentSearch] = useState('');
  const [selectedStudentIds, setSelectedStudentIds] = useState<Set<string>>(new Set());

  // Category form
  const [newCatName, setNewCatName] = useState('');

  // Loaded data
  const [classes, setClasses] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [bulkSections, setBulkSections] = useState<any[]>([]);

  // ── Queries ────────────────────────────────────────────────────────────────
  const yearsQ = useQuery({
    queryKey: ['academic-years'],
    queryFn: async () => {
      const data = unwrap(await academicYearsApi.list());
      return Array.isArray(data) ? data : (data?.items ?? []);
    },
  });

  const years = yearsQ.data ?? [];
  const currentYear = years.find((y: any) => y.is_current) ?? years[0];

  useEffect(() => {
    if (currentYear?.id && !academicYearId) setAcademicYearId(currentYear.id);
  }, [currentYear]);

  useEffect(() => {
    if (!academicYearId) return;
    classesApi.list(academicYearId).then(r => {
      const data = unwrap(r);
      setClasses(Array.isArray(data) ? data : (data?.items ?? []));
    });
  }, [academicYearId]);

  useEffect(() => {
    if (!classId) { setSections([]); setSectionId(''); return; }
    classesApi.listSections(classId).then(r => {
      const data = unwrap(r);
      setSections(Array.isArray(data) ? data : (data?.items ?? []));
      setSectionId('');
    });
  }, [classId]);

  useEffect(() => {
    if (!bulkTargetClassId) { setBulkSections([]); setBulkTargetSectionId(''); setBulkStudents([]); setSelectedStudentIds(new Set()); return; }
    classesApi.listSections(bulkTargetClassId).then(r => {
      const data = unwrap(r);
      setBulkSections(Array.isArray(data) ? data : (data?.items ?? []));
      setBulkTargetSectionId('');
    });
    // Load students for entire class immediately
    setBulkStudentsLoading(true);
    studentsApi.listStudents({ class_id: bulkTargetClassId, limit: 500 }).then((r: any) => {
      const data = unwrap(r);
      const list = Array.isArray(data) ? data : (data?.students ?? data?.items ?? []);
      setBulkStudents(list);
      setSelectedStudentIds(new Set(list.map((s: any) => s.id)));
    }).finally(() => setBulkStudentsLoading(false));
  }, [bulkTargetClassId]);

  useEffect(() => {
    if (!bulkTargetClassId) return;
    setBulkStudentsLoading(true);
    studentsApi.listStudents({ class_id: bulkTargetClassId, section_id: bulkTargetSectionId || undefined, limit: 500 }).then((r: any) => {
      const data = unwrap(r);
      const list = Array.isArray(data) ? data : (data?.students ?? data?.items ?? []);
      setBulkStudents(list);
      setSelectedStudentIds(new Set(list.map((s: any) => s.id)));
    }).finally(() => setBulkStudentsLoading(false));
  }, [bulkTargetSectionId]);

  const categoriesQ = useQuery({
    queryKey: ['personal-expense-categories'],
    queryFn: async () => {
      const data = unwrap(await personalExpensesApi.listCategories());
      return Array.isArray(data) ? data : (data?.items ?? []) as PersonalExpenseCategory[];
    },
  });
  const categories = categoriesQ.data ?? [];

  const schoolSummaryQ = useQuery({
    queryKey: ['pe-school-summary'],
    queryFn: async () => unwrap(await personalExpensesApi.getSchoolSummary()),
  });
  const summary = schoolSummaryQ.data ?? {};

  const expensesQ = useQuery({
    queryKey: ['personal-expenses', 'school', classId, sectionId, filterStatus, page],
    queryFn: async () => {
      const data = unwrap(await personalExpensesApi.list({
        class_id: classId || undefined,
        section_id: sectionId || undefined,
        status: filterStatus || undefined,
        skip: page * limit,
        limit,
      }));
      return data as { expenses: PersonalExpense[]; total: number };
    },
  });

  const expenses = expensesQ.data?.expenses ?? [];
  const totalExpenses = expensesQ.data?.total ?? 0;

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['personal-expenses'] });
    qc.invalidateQueries({ queryKey: ['pe-school-summary'] });
  };

  // ── Mutations ──────────────────────────────────────────────────────────────
  const bulkMutation = useMutation({
    mutationFn: () => personalExpensesApi.bulkAssign({
      title: bulkForm.title,
      amount: parseFloat(bulkForm.amount),
      category_id: bulkForm.category_id || undefined,
      expense_date: bulkForm.expense_date || undefined,
      notes: bulkForm.notes || undefined,
      student_ids: Array.from(selectedStudentIds),
    }),
    onSuccess: (r: any) => {
      const count = r?.data?.data?.assigned_count ?? r?.data?.assigned_count ?? selectedStudentIds.size;
      toast.success(`Assigned to ${count} students`);
      setBulkForm({ title: '', amount: '', category_id: '', expense_date: new Date().toISOString().split('T')[0], notes: '' });
      setBulkTargetClassId(''); setBulkTargetSectionId('');
      setBulkStudents([]); setSelectedStudentIds(new Set());
      setShowBulkForm(false);
      invalidate();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? 'Failed to assign'),
  });

  const waiveMutation = useMutation({
    mutationFn: (id: string) => personalExpensesApi.waiveExpense(id),
    onSuccess: () => { toast.success('Expense waived'); invalidate(); },
    onError: () => toast.error('Failed to waive'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => personalExpensesApi.deleteExpense(id),
    onSuccess: () => { toast.success('Expense deleted'); invalidate(); },
    onError: () => toast.error('Failed to delete'),
  });

  const addCatMutation = useMutation({
    mutationFn: () => personalExpensesApi.createCategory({ name: newCatName }),
    onSuccess: () => {
      toast.success('Category added');
      setNewCatName('');
      qc.invalidateQueries({ queryKey: ['personal-expense-categories'] });
    },
    onError: () => toast.error('Failed to add category'),
  });

  const getCatName = (id?: string) => categories.find(c => c.id === id)?.name ?? '—';

  const reprintReceipt = (exp: PersonalExpense) => {
    printExpenseReceipt({
      schoolName,
      receiptNo: `PE-${exp.id.slice(-6).toUpperCase()}`,
      studentName: exp.student_name || exp.student_id,
      admissionNo: exp.admission_number,
      expenseTitle: exp.title,
      categoryName: getCatName(exp.category_id),
      amount: exp.amount,
      paymentMethod: exp.payment_method || 'cash',
      paidAt: exp.paid_at || '',
    });
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800 dark:text-white">Personal Expenses</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Student-level charges — stationery, uniforms, trips etc. Independent from school fees.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCategoryForm(s => !s)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
            <Tag size={14} /> Categories
          </button>
          <button onClick={() => setShowBulkForm(s => !s)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700">
            <Plus size={14} /> Assign Expense
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total Assigned', value: summary.total_amount, color: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300', count: summary.total_count },
          { label: 'Collected', value: summary.paid_amount, color: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300' },
          { label: 'Pending', value: summary.pending_amount, color: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' },
          { label: 'Balance Due', value: summary.balance_due, color: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300' },
        ].map(card => (
          <div key={card.label} className={`rounded-xl p-4 ${card.color}`}>
            <p className="text-xs font-medium opacity-70">{card.label}</p>
            {card.count !== undefined && (
              <p className="text-xs opacity-60">{card.count} records</p>
            )}
            <p className="text-xl font-bold mt-1">
              ₹{(card.value ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </p>
          </div>
        ))}
      </div>

      {/* Category Manager */}
      {showCategoryForm && (
        <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4 border border-gray-200 dark:border-gray-600">
          <p className="text-sm font-semibold text-gray-700 dark:text-white mb-3">Expense Categories</p>
          <div className="flex flex-wrap gap-2 mb-3">
            {categories.map(c => (
              <span key={c.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-full px-3 py-1 text-sm text-gray-700 dark:text-gray-200">
                {c.name}
              </span>
            ))}
            {categories.length === 0 && <p className="text-sm text-gray-400">No categories yet.</p>}
          </div>
          <div className="flex gap-2">
            <input className="input-field flex-1" placeholder="New category name" value={newCatName} onChange={e => setNewCatName(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && newCatName) addCatMutation.mutate(); }} />
            <button className="btn-primary" onClick={() => newCatName && addCatMutation.mutate()} disabled={!newCatName || addCatMutation.isPending}>
              Add
            </button>
          </div>
        </div>
      )}

      {/* Bulk Assign Form */}
      {showBulkForm && (
        <div className="bg-blue-50 dark:bg-gray-700 rounded-xl p-5 border border-blue-200 dark:border-gray-600 space-y-4">
          <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
            <Users size={16} /> Assign Expense to Students
          </h3>

          {/* Expense Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Expense Title *</label>
              <input className="input-field w-full mt-1" value={bulkForm.title} onChange={e => setBulkForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. Term 1 Stationery Pack" />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Amount (₹) *</label>
              <input type="number" className="input-field w-full mt-1" value={bulkForm.amount} onChange={e => setBulkForm(f => ({ ...f, amount: e.target.value }))} placeholder="0.00" min="0" step="0.01" />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Category</label>
              <select className="input-field w-full mt-1" value={bulkForm.category_id} onChange={e => setBulkForm(f => ({ ...f, category_id: e.target.value }))}>
                <option value="">— None —</option>
                {categories.filter(c => c.is_active).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Date</label>
              <input type="date" className="input-field w-full mt-1" value={bulkForm.expense_date} onChange={e => setBulkForm(f => ({ ...f, expense_date: e.target.value }))} />
            </div>
            <div className="sm:col-span-2">
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Notes (optional)</label>
              <input className="input-field w-full mt-1" value={bulkForm.notes} onChange={e => setBulkForm(f => ({ ...f, notes: e.target.value }))} placeholder="Optional note" />
            </div>
          </div>

          {/* Student Picker */}
          <div className="border border-blue-200 dark:border-gray-500 rounded-xl overflow-hidden bg-white dark:bg-gray-800">
            <div className="p-3 border-b border-blue-100 dark:border-gray-600 bg-blue-50/60 dark:bg-gray-700 flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-gray-700 dark:text-white mr-auto">Select Students</p>
              <select className="input-field py-1 text-sm" style={{minWidth:'160px'}} value={bulkTargetClassId} onChange={e => { setBulkTargetClassId(e.target.value); setBulkStudentSearch(''); }}>
                <option value="">— Pick Class —</option>
                {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              {bulkTargetClassId && (
                <select className="input-field py-1 text-sm" style={{minWidth:'140px'}} value={bulkTargetSectionId} onChange={e => { setBulkTargetSectionId(e.target.value); setBulkStudentSearch(''); }}>
                  <option value="">All Sections</option>
                  {bulkSections.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              )}
              {bulkStudents.length > 0 && (
                <div className="relative">
                  <Search size={13} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input className="input-field py-1 pl-7 text-sm" style={{width:'160px'}} placeholder="Search student…"
                    value={bulkStudentSearch} onChange={e => setBulkStudentSearch(e.target.value)} />
                </div>
              )}
            </div>

            {!bulkTargetClassId ? (
              <p className="text-sm text-gray-400 text-center py-8">Select a class to see students</p>
            ) : bulkStudentsLoading ? (
              <p className="text-sm text-gray-400 text-center py-8">Loading students…</p>
            ) : bulkStudents.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No students found in this class/section</p>
            ) : (() => {
              const filtered = bulkStudents.filter((s: any) =>
                !bulkStudentSearch ||
                `${s.first_name} ${s.last_name} ${s.admission_number}`.toLowerCase().includes(bulkStudentSearch.toLowerCase())
              );
              const allFilteredSelected = filtered.length > 0 && filtered.every((s: any) => selectedStudentIds.has(s.id));
              return (
                <div>
                  {/* Select All row */}
                  <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-750 flex items-center gap-3">
                    <input type="checkbox" checked={allFilteredSelected}
                      onChange={e => {
                        setSelectedStudentIds(prev => {
                          const next = new Set(prev);
                          filtered.forEach((s: any) => e.target.checked ? next.add(s.id) : next.delete(s.id));
                          return next;
                        });
                      }} className="w-4 h-4 rounded accent-indigo-600" />
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      {selectedStudentIds.size} / {bulkStudents.length} selected
                      {filtered.length !== bulkStudents.length && ` (showing ${filtered.length})`}
                    </span>
                  </div>
                  {/* Student list */}
                  <div className="max-h-64 overflow-y-auto divide-y divide-gray-50 dark:divide-gray-700">
                    {filtered.map((s: any) => (
                      <label key={s.id} className="flex items-center gap-3 px-4 py-2 hover:bg-indigo-50 dark:hover:bg-gray-700/60 cursor-pointer">
                        <input type="checkbox" checked={selectedStudentIds.has(s.id)}
                          onChange={e => {
                            setSelectedStudentIds(prev => {
                              const next = new Set(prev);
                              e.target.checked ? next.add(s.id) : next.delete(s.id);
                              return next;
                            });
                          }} className="w-4 h-4 rounded accent-indigo-600" />
                        <div>
                          <p className="text-sm font-medium text-gray-800 dark:text-white">{s.first_name} {s.last_name}</p>
                          {s.admission_number && <p className="text-xs text-gray-400">{s.admission_number}</p>}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>

          <div className="flex gap-2">
            <button className="btn-primary flex items-center gap-2" onClick={() => bulkMutation.mutate()}
              disabled={bulkMutation.isPending || !bulkForm.title || !bulkForm.amount || selectedStudentIds.size === 0}>
              <Users size={14} /> {bulkMutation.isPending ? 'Assigning…' : `Assign to ${selectedStudentIds.size} Student${selectedStudentIds.size !== 1 ? 's' : ''}`}
            </button>
            <button className="btn-secondary" onClick={() => { setShowBulkForm(false); setBulkTargetClassId(''); setBulkStudents([]); setSelectedStudentIds(new Set()); }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <Filter size={14} className="text-gray-400" />
        <select className="input-field py-1.5 text-sm" value={academicYearId} onChange={e => { setAcademicYearId(e.target.value); setClassId(''); setSectionId(''); }}>
          {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
        </select>
        <select className="input-field py-1.5 text-sm" value={classId} onChange={e => setClassId(e.target.value)}>
          <option value="">All Classes</option>
          {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        {classId && (
          <select className="input-field py-1.5 text-sm" value={sectionId} onChange={e => setSectionId(e.target.value)}>
            <option value="">All Sections</option>
            {sections.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        )}
        <select className="input-field py-1.5 text-sm" value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(0); }}>
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="paid">Paid</option>
          <option value="waived">Waived</option>
        </select>
        <button onClick={() => expensesQ.refetch()} className="p-2 text-gray-500 hover:text-indigo-600">
          <RefreshCw size={14} />
        </button>
        <span className="ml-auto text-xs text-gray-500">{totalExpenses} records</span>
      </div>

      {/* Expenses Table */}
      {expensesQ.isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : expenses.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-sm">No personal expenses found.</p>
          <p className="text-xs mt-1">Use "Assign to Class" to add expenses for a group of students.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="px-4 py-3 text-left">Student</th>
                <th className="px-4 py-3 text-left">Expense</th>
                <th className="px-4 py-3 text-left">Category</th>
                <th className="px-4 py-3 text-left">Date</th>
                <th className="px-4 py-3 text-right">Billed</th>
                <th className="px-4 py-3 text-right">Collected</th>
                <th className="px-4 py-3 text-right">Balance</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {expenses.map(exp => (
                <tr key={exp.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/40 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-800 dark:text-white">{exp.student_name || '—'}</p>
                    {exp.admission_number && <p className="text-xs text-gray-400">{exp.admission_number}</p>}
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-gray-800 dark:text-white">{exp.title}</p>
                    {exp.notes && <p className="text-xs text-gray-400">{exp.notes}</p>}
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{getCatName(exp.category_id)}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{exp.expense_date ?? '—'}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-800 dark:text-white">
                    ₹{Number(exp.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 text-right text-green-600 font-medium">
                    {Number(exp.paid_amount ?? 0) > 0 ? `₹${Number(exp.paid_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-red-600">
                    {Number(exp.balance ?? (exp.amount - (exp.paid_amount ?? 0))) > 0
                      ? `₹${Number(exp.balance ?? (exp.amount - (exp.paid_amount ?? 0))).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[exp.status] ?? ''}`}>
                      {exp.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      {(exp.status === 'pending' || exp.status === 'partial') && (
                        <>
                          <button title="Collect Payment"
                            onClick={() => setCollectingExpense(exp)}
                            className="p-1.5 rounded text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30">
                            <CheckCircle size={15} />
                          </button>
                          <button title="Waive"
                            onClick={() => { if (confirm('Waive this expense?')) waiveMutation.mutate(exp.id); }}
                            className="p-1.5 rounded text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700">
                            <XCircle size={15} />
                          </button>
                        </>
                      )}
                      {(exp.status === 'paid' || exp.status === 'partial') && (
                        <button title="Reprint Receipt" onClick={() => reprintReceipt(exp)}
                          className="p-1.5 rounded text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30">
                          <Printer size={15} />
                        </button>
                      )}
                      <button title="Delete"
                        onClick={() => { if (confirm('Delete this expense?')) deleteMutation.mutate(exp.id); }}
                        className="p-1.5 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalExpenses > limit && (
        <div className="flex items-center justify-center gap-3">
          <button className="btn-secondary text-sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>Previous</button>
          <span className="text-sm text-gray-500">Page {page + 1} of {Math.ceil(totalExpenses / limit)}</span>
          <button className="btn-secondary text-sm" onClick={() => setPage(p => p + 1)} disabled={(page + 1) * limit >= totalExpenses}>Next</button>
        </div>
      )}

      {/* Collect Modal */}
      {collectingExpense && (
        <CollectModal
          expense={collectingExpense}
          categories={categories}
          schoolName={schoolName}
          onClose={() => setCollectingExpense(null)}
          onSuccess={() => { setCollectingExpense(null); invalidate(); }}
        />
      )}
    </div>
  );
};

export default PersonalExpensesPage;
