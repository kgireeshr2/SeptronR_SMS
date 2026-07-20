/**
 * Vendor Inventory Page
 * Tabs: Vendors | Products | Stock | Invoices | Sales | Balance Sheet
 * Allowed: superadmin, school_admin, principal, accountant, vendor
 */
import React, { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import apiClient from '@/api/axios';

// ─── Types ────────────────────────────────────────────────────────────────────
interface Vendor { id: string; name: string; contact_person?: string; phone?: string; email?: string; gst_number?: string; bank_name?: string; bank_account?: string; bank_ifsc?: string; is_active: boolean; }
interface Product { id: string; vendor_id: string; name: string; sku?: string; category?: string; unit: string; purchase_price_rs: number; selling_price_rs: number; is_active: boolean; }
interface StockRow { product_id: string; product_name: string; vendor_name: string; sku?: string; unit: string; category?: string; qty_available: number; selling_price_rs: number; }
interface Invoice { id: string; vendor_id: string; vendor_name: string; invoice_number: string; invoice_date: string; total_amount_rs: number; paid_amount_rs: number; balance_rs: number; status: string; notes?: string; }
interface Sale { id: string; vendor_id: string; vendor_name: string; student_name: string; sale_date: string; total_amount_rs: number; payment_mode: string; notes?: string; }
interface Payment { id: string; vendor_id: string; vendor_name: string; payment_date: string; amount_rs: number; direction: string; payment_mode: string; reference?: string; notes?: string; }
interface BalanceSummary { total_purchases_rs: number; total_paid_to_vendor_rs: number; outstanding_to_vendor_rs: number; total_sales_revenue_rs: number; cost_of_goods_sold_rs: number; gross_profit_rs: number; }
interface LedgerEntry { type: string; txn_date: string; reference: string; debit_rs: number; credit_rs: number; running_balance_rs: number; }

type Tab = 'vendors' | 'products' | 'stock' | 'invoices' | 'sales' | 'balance';

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (n?: number) => `₹${(n ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const today = () => new Date().toISOString().slice(0, 10);

const api = {
  get: async (path: string) => {
    const r: any = await apiClient.get(path);
    return r;
  },
  post: async (path: string, body: any) => {
    const r: any = await apiClient.post(path, body);
    return r;
  },
  put: async (path: string, body: any) => {
    const r: any = await apiClient.put(path, body);
    return r;
  },
};

// ─── Shared: tab button ───────────────────────────────────────────────────────
const TabBtn: React.FC<{ label: string; active: boolean; onClick: () => void }> = ({ label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
      active ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
    }`}
  >
    {label}
  </button>
);

