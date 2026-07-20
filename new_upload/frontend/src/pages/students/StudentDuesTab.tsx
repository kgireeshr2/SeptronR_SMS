/**
 * StudentDuesTab — unified screen showing ALL dues for a student:
 *   • Fee balance (from feesV2 ledger) — read-only summary
 *   • Personal expenses — pending / partial — with inline collection + receipt
 *   • Combined total shown prominently at top
 */
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { personalExpensesApi, PersonalExpense, PersonalExpenseCategory } from '@api/personalExpenses';
import { feesV2Api } from '@api/feesV2';
import { academicYearsApi } from '@api/academicYears';
import { useAuthStore } from '@store/authStore';
import { formatDate } from '@utils/formatters';
import { toast } from 'sonner';
import { CheckCircle, Printer, AlertCircle, Receipt, FileText } from 'lucide-react';

const unwrap = (r: any) => r?.data ?? r;
const PAYMENT_METHODS = ['cash', 'online', 'upi', 'card', 'cheque', 'neft'];
const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  partial: 'bg-orange-100 text-orange-700',
  paid: 'bg-green-100 text-green-800',
  waived: 'bg-gray-100 text-gray-600',
};

function printFullReport(params: {
  schoolName: string;
  studentName: string;
  admissionNo?: string;
  academicYearName: string;
  printDate: string;
  ledger: any;
  expenses: any[];
  categories: any[];
  feeDue: number;
  peDue: number;
  combinedDue: number;
}) {
  const fmt = (n: number) => '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2 });

  // Build fee rows
  const feeRows = (params.ledger?.entries ?? []).map((e: any) => `
    <tr>
      <td>${e.fee_type_name}</td>
      <td class="num">${fmt(e.amount_due)}</td>
      <td class="num green">${fmt(e.amount_paid)}</td>
      <td class="num ${Number(e.balance) > 0 ? 'red' : 'green'}">${Number(e.balance) > 0 ? fmt(e.balance) : '✓ Paid'}</td>
    </tr>`).join('');

  // Build personal expense rows
  const peRows = params.expenses.map((e: any) => {
    const cat = params.categories.find((c: any) => c.id === e.category_id)?.name ?? '—';
    const statusLabel = e.status === 'paid' ? 'Paid' : e.status === 'partial' ? 'Partial' : e.status === 'waived' ? 'Waived' : 'Pending';
    const statusClass = e.status === 'paid' ? 'green' : e.status === 'waived' ? 'gray' : e.status === 'partial' ? 'orange' : 'red';
    return `
    <tr>
      <td>${e.title}<br/><small class="gray">${cat} · ${e.expense_date ?? ''}</small></td>
      <td class="num">${fmt(e.amount)}</td>
      <td class="num green">${Number(e.paid_amount ?? 0) > 0 ? fmt(e.paid_amount) : '—'}</td>
      <td class="num ${Number(e.balance ?? e.amount) > 0 ? 'red' : 'green'}">${Number(e.balance ?? e.amount) > 0 ? fmt(e.balance ?? e.amount) : '—'}</td>
      <td class="center ${statusClass}">${statusLabel}</td>
    </tr>`;
  }).join('');

  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Student Due Report</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{font-family:Arial,sans-serif;font-size:12px;color:#222;padding:16px;}
    h1{font-size:18px;font-weight:bold;text-align:center;}
    .sub{text-align:center;font-size:11px;color:#555;margin-bottom:4px;}
    .meta{display:flex;justify-content:space-between;font-size:11px;color:#555;margin:8px 0 4px;}
    .dbl{border-top:3px double #000;margin:6px 0;}
    .div{border-top:1px dashed #aaa;margin:6px 0;}
    h2{font-size:13px;font-weight:bold;margin:10px 0 4px;background:#f3f4f6;padding:4px 8px;border-radius:4px;}
    table{width:100%;border-collapse:collapse;margin-bottom:8px;}
    th{background:#f3f4f6;font-size:11px;text-transform:uppercase;padding:4px 6px;text-align:left;}
    td{padding:4px 6px;border-bottom:1px solid #eee;vertical-align:top;}
    .num{text-align:right;font-variant-numeric:tabular-nums;}
    .center{text-align:center;}
    .red{color:#dc2626;font-weight:600;}
    .green{color:#16a34a;}
    .orange{color:#ea580c;font-weight:600;}
    .gray{color:#6b7280;}
    tfoot td{font-weight:bold;border-top:2px solid #000;font-size:12px;}
    .summary{margin-top:12px;border:2px solid #000;border-radius:6px;overflow:hidden;}
    .summary-row{display:flex;justify-content:space-between;padding:6px 12px;border-bottom:1px solid #ddd;font-size:13px;}
    .summary-row:last-child{border-bottom:none;background:#fee2e2;font-weight:bold;font-size:15px;}
    .summary-row.ok{background:#dcfce7;}
    small{font-size:10px;}
    @media print{body{print-color-adjust:exact;-webkit-print-color-adjust:exact;}}
  </style></head>
  <body onload="window.print();window.close();">
    <h1>${params.schoolName}</h1>
    <p class="sub">Student Due & Collection Report</p>
    <div class="dbl"></div>
    <div class="meta">
      <span><b>Student:</b> ${params.studentName}${params.admissionNo ? ' (' + params.admissionNo + ')' : ''}</span>
      <span><b>Academic Year:</b> ${params.academicYearName}</span>
    </div>
    <div class="meta"><span><b>Print Date:</b> ${params.printDate}</span></div>
    <div class="div"></div>

    ${params.ledger?.entries?.length > 0 ? `
    <h2>📋 Fee Assignments — ${params.ledger.fee_master_name ?? ''}</h2>
    <table>
      <thead><tr><th>Fee Type</th><th class="num">Billed</th><th class="num">Paid</th><th class="num">Balance</th></tr></thead>
      <tbody>${feeRows}</tbody>
      <tfoot><tr>
        <td>Total</td>
        <td class="num">${fmt(params.ledger.total_due ?? 0)}</td>
        <td class="num green">${fmt(params.ledger.total_paid ?? 0)}</td>
        <td class="num ${params.feeDue > 0 ? 'red' : 'green'}">${fmt(params.feeDue)}</td>
      </tr></tfoot>
    </table>` : '<p class="gray" style="margin:4px 0 8px">No fee assignments found.</p>'}

    ${params.expenses.length > 0 ? `
    <h2>🧾 Personal Expenses</h2>
    <table>
      <thead><tr><th>Description</th><th class="num">Billed</th><th class="num">Paid</th><th class="num">Balance</th><th class="center">Status</th></tr></thead>
      <tbody>${peRows}</tbody>
      <tfoot><tr>
        <td>Total</td>
        <td class="num">${fmt(params.expenses.reduce((s: number, e: any) => s + Number(e.amount), 0))}</td>
        <td class="num green">${fmt(params.expenses.reduce((s: number, e: any) => s + Number(e.paid_amount ?? 0), 0))}</td>
        <td class="num ${params.peDue > 0 ? 'red' : 'green'}">${fmt(params.peDue)}</td>
        <td></td>
      </tr></tfoot>
    </table>` : '<p class="gray" style="margin:4px 0 8px">No personal expenses recorded.</p>'}

    <div class="summary">
      <div class="summary-row"><span>Fee Balance Due</span><span class="${params.feeDue > 0 ? 'red' : 'green'}">${fmt(params.feeDue)}</span></div>
      <div class="summary-row"><span>Personal Expense Due</span><span class="${params.peDue > 0 ? 'orange' : 'green'}">${fmt(params.peDue)}</span></div>
      <div class="summary-row ${params.combinedDue === 0 ? 'ok' : ''}"><span>TOTAL OUTSTANDING</span><span class="${params.combinedDue > 0 ? 'red' : 'green'}">${fmt(params.combinedDue)}</span></div>
    </div>
    <p style="margin-top:20px;text-align:center;font-size:10px;color:#888;">Generated by ${params.schoolName} — SeptroSchool</p>
  </body></html>`;

  const w = window.open('', '_blank', 'width=800,height=900');
  if (w) { w.document.write(html); w.document.close(); }
}

function printExpenseReceipt(params: {
  schoolName: string; receiptNo: string; studentName: string; admissionNo?: string;
  expenseTitle: string; categoryName: string; amount: number; paymentMethod: string; paidAt: string;
}) {
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Receipt</title>
  <style>*{box-sizing:border-box;margin:0;padding:0;}body{font-family:Arial,sans-serif;font-size:13px;}
  .r{width:80mm;margin:0 auto;padding:8mm;}.center{text-align:center;}.sn{font-size:15px;font-weight:bold;}
  .sub{font-size:11px;color:#555;}.div{border-top:1px dashed #999;margin:6px 0;}
  .dbl{border-top:3px double #000;margin:6px 0;}table{width:100%;border-collapse:collapse;}
  td{padding:3px 0;vertical-align:top;}td:last-child{text-align:right;font-weight:500;}
  .lbl{color:#555;}.tot td{font-weight:bold;font-size:14px;border-top:1px solid #000;padding-top:4px;}
  .stmp{margin-top:12px;text-align:center;font-size:11px;color:#555;}
  @media print{body{print-color-adjust:exact;-webkit-print-color-adjust:exact;}}</style></head>
  <body onload="window.print();window.close();">
  <div class="r"><div class="center">
  <p class="sub">Personal Expense Receipt</p></div><div class="dbl"></div>
  <table><tr><td class="lbl">Receipt No</td><td>${params.receiptNo}</td></tr>
  <tr><td class="lbl">Date</td><td>${params.paidAt}</td></tr></table><div class="div"></div>
  <table><tr><td class="lbl">Student</td><td>${params.studentName}</td></tr>
  ${params.admissionNo ? `<tr><td class="lbl">Adm. No</td><td>${params.admissionNo}</td></tr>` : ''}</table>
  <div class="div"></div>
  <table><tr><td class="lbl">Description</td><td>${params.expenseTitle}</td></tr>
  <tr><td class="lbl">Category</td><td>${params.categoryName}</td></tr>
  <tr><td class="lbl">Method</td><td>${params.paymentMethod.toUpperCase()}</td></tr></table>
  <div class="div"></div><table><tr class="tot"><td>Amount Paid</td><td>&#8377;${params.amount.toFixed(2)}</td></tr></table>
  <div class="stmp"><p>Thank you!</p>
  <p style="margin-top:16px;border-top:1px solid #ccc;padding-top:6px;">Authorised Signatory</p></div>
  </div></body></html>`;
  const w = window.open('', '_blank', 'width=400,height=600');
  if (w) { w.document.write(html); w.document.close(); }
}

interface Props {
  studentId: string;
  studentName?: string;
  admissionNumber?: string;
}

const StudentDuesTab: React.FC<Props> = ({ studentId, studentName, admissionNumber }) => {
  const qc = useQueryClient();
  const { schoolInfo } = useAuthStore();
  const schoolName = schoolInfo?.name ?? 'School';

  const [academicYearId, setAcademicYearId] = useState('');
  const [collectingExp, setCollectingExp] = useState<PersonalExpense | null>(null);
  const [payForm, setPayForm] = useState({ payment_method: 'cash', paid_at: new Date().toISOString().split('T')[0], amount_paid: '' });

  // Load academic years to get current
  const yearsQ = useQuery({
    queryKey: ['academic-years'],
    queryFn: async () => {
      const d = unwrap(await academicYearsApi.list());
      return Array.isArray(d) ? d : (d?.items ?? []);
    },
  });
  const years = yearsQ.data ?? [];

  useEffect(() => {
    if (years.length && !academicYearId) {
      const cur = years.find((y: any) => y.is_current) ?? years[0];
      if (cur) setAcademicYearId(cur.id);
    }
  }, [years]);

  // Personal expense categories
  const categoriesQ = useQuery({
    queryKey: ['personal-expense-categories'],
    queryFn: async () => {
      const d = unwrap(await personalExpensesApi.listCategories());
      return Array.isArray(d) ? d : (d?.items ?? []) as PersonalExpenseCategory[];
    },
  });
  const categories = categoriesQ.data ?? [];

  // Personal expenses for this student
  const expensesQ = useQuery({
    queryKey: ['personal-expenses', studentId],
    queryFn: async () => {
      const d = unwrap(await personalExpensesApi.listByStudent(studentId));
      return d as { expenses: PersonalExpense[]; summary: any };
    },
  });
  const expenses = expensesQ.data?.expenses ?? [];
  const peSummary = expensesQ.data?.summary ?? {};
  const dueExpenses = expenses.filter(e => e.status === 'pending' || e.status === 'partial');

  // Fee ledger — now returns a list of ledgers (one per fee master)
  const ledgerQ = useQuery({
    queryKey: ['student-ledger', studentId, academicYearId],
    queryFn: async () => {
      const d = unwrap(await feesV2Api.getStudentLedger(studentId, academicYearId));
      return Array.isArray(d) ? d : (d ? [d] : []) as any[];
    },
    enabled: !!academicYearId,
  });
  const ledgers: any[] = ledgerQ.data ?? [];
  // Sum across all assigned fee masters
  const feeDue: number = ledgers.reduce((s, l) => s + (l.total_balance ?? 0), 0);
  const feePaid: number = ledgers.reduce((s, l) => s + (l.total_paid ?? 0), 0);

  // Single aggregated view of the ledgers for the read-only Fee Dues summary
  // below. null when there are no assignments (summary block stays hidden).
  const ledger: any =
    ledgers.length === 0
      ? null
      : ledgers.length === 1
        ? ledgers[0]
        : {
            fee_master_id: ledgers[0]?.fee_master_id ?? null,
            fee_master_name: ledgers
              .map((l: any) => l.fee_master_name)
              .filter(Boolean)
              .join(', '),
            entries: ledgers.flatMap((l: any) => l.entries ?? []),
            total_balance: ledgers.reduce((s: number, l: any) => s + (l.total_balance ?? 0), 0),
          };

  const peDue: number = peSummary.balance_due ?? 0;
  const combinedDue = feeDue + peDue;

  const invalidatePE = () => qc.invalidateQueries({ queryKey: ['personal-expenses', studentId] });

  // Collect personal expense
  const collectMutation = useMutation({
    mutationFn: (id: string) => {
      const parsedAmt = parseFloat(payForm.amount_paid);
      return personalExpensesApi.markPaid(id, {
        payment_method: payForm.payment_method,
        paid_at: payForm.paid_at,
        amount_paid: parsedAmt > 0 ? parsedAmt : undefined,
      });
    },
    onSuccess: (_data, _id) => {
      toast.success('Payment collected!');
      const exp = collectingExp;
      setCollectingExp(null);
      invalidatePE();
      if (exp) {
        const cat = categories.find(c => c.id === exp.category_id);
        const parsedAmt = parseFloat(payForm.amount_paid);
        printExpenseReceipt({
          schoolName,
          receiptNo: `PE-${exp.id.slice(-6).toUpperCase()}`,
          studentName: studentName ?? 'Student',
          admissionNo: admissionNumber,
          expenseTitle: exp.title,
          categoryName: cat?.name ?? 'General',
          amount: parsedAmt > 0 ? parsedAmt : Number(exp.balance ?? exp.amount),
          paymentMethod: payForm.payment_method,
          paidAt: payForm.paid_at,
        });
      }
    },
    onError: () => toast.error('Failed to collect payment'),
  });

  const getCatName = (id?: string) => categories.find(c => c.id === id)?.name ?? '—';

  const yearName = years.find((y: any) => y.id === academicYearId)?.name ?? academicYearId;

  const handlePrintReport = () => {
    printFullReport({
      schoolName,
      studentName: studentName ?? 'Student',
      admissionNo: admissionNumber,
      academicYearName: yearName,
      printDate: formatDate(new Date()),
      ledger: ledgers.length === 1 ? ledgers[0] : ledgers.length > 1 ? {
        fee_master_name: ledgers.map((l: any) => l.fee_master_name).join(', '),
        entries: ledgers.flatMap((l: any) => l.entries),
        total_due: ledgers.reduce((s: number, l: any) => s + l.total_due, 0),
        total_paid: ledgers.reduce((s: number, l: any) => s + l.total_paid, 0),
        total_discount: ledgers.reduce((s: number, l: any) => s + l.total_discount, 0),
      } : null,
      expenses,
      categories,
      feeDue,
      peDue,
      combinedDue,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header with Print button */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Collections &amp; Dues</h2>
        <button
          onClick={handlePrintReport}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <FileText size={15} /> Print Full Report
        </button>
      </div>

      {/* Combined Due Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-blue-50 dark:bg-blue-900/30 rounded-xl p-4">
          <p className="text-xs font-medium text-blue-600 dark:text-blue-300 mb-1">Fee Balance Due</p>
          <p className="text-xl font-bold text-blue-700 dark:text-blue-200">
            ₹{Number(feeDue).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-blue-500 mt-1">
              Paid: ₹{Number(feePaid).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </p>
        </div>
        <div className="bg-orange-50 dark:bg-orange-900/30 rounded-xl p-4">
          <p className="text-xs font-medium text-orange-600 dark:text-orange-300 mb-1">Personal Expense Due</p>
          <p className="text-xl font-bold text-orange-700 dark:text-orange-200">
            ₹{Number(peDue).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
          {peSummary.paid_amount > 0 && (
            <p className="text-xs text-orange-500 mt-1">
              Paid: ₹{Number(peSummary.paid_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </p>
          )}
        </div>
        <div className={`rounded-xl p-4 ${combinedDue > 0 ? 'bg-red-50 dark:bg-red-900/30' : 'bg-green-50 dark:bg-green-900/30'}`}>
          <p className={`text-xs font-medium mb-1 ${combinedDue > 0 ? 'text-red-600 dark:text-red-300' : 'text-green-600 dark:text-green-300'}`}>
            Total Outstanding
          </p>
          <p className={`text-2xl font-bold ${combinedDue > 0 ? 'text-red-700 dark:text-red-200' : 'text-green-700 dark:text-green-200'}`}>
            ₹{Number(combinedDue).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
          {combinedDue === 0 && <p className="text-xs text-green-600 mt-1">All dues cleared ✓</p>}
        </div>
      </div>

      {/* Personal Expenses Due */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
          <Receipt size={15} /> Personal Expenses — Pending Collection
          {dueExpenses.length > 0 && (
            <span className="ml-1 bg-orange-100 text-orange-700 rounded-full px-2 py-0.5 text-xs">{dueExpenses.length}</span>
          )}
        </h3>
        {dueExpenses.length === 0 ? (
          <div className="text-center py-8 text-gray-400 border border-dashed border-gray-200 dark:border-gray-700 rounded-xl">
            <p className="text-sm">No pending personal expenses</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-2 text-left">Expense</th>
                  <th className="px-4 py-2 text-left">Category</th>
                  <th className="px-4 py-2 text-left">Date</th>
                  <th className="px-4 py-2 text-right">Billed</th>
                  <th className="px-4 py-2 text-right">Collected</th>
                  <th className="px-4 py-2 text-right">Balance</th>
                  <th className="px-4 py-2 text-center">Status</th>
                  <th className="px-4 py-2 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {dueExpenses.map(exp => {
                  const bal = Number(exp.balance ?? (exp.amount - (exp.paid_amount ?? 0)));
                  return (
                    <tr key={exp.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/40 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-800 dark:text-white">
                        {exp.title}
                        {exp.notes && <p className="text-xs text-gray-400 font-normal">{exp.notes}</p>}
                      </td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{getCatName(exp.category_id)}</td>
                      <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{exp.expense_date ?? '—'}</td>
                      <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">₹{Number(exp.amount).toFixed(2)}</td>
                      <td className="px-4 py-3 text-right text-green-600 font-medium">
                        {Number(exp.paid_amount ?? 0) > 0 ? `₹${Number(exp.paid_amount).toFixed(2)}` : '—'}
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-red-600">₹{bal.toFixed(2)}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[exp.status] ?? ''}`}>
                          {exp.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          title="Collect Payment"
                          onClick={() => {
                            setCollectingExp(exp);
                            setPayForm({ payment_method: 'cash', paid_at: new Date().toISOString().split('T')[0], amount_paid: bal.toFixed(2) });
                          }}
                          className="flex items-center gap-1 px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium mx-auto"
                        >
                          <CheckCircle size={13} /> Collect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Fee Dues Summary (read-only) */}
      {ledger && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <AlertCircle size={15} /> Fee Dues — {years.find((y: any) => y.id === academicYearId)?.name ?? ''}
            <select className="ml-auto input-field py-1 text-xs" style={{ minWidth: 140 }} value={academicYearId} onChange={e => setAcademicYearId(e.target.value)}>
              {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
            </select>
          </h3>
          {ledger.entries?.length > 0 ? (
            <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
              {ledger.fee_master_name && (
                <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 text-xs font-semibold text-gray-600 dark:text-gray-300">
                  {ledger.fee_master_name}
                </div>
              )}
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {ledger.entries.map((item: any) => (
                  <div key={item.fee_type_id} className="px-4 py-2 flex justify-between items-center text-sm">
                    <div>
                      <span className="text-gray-700 dark:text-gray-300">{item.fee_type_name}</span>
                      {Number(item.discount_given) > 0 && (
                        <span className="ml-2 text-xs text-green-600">-₹{Number(item.discount_given).toFixed(2)} disc</span>
                      )}
                    </div>
                    <div className="text-right">
                      {Number(item.balance) > 0 ? (
                        <span className="font-semibold text-red-600">₹{Number(item.balance).toFixed(2)}</span>
                      ) : (
                        <span className="text-xs text-green-600 font-medium">✓ Paid</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 flex justify-between text-sm font-semibold border-t border-gray-200 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-300">Total Due</span>
                <span className={Number(ledger.total_balance) > 0 ? 'text-red-600' : 'text-green-600'}>
                  ₹{Number(ledger.total_balance).toFixed(2)}
                </span>
              </div>
            </div>
          ) : ledger.fee_master_id ? (
            <div className="text-center py-6 text-green-600 border border-dashed border-green-200 dark:border-green-800 rounded-xl">
              <p className="text-sm">✓ All fees cleared for this year</p>
            </div>
          ) : (
            <div className="text-center py-6 text-gray-400 border border-dashed border-gray-200 dark:border-gray-700 rounded-xl">
              <p className="text-sm">No fee assignments found. Go to the Fees tab to assign fees.</p>
            </div>
          )}
        </div>
      )}

      {/* Collect Modal */}
      {collectingExp && (() => {
        const parsedAmt = parseFloat(payForm.amount_paid) || 0;
        const balanceAmt = Number(collectingExp.balance ?? (collectingExp.amount - (collectingExp.paid_amount ?? 0)));
        return (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-sm shadow-xl">
              <h3 className="font-semibold text-gray-800 dark:text-white mb-1">Collect Payment</h3>
              <p className="text-sm text-gray-500 mb-3">{collectingExp.title}</p>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg px-3 py-2 mb-4 space-y-1 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Billed</span><span className="font-medium">₹{Number(collectingExp.amount).toFixed(2)}</span></div>
                {Number(collectingExp.paid_amount ?? 0) > 0 && (
                  <div className="flex justify-between"><span className="text-gray-500">Already Paid</span><span className="text-green-600 font-medium">₹{Number(collectingExp.paid_amount).toFixed(2)}</span></div>
                )}
                <div className="flex justify-between border-t border-gray-200 dark:border-gray-600 pt-1">
                  <span className="font-semibold text-red-600">Balance Due</span>
                  <span className="font-bold text-red-600">₹{balanceAmt.toFixed(2)}</span>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Amount to Collect (₹) *</label>
                  <input type="number" min="0.01" step="0.01" className="input-field w-full mt-1 text-lg font-bold"
                    value={payForm.amount_paid} onChange={e => setPayForm(f => ({ ...f, amount_paid: e.target.value }))} />
                  {parsedAmt > 0 && parsedAmt < balanceAmt && (
                    <p className="text-xs text-amber-600 mt-1">⚠ Partial — ₹{(balanceAmt - parsedAmt).toFixed(2)} will remain outstanding</p>
                  )}
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Payment Method</label>
                  <select className="input-field w-full mt-1" value={payForm.payment_method} onChange={e => setPayForm(f => ({ ...f, payment_method: e.target.value }))}>
                    {PAYMENT_METHODS.map(m => <option key={m} value={m}>{m.toUpperCase()}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Payment Date</label>
                  <input type="date" className="input-field w-full mt-1" value={payForm.paid_at} onChange={e => setPayForm(f => ({ ...f, paid_at: e.target.value }))} />
                </div>
              </div>
              <div className="flex gap-2 mt-5">
                <button className="btn-primary flex-1 flex items-center justify-center gap-2"
                  onClick={() => collectMutation.mutate(collectingExp.id)}
                  disabled={collectMutation.isPending || parsedAmt <= 0}>
                  <Printer size={14} />{collectMutation.isPending ? 'Processing…' : 'Collect & Print Receipt'}
                </button>
                <button className="btn-secondary" onClick={() => setCollectingExp(null)}>Cancel</button>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default StudentDuesTab;
