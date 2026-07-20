import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import {
  accountingApi, IncomeRecord, ExpenseRecord, MonthlySummaryItem
} from '../../api/accounting';

type Tab = 'income' | 'expenses' | 'summary' | 'categories';

interface Category { id: string; name: string; }

export default function AccountingPage() {
  const [tab, setTab] = useState<Tab>('income');
  const [income, setIncome] = useState<IncomeRecord[]>([]);
  const [expenses, setExpenses] = useState<ExpenseRecord[]>([]);
  const [summary, setSummary] = useState<MonthlySummaryItem[]>([]);
  const [incomeCategories, setIncomeCategories] = useState<Category[]>([]);
  const [expenseCategories, setExpenseCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [year, setYear] = useState(new Date().getFullYear());
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [newIncomeCatName, setNewIncomeCatName] = useState('');
  const [newExpenseCatName, setNewExpenseCatName] = useState('');
  const [newExpenseBudget, setNewExpenseBudget] = useState(''); 

  // Load categories once; seed defaults if none exist
  useEffect(() => {
    const seedAndLoad = async () => {
      try {
        let iCats: Category[] = await accountingApi.listIncomeCategories();
        if (!iCats.length) {
          await accountingApi.createIncomeCategory({ name: 'General Income' });
          iCats = await accountingApi.listIncomeCategories();
        }
        setIncomeCategories(iCats);
      } catch { /* ignore */ }

      try {
        let eCats: Category[] = await accountingApi.listExpenseCategories();
        if (!eCats.length) {
          await accountingApi.createExpenseCategory({ name: 'General Expense', budget_amount: 0 });
          eCats = await accountingApi.listExpenseCategories();
        }
        setExpenseCategories(eCats);
      } catch { /* ignore */ }
    };
    seedAndLoad();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      if (tab === 'income') setIncome(await accountingApi.listIncome({ year }));
      else if (tab === 'expenses') setExpenses(await accountingApi.listExpenses({ year }));
      else setSummary(await accountingApi.getMonthlySummary(year));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [tab, year]);

  const totalIncome = income.reduce((s, r) => s + r.amount, 0);
  const totalExpenses = expenses.reduce((s, r) => s + r.amount, 0);

  const submitIncome = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.category_id) { toast.error('Please select a category'); return; }
    setSaving(true);
    try {
      await accountingApi.createIncome({
        category_id: form.category_id,
        amount: Math.round(Number(form.amount) * 100), // ₹ → paise
        income_date: form.income_date,
        description: form.description || undefined,
        reference_number: form.reference_number || undefined,
        received_by: form.received_by || undefined,
      });
      toast.success('Income record saved');
      setShowForm(false);
      setForm({});
      load();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save income record');
    } finally {
      setSaving(false);
    }
  };

  const submitExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.category_id) { toast.error('Please select a category'); return; }
    setSaving(true);
    try {
      await accountingApi.createExpense({
        category_id: form.category_id,
        amount: Math.round(Number(form.amount) * 100), // ₹ → paise
        expense_date: form.expense_date,
        description: form.description || undefined,
        vendor_name: form.vendor_name || undefined,
        payment_mode: form.payment_mode || 'cash',
        reference_number: form.reference_number || undefined,
        approved_by: form.approved_by || undefined,
      });
      toast.success('Expense record saved');
      setShowForm(false);
      setForm({});
      load();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save expense record');
    } finally {
      setSaving(false);
    }
  };

  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Accounting</h1>
        <div className="flex items-center gap-3">
          <select value={year} onChange={e => setYear(Number(e.target.value))}
            className="border rounded px-3 py-2 text-sm">
            {[2023, 2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
          </select>
          {tab !== 'summary' && (
            <button onClick={() => { setShowForm(true); setForm({}); }}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              + Add {tab === 'income' ? 'Income' : 'Expense'}
            </button>
          )}
        </div>
      </div>

      <div className="flex space-x-1 mb-6 border-b">
        {[{ key: 'income', label: 'Income' }, { key: 'expenses', label: 'Expenses' }, { key: 'summary', label: 'Monthly Summary' }, { key: 'categories', label: '🏷️ Categories' }]
          .map(t => (
            <button key={t.key} onClick={() => setTab(t.key as Tab)}
              className={`px-4 py-2 text-sm font-medium rounded-t ${tab === t.key ? 'bg-white border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
              {t.label}
            </button>
          ))}
      </div>

      {!loading && tab === 'income' && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-sm">
          Total Income ({year}): <strong className="text-green-700">₹{(totalIncome / 100).toLocaleString()}</strong>
        </div>
      )}
      {!loading && tab === 'expenses' && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm">
          Total Expenses ({year}): <strong className="text-red-700">₹{(totalExpenses / 100).toLocaleString()}</strong>
        </div>
      )}

      {loading ? (
        <div className="text-center py-10 text-gray-500">Loading...</div>
      ) : (
        <>
          {tab === 'income' && (
            <table className="w-full text-sm border rounded overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {['Date', 'Description', 'Reference', 'Received By', 'Amount'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {income.map(r => (
                  <tr key={r.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2">{r.income_date}</td>
                    <td className="px-4 py-2">{r.description || '—'}</td>
                    <td className="px-4 py-2 font-mono text-xs">{r.reference_number || '—'}</td>
                    <td className="px-4 py-2">{r.received_by || '—'}</td>
                    <td className="px-4 py-2 font-medium text-green-700">₹{(r.amount / 100).toLocaleString()}</td>
                  </tr>
                ))}
                {income.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No income records.</td></tr>
                )}
              </tbody>
            </table>
          )}

          {tab === 'expenses' && (
            <table className="w-full text-sm border rounded overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {['Date', 'Description', 'Vendor', 'Payment Mode', 'Amount'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {expenses.map(r => (
                  <tr key={r.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2">{r.expense_date}</td>
                    <td className="px-4 py-2">{r.description || '—'}</td>
                    <td className="px-4 py-2">{r.vendor_name || '—'}</td>
                    <td className="px-4 py-2 capitalize">{r.payment_mode}</td>
                    <td className="px-4 py-2 font-medium text-red-700">₹{(r.amount / 100).toLocaleString()}</td>
                  </tr>
                ))}
                {expenses.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No expense records.</td></tr>
                )}
              </tbody>
            </table>
          )}

          {tab === 'summary' && (
            <div>
              <table className="w-full text-sm border rounded overflow-hidden">
                <thead className="bg-gray-50">
                  <tr>
                    {['Month', 'Income', 'Expenses', 'Net'].map(h => (
                      <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {summary.map(s => (
                    <tr key={s.month} className="border-t hover:bg-gray-50">
                      <td className="px-4 py-2 font-medium">{months[s.month - 1]} {s.year}</td>
                      <td className="px-4 py-2 text-green-700">₹{(s.total_income / 100).toLocaleString()}</td>
                      <td className="px-4 py-2 text-red-700">₹{(s.total_expense / 100).toLocaleString()}</td>
                      <td className={`px-4 py-2 font-semibold ${s.net >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                        {s.net >= 0 ? '+' : ''}₹{(s.net / 100).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                  {summary.length === 0 && (
                    <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">No data for {year}.</td></tr>
                  )}
                </tbody>
              </table>
              {summary.length > 0 && (
                <div className="mt-4 p-4 bg-gray-50 rounded border grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-gray-500">Total Income</div>
                    <div className="text-green-700 font-bold text-lg">
                      ₹{(summary.reduce((s, r) => s + r.total_income, 0) / 100).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500">Total Expenses</div>
                    <div className="text-red-700 font-bold text-lg">
                      ₹{(summary.reduce((s, r) => s + r.total_expense, 0) / 100).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500">Net Balance</div>
                    <div className={`font-bold text-lg ${summary.reduce((s, r) => s + r.net, 0) >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                      ₹{(summary.reduce((s, r) => s + r.net, 0) / 100).toLocaleString()}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {showForm && tab === 'income' && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Add Income Record</h2>
            <form onSubmit={submitIncome} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select required value={form.category_id || ''} onChange={e => setForm({ ...form, category_id: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm">
                  <option value="">Select category</option>
                  {incomeCategories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₹) *</label>
                <input required type="number" min="0.01" step="0.01" value={form.amount || ''}
                  onChange={e => setForm({ ...form, amount: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="0.00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date *</label>
                <input required type="date" value={form.income_date || ''}
                  onChange={e => setForm({ ...form, income_date: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input value={form.description || ''} onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="Optional" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reference Number</label>
                <input value={form.reference_number || ''} onChange={e => setForm({ ...form, reference_number: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="Optional" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Received By</label>
                <input value={form.received_by || ''} onChange={e => setForm({ ...form, received_by: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="Optional" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border rounded hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={saving}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
                  {saving ? 'Saving…' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showForm && tab === 'expenses' && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Add Expense Record</h2>
            <form onSubmit={submitExpense} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select required value={form.category_id || ''} onChange={e => setForm({ ...form, category_id: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm">
                  <option value="">Select category</option>
                  {expenseCategories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₹) *</label>
                <input required type="number" min="0.01" step="0.01" value={form.amount || ''}
                  onChange={e => setForm({ ...form, amount: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="0.00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date *</label>
                <input required type="date" value={form.expense_date || ''}
                  onChange={e => setForm({ ...form, expense_date: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input value={form.description || ''} onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="Optional" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Vendor</label>
                <input value={form.vendor_name || ''} onChange={e => setForm({ ...form, vendor_name: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="Optional" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Mode</label>
                <select value={form.payment_mode || 'cash'} onChange={e => setForm({ ...form, payment_mode: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm">
                  {['cash', 'bank_transfer', 'cheque', 'upi', 'card'].map(m => (
                    <option key={m} value={m}>{m.replace('_', ' ').toUpperCase()}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reference Number</label>
                <input value={form.reference_number || ''} onChange={e => setForm({ ...form, reference_number: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="Optional" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Approved By</label>
                <input value={form.approved_by || ''} onChange={e => setForm({ ...form, approved_by: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="Optional" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border rounded hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={saving}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
                  {saving ? 'Saving…' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Categories Tab */}
      {tab === 'categories' && (
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="mb-3 font-semibold text-gray-700">Income Categories</h3>
            <ul className="mb-4 space-y-1.5">
              {incomeCategories.map(c => <li key={c.id} className="flex items-center justify-between rounded border border-gray-100 px-3 py-2 text-sm"><span>{c.name}</span></li>)}
            </ul>
            <div className="flex gap-2">
              <input value={newIncomeCatName} onChange={e => setNewIncomeCatName(e.target.value)} className="flex-1 rounded border px-3 py-1.5 text-sm" placeholder="New category name" />
              <button onClick={async () => { if (!newIncomeCatName.trim()) return; try { await accountingApi.createIncomeCategory({ name: newIncomeCatName }); setNewIncomeCatName(''); const cats = await accountingApi.listIncomeCategories(); setIncomeCategories(cats); toast.success('Category added'); } catch { toast.error('Failed'); } }} className="rounded bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700">Add</button>
            </div>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="mb-3 font-semibold text-gray-700">Expense Categories</h3>
            <ul className="mb-4 space-y-1.5">
              {expenseCategories.map(c => <li key={c.id} className="flex items-center justify-between rounded border border-gray-100 px-3 py-2 text-sm"><span>{c.name}</span></li>)}
            </ul>
            <div className="flex gap-2">
              <input value={newExpenseCatName} onChange={e => setNewExpenseCatName(e.target.value)} className="flex-1 rounded border px-3 py-1.5 text-sm" placeholder="Category name" />
              <input value={newExpenseBudget} onChange={e => setNewExpenseBudget(e.target.value)} type="number" className="w-24 rounded border px-3 py-1.5 text-sm" placeholder="Budget ₹" />
              <button onClick={async () => { if (!newExpenseCatName.trim()) return; try { await accountingApi.createExpenseCategory({ name: newExpenseCatName, budget_amount: Number(newExpenseBudget || 0) * 100 }); setNewExpenseCatName(''); setNewExpenseBudget(''); const cats = await accountingApi.listExpenseCategories(); setExpenseCategories(cats); toast.success('Category added'); } catch { toast.error('Failed'); } }} className="rounded bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700">Add</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
