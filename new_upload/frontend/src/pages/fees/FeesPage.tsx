import React from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import { toast } from 'sonner';

import { academicYearsApi } from '@api/academicYears';
import { classesApi } from '@api/classes';
import { studentsApi } from '@api/students';
import { feesApi, FeeInvoice, PaymentMethod } from '@api/fees';
import { formatDate } from '@utils/formatters';

const unwrap = (res: any) => res?.data ?? res;

const paymentMethods: PaymentMethod[] = ['cash', 'cheque', 'online', 'card', 'neft', 'upi'];
const today = new Date().toISOString().slice(0, 10);
const TABS = ['Setup', 'Invoices', 'Payments', 'Students', 'Reports'] as const;
type TabId = typeof TABS[number];

const discountNatureOptions = [
  { value: '', label: '— None —' },
  { value: 'merit', label: 'Merit' },
  { value: 'sibling', label: 'Sibling' },
  { value: 'scholarship', label: 'Scholarship' },
  { value: 'staff_child', label: 'Staff Child' },
  { value: 'armed_forces', label: 'Armed Forces' },
  { value: 'ews', label: 'EWS' },
  { value: 'early_payment', label: 'Early Payment' },
  { value: 'financial_aid', label: 'Financial Aid' },
  { value: 'loyalty', label: 'Loyalty' },
  { value: 'custom', label: 'Custom' },
];

const Modal: React.FC<{ title: string; onClose: () => void; children: React.ReactNode }> = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold">{title}</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
      </div>
      {children}
    </div>
  </div>
);

const Card: React.FC<{ title?: string; children: React.ReactNode; className?: string }> = ({ title, children, className = '' }) => (
  <div className={`rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800 ${className}`}>
    {title && <h3 className="mb-3 text-sm font-semibold">{title}</h3>}
    {children}
  </div>
);

const inp = 'w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white';

