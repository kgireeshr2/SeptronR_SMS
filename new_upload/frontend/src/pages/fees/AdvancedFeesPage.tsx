import React from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import { toast } from 'sonner';
import { academicYearsApi } from '@api/academicYears';
import { classesApi } from '@api/classes';
import { studentsApi } from '@api/students';
import { feesV2Api, FeeType, FeeGroup, FeeMaster, FeeCollection, StudentFeeLedger, PaymentMethod } from '@api/feesV2';
import { formatDate } from '@utils/formatters';

const unwrap = (res: any) => res?.data ?? res;
const fmt = (n: number) => `₹${n.toLocaleString('en-IN')}`;
const today = new Date().toISOString().slice(0, 10);

const TABS = ['Fee Types', 'Fee Groups', 'Fee Master', 'Assignments', 'Collection'] as const;
type TabId = typeof TABS[number];

const paymentMethods: PaymentMethod[] = ['cash', 'cheque', 'online', 'card', 'neft', 'upi'];

// ─── Shared UI helpers ───────────────────────────────────────
const inp = 'w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500';
const btn = (variant: 'primary' | 'danger' | 'ghost' = 'primary') =>
  variant === 'primary'
    ? 'rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50'
    : variant === 'danger'
    ? 'rounded bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700'
    : 'rounded border border-gray-300 px-3 py-1.5 text-xs hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700';

