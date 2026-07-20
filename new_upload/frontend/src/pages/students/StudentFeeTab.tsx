import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { feesV2Api, FeeCollection, PaymentMethod } from '@api/feesV2';
import { academicYearsApi } from '@api/academicYears';
import { useAcademicYearStore } from '@store/academicYearStore';
import { formatDate } from '@utils/formatters';

const unwrap = (r: any) => r?.data ?? r;
const PAYMENT_METHODS: PaymentMethod[] = ['cash', 'cheque', 'online', 'card', 'neft', 'upi'];

function printContent(html: string, title: string) {
  const w = window.open('', '_blank', 'width=820,height=700');
  if (!w) return;
  w.document.write(`<!DOCTYPE html><html><head><title>${title}</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 24px; font-size: 13px; color: #222; }
    h2, h3 { margin: 0 0 4px; }
    .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 12px; }
    .header p { margin: 3px 0; color: #555; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 18px; }
    th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
    th { background: #f0f0f0; font-weight: bold; }
    td.right, th.right { text-align: right; }
    tr.total-row td { font-weight: bold; background: #f8f8f8; }
    .badge-reversed { color: #c00; font-size: 11px; font-weight: bold; }
    .footer { margin-top: 40px; display: flex; justify-content: space-between; }
    .footer div { text-align: center; }
    .print-btn { margin-bottom: 16px; padding: 6px 16px; cursor: pointer; }
    @media print { .print-btn { display: none; } }
  </style>
  </head><body>
  <button class="print-btn" onclick="window.print()">🖨 Print</button>
  ${html}
  </body></html>`);
  w.document.close();
}

interface Props {
  studentId: string;
  studentName: string;
  admissionNumber: string;
}

