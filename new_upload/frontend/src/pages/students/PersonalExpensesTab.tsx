import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { personalExpensesApi, PersonalExpense, PersonalExpenseCategory } from '@api/personalExpenses';
import { useAuthStore } from '@store/authStore';
import { toast } from 'sonner';
import { Plus, Trash2, CheckCircle, XCircle, Edit2, ChevronDown, ChevronUp, Tag, Printer } from 'lucide-react';

const unwrap = (r: any) => r?.data ?? r;

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  partial: 'bg-orange-100 text-orange-700',
  paid: 'bg-green-100 text-green-800',
  waived: 'bg-gray-100 text-gray-600',
};

const PAYMENT_METHODS = ['cash', 'online', 'upi', 'card', 'cheque', 'neft'];

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
}

const PersonalExpensesTab: React.FC<Props> = ({ studentId, studentName }) => {
  const qc = useQueryClient();
  const { schoolInfo } = useAuthStore();
  const schoolName = schoolInfo?.name ?? 'School';
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [showCategories, setShowCategories] = useState(false);
  const [editingExpense, setEditingExpense] = useState<PersonalExpense | null>(null);
  const [markingPaid, setMarkingPaid] = useState<PersonalExpense | null>(null);
  const [newCatName, setNewCatName] = useState('');
  const [newCatDesc, setNewCatDesc] = useState('');

  const [form, setForm] = useState({
    title: '',
    amount: '',
    category_id: '',
    expense_date: new Date().toISOString().split('T')[0],
    notes: '',
  });
  const [payForm, setPayForm] = useState({ payment_method: 'cash', paid_at: new Date().toISOString().split('T')[0], amount_paid: '' });

  // ── Queries ──────────────────────────────────────────────────────────────
  const categoriesQ = useQuery({
    queryKey: ['personal-expense-categories'],
    queryFn: async () => {
      const data = unwrap(await personalExpensesApi.listCategories());
      return Array.isArray(data) ? data : (data?.items ?? []) as PersonalExpenseCategory[];
    },
  });

  const expensesQ = useQuery({
    queryKey: ['personal-expenses', studentId],
    queryFn: async () => {
      const data = unwrap(await personalExpensesApi.listByStudent(studentId));
      return data as { expenses: PersonalExpense[]; summary: any };
    },
  });

  const expenses = expensesQ.data?.expenses ?? [];
  const summary = expensesQ.data?.summary ?? {};
  const categories = categoriesQ.data ?? [];
  const filtered = filterStatus === 'all' ? expenses : expenses.filter(e => e.status === filterStatus);

  const invalidate = () => qc.invalidateQueries({ queryKey: ['personal-expenses', studentId] });

  // ── Mutations ─────────────────────────────────────────────────────────────
  const addMutation = useMutation({
    mutationFn: () => personalExpensesApi.createExpense({
      student_id: studentId,
      title: form.title,
      amount: parseFloat(form.amount),
      category_id: form.category_id || undefined,
      expense_date: form.expense_date || undefined,
      notes: form.notes || undefined,
    }),
    onSuccess: () => { toast.success('Expense added'); setShowAddForm(false); setForm({ title: '', amount: '', category_id: '', expense_date: new Date().toISOString().split('T')[0], notes: '' }); invalidate(); },
    onError: () => toast.error('Failed to add expense'),
  });

  const editMutation = useMutation({
    mutationFn: () => personalExpensesApi.updateExpense(editingExpense!.id, {
      title: form.title,
      amount: parseFloat(form.amount),
      category_id: form.category_id || undefined,
      expense_date: form.expense_date || undefined,
      notes: form.notes || undefined,
    }),
    onSuccess: () => { toast.success('Expense updated'); setEditingExpense(null); invalidate(); },
    onError: () => toast.error('Failed to update expense'),
  });

  const paidMutation = useMutation({
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
      const exp = markingPaid;
      const parsedAmt = parseFloat(payForm.amount_paid);
      setMarkingPaid(null);
      invalidate();
      if (exp) {
        const cat = categoriesQ.data ? (unwrap(categoriesQ.data) as PersonalExpenseCategory[]).find(c => c.id === exp.category_id) : undefined;
        printExpenseReceipt({
          schoolName,
          receiptNo: `PE-${exp.id.slice(-6).toUpperCase()}`,
          studentName: studentName ?? 'Student',
          expenseTitle: exp.title,
          categoryName: cat?.name ?? 'General',
          amount: (parsedAmt > 0 ? parsedAmt : Number(exp.amount)),
          paymentMethod: payForm.payment_method,
          paidAt: payForm.paid_at,
        });
      }
    },
    onError: () => toast.error('Failed to mark paid'),
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
    mutationFn: () => personalExpensesApi.createCategory({ name: newCatName, description: newCatDesc }),
    onSuccess: () => { toast.success('Category added'); setNewCatName(''); setNewCatDesc(''); qc.invalidateQueries({ queryKey: ['personal-expense-categories'] }); },
    onError: () => toast.error('Failed to add category'),
  });

  const deleteCatMutation = useMutation({
    mutationFn: (id: string) => personalExpensesApi.deleteCategory(id),
    onSuccess: () => { toast.success('Category deleted'); qc.invalidateQueries({ queryKey: ['personal-expense-categories'] }); },
    onError: () => toast.error('Failed to delete category'),
  });

  const getCatName = (id?: string) => categories.find(c => c.id === id)?.name ?? '—';

  const openEdit = (e: PersonalExpense) => {
    setEditingExpense(e);
    setForm({ title: e.title, amount: String(e.amount), category_id: e.category_id ?? '', expense_date: e.expense_date ?? '', notes: e.notes ?? '' });
    setShowAddForm(false);
  };

  const openAdd = () => { setEditingExpense(null); setForm({ title: '', amount: '', category_id: '', expense_date: new Date().toISOString().split('T')[0], notes: '' }); setShowAddForm(true); };

  const expenseFormJsx = (onSubmit: () => void, loading: boolean) => (
    <div className="bg-blue-50 dark:bg-gray-700 rounded-lg p-4 mb-4 border border-blue-200 dark:border-gray-600">
      <h4 className="font-semibold text-gray-800 dark:text-white mb-3">{editingExpense ? 'Edit Expense' : 'Add Expense'}</h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Title *</label>
          <input className="input-field w-full mt-1" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. Art supplies" />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Amount (₹) *</label>
          <input type="number" className="input-field w-full mt-1" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="0.00" min="0" step="0.01" />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Category</label>
          <select className="input-field w-full mt-1" value={form.category_id} onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}>
            <option value="">— None —</option>
            {categories.filter(c => c.is_active).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Date</label>
          <input type="date" className="input-field w-full mt-1" value={form.expense_date} onChange={e => setForm(f => ({ ...f, expense_date: e.target.value }))} />
        </div>
        <div className="sm:col-span-2">
          <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Notes</label>
          <input className="input-field w-full mt-1" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Optional notes" />
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button className="btn-primary" onClick={onSubmit} disabled={loading || !form.title || !form.amount}>
          {loading ? 'Saving…' : (editingExpense ? 'Update' : 'Add Expense')}
        </button>
        <button className="btn-secondary" onClick={() => { setShowAddForm(false); setEditingExpense(null); }}>Cancel</button>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total', value: summary.total_amount, color: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30' },
          { label: 'Paid', value: summary.paid_amount, color: 'bg-green-50 text-green-700 dark:bg-green-900/30' },
          { label: 'Pending', value: summary.pending_amount, color: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30' },
          { label: 'Balance Due', value: summary.balance_due, color: 'bg-red-50 text-red-700 dark:bg-red-900/30' },
        ].map(card => (
          <div key={card.label} className={`rounded-lg p-3 ${card.color}`}>
            <p className="text-xs font-medium opacity-70">{card.label}</p>
            <p className="text-lg font-bold">₹{(card.value ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 justify-between">
        <div className="flex gap-1">
          {['all', 'pending', 'paid', 'waived'].map(s => (
            <button key={s} onClick={() => setFilterStatus(s)}
              className={`px-3 py-1 rounded-full text-xs font-medium capitalize transition-colors ${filterStatus === s ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'}`}>
              {s}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCategories(s => !s)}
            className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
            <Tag size={13} /> Categories {showCategories ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>
          <button onClick={openAdd}
            className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-indigo-600 text-white hover:bg-indigo-700">
            <Plus size={13} /> Add Expense
          </button>
        </div>
      </div>

      {/* Category Manager */}
      {showCategories && (
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
          <p className="text-sm font-semibold text-gray-700 dark:text-white mb-3">Expense Categories</p>
          <div className="flex flex-wrap gap-2 mb-3">
            {categories.map(c => (
              <div key={c.id} className="flex items-center gap-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-full px-3 py-1 text-sm">
                <span className={c.is_active ? 'text-gray-700 dark:text-gray-200' : 'text-gray-400 line-through'}>{c.name}</span>
                <button onClick={() => { if (confirm(`Delete category "${c.name}"?`)) deleteCatMutation.mutate(c.id) }}
                  className="ml-1 text-red-400 hover:text-red-600"><Trash2 size={12} /></button>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <input className="input-field flex-1" placeholder="Category name" value={newCatName} onChange={e => setNewCatName(e.target.value)} />
            <input className="input-field flex-1" placeholder="Description (optional)" value={newCatDesc} onChange={e => setNewCatDesc(e.target.value)} />
            <button className="btn-primary text-sm" onClick={() => newCatName && addCatMutation.mutate()} disabled={!newCatName || addCatMutation.isPending}>
              Add
            </button>
          </div>
        </div>
      )}

      {/* Add / Edit Form */}
      {showAddForm && expenseFormJsx(() => addMutation.mutate(), addMutation.isPending)}
      {editingExpense && expenseFormJsx(() => editMutation.mutate(), editMutation.isPending)}

      {/* Collect Payment Modal */}
      {markingPaid && (() => {
        const parsedAmt = parseFloat(payForm.amount_paid) || 0;
        const balanceAmt = Number(markingPaid.balance ?? (markingPaid.amount - (markingPaid.paid_amount ?? 0)));
        return (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-sm shadow-xl">
              <h3 className="font-semibold text-gray-800 dark:text-white mb-1">Collect Payment</h3>
              <p className="text-sm text-gray-500 mb-3">{markingPaid.title}</p>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg px-3 py-2 mb-4 space-y-1 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Billed</span><span className="font-medium">₹{Number(markingPaid.amount).toFixed(2)}</span></div>
                {Number(markingPaid.paid_amount ?? 0) > 0 && (
                  <div className="flex justify-between"><span className="text-gray-500">Already Paid</span><span className="text-green-600 font-medium">₹{Number(markingPaid.paid_amount).toFixed(2)}</span></div>
                )}
                <div className="flex justify-between border-t border-gray-200 dark:border-gray-600 pt-1">
                  <span className="font-semibold text-red-600">Balance Due</span>
                  <span className="font-bold text-red-600">₹{Number(markingPaid.balance ?? (markingPaid.amount - (markingPaid.paid_amount ?? 0))).toFixed(2)}</span>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Amount to Collect (₹) *</label>
                  <input type="number" min="0.01" step="0.01"
                    className="input-field w-full mt-1 text-lg font-bold"
                    value={payForm.amount_paid}
                    onChange={e => setPayForm(f => ({ ...f, amount_paid: e.target.value }))} />
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
                  onClick={() => paidMutation.mutate(markingPaid.id)} disabled={paidMutation.isPending || parsedAmt <= 0}>
                  <Printer size={14} />{paidMutation.isPending ? 'Processing…' : 'Collect & Print Receipt'}
                </button>
                <button className="btn-secondary" onClick={() => setMarkingPaid(null)}>Cancel</button>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Expense List */}
      {expensesQ.isLoading ? (
        <p className="text-sm text-gray-500 py-8 text-center">Loading…</p>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm">No expenses found.</p>
          {filterStatus !== 'all' && <p className="text-xs mt-1">Try changing the filter above.</p>}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-2 text-left">Title</th>
                <th className="px-4 py-2 text-left">Category</th>
                <th className="px-4 py-2 text-left">Date</th>
                <th className="px-4 py-2 text-right">Billed</th>
                <th className="px-4 py-2 text-right">Collected</th>
                <th className="px-4 py-2 text-right">Balance</th>
                <th className="px-4 py-2 text-center">Status</th>
                <th className="px-4 py-2 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {filtered.map(exp => (
                <tr key={exp.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-800 dark:text-white">
                    {exp.title}
                    {exp.notes && <p className="text-xs text-gray-400 font-normal mt-0.5">{exp.notes}</p>}
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{getCatName(exp.category_id)}</td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{exp.expense_date ?? '—'}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-800 dark:text-white">
                    ₹{Number(exp.amount).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right text-green-600 font-medium text-sm">
                    {Number(exp.paid_amount ?? 0) > 0 ? `₹${Number(exp.paid_amount).toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-red-600">
                    {Number(exp.balance ?? (exp.amount - (exp.paid_amount ?? 0))) > 0
                      ? `₹${Number(exp.balance ?? (exp.amount - (exp.paid_amount ?? 0))).toFixed(2)}`
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
                          <button title="Collect Payment" onClick={() => {
                            const bal = exp.balance ?? (exp.amount - (exp.paid_amount ?? 0));
                            setMarkingPaid(exp);
                            setPayForm({ payment_method: 'cash', paid_at: new Date().toISOString().split('T')[0], amount_paid: Number(bal).toFixed(2) });
                          }}
                            className="p-1.5 rounded text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30">
                            <CheckCircle size={14} />
                          </button>
                          {exp.status === 'pending' && (
                            <button title="Waive" onClick={() => { if (confirm('Waive this expense?')) waiveMutation.mutate(exp.id) }}
                              className="p-1.5 rounded text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700">
                              <XCircle size={14} />
                            </button>
                          )}
                          <button title="Edit" onClick={() => openEdit(exp)}
                            className="p-1.5 rounded text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30">
                            <Edit2 size={14} />
                          </button>
                        </>
                      )}
                      {(exp.status === 'paid' || exp.status === 'partial') && (
                        <button title="Reprint Receipt" onClick={() => {
                          const cat = categoriesQ.data ? (unwrap(categoriesQ.data) as PersonalExpenseCategory[]).find(c => c.id === exp.category_id) : undefined;
                          printExpenseReceipt({
                            schoolName,
                            receiptNo: `PE-${exp.id.slice(-6).toUpperCase()}`,
                            studentName: studentName ?? 'Student',
                            expenseTitle: exp.title,
                            categoryName: cat?.name ?? 'General',
                            amount: Number(exp.paid_amount ?? exp.amount),
                            paymentMethod: exp.payment_method ?? 'cash',
                            paidAt: exp.paid_at ?? '',
                          });
                        }} className="p-1.5 rounded text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/30">
                          <Printer size={14} />
                        </button>
                      )}
                      <button title="Delete" onClick={() => { if (confirm('Delete this expense?')) deleteMutation.mutate(exp.id) }}
                        className="p-1.5 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PersonalExpensesTab;