const Card: React.FC<{ title?: string; children: React.ReactNode; className?: string }> = ({ title, children, className = '' }) => (
  <div className={`rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800 ${className}`}>
    {title && <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">{title}</h3>}
    {children}
  </div>
);

const Modal: React.FC<{ title: string; onClose: () => void; children: React.ReactNode; size?: 'sm' | 'md' | 'lg' }> = ({
  title, onClose, children, size = 'md',
}) => {
  const w = size === 'lg' ? 'max-w-2xl' : size === 'sm' ? 'max-w-sm' : 'max-w-md';
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 pt-10">
      <div className={`w-full ${w} rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800 mb-10`}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-lg">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
};

const Badge: React.FC<{ active: boolean }> = ({ active }) => (
  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
    {active ? 'Active' : 'Inactive'}
  </span>
);

// ─── Main Component ────────────────────────────────────────
const AdvancedFeesPage: React.FC = () => {
  const [tab, setTab] = React.useState<TabId>('Fee Types');

  // Master data
  const [years, setYears] = React.useState<any[]>([]);
  const [classes, setClasses] = React.useState<any[]>([]);
  const [feeTypes, setFeeTypes] = React.useState<FeeType[]>([]);
  const [feeGroups, setFeeGroups] = React.useState<FeeGroup[]>([]);
  const [feeMasters, setFeeMasters] = React.useState<FeeMaster[]>([]);
  const [assignments, setAssignments] = React.useState<any[]>([]);
  const [collections, setCollections] = React.useState<FeeCollection[]>([]);

  // Filters
  const [yearId, setYearId] = React.useState('');
  const [includeReversed, setIncludeReversed] = React.useState(false);

  // ── Load master data on mount
  React.useEffect(() => {
    (async () => {
      try {
        const [yearsRes, typesRes, groupsRes] = await Promise.all([
          academicYearsApi.list(),
          feesV2Api.listFeeTypes(),
          feesV2Api.listFeeGroups(),
        ]);
        const yrs = Array.isArray(unwrap(yearsRes)) ? unwrap(yearsRes) : unwrap(yearsRes)?.items ?? [];
        setYears(yrs);
        const cur = yrs.find((y: any) => y.is_current) || yrs[0];
        if (cur?.id) setYearId(cur.id);
        setFeeTypes(unwrap(typesRes) ?? []);
        setFeeGroups(unwrap(groupsRes) ?? []);
      } catch { toast.error('Failed to load initial data'); }
    })();
  }, []);

  React.useEffect(() => {
    if (!yearId) return;
    (async () => {
      // Use allSettled so one failing endpoint doesn't block the others
      const [mastersRes, assignRes, collRes] = await Promise.allSettled([
        feesV2Api.listFeeMasters({ academic_year_id: yearId }),
        feesV2Api.listAssignments({ academic_year_id: yearId }),
        feesV2Api.listCollections({ academic_year_id: yearId, include_reversed: includeReversed }),
      ]);
      if (mastersRes.status === 'fulfilled') setFeeMasters(unwrap(mastersRes.value) ?? []);
      else console.error('Fee masters load failed:', mastersRes.reason);

      if (assignRes.status === 'fulfilled') setAssignments(unwrap(assignRes.value) ?? []);
      else { console.error('Assignments load failed:', assignRes.reason); toast.error('Failed to load assignments'); }

      if (collRes.status === 'fulfilled') setCollections(unwrap(collRes.value) ?? []);
      else console.error('Collections load failed:', collRes.reason);
    })();
  }, [yearId, includeReversed]);

  React.useEffect(() => {
    if (!yearId) return;
    (async () => {
      try {
        const clsRes = await classesApi.list(yearId);
        const rows = Array.isArray(unwrap(clsRes)) ? unwrap(clsRes) : unwrap(clsRes)?.items ?? [];
        setClasses(rows);
      } catch {}
    })();
  }, [yearId]);

  const reloadFeeTypes = async () => { setFeeTypes(unwrap(await feesV2Api.listFeeTypes()) ?? []); };
  const reloadGroups = async () => { setFeeGroups(unwrap(await feesV2Api.listFeeGroups()) ?? []); };
  const reloadMasters = async () => { setFeeMasters(unwrap(await feesV2Api.listFeeMasters({ academic_year_id: yearId })) ?? []); };
  const reloadAssignments = async () => { setAssignments(unwrap(await feesV2Api.listAssignments({ academic_year_id: yearId })) ?? []); };
  const reloadCollections = async () => {
    setCollections(unwrap(await feesV2Api.listCollections({ academic_year_id: yearId, include_reversed: includeReversed })) ?? []);
  };

  // ─────────────────────────────────────────────────────────
  //  TAB: FEE TYPES
  // ─────────────────────────────────────────────────────────
  const [typeModal, setTypeModal] = React.useState<null | 'create' | FeeType>(null);
  const [typeName, setTypeName] = React.useState('');
  const [typeDesc, setTypeDesc] = React.useState('');
  const [typeActive, setTypeActive] = React.useState(true);

  const openTypeModal = (t?: FeeType) => {
    if (t) { setTypeName(t.name); setTypeDesc(t.description ?? ''); setTypeActive(t.is_active); setTypeModal(t); }
    else { setTypeName(''); setTypeDesc(''); setTypeActive(true); setTypeModal('create'); }
  };

  const saveType = async () => {
    if (!typeName.trim()) return toast.error('Name is required');
    try {
      if (typeModal === 'create') {
        await feesV2Api.createFeeType({ name: typeName.trim(), description: typeDesc.trim() || undefined, is_active: typeActive });
        toast.success('Fee type created');
      } else if (typeModal) {
        await feesV2Api.updateFeeType(typeModal.id, { name: typeName.trim(), description: typeDesc.trim() || undefined, is_active: typeActive });
        toast.success('Fee type updated');
      }
      setTypeModal(null);
      await reloadFeeTypes();
    } catch { toast.error('Failed to save fee type'); }
  };

  const deleteType = async (t: FeeType) => {
    if (!confirm(`Delete "${t.name}"?`)) return;
    try { await feesV2Api.deleteFeeType(t.id); toast.success('Deleted'); await reloadFeeTypes(); }
    catch { toast.error('Delete failed — may be in use'); }
  };

  // ─────────────────────────────────────────────────────────
  //  TAB: FEE GROUPS
  // ─────────────────────────────────────────────────────────
  const [groupModal, setGroupModal] = React.useState<null | 'create' | FeeGroup>(null);
  const [groupName, setGroupName] = React.useState('');
  const [groupDesc, setGroupDesc] = React.useState('');
  const [groupActive, setGroupActive] = React.useState(true);
  const [groupTypeIds, setGroupTypeIds] = React.useState<string[]>([]);

  const openGroupModal = (g?: FeeGroup) => {
    if (g) { setGroupName(g.name); setGroupDesc(g.description ?? ''); setGroupActive(g.is_active); setGroupTypeIds(g.fee_types.map(t => t.id)); setGroupModal(g); }
    else { setGroupName(''); setGroupDesc(''); setGroupActive(true); setGroupTypeIds([]); setGroupModal('create'); }
  };

  const toggleGroupType = (id: string) =>
    setGroupTypeIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const saveGroup = async () => {
    if (!groupName.trim()) return toast.error('Name is required');
    if (groupTypeIds.length === 0) return toast.error('Select at least one fee type');
    try {
      if (groupModal === 'create') {
        await feesV2Api.createFeeGroup({ name: groupName.trim(), description: groupDesc.trim() || undefined, fee_type_ids: groupTypeIds, is_active: groupActive });
        toast.success('Fee group created');
      } else if (groupModal) {
        await feesV2Api.updateFeeGroup(groupModal.id, { name: groupName.trim(), description: groupDesc.trim() || undefined, fee_type_ids: groupTypeIds, is_active: groupActive });
        toast.success('Fee group updated');
      }
      setGroupModal(null);
      await reloadGroups();
    } catch { toast.error('Failed to save fee group'); }
  };

  const deleteGroup = async (g: FeeGroup) => {
    if (!confirm(`Delete "${g.name}"?`)) return;
    try { await feesV2Api.deleteFeeGroup(g.id); toast.success('Deleted'); await reloadGroups(); }
    catch { toast.error('Delete failed — may be in use'); }
  };

  // ─────────────────────────────────────────────────────────
  //  TAB: FEE MASTER
  // ─────────────────────────────────────────────────────────
  const [masterModal, setMasterModal] = React.useState<null | 'create' | FeeMaster>(null);
  const [masterName, setMasterName] = React.useState('');
  const [masterClassId, setMasterClassId] = React.useState('');
  const [masterYearId, setMasterYearId] = React.useState('');
  const [masterGroupId, setMasterGroupId] = React.useState('');
  const [masterAmounts, setMasterAmounts] = React.useState<Record<string, string>>({});

  const selectedGroup = feeGroups.find(g => g.id === masterGroupId);

  const openMasterModal = (m?: FeeMaster) => {
    if (m) {
      setMasterName(m.name); setMasterClassId(m.class_id); setMasterYearId(m.academic_year_id);
      setMasterGroupId(m.fee_group_id);
      const amounts: Record<string, string> = {};
      m.items.forEach(it => { amounts[it.fee_type_id] = String(it.amount); });
      setMasterAmounts(amounts);
      setMasterModal(m);
    } else {
      setMasterName(''); setMasterClassId(''); setMasterYearId(yearId); setMasterGroupId(''); setMasterAmounts({});
      setMasterModal('create');
    }
  };

  const saveMaster = async () => {
    if (!masterName.trim() || !masterClassId || !masterYearId || !masterGroupId) return toast.error('Fill all required fields');
    const grp = feeGroups.find(g => g.id === masterGroupId);
    if (!grp) return toast.error('Invalid fee group');
    const items = grp.fee_types.map(ft => ({
      fee_type_id: ft.id,
      amount: parseInt(masterAmounts[ft.id] || '0', 10),
    }));
    try {
      if (masterModal === 'create') {
        await feesV2Api.createFeeMaster({ name: masterName.trim(), class_id: masterClassId, academic_year_id: masterYearId, fee_group_id: masterGroupId, items });
        toast.success('Fee master created');
      } else if (masterModal) {
        await feesV2Api.updateFeeMaster(masterModal.id, { name: masterName.trim(), items });
        toast.success('Fee master updated');
      }
      setMasterModal(null);
      await reloadMasters();
    } catch { toast.error('Failed to save fee master'); }
  };

  const deleteMaster = async (m: FeeMaster) => {
    if (!confirm(`Delete "${m.name}"?`)) return;
    try { await feesV2Api.deleteFeeMaster(m.id); toast.success('Deleted'); await reloadMasters(); }
    catch { toast.error('Delete failed'); }
  };

  // ─────────────────────────────────────────────────────────
  //  TAB: ASSIGNMENTS
  // ─────────────────────────────────────────────────────────
  const [assignModal, setAssignModal] = React.useState(false);
  const [assignMasterId, setAssignMasterId] = React.useState('');
  const [assignStudentIds, setAssignStudentIds] = React.useState<string[]>([]);
  const [assignClassId, setAssignClassId] = React.useState('');
  const [assignSearchQuery, setAssignSearchQuery] = React.useState('');
  const [assignSearchClass, setAssignSearchClass] = React.useState('');
  const [assignSearchResults, setAssignSearchResults] = React.useState<any[]>([]);
  const [assignSearchLoading, setAssignSearchLoading] = React.useState(false);

  const searchStudentsForAssign = async () => {
    if (!assignSearchClass && assignSearchQuery.trim().length < 2) {
      toast.error('Select a class or enter at least 2 characters to search');
      return;
    }
    setAssignSearchLoading(true);
    try {
      const res = await studentsApi.listStudents({
        ...(assignSearchClass ? { class_id: assignSearchClass } : {}),
        ...(assignSearchQuery.trim() ? { search: assignSearchQuery.trim() } : {}),
        academic_year_id: yearId,
      });
      const rows = unwrap(res)?.students ?? unwrap(res)?.items ?? unwrap(res) ?? [];
      setAssignSearchResults(Array.isArray(rows) ? rows : []);
    } catch { toast.error('Search failed'); }
    finally { setAssignSearchLoading(false); }
  };

  const toggleAssignStudent = (id: string) =>
    setAssignStudentIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const doAssign = async () => {
    if (!assignMasterId || assignStudentIds.length === 0) return toast.error('Select a master and at least one student');
    try {
      const r = unwrap(await feesV2Api.assignFeeMaster({ student_ids: assignStudentIds, fee_master_id: assignMasterId, academic_year_id: yearId }));
      toast.success(r?.message ?? 'Assigned');
      setAssignModal(false); setAssignStudentIds([]);
      await reloadAssignments();
    } catch { toast.error('Assignment failed'); }
  };

  const removeAssign = async (id: string) => {
    if (!confirm('Remove this assignment?')) return;
    try { await feesV2Api.removeAssignment(id); toast.success('Removed'); await reloadAssignments(); }
    catch { toast.error('Remove failed'); }
  };

  // Filter assignments by class + name search
  const [assignTableSearch, setAssignTableSearch] = React.useState('');
  const assignMasterIds = new Set(feeMasters.filter(m => !assignClassId || m.class_id === assignClassId).map(m => m.id));
  const filteredAssignments = assignments.filter(a => {
    const byClass = !assignClassId || assignMasterIds.has(a.fee_master_id);
    const q = assignTableSearch.trim().toLowerCase();
    const bySearch = !q || a.student_name?.toLowerCase().includes(q) || a.fee_master_name?.toLowerCase().includes(q);
    return byClass && bySearch;
  });

  // ─────────────────────────────────────────────────────────
  //  TAB: COLLECTION
  // ─────────────────────────────────────────────────────────
  const [collectStudentId, setCollectStudentId] = React.useState('');
  const [ledger, setLedger] = React.useState<StudentFeeLedger | null>(null);
  const [ledgerLoading, setLedgerLoading] = React.useState(false);
  const [collectModal, setCollectModal] = React.useState(false);
  const [collectAmounts, setCollectAmounts] = React.useState<Record<string, string>>({});
  const [collectDiscounts, setCollectDiscounts] = React.useState<Record<string, string>>({});
  const [collectDiscountReasons, setCollectDiscountReasons] = React.useState<Record<string, string>>({});
  const [collectMethod, setCollectMethod] = React.useState<PaymentMethod>('cash');
  const [collectDate, setCollectDate] = React.useState(today);
  const [collectRef, setCollectRef] = React.useState('');
  const [collectRemarks, setCollectRemarks] = React.useState('');
  const [reverseReason, setReverseReason] = React.useState('');
  const [reverseId, setReverseId] = React.useState<string | null>(null);
  const [collectionClassFilter, setCollectionClassFilter] = React.useState('');
  const [collectionStudentFilter, setCollectionStudentFilter] = React.useState('');

  // Collection tab student search
  const [collSearchClass, setCollSearchClass] = React.useState('');
  const [collSearchQuery, setCollSearchQuery] = React.useState('');
  const [collSearchResults, setCollSearchResults] = React.useState<{ id: string; name: string; admission_number?: string; class_name?: string }[]>([]);
  const [collSearchLoading, setCollSearchLoading] = React.useState(false);
  const [collSearchDone, setCollSearchDone] = React.useState(false);

  const searchStudentsForCollection = async () => {
    if (!collSearchClass && collSearchQuery.trim().length < 2) {
      toast.error('Select a class or enter at least 2 characters to search');
      return;
    }
    setCollSearchLoading(true);
    setCollSearchDone(false);
    try {
      const res = await studentsApi.listStudents({
        ...(collSearchClass ? { class_id: collSearchClass } : {}),
        ...(collSearchQuery.trim() ? { search: collSearchQuery.trim() } : {}),
        academic_year_id: yearId,
      });
      const rows = unwrap(res)?.students ?? unwrap(res)?.items ?? unwrap(res) ?? [];
      const list = (Array.isArray(rows) ? rows : []).map((s: any) => ({
        id: s.id,
        name: `${s.first_name} ${s.last_name}`,
        admission_number: s.admission_number,
        class_name: s.class_name,
      }));
      setCollSearchResults(list);
      setCollSearchDone(true);
      if (list.length === 0) toast.error('No students found');
    } catch { toast.error('Search failed'); }
    finally { setCollSearchLoading(false); }
  };

  const loadLedger = async (sid: string) => {
    if (!sid || !yearId) return false;
    setLedgerLoading(true);
    try {
      const data = unwrap(await feesV2Api.getStudentLedger(sid, yearId));
      setLedger(data);
      // Pre-fill amounts with balance
      const amounts: Record<string, string> = {};
      const discounts: Record<string, string> = {};
      const reasons: Record<string, string> = {};
      (data?.entries ?? []).forEach((e: any) => {
        amounts[e.fee_type_id] = String(e.balance > 0 ? e.balance : 0);
        discounts[e.fee_type_id] = '0';
        reasons[e.fee_type_id] = '';
      });
      setCollectAmounts(amounts);
      setCollectDiscounts(discounts);
      setCollectDiscountReasons(reasons);
      return true;
    } catch { setLedger(null); toast.error('No fee assignment found for this student'); return false; }
    finally { setLedgerLoading(false); }
  };

  const openCollectModal = async (sid: string) => {
    setCollectStudentId(sid);
    const ok = await loadLedger(sid);
    if (!ok) return;
    setCollectModal(true);
    setCollectDate(today); setCollectMethod('cash'); setCollectRef(''); setCollectRemarks('');
  };

  const doCollect = async () => {
    if (!ledger) return;
    const items = ledger.entries
      .map(e => ({
        fee_type_id: e.fee_type_id,
        amount_paid: parseInt(collectAmounts[e.fee_type_id] || '0', 10),
        discount_amount: parseInt(collectDiscounts[e.fee_type_id] || '0', 10),
        discount_reason: collectDiscountReasons[e.fee_type_id] || undefined,
      }))
      .filter(i => i.amount_paid > 0 || i.discount_amount > 0);

    if (items.length === 0) return toast.error('Enter at least one amount');
    try {
      const result = unwrap(await feesV2Api.collectFee({
        student_id: collectStudentId,
        fee_master_id: ledger.fee_master_id,
        academic_year_id: yearId,
        payment_date: collectDate,
        payment_method: collectMethod,
        transaction_ref: collectRef || undefined,
        remarks: collectRemarks || undefined,
        items,
      }));
      toast.success(`Fee collected — Receipt: ${result?.receipt_number}`);
      setCollectModal(false);
      await Promise.all([reloadCollections(), loadLedger(collectStudentId)]);
    } catch { toast.error('Collection failed'); }
  };

  const doReverse = async () => {
    if (!reverseId || !reverseReason.trim()) return toast.error('Reason is required');
    try {
      await feesV2Api.reverseCollection(reverseId, reverseReason.trim());
      toast.success('Collection reversed');
      setReverseId(null); setReverseReason('');
      await reloadCollections();
    } catch { toast.error('Reversal failed'); }
  };

  // Filter collections for display
  const filteredCollections = collections.filter(c => {
    const byStudent = !collectionStudentFilter || c.student_name?.toLowerCase().includes(collectionStudentFilter.toLowerCase());
    return byStudent;
  });

  const totalCollected = filteredCollections.filter(c => !c.is_reversed).reduce((sum, c) => sum + c.total_amount, 0);
  const totalDiscount = filteredCollections.filter(c => !c.is_reversed).reduce((sum, c) => sum + c.total_discount, 0);

  // ─────────────────────────────────────────────────────────
  //  RENDER
  // ─────────────────────────────────────────────────────────
  return (
    <div className="space-y-4 p-4">
      <div className="flex items-start justify-between">
        <PageHeader
          title="Advanced Fee Management"
          subtitle="Manage fee types, groups, masters, and collections"
        />
        <a href="/admin/fees"
          className="mt-1 rounded border border-gray-300 px-3 py-1.5 text-xs hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700">
          ← Switch to Classic Mode
        </a>
      </div>

      {/* Year selector */}
      <div className="flex flex-wrap items-center gap-3">
        <select className={inp + ' w-48'} value={yearId} onChange={e => setYearId(e.target.value)}>
          {years.map(y => <option key={y.id} value={y.id}>{y.name}</option>)}
        </select>
        <span className="text-xs text-gray-500">Academic Year</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${tab === t ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}>
            {t}
          </button>
        ))}
      </div>

      {/* ══════════════════════════════════════════════
          TAB: FEE TYPES
         ══════════════════════════════════════════════ */}
      {tab === 'Fee Types' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">Define individual fee heads (School Fee, Bus Fee, Library Fee, etc.)</p>
            <button className={btn('primary')} onClick={() => openTypeModal()}>+ New Fee Type</button>
          </div>
          <Card>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs font-medium text-gray-500 dark:border-gray-700">
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Description</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {feeTypes.length === 0 && (
                  <tr><td colSpan={4} className="py-6 text-center text-gray-400 text-xs">No fee types yet. Create one to get started.</td></tr>
                )}
                {feeTypes.map(t => (
                  <tr key={t.id} className="border-b dark:border-gray-700">
                    <td className="py-2 font-medium">{t.name}</td>
                    <td className="py-2 text-gray-500">{t.description || '—'}</td>
                    <td className="py-2"><Badge active={t.is_active} /></td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <button className={btn('ghost')} onClick={() => openTypeModal(t)}>Edit</button>
                        <button className={btn('danger')} onClick={() => deleteType(t)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* ══════════════════════════════════════════════
          TAB: FEE GROUPS
         ══════════════════════════════════════════════ */}
      {tab === 'Fee Groups' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">Bundle multiple fee types into a group (e.g. "Day Scholar" = School + Bus fees)</p>
            <button className={btn('primary')} onClick={() => openGroupModal()}>+ New Fee Group</button>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {feeGroups.length === 0 && (
              <p className="col-span-3 py-6 text-center text-xs text-gray-400">No fee groups yet.</p>
            )}
            {feeGroups.map(g => (
              <Card key={g.id}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{g.name}</p>
                    {g.description && <p className="mt-0.5 text-xs text-gray-500">{g.description}</p>}
                    <Badge active={g.is_active} />
                  </div>
                  <div className="flex gap-1">
                    <button className={btn('ghost')} onClick={() => openGroupModal(g)}>Edit</button>
                    <button className={btn('danger')} onClick={() => deleteGroup(g)}>Del</button>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {g.fee_types.map(ft => (
                    <span key={ft.id} className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                      {ft.name}
                    </span>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════
          TAB: FEE MASTER
         ══════════════════════════════════════════════ */}
      {tab === 'Fee Master' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">Set per-type amounts for each class (e.g. Class 1 — School ₹15,000, Bus ₹2,000)</p>
            <button className={btn('primary')} onClick={() => openMasterModal()}>+ New Fee Master</button>
          </div>
          <Card>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs font-medium text-gray-500 dark:border-gray-700">
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Class</th>
                  <th className="pb-2">Fee Group</th>
                  <th className="pb-2">Fee Breakdown</th>
                  <th className="pb-2">Total</th>
                  <th className="pb-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {feeMasters.length === 0 && (
                  <tr><td colSpan={6} className="py-6 text-center text-xs text-gray-400">No fee masters yet.</td></tr>
                )}
                {feeMasters.map(m => (
                  <tr key={m.id} className="border-b dark:border-gray-700">
                    <td className="py-2 font-medium">{m.name}</td>
                    <td className="py-2">{m.class_name}</td>
                    <td className="py-2 text-gray-500">{m.fee_group_name}</td>
                    <td className="py-2">
                      <div className="flex flex-wrap gap-1">
                        {m.items.map(it => (
                          <span key={it.id} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs dark:bg-gray-700">
                            {it.fee_type_name}: {fmt(it.amount)}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-2 font-semibold text-green-700">
                      {fmt(m.items.reduce((s, i) => s + i.amount, 0))}
                    </td>
                    <td className="py-2">
                      <div className="flex gap-1">
                        <button className={btn('ghost')} onClick={() => openMasterModal(m)}>Edit</button>
                        <button className={btn('danger')} onClick={() => deleteMaster(m)}>Del</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* ══════════════════════════════════════════════
          TAB: ASSIGNMENTS
         ══════════════════════════════════════════════ */}
      {tab === 'Assignments' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              <select className={inp + ' w-44'} value={assignClassId}
                onChange={e => setAssignClassId(e.target.value)}>
                <option value="">— All Classes —</option>
                {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <input className={inp + ' w-52'} placeholder="Search by name or fee master..."
                value={assignTableSearch} onChange={e => setAssignTableSearch(e.target.value)} />
            </div>
            <button className={btn('primary')}
              onClick={() => { setAssignStudentIds([]); setAssignMasterId(''); setAssignSearchQuery(''); setAssignSearchClass(''); setAssignSearchResults([]); setAssignModal(true); }}>
              + Assign Fee Master
            </button>
          </div>
          <Card>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs font-medium text-gray-500 dark:border-gray-700">
                  <th className="pb-2">Student</th>
                  <th className="pb-2">Fee Master</th>
                  <th className="pb-2">Assigned On</th>
                  <th className="pb-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAssignments.length === 0 && (
                  <tr><td colSpan={4} className="py-6 text-center text-xs text-gray-400">No assignments found.</td></tr>
                )}
                {filteredAssignments.map((a: any) => (
                  <tr key={a.id} className="border-b dark:border-gray-700">
                    <td className="py-2 font-medium">{a.student_name}</td>
                    <td className="py-2">{a.fee_master_name}</td>
                    <td className="py-2 text-gray-500">{formatDate(a.created_at)}</td>
                    <td className="py-2">
                      <button className={btn('danger')} onClick={() => removeAssign(a.id)}>Remove</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* ══════════════════════════════════════════════
          TAB: COLLECTION
         ══════════════════════════════════════════════ */}
      {tab === 'Collection' && (
        <div className="space-y-4">
          {/* Summary bar */}
          <div className="flex flex-wrap gap-4">
            <div className="rounded-lg bg-green-50 px-4 py-2 dark:bg-green-900/20">
              <p className="text-xs text-green-600">Total Collected</p>
              <p className="text-lg font-bold text-green-700">{fmt(totalCollected)}</p>
            </div>
            <div className="rounded-lg bg-purple-50 px-4 py-2 dark:bg-purple-900/20">
              <p className="text-xs text-purple-600">Total Discount</p>
              <p className="text-lg font-bold text-purple-700">{fmt(totalDiscount)}</p>
            </div>
          </div>

          {/* Collect Fee — student search card */}
          <Card title="Collect Fee for Student">
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-[160px]">
                <label className="mb-1 block text-xs font-medium">Class</label>
                <select className={inp} value={collSearchClass} onChange={e => setCollSearchClass(e.target.value)}>
                  <option value="">— All Classes —</option>
                  {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="flex-[2] min-w-[200px]">
                <label className="mb-1 block text-xs font-medium">Name or Admission Number</label>
                <input className={inp} placeholder="e.g. Aryan or ADM-2024-001..."
                  value={collSearchQuery} onChange={e => setCollSearchQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && searchStudentsForCollection()} />
              </div>
              <button className={btn('primary')} onClick={searchStudentsForCollection} disabled={collSearchLoading}>
                {collSearchLoading ? 'Searching...' : '🔍 Search'}
              </button>
            </div>
            {collSearchDone && collSearchResults.length > 0 && (
              <div className="mt-3 rounded border border-gray-200 dark:border-gray-700 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Student</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Admission No</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Class</th>
                      <th className="px-3 py-2 text-xs font-medium text-gray-500"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {collSearchResults.map(s => (
                      <tr key={s.id} className="border-t dark:border-gray-700">
                        <td className="px-3 py-2 font-medium">{s.name}</td>
                        <td className="px-3 py-2 text-gray-500">{s.admission_number || '—'}</td>
                        <td className="px-3 py-2 text-gray-500">{s.class_name || '—'}</td>
                        <td className="px-3 py-2 text-right">
                          <button className={btn('primary')} onClick={() => openCollectModal(s.id)}>
                            Collect Fee
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {collSearchDone && collSearchResults.length === 0 && (
              <p className="mt-3 text-center text-xs text-yellow-600 dark:text-yellow-400">No students found. Try a different search.</p>
            )}
            {!collSearchDone && (
              <p className="mt-3 text-center text-xs text-gray-400">Search by class, name, or admission number to find a student and collect fee.</p>
            )}
          </Card>

          {/* Transaction history filters */}
          <div className="flex flex-wrap items-center gap-3">
            <select className={inp + ' w-48'} value={collectionClassFilter}
              onChange={e => setCollectionClassFilter(e.target.value)}>
              <option value="">— All Classes —</option>
              {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <input className={inp + ' w-48'} placeholder="Filter transactions by student name..."
              value={collectionStudentFilter} onChange={e => setCollectionStudentFilter(e.target.value)} />
            <label className="flex items-center gap-1 text-xs">
              <input type="checkbox" checked={includeReversed} onChange={e => setIncludeReversed(e.target.checked)} />
              Show reversed
            </label>
          </div>

          {/* Transaction table (receipt-style) */}
          <Card title="Fee Transactions">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b text-left font-medium text-gray-500 dark:border-gray-700">
                    <th className="pb-2 pr-3">Receipt No</th>
                    <th className="pb-2 pr-3">Date</th>
                    <th className="pb-2 pr-3">Student</th>
                    <th className="pb-2 pr-3">Fee Master</th>
                    <th className="pb-2 pr-3">Breakdown</th>
                    <th className="pb-2 pr-3">Amount</th>
                    <th className="pb-2 pr-3">Discount</th>
                    <th className="pb-2 pr-3">Method</th>
                    <th className="pb-2 pr-3">Collected By</th>
                    <th className="pb-2 pr-3">Status</th>
                    <th className="pb-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCollections.length === 0 && (
                    <tr><td colSpan={11} className="py-8 text-center text-gray-400">No transactions found.</td></tr>
                  )}
                  {filteredCollections.map(c => (
                    <tr key={c.id} className={`border-b dark:border-gray-700 ${c.is_reversed ? 'opacity-50 line-through' : ''}`}>
                      <td className="py-2 pr-3 font-mono font-semibold text-blue-700">{c.receipt_number}</td>
                      <td className="py-2 pr-3">{formatDate(c.payment_date)}</td>
                      <td className="py-2 pr-3 font-medium">{c.student_name}</td>
                      <td className="py-2 pr-3 text-gray-500">{c.fee_master_name}</td>
                      <td className="py-2 pr-3">
                        <div className="flex flex-wrap gap-1">
                          {c.items.map(it => (
                            <span key={it.id} className="rounded bg-gray-100 px-1 dark:bg-gray-700">
                              {it.fee_type_name}: {fmt(it.amount_paid)}{it.discount_amount > 0 ? ` (disc: ${fmt(it.discount_amount)})` : ''}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-2 pr-3 font-semibold text-green-700">{fmt(c.total_amount)}</td>
                      <td className="py-2 pr-3 text-purple-600">{c.total_discount > 0 ? fmt(c.total_discount) : '—'}</td>
                      <td className="py-2 pr-3 capitalize">{c.payment_method}</td>
                      <td className="py-2 pr-3 text-gray-500">{c.collected_by_name}</td>
                      <td className="py-2 pr-3">
                        {c.is_reversed
                          ? <span className="rounded-full bg-red-100 px-2 py-0.5 text-red-700">Reversed</span>
                          : <span className="rounded-full bg-green-100 px-2 py-0.5 text-green-700">Paid</span>}
                      </td>
                      <td className="py-2">
                        {!c.is_reversed && (
                          <button className={btn('danger')} onClick={() => { setReverseId(c.id); setReverseReason(''); }}>
                            Reverse
                          </button>
                        )}
                        {c.is_reversed && c.reversal_reason && (
                          <span className="text-gray-400 italic">{c.reversal_reason}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ═══════════ MODALS ══════════════════════════ */}

      {/* Fee Type Modal */}
      {typeModal !== null && (
        <Modal title={typeModal === 'create' ? 'New Fee Type' : 'Edit Fee Type'} onClose={() => setTypeModal(null)} size="sm">
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs font-medium">Name *</label>
              <input className={inp} value={typeName} onChange={e => setTypeName(e.target.value)} placeholder="e.g. School Fee, Bus Fee" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium">Description</label>
              <input className={inp} value={typeDesc} onChange={e => setTypeDesc(e.target.value)} />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={typeActive} onChange={e => setTypeActive(e.target.checked)} />
              Active
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button className={btn('ghost')} onClick={() => setTypeModal(null)}>Cancel</button>
              <button className={btn('primary')} onClick={saveType}>Save</button>
            </div>
          </div>
        </Modal>
      )}

      {/* Fee Group Modal */}
      {groupModal !== null && (
        <Modal title={groupModal === 'create' ? 'New Fee Group' : 'Edit Fee Group'} onClose={() => setGroupModal(null)}>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs font-medium">Name *</label>
              <input className={inp} value={groupName} onChange={e => setGroupName(e.target.value)} placeholder="e.g. Day Scholar, Boarder" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium">Description</label>
              <input className={inp} value={groupDesc} onChange={e => setGroupDesc(e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium">Fee Types * (select one or more)</label>
              <div className="rounded border border-gray-300 p-2 space-y-1 max-h-40 overflow-y-auto dark:border-gray-600">
                {feeTypes.filter(t => t.is_active).map(t => (
                  <label key={t.id} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" checked={groupTypeIds.includes(t.id)} onChange={() => toggleGroupType(t.id)} />
                    {t.name}
                  </label>
                ))}
                {feeTypes.filter(t => t.is_active).length === 0 && (
                  <p className="text-xs text-gray-400">No active fee types. Create fee types first.</p>
                )}
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={groupActive} onChange={e => setGroupActive(e.target.checked)} />
              Active
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button className={btn('ghost')} onClick={() => setGroupModal(null)}>Cancel</button>
              <button className={btn('primary')} onClick={saveGroup}>Save</button>
            </div>
          </div>
        </Modal>
      )}

      {/* Fee Master Modal */}
      {masterModal !== null && (
        <Modal title={masterModal === 'create' ? 'New Fee Master' : 'Edit Fee Master'} onClose={() => setMasterModal(null)} size="lg">
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium">Name *</label>
                <input className={inp} value={masterName} onChange={e => setMasterName(e.target.value)} placeholder="e.g. Class 1 Day Scholar Fees" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Academic Year *</label>
                <select className={inp} value={masterYearId} onChange={e => setMasterYearId(e.target.value)} disabled={masterModal !== 'create'}>
                  <option value="">— Select —</option>
                  {years.map(y => <option key={y.id} value={y.id}>{y.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Class *</label>
                <select className={inp} value={masterClassId} onChange={e => setMasterClassId(e.target.value)} disabled={masterModal !== 'create'}>
                  <option value="">— Select —</option>
                  {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Fee Group *</label>
                <select className={inp} value={masterGroupId} onChange={e => { setMasterGroupId(e.target.value); setMasterAmounts({}); }} disabled={masterModal !== 'create'}>
                  <option value="">— Select —</option>
                  {feeGroups.filter(g => g.is_active).map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                </select>
              </div>
            </div>

            {selectedGroup && (
              <div>
                <label className="mb-2 block text-xs font-semibold text-gray-600 dark:text-gray-400">
                  Fee Amounts by Type (under group: {selectedGroup.name})
                </label>
                <div className="rounded border border-gray-200 dark:border-gray-700 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Fee Type</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Amount (₹)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedGroup.fee_types.map(ft => (
                        <tr key={ft.id} className="border-t dark:border-gray-700">
                          <td className="px-3 py-2 font-medium">{ft.name}</td>
                          <td className="px-3 py-2">
                            <input type="number" min="0" className={inp + ' w-36'}
                              value={masterAmounts[ft.id] ?? '0'}
                              onChange={e => setMasterAmounts(prev => ({ ...prev, [ft.id]: e.target.value }))} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="border-t dark:border-gray-700">
                      <tr>
                        <td className="px-3 py-2 font-semibold">Total</td>
                        <td className="px-3 py-2 font-bold text-green-700">
                          {fmt(selectedGroup.fee_types.reduce((s, ft) => s + parseInt(masterAmounts[ft.id] || '0', 10), 0))}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button className={btn('ghost')} onClick={() => setMasterModal(null)}>Cancel</button>
              <button className={btn('primary')} onClick={saveMaster}>Save</button>
            </div>
          </div>
        </Modal>
      )}

      {/* Assign Modal */}
      {assignModal && (
        <Modal title="Assign Fee Master to Students" onClose={() => setAssignModal(false)} size="lg">
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs font-medium">Fee Master *</label>
              <select className={inp} value={assignMasterId} onChange={e => setAssignMasterId(e.target.value)}>
                <option value="">— Select Fee Master —</option>
                {feeMasters.filter(m => m.is_active).map(m => (
                  <option key={m.id} value={m.id}>{m.name} ({m.class_name})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-gray-600 dark:text-gray-400">Search Students</label>
              <div className="flex flex-wrap gap-2">
                <select className={inp + ' flex-1 min-w-[160px]'} value={assignSearchClass} onChange={e => setAssignSearchClass(e.target.value)}>
                  <option value="">— Filter by Class —</option>
                  {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
                <input className={inp + ' flex-1 min-w-[160px]'} placeholder="Name or admission number..."
                  value={assignSearchQuery} onChange={e => setAssignSearchQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && searchStudentsForAssign()} />
                <button className={btn('primary')} onClick={searchStudentsForAssign} disabled={assignSearchLoading}>
                  {assignSearchLoading ? 'Searching...' : 'Search'}
                </button>
              </div>
              <p className="mt-1 text-xs text-gray-400">Select a class or enter name / admission number then click Search.</p>
            </div>
            {assignSearchResults.length > 0 && (
              <div>
                <label className="mb-1 block text-xs font-medium">
                  Results ({assignSearchResults.length}) — {assignStudentIds.length} selected
                  <button className="ml-2 text-blue-600 hover:underline text-xs"
                    onClick={() => setAssignStudentIds(assignSearchResults.map((s: any) => s.id))}>
                    Select all
                  </button>
                  {assignStudentIds.length > 0 && (
                    <button className="ml-2 text-gray-400 hover:underline text-xs" onClick={() => setAssignStudentIds([])}>
                      Clear
                    </button>
                  )}
                </label>
                <div className="rounded border border-gray-300 p-2 max-h-48 overflow-y-auto dark:border-gray-600 space-y-1">
                  {assignSearchResults.map((s: any) => (
                    <label key={s.id} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input type="checkbox" checked={assignStudentIds.includes(s.id)} onChange={() => toggleAssignStudent(s.id)} />
                      <span className="font-medium">{s.first_name} {s.last_name}</span>
                      {s.admission_number && <span className="text-gray-400 text-xs">({s.admission_number})</span>}
                      {s.class_name && <span className="rounded bg-gray-100 px-1 text-xs dark:bg-gray-700">{s.class_name}</span>}
                    </label>
                  ))}
                </div>
              </div>
            )}
            {assignSearchResults.length === 0 && assignSearchLoading === false && assignSearchQuery === '' && assignSearchClass === '' && (
              <p className="rounded bg-gray-50 px-3 py-4 text-center text-xs text-gray-400 dark:bg-gray-700">
                Search for students above to select and assign.
              </p>
            )}
            {assignSearchResults.length === 0 && !assignSearchLoading && (assignSearchQuery !== '' || assignSearchClass !== '') && (
              <p className="rounded bg-yellow-50 px-3 py-3 text-center text-xs text-yellow-700 dark:bg-yellow-900/20">
                No students found. Try a different class or search term.
              </p>
            )}
            <div className="flex justify-end gap-2 pt-2 border-t dark:border-gray-700">
              <button className={btn('ghost')} onClick={() => setAssignModal(false)}>Cancel</button>
              <button className={btn('primary')} onClick={doAssign} disabled={assignStudentIds.length === 0 || !assignMasterId}>
                Assign to {assignStudentIds.length} student{assignStudentIds.length !== 1 ? 's' : ''}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Collect Fee Modal */}
      {collectModal && ledger && (
        <Modal title={`Collect Fee — ${ledger.student_name}`} onClose={() => setCollectModal(false)} size="lg">
          <div className="space-y-4">
            {/* Ledger summary */}
            <div className="rounded bg-gray-50 p-3 dark:bg-gray-700 text-sm">
              <div className="flex flex-wrap gap-4">
                <div><span className="text-gray-500">Fee Master:</span> <strong>{ledger.fee_master_name}</strong></div>
                <div><span className="text-gray-500">Total Due:</span> <strong className="text-red-600">{fmt(ledger.total_due)}</strong></div>
                <div><span className="text-gray-500">Paid So Far:</span> <strong className="text-green-600">{fmt(ledger.total_paid)}</strong></div>
                <div><span className="text-gray-500">Discount So Far:</span> <strong className="text-purple-600">{fmt(ledger.total_discount)}</strong></div>
                <div><span className="text-gray-500">Balance:</span> <strong className="text-orange-600">{fmt(ledger.total_balance)}</strong></div>
              </div>
            </div>

            {/* Per fee type amounts */}
            <div className="rounded border dark:border-gray-700 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Fee Type</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Total Due</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Paid</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Disc. Given</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Balance</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Collect (₹)</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Discount (₹)</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Disc. Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {ledger.entries.map(e => (
                    <tr key={e.fee_type_id} className="border-t dark:border-gray-700">
                      <td className="px-3 py-2 font-medium">{e.fee_type_name}</td>
                      <td className="px-3 py-2 text-right">{fmt(e.amount_due)}</td>
                      <td className="px-3 py-2 text-right text-green-600">{fmt(e.amount_paid)}</td>
                      <td className="px-3 py-2 text-right text-purple-600">{fmt(e.discount_given)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-orange-600">{fmt(e.balance)}</td>
                      <td className="px-3 py-2">
                        <input type="number" min="0" max={e.balance}
                          className={inp + ' w-28'}
                          value={collectAmounts[e.fee_type_id] ?? '0'}
                          onChange={v => setCollectAmounts(prev => ({ ...prev, [e.fee_type_id]: v.target.value }))} />
                      </td>
                      <td className="px-3 py-2">
                        <input type="number" min="0" className={inp + ' w-24'}
                          value={collectDiscounts[e.fee_type_id] ?? '0'}
                          onChange={v => setCollectDiscounts(prev => ({ ...prev, [e.fee_type_id]: v.target.value }))} />
                      </td>
                      <td className="px-3 py-2">
                        <input className={inp + ' w-32'} placeholder="Reason..." disabled={!parseInt(collectDiscounts[e.fee_type_id] || '0')}
                          value={collectDiscountReasons[e.fee_type_id] ?? ''}
                          onChange={v => setCollectDiscountReasons(prev => ({ ...prev, [e.fee_type_id]: v.target.value }))} />
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="border-t font-semibold dark:border-gray-700">
                  <tr>
                    <td className="px-3 py-2" colSpan={5}>Totals for this payment</td>
                    <td className="px-3 py-2 text-green-700">
                      {fmt(ledger.entries.reduce((s, e) => s + parseInt(collectAmounts[e.fee_type_id] || '0', 10), 0))}
                    </td>
                    <td className="px-3 py-2 text-purple-700">
                      {fmt(ledger.entries.reduce((s, e) => s + parseInt(collectDiscounts[e.fee_type_id] || '0', 10), 0))}
                    </td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Payment details */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium">Payment Date *</label>
                <input type="date" className={inp} value={collectDate} onChange={e => setCollectDate(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Payment Method *</label>
                <select className={inp} value={collectMethod} onChange={e => setCollectMethod(e.target.value as PaymentMethod)}>
                  {paymentMethods.map(m => <option key={m} value={m}>{m.toUpperCase()}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Transaction Ref / Cheque No</label>
                <input className={inp} value={collectRef} onChange={e => setCollectRef(e.target.value)} placeholder="Optional" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium">Remarks</label>
                <input className={inp} value={collectRemarks} onChange={e => setCollectRemarks(e.target.value)} placeholder="Optional" />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button className={btn('ghost')} onClick={() => setCollectModal(false)}>Cancel</button>
              <button className={btn('primary')} onClick={doCollect}>Collect Fee</button>
            </div>
          </div>
        </Modal>
      )}

      {/* Reverse Collection Modal */}
      {reverseId !== null && (
        <Modal title="Reverse Fee Collection" onClose={() => setReverseId(null)} size="sm">
          <div className="space-y-3">
            <p className="text-sm text-gray-600 dark:text-gray-400">This will mark the collection as reversed and restore the balance. Please provide a reason.</p>
            <div>
              <label className="mb-1 block text-xs font-medium">Reason *</label>
              <textarea className={inp} rows={3} value={reverseReason} onChange={e => setReverseReason(e.target.value)}
                placeholder="e.g. Duplicate entry, wrong amount, returned cheque..." />
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button className={btn('ghost')} onClick={() => setReverseId(null)}>Cancel</button>
              <button className={btn('danger')} onClick={doReverse}>Reverse Collection</button>
            </div>
          </div>
        </Modal>
      )}

      {/* Ledger loading indicator */}
      {ledgerLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="rounded-lg bg-white px-6 py-4 shadow-lg dark:bg-gray-800">Loading ledger...</div>
        </div>
      )}
    </div>
  );
};

export default AdvancedFeesPage;