const StudentFeeTab: React.FC<Props> = ({ studentId, studentName, admissionNumber }) => {
  const queryClient = useQueryClient();
  const { selectedYear } = useAcademicYearStore();
  const [yearId, setYearId] = useState('');
  const [showCollectModal, setShowCollectModal] = useState(false);
  const [collectingLedger, setCollectingLedger] = useState<any>(null);
  const [collectAmounts, setCollectAmounts] = useState<
    Record<string, { amount: number; discount: number; discountReason: string }>
  >({});  
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash');
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10));
  const [txnRef, setTxnRef] = useState('');
  const [remarks, setRemarks] = useState('');
  const [collecting, setCollecting] = useState(false);

  // Academic years
  const { data: years = [] } = useQuery({
    queryKey: ['academic-years-select'],
    queryFn: async () => {
      const d = unwrap(await academicYearsApi.list());
      return Array.isArray(d) ? d : (d?.items ?? []);
    },
  });

  const activeYearId: string = yearId || (selectedYear?.id ?? '');

  // All fee master ledgers for this student (backend now returns a list)
  const { data: ledgers = [] } = useQuery({
    queryKey: ['fee-ledger', studentId, activeYearId],
    enabled: !!activeYearId,
    queryFn: async () => {
      const d = unwrap(await feesV2Api.getStudentLedger(studentId, activeYearId));
      return Array.isArray(d) ? d : (d ? [d] : []);
    },
  });

  // Derived: does student have any assignment at all?
  const hasAssignments = ledgers.length > 0;

  // Collections (including reversed)
  const { data: collections = [] } = useQuery({
    queryKey: ['fee-collections-student', studentId, activeYearId],
    enabled: !!activeYearId,
    queryFn: async () => {
      const d = unwrap(
        await feesV2Api.listCollections({
          student_id: studentId,
          academic_year_id: activeYearId,
          include_reversed: true,
        }),
      );
      return Array.isArray(d) ? d : (d?.items ?? []);
    },
  });

  // ── Collect modal ──────────────────────────────────────────────────────────
  const openCollect = (ledger: any) => {
    if (!ledger?.entries) return;
    const init: typeof collectAmounts = {};
    ledger.entries.forEach((e: any) => {
      init[e.fee_type_id] = {
        amount: e.balance > 0 ? parseFloat(e.balance.toFixed(2)) : 0,
        discount: 0,
        discountReason: '',
      };
    });
    setCollectAmounts(init);
    setCollectingLedger(ledger);
    setPaymentMethod('cash');
    setPaymentDate(new Date().toISOString().slice(0, 10));
    setTxnRef('');
    setRemarks('');
    setShowCollectModal(true);
  };

  const handleCollect = async () => {
    if (!collectingLedger) return;
    const items = collectingLedger.entries
      .map((e: any) => ({
        fee_type_id: e.fee_type_id,
        amount_paid: collectAmounts[e.fee_type_id]?.amount ?? 0,
        discount_amount: collectAmounts[e.fee_type_id]?.discount ?? 0,
        discount_reason: collectAmounts[e.fee_type_id]?.discountReason || undefined,
      }))
      .filter((i: any) => i.amount_paid > 0 || i.discount_amount > 0);

    if (!items.length) return toast.error('Enter at least one payment or discount amount');

    setCollecting(true);
    try {
      await feesV2Api.collectFee({
        student_id: studentId,
        fee_master_id: collectingLedger.fee_master_id,
        academic_year_id: activeYearId,
        payment_date: paymentDate,
        payment_method: paymentMethod,
        transaction_ref: txnRef || undefined,
        remarks: remarks || undefined,
        items,
      });
      toast.success('Fee collected successfully');
      setShowCollectModal(false);
      setCollectingLedger(null);
      queryClient.invalidateQueries({ queryKey: ['fee-ledger', studentId, activeYearId] });
      queryClient.invalidateQueries({ queryKey: ['fee-collections-student', studentId, activeYearId] });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to collect fee');
    } finally {
      setCollecting(false);
    }
  };

  // ── Reverse collection ─────────────────────────────────────────────────────
  const handleReverse = async (id: string) => {
    const reason = window.prompt('Reason for reversal:');
    if (!reason) return;
    try {
      await feesV2Api.reverseCollection(id, reason);
      toast.success('Collection reversed');
      queryClient.invalidateQueries({ queryKey: ['fee-collections-student', studentId, activeYearId] });
      queryClient.invalidateQueries({ queryKey: ['fee-ledger', studentId, activeYearId] });
    } catch {
      toast.error('Failed to reverse collection');
    }
  };

  // ── Print helpers ──────────────────────────────────────────────────────────
  const printReceipt = (col: FeeCollection) => {
    const html = `
      <div class="header">
        <h2>Fee Receipt</h2>
      </div>
      <table>
        <tr><td><b>Receipt No:</b></td><td>${col.receipt_number}</td><td><b>Date:</b></td><td>${formatDate(col.payment_date)}</td></tr>
        <tr><td><b>Student:</b></td><td>${studentName}</td><td><b>Admission No:</b></td><td>${admissionNumber}</td></tr>
        <tr><td><b>Class:</b></td><td>${col.class_name ?? ''}</td><td><b>Payment Via:</b></td><td>${col.payment_method.toUpperCase()}</td></tr>
        ${col.transaction_ref ? `<tr><td><b>Txn Ref:</b></td><td colspan="3">${col.transaction_ref}</td></tr>` : ''}
      </table>
      <table>
        <thead><tr><th>Fee Type</th><th class="right">Due Amount</th><th class="right">Discount</th><th class="right">Net Paid</th></tr></thead>
        <tbody>
          ${col.items
            .map(
              (i) => `<tr>
            <td>${i.fee_type_name ?? i.fee_type_id}</td>
            <td class="right">₹${(i.amount_paid + i.discount_amount).toFixed(2)}</td>
            <td class="right">₹${i.discount_amount.toFixed(2)}</td>
            <td class="right">₹${i.amount_paid.toFixed(2)}</td>
          </tr>`,
            )
            .join('')}
        </tbody>
        <tfoot>
          <tr class="total-row">
            <td><b>Total</b></td>
            <td class="right">₹${(col.total_amount + col.total_discount).toFixed(2)}</td>
            <td class="right">₹${col.total_discount.toFixed(2)}</td>
            <td class="right">₹${col.total_amount.toFixed(2)}</td>
          </tr>
        </tfoot>
      </table>
      ${col.remarks ? `<p><b>Remarks:</b> ${col.remarks}</p>` : ''}
      <div class="footer">
        <div><p>___________________________</p><p>Student / Parent Signature</p></div>
        <div><p>___________________________</p><p>Authorised Signatory</p></div>
      </div>`;
    printContent(html, `Receipt ${col.receipt_number}`);
  };

  const printFullReport = () => {
    const yearName = (years as any[]).find((y: any) => y.id === activeYearId)?.name ?? activeYearId;
    const html = `
      <div class="header">
        <h2>Fee Report</h2>
        <p>${studentName} &nbsp;|&nbsp; Admission No: ${admissionNumber}</p>
        <p>Academic Year: ${yearName}</p>
      </div>
      ${
        ledgers.length > 0
          ? ledgers.map((ledger: any) => `
      <h3>Fee Summary — ${ledger.fee_master_name}</h3>
      <table>
        <thead><tr><th>Fee Type</th><th class="right">Due</th><th class="right">Paid</th><th class="right">Discount</th><th class="right">Balance</th></tr></thead>
        <tbody>
          ${ledger.entries
            .map(
              (e: any) => `<tr>
            <td>${e.fee_type_name}</td>
            <td class="right">₹${e.amount_due.toFixed(2)}</td>
            <td class="right">₹${e.amount_paid.toFixed(2)}</td>
            <td class="right">₹${e.discount_given.toFixed(2)}</td>
            <td class="right">₹${e.balance.toFixed(2)}</td>
          </tr>`,
            )
            .join('')}
        </tbody>
        <tfoot>
          <tr class="total-row">
            <td><b>Total</b></td>
            <td class="right">₹${ledger.total_due.toFixed(2)}</td>
            <td class="right">₹${ledger.total_paid.toFixed(2)}</td>
            <td class="right">₹${ledger.total_discount.toFixed(2)}</td>
            <td class="right">₹${ledger.total_balance.toFixed(2)}</td>
          </tr>
        </tfoot>
      </table>`).join('')
          : '<p>No fee master assigned.</p>'
      }
      <h3>Transaction History</h3>
      ${
        (collections as FeeCollection[]).length === 0
          ? '<p>No transactions found.</p>'
          : `<table>
        <thead><tr><th>Receipt No</th><th>Date</th><th class="right">Amount</th><th class="right">Discount</th><th>Method</th><th>Status</th></tr></thead>
        <tbody>
          ${(collections as FeeCollection[])
            .map(
              (c) => `<tr>
            <td>${c.receipt_number}</td>
            <td>${formatDate(c.payment_date)}</td>
            <td class="right">₹${c.total_amount.toFixed(2)}</td>
            <td class="right">₹${c.total_discount.toFixed(2)}</td>
            <td>${c.payment_method.toUpperCase()}</td>
            <td>${c.is_reversed ? '<span class="badge-reversed">REVERSED</span>' : 'Active'}</td>
          </tr>`,
            )
            .join('')}
        </tbody>
      </table>`
      }`;
    printContent(html, `Fee Report — ${studentName}`);
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div>
      {/* Toolbar */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Academic Year:</label>
          <select
            value={activeYearId}
            onChange={(e) => setYearId(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800"
          >
            <option value="">— select —</option>
            {(years as any[]).map((y: any) => (
              <option key={y.id} value={y.id}>
                {y.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <button
            onClick={printFullReport}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Print Full Report
          </button>
        </div>
      </div>

      {!activeYearId && (
        <div className="py-8 text-center text-gray-500">
          Select an academic year to view fee details.
        </div>
      )}

      {activeYearId && !hasAssignments && (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-300">
          No fee master assigned for this student in the selected academic year.
          <br />
          Go to <b>Advanced Fees → Assignments</b> to assign a fee master.
        </div>
      )}

      {/* Fee Ledgers — one card per fee master */}
      {ledgers.map((ledger: any) => (
        <div key={ledger.fee_master_id} className="mb-6 rounded-lg border border-gray-200 dark:border-gray-700">
          {/* Header row */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-900">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {ledger.fee_master_name}
            </h4>
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <span>Due: <b>₹{Number(ledger.total_due).toFixed(2)}</b></span>
              <span>Paid: <b className="text-green-600">₹{Number(ledger.total_paid).toFixed(2)}</b></span>
              <span>Discount: <b className="text-orange-500">₹{Number(ledger.total_discount).toFixed(2)}</b></span>
              <span>Balance: <b className={Number(ledger.total_balance) > 0 ? 'text-red-600' : 'text-green-600'}>₹{Number(ledger.total_balance).toFixed(2)}</b></span>
              <button
                onClick={() => openCollect(ledger)}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
              >
                Collect Fee
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Fee Type</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-500">Due (₹)</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-500">Paid (₹)</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-500">Discount (₹)</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-500">Balance (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {ledger.entries.map((e: any) => (
                  <tr key={e.fee_type_id}>
                    <td className="px-4 py-2 text-gray-900 dark:text-white">{e.fee_type_name}</td>
                    <td className="px-4 py-2 text-right text-gray-700">{Number(e.amount_due).toFixed(2)}</td>
                    <td className="px-4 py-2 text-right text-green-600">{Number(e.amount_paid).toFixed(2)}</td>
                    <td className="px-4 py-2 text-right text-orange-500">{Number(e.discount_given).toFixed(2)}</td>
                    <td className={`px-4 py-2 text-right font-semibold ${Number(e.balance) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {Number(e.balance).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {/* Transaction History */}
      {activeYearId && (
        <div>
          <h4 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Transaction History
          </h4>
          {(collections as FeeCollection[]).length === 0 ? (
            <div className="text-center text-gray-500 py-6 text-sm">No transactions found.</div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="w-full text-sm">
                <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Receipt #</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Date</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-500">Amount (₹)</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-500">Discount (₹)</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Method</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Status</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {(collections as FeeCollection[]).map((col) => (
                    <tr key={col.id} className={col.is_reversed ? 'opacity-60' : ''}>
                      <td className="px-4 py-2 font-mono text-gray-900 dark:text-white">
                        {col.receipt_number}
                      </td>
                      <td className="px-4 py-2 text-gray-600">
                        {formatDate(col.payment_date)}
                      </td>
                      <td className="px-4 py-2 text-right text-gray-900">
                        {Number(col.total_amount).toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-right text-orange-500">
                        {Number(col.total_discount).toFixed(2)}
                      </td>
                      <td className="px-4 py-2 uppercase text-gray-600">{col.payment_method}</td>
                      <td className="px-4 py-2">
                        {col.is_reversed ? (
                          <span className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                            Reversed
                          </span>
                        ) : (
                          <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
                            Active
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex gap-3">
                          <button
                            onClick={() => printReceipt(col)}
                            className="text-xs text-blue-600 hover:underline"
                          >
                            Receipt
                          </button>
                          {!col.is_reversed && (
                            <button
                              onClick={() => handleReverse(col.id)}
                              className="text-xs text-red-600 hover:underline"
                            >
                              Reverse
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Collect Fee Modal ─────────────────────────────────────────────── */}
      {showCollectModal && collectingLedger && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-xl dark:bg-gray-900" style={{ maxHeight: '90vh' }}>
            {/* Modal header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
              <div>
                <h3 className="text-base font-semibold text-gray-900 dark:text-white">Collect Fee</h3>
                <p className="text-xs text-gray-500">{studentName} · {collectingLedger.fee_master_name}</p>
              </div>
              <button
                onClick={() => { setShowCollectModal(false); setCollectingLedger(null); }}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-5">
              {/* Fee type breakdown */}
              <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                <table className="w-full text-sm">
                  <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-500">Fee Type</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-500">Balance</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-500">Amount</th>
                      <th className="px-3 py-2 text-right font-medium text-gray-500">Discount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                    {collectingLedger.entries.map((e: any) => (
                      <tr key={e.fee_type_id}>
                        <td className="px-3 py-2 text-gray-900 dark:text-white">{e.fee_type_name}</td>
                        <td className="px-3 py-2 text-right text-red-600">₹{Number(e.balance).toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">
                          <input
                            type="number"
                            min={0}
                            max={e.balance}
                            value={collectAmounts[e.fee_type_id]?.amount ?? 0}
                            onChange={(ev) =>
                              setCollectAmounts((p) => ({
                                ...p,
                                [e.fee_type_id]: {
                                  ...p[e.fee_type_id],
                                  amount: parseFloat(ev.target.value) || 0,
                                },
                              }))
                            }
                            className="w-24 rounded border border-gray-300 px-2 py-1 text-right text-sm dark:border-gray-600 dark:bg-gray-800"
                          />
                        </td>
                        <td className="px-3 py-2 text-right">
                          <input
                            type="number"
                            min={0}
                            value={collectAmounts[e.fee_type_id]?.discount ?? 0}
                            onChange={(ev) =>
                              setCollectAmounts((p) => ({
                                ...p,
                                [e.fee_type_id]: {
                                  ...p[e.fee_type_id],
                                  discount: parseFloat(ev.target.value) || 0,
                                },
                              }))
                            }
                            className="w-20 rounded border border-gray-300 px-2 py-1 text-right text-sm dark:border-gray-600 dark:bg-gray-800"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Payment details */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                    Payment Method
                  </label>
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  >
                    {PAYMENT_METHODS.map((m) => (
                      <option key={m} value={m}>
                        {m.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                    Payment Date
                  </label>
                  <input
                    type="date"
                    value={paymentDate}
                    onChange={(e) => setPaymentDate(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                    Transaction Ref
                  </label>
                  <input
                    value={txnRef}
                    onChange={(e) => setTxnRef(e.target.value)}
                    placeholder="Optional"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
                    Remarks
                  </label>
                  <input
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                    placeholder="Optional"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800"
                  />
                </div>
              </div>

              {/* Summary bar */}
              <div className="rounded-lg bg-gray-50 px-4 py-3 text-sm dark:bg-gray-800">
                Collecting:{' '}
                <b>
                  ₹
                  {Object.values(collectAmounts)
                    .reduce((s, v) => s + (v.amount || 0), 0)
                    .toFixed(2)}
                </b>{' '}
                &nbsp;|&nbsp; Discount:{' '}
                <b className="text-orange-500">
                  ₹
                  {Object.values(collectAmounts)
                    .reduce((s, v) => s + (v.discount || 0), 0)
                    .toFixed(2)}
                </b>
              </div>
            </div>

            {/* Modal footer */}
            <div className="flex justify-end gap-2 border-t border-gray-200 px-6 py-4 dark:border-gray-700">
              <button
                onClick={() => { setShowCollectModal(false); setCollectingLedger(null); }}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleCollect}
                disabled={collecting}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {collecting ? 'Collecting…' : 'Collect'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentFeeTab;