const Page: React.FC = () => {
  const [tab, setTab] = React.useState<TabId>('Invoices');

  const [years, setYears] = React.useState<any[]>([]);
  const [classes, setClasses] = React.useState<any[]>([]);
  const [sections, setSections] = React.useState<any[]>([]);
  const [categories, setCategories] = React.useState<any[]>([]);
  const [discounts, setDiscounts] = React.useState<any[]>([]);

  const [academicYearId, setAcademicYearId] = React.useState('');
  const [classId, setClassId] = React.useState('');
  const [sectionId, setSectionId] = React.useState('');
  const [invoiceMonthYear, setInvoiceMonthYear] = React.useState(
    `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`
  );
  const invoiceYear = Number(invoiceMonthYear.split('-')[0]);
  const invoiceMonth = Number(invoiceMonthYear.split('-')[1]);

  // Setup tab
  const [categoryName, setCategoryName] = React.useState('');
  const [categoryDesc, setCategoryDesc] = React.useState('');
  const [structureCategoryId, setStructureCategoryId] = React.useState('');
  const [structureAmount, setStructureAmount] = React.useState('0');
  const [structureFrequency, setStructureFrequency] = React.useState<any>('monthly');
  const [structureDueDay, setStructureDueDay] = React.useState('10');
  const [structures, setStructures] = React.useState<any[]>([]);
  const [discountName, setDiscountName] = React.useState('');
  const [discountType, setDiscountType] = React.useState<'percentage' | 'fixed'>('percentage');
  const [discountValue, setDiscountValue] = React.useState('0');
  const [discountNature, setDiscountNature] = React.useState('');

  // Invoices tab
  const [invoiceStatus, setInvoiceStatus] = React.useState('');
  const [invoices, setInvoices] = React.useState<FeeInvoice[]>([]);

  // Payments tab
  const [payments, setPayments] = React.useState<any[]>([]);
  const [selectedInvoiceId, setSelectedInvoiceId] = React.useState('');
  const [paymentAmount, setPaymentAmount] = React.useState('0');
  const [paymentMethod, setPaymentMethod] = React.useState<PaymentMethod>('cash');
  const [paymentDate, setPaymentDate] = React.useState(today);
  const [transactionId, setTransactionId] = React.useState('');
  const [payFromDate, setPayFromDate] = React.useState('');
  const [payToDate, setPayToDate] = React.useState('');
  const [reversalPaymentId, setReversalPaymentId] = React.useState('');
  const [reversalReason, setReversalReason] = React.useState('');

  // Students tab
  const [allStudents, setAllStudents] = React.useState<any[]>([]);
  const [studentSearch, setStudentSearch] = React.useState('');
  const [selectedStudentId, setSelectedStudentId] = React.useState('');
  const [selectedStudentName, setSelectedStudentName] = React.useState('');
  const [studentDiscounts, setStudentDiscounts] = React.useState<any[]>([]);
  const [studentStatement, setStudentStatement] = React.useState<any>(null);
  const [clearance, setClearance] = React.useState<any>(null);
  const [assignDiscountId, setAssignDiscountId] = React.useState('');
  const [assignDiscountYear, setAssignDiscountYear] = React.useState('');
  const [assignRemarks, setAssignRemarks] = React.useState('');

  // Reports tab
  const [dailyCollection, setDailyCollection] = React.useState<any>(null);
  const [monthlyCollection, setMonthlyCollection] = React.useState<any>(null);
  const [defaulters, setDefaulters] = React.useState<any[]>([]);
  const [rolloverFromYear, setRolloverFromYear] = React.useState('');
  const [rolloverToYear, setRolloverToYear] = React.useState('');

  // Bootstrap
  React.useEffect(() => {
    (async () => {
      try {
        const [yearsData, catsData, discsData] = await Promise.all([
          academicYearsApi.list(),
          feesApi.listCategories(),
          feesApi.listDiscounts(),
        ]);
        const yearRows: any[] = Array.isArray(unwrap(yearsData)) ? unwrap(yearsData) : unwrap(yearsData)?.items ?? [];
        setYears(yearRows);
        const current = yearRows.find((x: any) => x.is_current) || yearRows[0];
        if (current?.id) { setAcademicYearId(current.id); setAssignDiscountYear(current.id); }
        const catRows: any[] = Array.isArray(unwrap(catsData)) ? unwrap(catsData) : unwrap(catsData)?.items ?? [];
        setCategories(catRows);
        if (catRows[0]?.id) setStructureCategoryId(catRows[0].id);
        const discRows: any[] = Array.isArray(unwrap(discsData)) ? unwrap(discsData) : [];
        setDiscounts(discRows);
      } catch { toast.error('Failed to load master data'); }
    })();
  }, []);

  React.useEffect(() => {
    if (!academicYearId) return;
    (async () => {
      try {
        const rows = unwrap(await classesApi.list(academicYearId));
        setClasses(Array.isArray(rows) ? rows : rows?.items ?? []);
        setClassId(''); setSectionId(''); setSections([]);
      } catch { toast.error('Failed to load classes'); }
    })();
  }, [academicYearId]);

  React.useEffect(() => {
    if (!classId) { setSections([]); setSectionId(''); return; }
    (async () => {
      try {
        const rows = unwrap(await classesApi.listSections(classId));
        setSections(Array.isArray(rows) ? rows : rows?.items ?? []);
        setSectionId('');
      } catch { toast.error('Failed to load sections'); }
    })();
  }, [classId]);

  const loadInvoices = React.useCallback(async () => {
    if (!academicYearId) return;
    try {
      const data = unwrap(await feesApi.listInvoices({
        academic_year_id: academicYearId,
        month: invoiceMonth,
        year: invoiceYear,
        class_id: classId || undefined,
        section_id: sectionId || undefined,
        status: (invoiceStatus as any) || undefined,
      }));
      const rows: FeeInvoice[] = Array.isArray(data) ? data : data?.items ?? [];
      setInvoices(rows);
      if (rows[0]?.id && !selectedInvoiceId) {
        setSelectedInvoiceId(rows[0].id);
        setPaymentAmount(String((rows[0] as any).balance_amount || 0));
      }
    } catch { toast.error('Failed to load invoices'); }
  }, [academicYearId, classId, sectionId, invoiceMonthYear, invoiceStatus, selectedInvoiceId, invoiceMonth, invoiceYear]);

  React.useEffect(() => { void loadInvoices(); }, [loadInvoices]);

  const loadStructures = React.useCallback(async () => {
    if (!academicYearId) return;
    try {
      const data = unwrap(await feesApi.listStructures({ academic_year_id: academicYearId, class_id: classId || undefined }));
      setStructures(Array.isArray(data) ? data : data?.items ?? []);
    } catch { toast.error('Failed to load structures'); }
  }, [academicYearId, classId]);

  React.useEffect(() => { void loadStructures(); }, [loadStructures]);

  const loadPayments = React.useCallback(async () => {
    try {
      const data = unwrap(await feesApi.listPayments({ from_date: payFromDate || undefined, to_date: payToDate || undefined }));
      setPayments(Array.isArray(data) ? data : data?.items ?? []);
    } catch { toast.error('Failed to load payments'); }
  }, [payFromDate, payToDate]);

  React.useEffect(() => { if (tab === 'Payments') void loadPayments(); }, [tab, loadPayments]);

  const loadReports = React.useCallback(async () => {
    if (!academicYearId) return;
    try {
      const [daily, monthly, defs] = await Promise.all([
        feesApi.getDailyCollection(today),
        feesApi.getMonthlyCollection(invoiceMonth, invoiceYear),
        feesApi.getDefaulters(academicYearId, today),
      ]);
      setDailyCollection(unwrap(daily));
      setMonthlyCollection(unwrap(monthly));
      setDefaulters(Array.isArray(unwrap(defs)) ? unwrap(defs) : []);
    } catch { toast.error('Failed to load reports'); }
  }, [academicYearId, invoiceMonth, invoiceYear]);

  React.useEffect(() => { if (tab === 'Reports') void loadReports(); }, [tab, loadReports]);

  React.useEffect(() => {
    if (tab !== 'Students') return;
    (async () => {
      try {
        const data = unwrap(await studentsApi.listStudents({ academic_year_id: academicYearId || undefined }));
        setAllStudents(Array.isArray(data) ? data : data?.items ?? []);
      } catch { /* silent */ }
    })();
  }, [tab, academicYearId]);

  const filteredStudents = allStudents.filter((s: any) => {
    const name = `${s.first_name} ${s.last_name}`.toLowerCase();
    const adm = (s.admission_number || '').toLowerCase();
    const q = studentSearch.toLowerCase();
    return name.includes(q) || adm.includes(q);
  });

  const selectStudent = async (student: any) => {
    setSelectedStudentId(student.id);
    setSelectedStudentName(`${student.first_name} ${student.last_name}`);
    setStudentStatement(null); setClearance(null); setStudentDiscounts([]);
    if (!academicYearId) return;
    const [discData, clearData, stmtData] = await Promise.allSettled([
      feesApi.getStudentDiscounts(student.id, academicYearId),
      feesApi.getFeeClearance(student.id, academicYearId),
      feesApi.getStudentStatement(student.id, academicYearId),
    ]);
    if (discData.status === 'fulfilled') setStudentDiscounts(Array.isArray(unwrap(discData.value)) ? unwrap(discData.value) : []);
    if (clearData.status === 'fulfilled') setClearance(unwrap(clearData.value));
    if (stmtData.status === 'fulfilled') setStudentStatement(unwrap(stmtData.value));
  };

  // Actions
  const createCategory = async () => {
    if (!categoryName.trim()) { toast.error('Category name required'); return; }
    try {
      await feesApi.createCategory({ name: categoryName.trim(), description: categoryDesc || undefined });
      setCategoryName(''); setCategoryDesc('');
      toast.success('Category created');
      const cats = unwrap(await feesApi.listCategories());
      setCategories(Array.isArray(cats) ? cats : cats?.items ?? []);
    } catch { toast.error('Failed to create category'); }
  };

  const createStructure = async () => {
    if (!academicYearId || !classId || !structureCategoryId) { toast.error('Select year, class and category'); return; }
    try {
      await feesApi.upsertStructures({
        academic_year_id: academicYearId, class_id: classId,
        items: [{ fee_category_id: structureCategoryId, amount: Math.max(0, Number(structureAmount) || 0), frequency: structureFrequency, due_day: Number(structureDueDay) || 10, is_active: true }],
      });
      toast.success('Structure saved');
      await loadStructures();
    } catch { toast.error('Failed to save structure'); }
  };

  const createDiscount = async () => {
    if (!discountName.trim()) { toast.error('Discount name required'); return; }
    try {
      await feesApi.createDiscount({ name: discountName.trim(), type: discountType, value: Number(discountValue) || 0, applicable_to: 'student', nature: discountNature || undefined } as any);
      setDiscountName(''); setDiscountType('percentage'); setDiscountValue('0'); setDiscountNature('');
      toast.success('Discount created');
      const discs = unwrap(await feesApi.listDiscounts());
      setDiscounts(Array.isArray(discs) ? discs : []);
    } catch { toast.error('Failed to create discount'); }
  };

  const generateInvoices = async () => {
    if (!academicYearId) { toast.error('Select academic year'); return; }
    try {
      const res = unwrap(await feesApi.generateInvoices({ academic_year_id: academicYearId, month: invoiceMonth, year: invoiceYear, class_id: classId || undefined }));
      toast.success(`Created: ${res.created ?? 0}, Skipped: ${res.skipped ?? 0}`);
      await loadInvoices();
    } catch { toast.error('Failed to generate invoices'); }
  };

  const assignFees = async () => {
    if (!academicYearId) { toast.error('Select academic year'); return; }
    try {
      const res = unwrap(await feesApi.assignFees({ academic_year_id: academicYearId, class_id: classId || undefined }));
      toast.success(`Assigned: ${res.assigned ?? 0}, Skipped: ${res.skipped ?? 0}`);
    } catch { toast.error('Failed to assign fees'); }
  };

  const collectPayment = async () => {
    if (!selectedInvoiceId) { toast.error('Select an invoice'); return; }
    try {
      await feesApi.collectPayment({ invoice_id: selectedInvoiceId, amount: Number(paymentAmount) || 0, payment_date: paymentDate, payment_method: paymentMethod, transaction_id: transactionId || undefined });
      toast.success('Payment collected');
      setTransactionId('');
      await loadInvoices(); await loadPayments();
    } catch { toast.error('Failed to collect payment'); }
  };

  const submitReversal = async () => {
    if (!reversalReason.trim()) { toast.error('Reason required'); return; }
    try {
      await feesApi.reversePayment(reversalPaymentId, reversalReason);
      toast.success('Payment reversed');
      setReversalPaymentId(''); setReversalReason('');
      await loadPayments(); await loadInvoices();
    } catch (e: any) { toast.error(e?.response?.data?.detail || 'Failed to reverse payment'); }
  };

  const downloadReceipt = async (paymentId: string, receiptNumber: string) => {
    try {
      const blob = await feesApi.downloadReceipt(paymentId);
      const url = URL.createObjectURL(blob as Blob);
      const a = document.createElement('a'); a.href = url; a.download = `receipt-${receiptNumber}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch { toast.error('Failed to download receipt'); }
  };

  const assignStudentDiscount = async () => {
    if (!selectedStudentId || !assignDiscountId || !assignDiscountYear) { toast.error('Select student, discount and year'); return; }
    try {
      await feesApi.assignStudentDiscount(selectedStudentId, { discount_id: assignDiscountId, academic_year_id: assignDiscountYear, remarks: assignRemarks || undefined });
      toast.success('Discount assigned');
      setAssignDiscountId(''); setAssignRemarks('');
      const data = unwrap(await feesApi.getStudentDiscounts(selectedStudentId, assignDiscountYear));
      setStudentDiscounts(Array.isArray(data) ? data : []);
    } catch (e: any) { toast.error(e?.response?.data?.detail || 'Failed to assign discount'); }
  };

  const removeStudentDiscount = async (assignmentId: string) => {
    try {
      await feesApi.removeStudentDiscount(selectedStudentId, assignmentId);
      toast.success('Discount removed');
      const data = unwrap(await feesApi.getStudentDiscounts(selectedStudentId, academicYearId));
      setStudentDiscounts(Array.isArray(data) ? data : []);
    } catch { toast.error('Failed to remove discount'); }
  };

  const doRollover = async () => {
    if (!rolloverFromYear || !rolloverToYear) { toast.error('Select both years'); return; }
    try {
      const res = unwrap(await feesApi.rolloverStructures(rolloverFromYear, rolloverToYear));
      toast.success(`Rollover complete: created ${res.created}, skipped ${res.skipped}`);
    } catch { toast.error('Rollover failed'); }
  };

  const statusBadge = (s: string) => {
    const map: Record<string, string> = { paid: 'bg-green-100 text-green-800', partial: 'bg-yellow-100 text-yellow-800', unpaid: 'bg-red-100 text-red-800', overdue: 'bg-orange-100 text-orange-800', waived: 'bg-blue-100 text-blue-700', cancelled: 'bg-gray-100 text-gray-600' };
    return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${map[s] || 'bg-gray-100 text-gray-600'}`}>{s}</span>;
  };

  const filterBar = (
    <div className="mb-4 grid gap-3 md:grid-cols-6">
      <select className={inp} value={academicYearId} onChange={(e) => setAcademicYearId(e.target.value)}>
        <option value="">Academic Year</option>
        {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
      </select>
      <select className={inp} value={classId} onChange={(e) => { setClassId(e.target.value); setSectionId(''); }}>
        <option value="">All Classes</option>
        {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>
      <select className={inp} value={sectionId} onChange={(e) => setSectionId(e.target.value)} disabled={sections.length === 0}>
        <option value="">All Sections</option>
        {sections.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>
      <input type="month" className={inp} value={invoiceMonthYear} onChange={(e) => setInvoiceMonthYear(e.target.value)} />
      <select className={inp} value={invoiceStatus} onChange={(e) => setInvoiceStatus(e.target.value)}>
        <option value="">All Status</option>
        {['unpaid', 'partial', 'paid', 'overdue', 'waived', 'cancelled'].map((s) => <option key={s} value={s}>{s}</option>)}
      </select>
      <div className="flex gap-2">
        <button onClick={assignFees} className="flex-1 rounded border border-gray-300 px-2 py-2 text-xs hover:bg-gray-50">Assign Fees</button>
        <button onClick={generateInvoices} className="flex-1 rounded bg-brand-600 px-2 py-2 text-xs font-semibold text-white hover:bg-brand-700">Generate</button>
      </div>
    </div>
  );

  const setupTab = (
    <div className="grid gap-4 md:grid-cols-3">
      <Card title="Fee Categories">
        <div className="space-y-2">
          <input className={inp} placeholder="Category name *" value={categoryName} onChange={(e) => setCategoryName(e.target.value)} />
          <input className={inp} placeholder="Description" value={categoryDesc} onChange={(e) => setCategoryDesc(e.target.value)} />
          <button onClick={createCategory} className="rounded bg-brand-600 px-3 py-2 text-sm font-semibold text-white">Add Category</button>
        </div>
        <ul className="mt-3 divide-y divide-gray-100 dark:divide-gray-700">
          {categories.map((c: any) => <li key={c.id} className="py-1 text-xs text-gray-700 dark:text-gray-300">{c.name}</li>)}
        </ul>
      </Card>

      <Card title="Fee Structure">
        <div className="space-y-2">
          <select className={inp} value={academicYearId} onChange={(e) => setAcademicYearId(e.target.value)}>
            <option value="">Select Academic Year *</option>
            {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
          </select>
          <select className={inp} value={classId} onChange={(e) => { setClassId(e.target.value); setSectionId(''); }} disabled={!academicYearId || classes.length === 0}>
            <option value="">{!academicYearId ? 'Select year first' : classes.length === 0 ? 'No classes found' : 'Select Class *'}</option>
            {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select className={inp} value={structureCategoryId} onChange={(e) => setStructureCategoryId(e.target.value)}>
            <option value="">Select Category *</option>
            {categories.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <input type="number" className={inp} placeholder="Amount (paise)" value={structureAmount} onChange={(e) => setStructureAmount(e.target.value)} />
          <div className="grid grid-cols-2 gap-2">
            <select className={inp} value={structureFrequency} onChange={(e) => setStructureFrequency(e.target.value)}>
              {['monthly', 'quarterly', 'semi_annual', 'annual', 'one_time'].map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
            <input type="number" min={1} max={31} className={inp} placeholder="Due day" value={structureDueDay} onChange={(e) => setStructureDueDay(e.target.value)} />
          </div>
          <button onClick={createStructure} className="rounded bg-brand-600 px-3 py-2 text-sm font-semibold text-white">Save Structure</button>
        </div>
        <div className="mt-3 space-y-1">
          {structures.slice(0, 8).map((s: any) => (
            <div key={s.id} className="rounded border border-gray-100 p-1.5 text-xs dark:border-gray-700">
              {s.fee_category_name} — {s.amount} — {s.frequency}
            </div>
          ))}
        </div>
      </Card>

      <Card title="Fee Discounts">
        <div className="space-y-2">
          <input className={inp} placeholder="Discount name *" value={discountName} onChange={(e) => setDiscountName(e.target.value)} />
          <div className="grid grid-cols-2 gap-2">
            <select className={inp} value={discountType} onChange={(e) => setDiscountType(e.target.value as any)}>
              <option value="percentage">percentage</option>
              <option value="fixed">fixed</option>
            </select>
            <input type="number" className={inp} placeholder="Value" value={discountValue} onChange={(e) => setDiscountValue(e.target.value)} />
          </div>
          <select className={inp} value={discountNature} onChange={(e) => setDiscountNature(e.target.value)}>
            {discountNatureOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <button onClick={createDiscount} className="rounded bg-brand-600 px-3 py-2 text-sm font-semibold text-white">Add Discount</button>
        </div>
        <ul className="mt-3 divide-y divide-gray-100 dark:divide-gray-700">
          {discounts.map((d: any) => (
            <li key={d.id} className="py-1 text-xs text-gray-700 dark:text-gray-300">
              {d.name} · {d.type} · {d.value}{d.type === 'percentage' ? '%' : ''}
              {d.nature && <span className="ml-1 rounded bg-gray-100 px-1 dark:bg-gray-700">{d.nature}</span>}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );

  const invoicesTab = (
    <Card>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700 text-left text-xs uppercase text-gray-500">
              <th className="px-3 py-2">Invoice #</th>
              <th className="px-3 py-2">Student</th>
              <th className="px-3 py-2">Class</th>
              <th className="px-3 py-2">Section</th>
              <th className="px-3 py-2">Due Date</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2 text-right">Total</th>
              <th className="px-3 py-2 text-right">Paid</th>
              <th className="px-3 py-2 text-right">Balance</th>
            </tr>
          </thead>
          <tbody>
            {invoices.length === 0 ? (
              <tr><td colSpan={9} className="px-3 py-8 text-center text-gray-500">No invoices for selected period.</td></tr>
            ) : invoices.map((inv: any) => (
              <tr key={inv.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                <td className="px-3 py-2 font-mono text-xs">{inv.invoice_number}</td>
                <td className="px-3 py-2">{inv.student_name || '—'}</td>
                <td className="px-3 py-2">{inv.class_name || '—'}</td>
                <td className="px-3 py-2">{inv.section_name || '—'}</td>
                <td className="px-3 py-2 text-xs">{formatDate(inv.due_date)}</td>
                <td className="px-3 py-2">{statusBadge(inv.status)}</td>
                <td className="px-3 py-2 text-right">{inv.total_amount}</td>
                <td className="px-3 py-2 text-right">{inv.paid_amount}</td>
                <td className="px-3 py-2 text-right font-semibold">{inv.balance_amount > 0 ? inv.balance_amount : <span className="text-green-600">Paid</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );

  const paymentsTab = (
    <div className="space-y-4">
      <Card title="Collect Payment">
        <div className="grid gap-2 md:grid-cols-6">
          <select className={inp} value={selectedInvoiceId} onChange={(e) => {
            setSelectedInvoiceId(e.target.value);
            const inv: any = invoices.find((i) => i.id === e.target.value);
            if (inv) setPaymentAmount(String(inv.balance_amount));
          }}>
            <option value="">Select Invoice</option>
            {invoices.filter((inv: any) => inv.balance_amount > 0).map((inv: any) => (
              <option key={inv.id} value={inv.id}>{inv.invoice_number} — {inv.student_name} — Bal {inv.balance_amount}</option>
            ))}
          </select>
          <input type="number" className={inp} placeholder="Amount (paise)" value={paymentAmount} onChange={(e) => setPaymentAmount(e.target.value)} />
          <select className={inp} value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}>
            {paymentMethods.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          <input type="date" className={inp} value={paymentDate} onChange={(e) => setPaymentDate(e.target.value)} />
          <input className={inp} placeholder="Transaction ID (opt)" value={transactionId} onChange={(e) => setTransactionId(e.target.value)} />
          <button onClick={collectPayment} className="rounded bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700">Collect</button>
        </div>
      </Card>

      <div className="flex gap-3">
        <input type="date" className="rounded border border-gray-300 px-3 py-2 text-sm" value={payFromDate} onChange={(e) => setPayFromDate(e.target.value)} />
        <input type="date" className="rounded border border-gray-300 px-3 py-2 text-sm" value={payToDate} onChange={(e) => setPayToDate(e.target.value)} />
        <button onClick={loadPayments} className="rounded border border-gray-300 px-3 py-2 text-sm">Filter</button>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 text-left text-xs uppercase text-gray-500">
                <th className="px-3 py-2">Receipt</th>
                <th className="px-3 py-2">Student</th>
                <th className="px-3 py-2">Invoice</th>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Method</th>
                <th className="px-3 py-2 text-right">Amount</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {payments.length === 0 ? (
                <tr><td colSpan={8} className="px-3 py-8 text-center text-gray-500">No payments found.</td></tr>
              ) : payments.map((p: any) => (
                <tr key={p.id} className={`border-b border-gray-100 dark:border-gray-800 ${p.is_reversed ? 'opacity-50' : ''}`}>
                  <td className="px-3 py-2 font-mono text-xs">{p.receipt_number}</td>
                  <td className="px-3 py-2">{p.student_name || '—'}</td>
                  <td className="px-3 py-2 text-xs">{p.invoice_number}</td>
                  <td className="px-3 py-2 text-xs">{formatDate(p.payment_date)}</td>
                  <td className="px-3 py-2 text-xs">{p.payment_method}</td>
                  <td className="px-3 py-2 text-right">{p.amount}</td>
                  <td className="px-3 py-2">
                    {p.is_reversed
                      ? <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">Reversed</span>
                      : <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">Active</span>}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      {!p.is_reversed && (
                        <button onClick={() => downloadReceipt(p.id, p.receipt_number)} className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-700 hover:bg-blue-200">⬇ Receipt</button>
                      )}
                      {!p.is_reversed && (
                        <button onClick={() => { setReversalPaymentId(p.id); setReversalReason(''); }} className="rounded bg-red-100 px-2 py-1 text-xs text-red-700 hover:bg-red-200">Reverse</button>
                      )}
                      {p.is_reversed && p.reversal_reason && (
                        <span className="cursor-help text-xs text-gray-400" title={p.reversal_reason}>ℹ</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {reversalPaymentId && (
        <Modal title="Reverse Payment" onClose={() => setReversalPaymentId('')}>
          <p className="mb-3 text-sm text-gray-600">Provide a reason for reversing this payment.</p>
          <textarea className="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm" rows={3} placeholder="Reason (required)" value={reversalReason} onChange={(e) => setReversalReason(e.target.value)} />
          <div className="flex justify-end gap-2">
            <button onClick={() => setReversalPaymentId('')} className="rounded border border-gray-300 px-3 py-2 text-sm">Cancel</button>
            <button onClick={submitReversal} className="rounded bg-red-600 px-3 py-2 text-sm font-semibold text-white">Confirm Reverse</button>
          </div>
        </Modal>
      )}
    </div>
  );

  const studentsTab = (
    <div className="grid gap-4 md:grid-cols-3">
      <Card title="Student Search">
        <input className={inp} placeholder="Search by name or admission no." value={studentSearch} onChange={(e) => setStudentSearch(e.target.value)} />
        <ul className="mt-2 max-h-72 divide-y divide-gray-100 overflow-y-auto dark:divide-gray-700">
          {filteredStudents.slice(0, 30).map((s: any) => (
            <li key={s.id} onClick={() => void selectStudent(s)} className={`cursor-pointer px-2 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-700/30 ${selectedStudentId === s.id ? 'bg-brand-50 font-semibold' : ''}`}>
              {s.first_name} {s.last_name}
              {s.admission_number && <span className="ml-1 text-xs text-gray-400">({s.admission_number})</span>}
            </li>
          ))}
        </ul>
      </Card>

      <Card title={selectedStudentName ? `Discounts — ${selectedStudentName}` : 'Select a student'}>
        {selectedStudentId ? (
          <>
            <div className="space-y-2">
              <select className={inp} value={assignDiscountId} onChange={(e) => setAssignDiscountId(e.target.value)}>
                <option value="">Select Discount</option>
                {discounts.map((d: any) => <option key={d.id} value={d.id}>{d.name} ({d.type}: {d.value})</option>)}
              </select>
              <select className={inp} value={assignDiscountYear} onChange={(e) => setAssignDiscountYear(e.target.value)}>
                <option value="">Select Year</option>
                {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
              </select>
              <input className={inp} placeholder="Remarks (optional)" value={assignRemarks} onChange={(e) => setAssignRemarks(e.target.value)} />
              <button onClick={assignStudentDiscount} className="rounded bg-brand-600 px-3 py-2 text-sm font-semibold text-white">Assign Discount</button>
            </div>
            <ul className="mt-3 divide-y divide-gray-100 dark:divide-gray-700">
              {studentDiscounts.map((d: any) => (
                <li key={d.id} className="flex items-center justify-between py-1.5 text-xs">
                  <span>{d.discount_name} · {d.discount_type} · {d.discount_value}
                    {d.discount_nature && <span className="ml-1 rounded bg-gray-100 px-1 dark:bg-gray-700">{d.discount_nature}</span>}
                  </span>
                  <button onClick={() => removeStudentDiscount(d.id)} className="text-red-500 hover:text-red-700">✕</button>
                </li>
              ))}
              {studentDiscounts.length === 0 && <li className="py-2 text-gray-400">No discounts assigned.</li>}
            </ul>
            {clearance && (
              <div className={`mt-3 rounded p-3 text-sm ${clearance.has_outstanding ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                {clearance.has_outstanding
                  ? `Outstanding: ${clearance.total_outstanding} across ${clearance.outstanding_invoices} invoice(s)`
                  : 'No outstanding dues — Clearance granted'}
              </div>
            )}
          </>
        ) : <p className="text-sm text-gray-400">Select a student to manage discounts and view clearance.</p>}
      </Card>

      <Card title={selectedStudentName ? `Statement — ${selectedStudentName}` : 'Statement'}>
        {studentStatement ? (
          <>
            <div className="mb-2 grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded bg-gray-50 p-2 dark:bg-gray-700"><p className="text-gray-500">Total</p><p className="font-semibold">{studentStatement.total_amount}</p></div>
              <div className="rounded bg-green-50 p-2 dark:bg-green-900/20"><p className="text-gray-500">Paid</p><p className="font-semibold text-green-600">{studentStatement.total_paid}</p></div>
              <div className="rounded bg-red-50 p-2 dark:bg-red-900/20"><p className="text-gray-500">Due</p><p className="font-semibold text-red-600">{studentStatement.total_due}</p></div>
            </div>
            <ul className="max-h-56 divide-y divide-gray-100 overflow-y-auto dark:divide-gray-700">
              {(studentStatement.invoices || []).map((inv: any) => (
                <li key={inv.id} className="flex items-center justify-between py-1 text-xs">
                  <span>{inv.invoice_number}</span>
                  {statusBadge(inv.status)}
                  <span>{inv.balance_amount}</span>
                </li>
              ))}
            </ul>
          </>
        ) : selectedStudentId ? (
          <p className="text-sm text-gray-400">Loading...</p>
        ) : (
          <p className="text-sm text-gray-400">Select a student to view statement.</p>
        )}
      </Card>
    </div>
  );

  const reportsTab = (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <Card title="Daily Collection">
          <p className="text-2xl font-bold">{dailyCollection?.total_collected ?? 0}</p>
          <p className="text-sm text-gray-500">{dailyCollection?.transaction_count ?? 0} transactions today</p>
        </Card>
        <Card title={`Monthly Collection (${invoiceMonthYear})`}>
          <p className="text-2xl font-bold">{monthlyCollection?.total_collected ?? 0}</p>
          <p className="text-sm text-gray-500">{monthlyCollection?.transaction_count ?? 0} transactions</p>
        </Card>
        <Card title="Defaulters">
          <p className="text-2xl font-bold text-red-600">{defaulters.length}</p>
          <p className="text-sm text-gray-500">Students with overdue invoices</p>
        </Card>
      </div>

      {defaulters.length > 0 && (
        <Card title="Defaulter List">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs uppercase text-gray-500">
                <th className="px-3 py-2">Student</th>
                <th className="px-3 py-2 text-right">Outstanding</th>
                <th className="px-3 py-2">Since</th>
              </tr>
            </thead>
            <tbody>
              {defaulters.map((d: any, i: number) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="px-3 py-2">{d.student_name}</td>
                  <td className="px-3 py-2 text-right text-red-600">{d.outstanding_amount}</td>
                  <td className="px-3 py-2 text-xs text-gray-500">{d.oldest_due_date || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <Card title="Fee Structure Rollover">
        <p className="mb-3 text-sm text-gray-600">Copy all active fee structures from one academic year to another.</p>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-gray-500">From Year</label>
            <select className="rounded border border-gray-300 px-3 py-2 text-sm" value={rolloverFromYear} onChange={(e) => setRolloverFromYear(e.target.value)}>
              <option value="">Select Year</option>
              {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-500">To Year</label>
            <select className="rounded border border-gray-300 px-3 py-2 text-sm" value={rolloverToYear} onChange={(e) => setRolloverToYear(e.target.value)}>
              <option value="">Select Year</option>
              {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}</option>)}
            </select>
          </div>
          <button onClick={doRollover} className="rounded bg-brand-600 px-4 py-2 text-sm font-semibold text-white">Rollover Structures</button>
        </div>
      </Card>
    </div>
  );

  return (
    <div>
      <PageHeader title="Fee Management" subtitle="Fee structures, billing, collection, and reports" />
      <div className="mb-3 flex items-center justify-end">
        <a href="/admin/fees-advanced"
          className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700">
          ⚡ Switch to Advanced Fee Mode
        </a>
      </div>
      <div className="mb-4 flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-sm font-medium transition-colors ${tab === t ? 'border-b-2 border-brand-600 text-brand-600' : 'text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'}`}>{t}</button>
        ))}
      </div>
      {filterBar}
      {tab === 'Setup' && setupTab}
      {tab === 'Invoices' && invoicesTab}
      {tab === 'Payments' && paymentsTab}
      {tab === 'Students' && studentsTab}
      {tab === 'Reports' && reportsTab}
    </div>
  );
};

export default Page;