// ─── Inline form field ────────────────────────────────────────────────────────
const F: React.FC<{ label: string; children: React.ReactNode; required?: boolean }> = ({ label, children, required }) => (
  <div>
    <label className="block text-xs font-medium text-gray-700 mb-1">{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
    {children}
  </div>
);

const inp = "w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400";
const sel = "w-full border border-gray-300 rounded px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-indigo-400";

// ─── Status badge ─────────────────────────────────────────────────────────────
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colors: Record<string, string> = {
    unpaid: 'bg-red-100 text-red-700',
    partial: 'bg-yellow-100 text-yellow-700',
    paid: 'bg-green-100 text-green-700',
    cancelled: 'bg-gray-100 text-gray-500',
    to_vendor: 'bg-orange-100 text-orange-700',
    from_vendor: 'bg-green-100 text-green-700',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${colors[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status.replace('_', ' ')}
    </span>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function VendorInventoryPage() {
  const [tab, setTab] = useState<Tab>('vendors');
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selectedVendor, setSelectedVendor] = useState<string>('');
  const [loading, setLoading] = useState(false);

  // Tab data
  const [products, setProducts] = useState<Product[]>([]);
  const [stock, setStock] = useState<StockRow[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [sales, setSales] = useState<Sale[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [bsSummary, setBsSummary] = useState<BalanceSummary | null>(null);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);

  // Forms visible
  const [showVendorForm, setShowVendorForm] = useState(false);
  const [showProductForm, setShowProductForm] = useState(false);
  const [showStockForm, setShowStockForm] = useState(false);
  const [showInvoiceForm, setShowInvoiceForm] = useState(false);
  const [showSaleForm, setShowSaleForm] = useState(false);
  const [showPaymentForm, setShowPaymentForm] = useState(false);

  // Balance sheet date filter
  const [bsFrom, setBsFrom] = useState('');
  const [bsTo, setBsTo] = useState('');

  // ── Load vendors on mount ──────────────────────────────────────────────────
  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    try {
      const r = await api.get('/vendor-inventory/vendors');
      setVendors(r.data ?? []);
      if (!selectedVendor && (r.data ?? []).length > 0) {
        setSelectedVendor(r.data[0].id);
      }
    } catch (e: any) {
      toast.error('Failed to load vendors');
    }
  };

  // ── Load tab data whenever tab or selectedVendor changes ──────────────────
  const loadTab = useCallback(async () => {
    if (!selectedVendor && tab !== 'vendors') return;
    setLoading(true);
    try {
      if (tab === 'products' && selectedVendor) {
        const r = await api.get(`/vendor-inventory/vendors/${selectedVendor}/products`);
        setProducts(r.data ?? []);
      } else if (tab === 'stock') {
        const q = selectedVendor ? `?vendor_id=${selectedVendor}` : '';
        const r = await api.get(`/vendor-inventory/stock${q}`);
        setStock(r.data ?? []);
      } else if (tab === 'invoices') {
        const q = selectedVendor ? `?vendor_id=${selectedVendor}` : '';
        const r = await api.get(`/vendor-inventory/invoices${q}`);
        setInvoices(r.data ?? []);
      } else if (tab === 'sales') {
        const q = selectedVendor ? `?vendor_id=${selectedVendor}` : '';
        const [rSales, rPay] = await Promise.all([
          api.get(`/vendor-inventory/sales${q}`),
          api.get(`/vendor-inventory/payments${q}`),
        ]);
        setSales(rSales.data ?? []);
        setPayments(rPay.data ?? []);
      } else if (tab === 'balance' && selectedVendor) {
        let q = `?vendor_id=${selectedVendor}`;
        if (bsFrom) q += `&from_date=${bsFrom}`;
        if (bsTo) q += `&to_date=${bsTo}`;
        const r = await api.get(`/vendor-inventory/balance-sheet${q}`);
        setBsSummary(r.data?.summary ?? null);
        setLedger(r.data?.ledger ?? []);
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [tab, selectedVendor, bsFrom, bsTo]);

  useEffect(() => { loadTab(); }, [loadTab]);

  // ── Vendor form ──────────────────────────────────────────────────────────
  const VendorForm = () => {
    const [form, setForm] = useState<Record<string, string>>({ name: '', contact_person: '', phone: '', email: '', address: '', gst_number: '', bank_name: '', bank_account: '', bank_ifsc: '' });
    const [saving, setSaving] = useState(false);
    const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

    const submit = async () => {
      if (!form.name.trim()) { toast.error('Vendor name is required'); return; }
      setSaving(true);
      try {
        await api.post('/vendor-inventory/vendors', form);
        toast.success('Vendor created');
        setShowVendorForm(false);
        loadVendors();
      } catch (e: any) { toast.error(e?.response?.data?.detail ?? 'Failed to create vendor'); }
      finally { setSaving(false); }
    };

    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">New Vendor</h3>
        <div className="grid grid-cols-2 gap-3">
          <F label="Vendor Name" required><input className={inp} value={form.name} onChange={e => set('name', e.target.value)} placeholder="e.g. Sunrise Suppliers" /></F>
          <F label="Contact Person"><input className={inp} value={form.contact_person} onChange={e => set('contact_person', e.target.value)} /></F>
          <F label="Phone"><input className={inp} value={form.phone} onChange={e => set('phone', e.target.value)} /></F>
          <F label="Email"><input className={inp} type="email" value={form.email} onChange={e => set('email', e.target.value)} /></F>
          <F label="GST Number"><input className={inp} value={form.gst_number} onChange={e => set('gst_number', e.target.value)} /></F>
          <F label="Bank Name"><input className={inp} value={form.bank_name} onChange={e => set('bank_name', e.target.value)} /></F>
          <F label="Bank Account"><input className={inp} value={form.bank_account} onChange={e => set('bank_account', e.target.value)} /></F>
          <F label="IFSC Code"><input className={inp} value={form.bank_ifsc} onChange={e => set('bank_ifsc', e.target.value)} /></F>
          <div className="col-span-2"><F label="Address"><input className={inp} value={form.address} onChange={e => set('address', e.target.value)} /></F></div>
        </div>
        <div className="flex gap-2 mt-3">
          <button onClick={submit} disabled={saving} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50">{saving ? 'Saving…' : 'Create Vendor'}</button>
          <button onClick={() => setShowVendorForm(false)} className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">Cancel</button>
        </div>
      </div>
    );
  };

  // ── Product form ──────────────────────────────────────────────────────────
  const ProductForm = () => {
    const [form, setForm] = useState<Record<string, string>>({ name: '', sku: '', category: '', unit: 'pcs', description: '', purchase_price: '0', selling_price: '0' });
    const [saving, setSaving] = useState(false);
    const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));
    const submit = async () => {
      if (!form.name.trim() || !selectedVendor) return;
      setSaving(true);
      try {
        await api.post(`/vendor-inventory/vendors/${selectedVendor}/products`, {
          ...form,
          purchase_price: parseFloat(form.purchase_price) || 0,
          selling_price: parseFloat(form.selling_price) || 0,
        });
        toast.success('Product added');
        setShowProductForm(false);
        loadTab();
      } catch (e: any) { toast.error(e?.response?.data?.detail ?? 'Failed to add product'); }
      finally { setSaving(false); }
    };
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">New Product</h3>
        <div className="grid grid-cols-2 gap-3">
          <F label="Product Name" required><input className={inp} value={form.name} onChange={e => set('name', e.target.value)} /></F>
          <F label="SKU"><input className={inp} value={form.sku} onChange={e => set('sku', e.target.value)} /></F>
          <F label="Category"><input className={inp} value={form.category} onChange={e => set('category', e.target.value)} /></F>
          <F label="Unit"><input className={inp} value={form.unit} onChange={e => set('unit', e.target.value)} placeholder="pcs / kg / box" /></F>
          <F label="Purchase Price (₹)" required><input className={inp} type="number" value={form.purchase_price} onChange={e => set('purchase_price', e.target.value)} /></F>
          <F label="Selling Price (₹)" required><input className={inp} type="number" value={form.selling_price} onChange={e => set('selling_price', e.target.value)} /></F>
        </div>
        <div className="flex gap-2 mt-3">
          <button onClick={submit} disabled={saving} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50">{saving ? 'Saving…' : 'Add Product'}</button>
          <button onClick={() => setShowProductForm(false)} className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">Cancel</button>
        </div>
      </div>
    );
  };

  // ── Stock form ──────────────────────────────────────────────────────────
  const StockForm = () => {
    const [vendorId, setVendorId] = useState(selectedVendor || '');
    const [productId, setProductId] = useState('');
    const [qty, setQty] = useState('1');
    const [vendorProducts, setVendorProducts] = useState<Product[]>([]);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
      if (!vendorId) { setVendorProducts([]); return; }
      api.get(`/vendor-inventory/vendors/${vendorId}/products`).then(r => setVendorProducts(r.data ?? []));
    }, [vendorId]);

    const submit = async () => {
      if (!vendorId) { toast.error('Select a vendor'); return; }
      if (!productId) { toast.error('Select a product'); return; }
      if (!qty || parseInt(qty) <= 0) { toast.error('Qty must be > 0'); return; }
      setSaving(true);
      try {
        await api.post('/vendor-inventory/stock', { vendor_id: vendorId, product_id: productId, qty: parseInt(qty) });
        toast.success('Stock added successfully');
        setShowStockForm(false);
        loadTab();
      } catch (e: any) { toast.error(e?.response?.data?.detail ?? 'Failed to add stock'); }
      finally { setSaving(false); }
    };

    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Add Stock</h3>
        <div className="grid grid-cols-3 gap-3">
          <F label="Vendor" required>
            <select className={sel} value={vendorId} onChange={e => { setVendorId(e.target.value); setProductId(''); }}>
              <option value="">Select vendor…</option>
              {vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
            </select>
          </F>
          <F label="Product" required>
            <select className={sel} value={productId} onChange={e => setProductId(e.target.value)} disabled={!vendorId}>
              <option value="">Select product…</option>
              {vendorProducts.map(p => <option key={p.id} value={p.id}>{p.name} ({p.unit})</option>)}
            </select>
          </F>
          <F label="Quantity to Add" required>
            <input className={inp} type="number" min="1" value={qty} onChange={e => setQty(e.target.value)} />
          </F>
        </div>
        <div className="flex gap-2 mt-3">
          <button onClick={submit} disabled={saving} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50">{saving ? 'Saving…' : 'Add Stock'}</button>
          <button onClick={() => setShowStockForm(false)} className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">Cancel</button>
        </div>
      </div>
    );
  };

  // ── Invoice form ──────────────────────────────────────────────────────────
  const InvoiceForm = () => {
    const [invNum, setInvNum] = useState('');
    const [invDate, setInvDate] = useState(today());
    const [notes, setNotes] = useState('');
    const [items, setItems] = useState([{ product_id: '', qty: 1, unit_price: 0 }]);
    const [saving, setSaving] = useState(false);
    const [formProducts, setFormProducts] = useState<Product[]>([]);
    const addItem = () => setItems(prev => [...prev, { product_id: '', qty: 1, unit_price: 0 }]);
    const removeItem = (i: number) => setItems(prev => prev.filter((_, idx) => idx !== i));
    const setItem = (i: number, k: string, v: any) => setItems(prev => prev.map((item, idx) => idx === i ? { ...item, [k]: v } : item));

    useEffect(() => {
      if (!selectedVendor) return;
      api.get(`/vendor-inventory/vendors/${selectedVendor}/products`)
        .then(r => setFormProducts((r.data ?? []).filter((p: Product) => p.is_active)));
    }, []);

    const submit = async () => {
      if (!invNum.trim()) { toast.error('Invoice number is required'); return; }
      if (!selectedVendor) { toast.error('Select a vendor first'); return; }
      const validItems = items.filter(i => i.product_id);
      if (validItems.length === 0) { toast.error('Add at least one product item'); return; }
      setSaving(true);
      try {
        await api.post('/vendor-inventory/invoices', {
          vendor_id: selectedVendor, invoice_number: invNum, invoice_date: invDate, notes,
          items: validItems.map(i => ({ ...i, qty: parseInt(String(i.qty)), unit_price: parseFloat(String(i.unit_price)) })),
        });
        toast.success('Invoice created — stock updated');
        setShowInvoiceForm(false);
        loadTab();
      } catch (e: any) { toast.error(e?.response?.data?.detail ?? 'Failed to create invoice'); }
      finally { setSaving(false); }
    };

    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">New Vendor Invoice (Goods In)</h3>
        {!selectedVendor && <p className="text-xs text-amber-600 mb-2">⚠ Select a vendor from the dropdown above first.</p>}
        <div className="grid grid-cols-3 gap-3 mb-3">
          <F label="Invoice Number" required><input className={inp} value={invNum} onChange={e => setInvNum(e.target.value)} placeholder="e.g. INV-001" /></F>
          <F label="Invoice Date" required><input className={inp} type="date" value={invDate} onChange={e => setInvDate(e.target.value)} /></F>
          <F label="Notes"><input className={inp} value={notes} onChange={e => setNotes(e.target.value)} /></F>
        </div>
        <div className="space-y-2 mb-3">
          <p className="text-xs font-medium text-gray-600">Items</p>
          {items.map((item, i) => (
            <div key={i} className="flex gap-2 items-end">
              <div className="flex-1">
                <select className={sel} value={item.product_id} onChange={e => {
                  const p = formProducts.find(pr => pr.id === e.target.value);
                  setItem(i, 'product_id', e.target.value);
                  if (p) setItem(i, 'unit_price', p.purchase_price_rs);
                }}>
                  <option value="">Select product</option>
                  {formProducts.map(p => <option key={p.id} value={p.id}>{p.name} ({p.unit})</option>)}
                </select>
              </div>
              <div className="w-20"><input className={inp} type="number" min="1" placeholder="Qty" value={item.qty} onChange={e => setItem(i, 'qty', e.target.value)} /></div>
              <div className="w-28"><input className={inp} type="number" step="0.01" placeholder="Price ₹" value={item.unit_price} onChange={e => setItem(i, 'unit_price', e.target.value)} /></div>
              <button onClick={() => removeItem(i)} className="text-red-400 hover:text-red-600 text-sm px-2">✕</button>
            </div>
          ))}
          <button onClick={addItem} className="text-xs text-indigo-600 hover:text-indigo-800">+ Add item</button>
        </div>
        <div className="flex gap-2">
          <button onClick={submit} disabled={saving || !selectedVendor} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50">{saving ? 'Saving…' : 'Create Invoice'}</button>
          <button onClick={() => setShowInvoiceForm(false)} className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">Cancel</button>
        </div>
      </div>
    );
  };

  // ── Sale form ─────────────────────────────────────────────────────────────
  const SaleForm = () => {
    const [saleDate, setSaleDate] = useState(today());
    const [payMode, setPayMode] = useState('cash');
    const [notes, setNotes] = useState('');
    const [items, setItems] = useState([{ product_id: '', qty: 1, unit_price: 0 }]);
    const [saving, setSaving] = useState(false);
    const [formStock, setFormStock] = useState<StockRow[]>([]);
    const addItem = () => setItems(prev => [...prev, { product_id: '', qty: 1, unit_price: 0 }]);
    const removeItem = (i: number) => setItems(prev => prev.filter((_, idx) => idx !== i));
    const setItem = (i: number, k: string, v: any) => setItems(prev => prev.map((item, idx) => idx === i ? { ...item, [k]: v } : item));
    const total = items.reduce((s, i) => s + (parseFloat(String(i.unit_price)) || 0) * (parseInt(String(i.qty)) || 1), 0);

    useEffect(() => {
      const q = selectedVendor ? `?vendor_id=${selectedVendor}` : '';
      api.get(`/vendor-inventory/stock${q}`).then(r => setFormStock(r.data ?? []));
    }, []);

    const submit = async () => {
      if (!selectedVendor) return;
      setSaving(true);
      try {
        await api.post('/vendor-inventory/sales', {
          vendor_id: selectedVendor, sale_date: saleDate, payment_mode: payMode, notes,
          student_id: null,
          items: items.filter(i => i.product_id).map(i => ({ ...i, qty: parseInt(String(i.qty)), unit_price: parseFloat(String(i.unit_price)) })),
        });
        toast.success('Sale recorded — stock updated');
        setShowSaleForm(false);
        loadTab();
      } catch (e: any) { toast.error(e?.response?.data?.detail ?? 'Failed to record sale'); }
      finally { setSaving(false); }
    };

    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">New Sale (Goods Out)</h3>
        <div className="grid grid-cols-3 gap-3 mb-3">
          <F label="Sale Date" required><input className={inp} type="date" value={saleDate} onChange={e => setSaleDate(e.target.value)} /></F>
          <F label="Payment Mode">
            <select className={sel} value={payMode} onChange={e => setPayMode(e.target.value)}>
              {['cash', 'upi', 'card', 'bank_transfer', 'other'].map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </F>
          <F label="Notes"><input className={inp} value={notes} onChange={e => setNotes(e.target.value)} /></F>
        </div>
        <div className="space-y-2 mb-3">
          <p className="text-xs font-medium text-gray-600">Items</p>
          {items.map((item, i) => (
            <div key={i} className="flex gap-2 items-end">
              <div className="flex-1">
                <select className={sel} value={item.product_id} onChange={e => {
                  const p = formStock.find(s => s.product_id === e.target.value);
                  setItem(i, 'product_id', e.target.value);
                  if (p) setItem(i, 'unit_price', p.selling_price_rs);
                }}>
                  <option value="">Select product</option>
                  {formStock.map(s => (
                    <option key={s.product_id} value={s.product_id}>{s.product_name} (qty: {s.qty_available})</option>
                  ))}
                </select>
              </div>
              <div className="w-20"><input className={inp} type="number" min="1" placeholder="Qty" value={item.qty} onChange={e => setItem(i, 'qty', e.target.value)} /></div>
              <div className="w-28"><input className={inp} type="number" step="0.01" placeholder="Price ₹" value={item.unit_price} onChange={e => setItem(i, 'unit_price', e.target.value)} /></div>
              <button onClick={() => removeItem(i)} className="text-red-400 hover:text-red-600 text-sm px-2">✕</button>
            </div>
          ))}
          <button onClick={addItem} className="text-xs text-indigo-600 hover:text-indigo-800">+ Add item</button>
        </div>
        <p className="text-sm font-semibold text-gray-700 mb-2">Total: {fmt(total)}</p>
        <div className="flex gap-2">
          <button onClick={submit} disabled={saving} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50">{saving ? 'Saving…' : 'Record Sale'}</button>
          <button onClick={() => setShowSaleForm(false)} className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">Cancel</button>
        </div>
      </div>
    );
  };

  // ── Payment form ──────────────────────────────────────────────────────────
  const PaymentForm = () => {
    const [form, setForm] = useState({ payment_date: today(), amount: '', direction: 'to_vendor', payment_mode: 'bank_transfer', reference: '', notes: '' });
    const [saving, setSaving] = useState(false);
    const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));
    const submit = async () => {
      if (!selectedVendor || !form.amount) return;
      setSaving(true);
      try {
        await api.post('/vendor-inventory/payments', { ...form, vendor_id: selectedVendor, amount: parseFloat(form.amount) });
        toast.success('Payment recorded');
        setShowPaymentForm(false);
        loadTab();
      } catch (e: any) { toast.error(e?.response?.data?.detail ?? 'Failed'); }
      finally { setSaving(false); }
    };
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Record Payment</h3>
        <div className="grid grid-cols-3 gap-3">
          <F label="Date"><input className={inp} type="date" value={form.payment_date} onChange={e => set('payment_date', e.target.value)} /></F>
          <F label="Amount (₹)" required><input className={inp} type="number" step="0.01" value={form.amount} onChange={e => set('amount', e.target.value)} /></F>
          <F label="Direction">
            <select className={sel} value={form.direction} onChange={e => set('direction', e.target.value)}>
              <option value="to_vendor">To Vendor (we pay)</option>
              <option value="from_vendor">From Vendor (refund)</option>
            </select>
          </F>
          <F label="Payment Mode">
            <select className={sel} value={form.payment_mode} onChange={e => set('payment_mode', e.target.value)}>
              {['bank_transfer', 'cash', 'cheque', 'upi', 'other'].map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </F>
          <F label="Reference"><input className={inp} value={form.reference} onChange={e => set('reference', e.target.value)} /></F>
          <F label="Notes"><input className={inp} value={form.notes} onChange={e => set('notes', e.target.value)} /></F>
        </div>
        <div className="flex gap-2 mt-3">
          <button onClick={submit} disabled={saving} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50">{saving ? 'Saving…' : 'Record Payment'}</button>
          <button onClick={() => setShowPaymentForm(false)} className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">Cancel</button>
        </div>
      </div>
    );
  };

  // ── Vendor selector ───────────────────────────────────────────────────────
  const VendorSelector = () => (
    <div className="flex items-center gap-3 mb-4 bg-white border border-gray-200 rounded-lg px-4 py-2">
      <span className="text-sm text-gray-500 whitespace-nowrap">Active Vendor:</span>
      <select className={`${sel} max-w-xs`} value={selectedVendor} onChange={e => setSelectedVendor(e.target.value)}>
        <option value="">— select vendor —</option>
        {vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
      </select>
    </div>
  );

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="p-4 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Vendor Inventory</h1>
          <p className="text-xs text-gray-500 mt-0.5">Third-party vendor products, stock, and balance sheet</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-4 gap-1">
        {(['vendors', 'products', 'stock', 'invoices', 'sales', 'balance'] as Tab[]).map(t => (
          <TabBtn key={t} label={t === 'balance' ? 'Balance Sheet' : t.charAt(0).toUpperCase() + t.slice(1)} active={tab === t} onClick={() => setTab(t)} />
        ))}
      </div>

      {/* ── VENDORS TAB ── */}
      {tab === 'vendors' && (
        <div>
          <div className="flex justify-between items-center mb-3">
            <p className="text-sm text-gray-600">Vendors registered for your school.</p>
            <button onClick={() => setShowVendorForm(f => !f)} className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700">+ New Vendor</button>
          </div>
          {showVendorForm && <VendorForm />}
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead className="bg-gray-50">
                <tr>{['Name', 'Contact', 'Phone', 'Email', 'GST', 'Bank', 'Status'].map(h => <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-gray-500 border-b">{h}</th>)}</tr>
              </thead>
              <tbody>
                {vendors.length === 0 && <tr><td colSpan={7} className="text-center py-8 text-gray-400 text-sm">No vendors yet. Create one to get started.</td></tr>}
                {vendors.map(v => (
                  <tr key={v.id} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedVendor(v.id)}>
                    <td className="px-3 py-2 font-medium text-indigo-700">{v.name}</td>
                    <td className="px-3 py-2 text-gray-600">{v.contact_person ?? '—'}</td>
                    <td className="px-3 py-2">{v.phone ?? '—'}</td>
                    <td className="px-3 py-2">{v.email ?? '—'}</td>
                    <td className="px-3 py-2">{v.gst_number ?? '—'}</td>
                    <td className="px-3 py-2 text-xs text-gray-500">{v.bank_name ? `${v.bank_name} • ${v.bank_ifsc ?? ''}` : '—'}</td>
                    <td className="px-3 py-2"><StatusBadge status={v.is_active ? 'paid' : 'cancelled'} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── PRODUCTS TAB ── */}
      {tab === 'products' && (
        <div>
          <VendorSelector />
          <div className="flex justify-between items-center mb-3">
            <p className="text-sm text-gray-600">Product catalog for <strong>{vendors.find(v => v.id === selectedVendor)?.name ?? '…'}</strong></p>
            <button onClick={() => setShowProductForm(f => !f)} className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700">+ Add Product</button>
          </div>
          {showProductForm && <ProductForm />}
          <table className="w-full text-sm border-collapse">
            <thead className="bg-gray-50">
              <tr>{['Name', 'SKU', 'Category', 'Unit', 'Purchase ₹', 'Selling ₹', 'Status'].map(h => <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-gray-500 border-b">{h}</th>)}</tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={7} className="text-center py-6 text-gray-400">Loading…</td></tr>}
              {!loading && products.length === 0 && <tr><td colSpan={7} className="text-center py-6 text-gray-400">No products for this vendor.</td></tr>}
              {products.map(p => (
                <tr key={p.id} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2 font-medium">{p.name}</td>
                  <td className="px-3 py-2 text-gray-500">{p.sku ?? '—'}</td>
                  <td className="px-3 py-2">{p.category ?? '—'}</td>
                  <td className="px-3 py-2">{p.unit}</td>
                  <td className="px-3 py-2">{fmt(p.purchase_price_rs)}</td>
                  <td className="px-3 py-2 font-semibold text-indigo-700">{fmt(p.selling_price_rs)}</td>
                  <td className="px-3 py-2"><span className={`px-2 py-0.5 text-xs rounded-full ${p.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>{p.is_active ? 'Active' : 'Inactive'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── STOCK TAB ── */}
      {tab === 'stock' && (
        <div>
          <div className="flex justify-between items-center mb-3">
            <VendorSelector />
            <button onClick={() => setShowStockForm(f => !f)} className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700">+ Add Stock</button>
          </div>
          {showStockForm && <StockForm />}
          <table className="w-full text-sm border-collapse">
            <thead className="bg-gray-50">
              <tr>{['Product', 'Vendor', 'Category', 'Unit', 'Available', 'Selling Price'].map(h => <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-gray-500 border-b">{h}</th>)}</tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={6} className="text-center py-6 text-gray-400">Loading…</td></tr>}
              {!loading && stock.length === 0 && <tr><td colSpan={6} className="text-center py-6 text-gray-400">No stock data. Create invoices to add stock.</td></tr>}
              {stock.map((s, i) => (
                <tr key={i} className={`border-b hover:bg-gray-50 ${s.qty_available === 0 ? 'bg-red-50' : s.qty_available < 5 ? 'bg-yellow-50' : ''}`}>
                  <td className="px-3 py-2 font-medium">{s.product_name}</td>
                  <td className="px-3 py-2 text-gray-500">{s.vendor_name}</td>
                  <td className="px-3 py-2">{s.category ?? '—'}</td>
                  <td className="px-3 py-2">{s.unit}</td>
                  <td className="px-3 py-2">
                    <span className={`font-semibold ${s.qty_available === 0 ? 'text-red-600' : s.qty_available < 5 ? 'text-yellow-600' : 'text-green-700'}`}>
                      {s.qty_available}
                    </span>
                  </td>
                  <td className="px-3 py-2">{fmt(s.selling_price_rs)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── INVOICES TAB ── */}
      {tab === 'invoices' && (
        <div>
          <VendorSelector />
          <div className="flex justify-between items-center mb-3">
            <p className="text-sm text-gray-600">Goods-in invoices from vendor (increases stock)</p>
            <button onClick={() => setShowInvoiceForm(f => !f)} className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700">+ New Invoice</button>
          </div>
          {showInvoiceForm && <InvoiceForm />}
          <table className="w-full text-sm border-collapse">
            <thead className="bg-gray-50">
              <tr>{['Invoice #', 'Vendor', 'Date', 'Total', 'Paid', 'Balance', 'Status'].map(h => <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-gray-500 border-b">{h}</th>)}</tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={7} className="text-center py-6 text-gray-400">Loading…</td></tr>}
              {!loading && invoices.length === 0 && <tr><td colSpan={7} className="text-center py-6 text-gray-400">No invoices yet.</td></tr>}
              {invoices.map(inv => (
                <tr key={inv.id} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2 font-medium text-indigo-700">{inv.invoice_number}</td>
                  <td className="px-3 py-2">{inv.vendor_name}</td>
                  <td className="px-3 py-2 text-gray-500">{inv.invoice_date}</td>
                  <td className="px-3 py-2">{fmt(inv.total_amount_rs)}</td>
                  <td className="px-3 py-2 text-green-700">{fmt(inv.paid_amount_rs)}</td>
                  <td className="px-3 py-2 font-semibold text-red-600">{fmt(inv.balance_rs)}</td>
                  <td className="px-3 py-2"><StatusBadge status={inv.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── SALES TAB ── */}
      {tab === 'sales' && (
        <div>
          <VendorSelector />
          <div className="flex justify-between items-center mb-3">
            <p className="text-sm text-gray-600">Sales to students (decreases stock)</p>
            <div className="flex gap-2">
              <button onClick={() => { setShowPaymentForm(f => !f); setShowSaleForm(false); }} className="px-3 py-1.5 text-xs bg-white border border-indigo-300 text-indigo-600 rounded hover:bg-indigo-50">+ Payment</button>
              <button onClick={() => { setShowSaleForm(f => !f); setShowPaymentForm(false); }} className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700">+ New Sale</button>
            </div>
          </div>
          {showSaleForm && <SaleForm />}
          {showPaymentForm && <PaymentForm />}
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-4 mb-1">Sales (Goods Out to Students)</p>
          <table className="w-full text-sm border-collapse mb-6">
            <thead className="bg-gray-50">
              <tr>{['Date', 'Vendor', 'Student', 'Amount', 'Payment Mode'].map(h => <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-gray-500 border-b">{h}</th>)}</tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={5} className="text-center py-6 text-gray-400">Loading…</td></tr>}
              {!loading && sales.length === 0 && <tr><td colSpan={5} className="text-center py-6 text-gray-400">No sales yet.</td></tr>}
              {sales.map(s => (
                <tr key={s.id} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2">{s.sale_date}</td>
                  <td className="px-3 py-2">{s.vendor_name}</td>
                  <td className="px-3 py-2 text-indigo-700">{s.student_name}</td>
                  <td className="px-3 py-2 font-semibold">{fmt(s.total_amount_rs)}</td>
                  <td className="px-3 py-2 capitalize">{s.payment_mode}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Payments to / from Vendor</p>
          <table className="w-full text-sm border-collapse">
            <thead className="bg-gray-50">
              <tr>{['Date', 'Vendor', 'Direction', 'Amount', 'Mode', 'Reference'].map(h => <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-gray-500 border-b">{h}</th>)}</tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={6} className="text-center py-6 text-gray-400">Loading…</td></tr>}
              {!loading && payments.length === 0 && <tr><td colSpan={6} className="text-center py-6 text-gray-400">No payments recorded yet.</td></tr>}
              {payments.map(p => (
                <tr key={p.id} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2">{p.payment_date}</td>
                  <td className="px-3 py-2">{p.vendor_name}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${p.direction === 'to_vendor' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                      {p.direction === 'to_vendor' ? 'Paid to vendor' : 'Received from vendor'}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-semibold">{fmt(p.amount_rs)}</td>
                  <td className="px-3 py-2 capitalize">{p.payment_mode.replace('_', ' ')}</td>
                  <td className="px-3 py-2 text-gray-500">{p.reference ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── BALANCE SHEET TAB ── */}
      {tab === 'balance' && (
        <div>
          <VendorSelector />
          {/* Date filter */}
          <div className="flex gap-3 items-end mb-4 bg-white border border-gray-200 rounded-lg px-4 py-3">
            <F label="From Date"><input className={inp} type="date" value={bsFrom} onChange={e => setBsFrom(e.target.value)} /></F>
            <F label="To Date"><input className={inp} type="date" value={bsTo} onChange={e => setBsTo(e.target.value)} /></F>
            <button onClick={loadTab} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700">Apply</button>
            <button onClick={() => { setBsFrom(''); setBsTo(''); }} className="px-4 py-1.5 bg-gray-100 text-gray-600 text-sm rounded hover:bg-gray-200">Clear</button>
          </div>

          {/* Summary cards */}
          {bsSummary && (
            <div className="grid grid-cols-3 gap-3 mb-5">
              {[
                { label: 'Total Purchases', value: fmt(bsSummary.total_purchases_rs), color: 'text-gray-700' },
                { label: 'Total Paid to Vendor', value: fmt(bsSummary.total_paid_to_vendor_rs), color: 'text-green-700' },
                { label: 'Outstanding to Vendor', value: fmt(bsSummary.outstanding_to_vendor_rs), color: 'text-red-600' },
                { label: 'Total Sales Revenue', value: fmt(bsSummary.total_sales_revenue_rs), color: 'text-indigo-700' },
                { label: 'Cost of Goods Sold', value: fmt(bsSummary.cost_of_goods_sold_rs), color: 'text-gray-700' },
                { label: 'Gross Profit', value: fmt(bsSummary.gross_profit_rs), color: bsSummary.gross_profit_rs >= 0 ? 'text-emerald-700' : 'text-red-600' },
              ].map(c => (
                <div key={c.label} className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <p className="text-xs text-gray-500 mb-1">{c.label}</p>
                  <p className={`text-lg font-bold ${c.color}`}>{c.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Ledger */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead className="bg-gray-50">
                <tr>{['Date', 'Type', 'Reference', 'Debit (↑ owe vendor)', 'Credit (↓ owe vendor)', 'Running Balance'].map(h => <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-gray-500 border-b">{h}</th>)}</tr>
              </thead>
              <tbody>
                {loading && <tr><td colSpan={6} className="text-center py-6 text-gray-400">Loading…</td></tr>}
                {!loading && ledger.length === 0 && <tr><td colSpan={6} className="text-center py-6 text-gray-400">No transactions for this period.</td></tr>}
                {ledger.map((e, i) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-500">{String(e.txn_date).slice(0, 10)}</td>
                    <td className="px-3 py-2"><span className="capitalize text-xs bg-gray-100 px-2 py-0.5 rounded">{e.type}</span></td>
                    <td className="px-3 py-2 text-xs font-mono text-gray-600">{String(e.reference).slice(0, 30)}</td>
                    <td className="px-3 py-2 text-red-600">{e.debit_rs > 0 ? fmt(e.debit_rs) : '—'}</td>
                    <td className="px-3 py-2 text-green-700">{e.credit_rs > 0 ? fmt(e.credit_rs) : '—'}</td>
                    <td className={`px-3 py-2 font-semibold ${e.running_balance_rs > 0 ? 'text-red-600' : 'text-green-700'}`}>{fmt(e.running_balance_rs)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
