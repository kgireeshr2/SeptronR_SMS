import React, { useEffect, useState } from 'react';
import { inventoryApi, Item, Supplier, PurchaseOrder, InventoryCategory } from '../../api/inventory';
import { toast } from 'sonner';

type Tab = 'items' | 'suppliers' | 'purchase-orders' | 'categories';

export default function InventoryPage() {
  const [tab, setTab] = useState<Tab>('items');
  const [items, setItems] = useState<Item[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [pos, setPOs] = useState<PurchaseOrder[]>([]);
  const [categories, setCategories] = useState<InventoryCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [issueForm, setIssueForm] = useState<{ itemId: string; qty: string; to: string } | null>(null);
  const [newCatName, setNewCatName] = useState('');
  const [newCatDesc, setNewCatDesc] = useState('');
  const [addingCat, setAddingCat] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      if (tab === 'items') setItems(await inventoryApi.listItems());
      else if (tab === 'suppliers') setSuppliers(await inventoryApi.listSuppliers());
      else if (tab === 'purchase-orders') setPOs(await inventoryApi.listPOs());
      else if (tab === 'categories') setCategories(await inventoryApi.listCategories());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [tab]);

  const submitItem = async (e: React.FormEvent) => {
    e.preventDefault();
    await inventoryApi.createItem({
      name: form.name,
      unit: form.unit || 'pcs',
      min_stock_level: Number(form.min_stock_level || 0),
      unit_cost: Number(form.unit_cost || 0),
    });
    setShowForm(false);
    setForm({});
    load();
  };

  const submitSupplier = async (e: React.FormEvent) => {
    e.preventDefault();
    await inventoryApi.createSupplier({ name: form.name, phone: form.phone, email: form.email });
    setShowForm(false);
    setForm({});
    load();
  };

  const submitIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!issueForm) return;
    await inventoryApi.issueStock(issueForm.itemId, {
      quantity: Number(issueForm.qty),
      issued_to: issueForm.to,
      issue_date: new Date().toISOString().slice(0, 10),
    });
    setIssueForm(null);
    load();
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'items', label: 'Items & Stock' },
    { key: 'suppliers', label: 'Suppliers' },
    { key: 'purchase-orders', label: 'Purchase Orders' },
    { key: 'categories', label: '🏷️ Categories' },
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Inventory Management</h1>
        <button onClick={() => { setShowForm(true); setForm({}); }}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          + Add {tab === 'items' ? 'Item' : tab === 'suppliers' ? 'Supplier' : 'Purchase Order'}
        </button>
      </div>

      <div className="flex space-x-1 mb-6 border-b">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium rounded-t ${tab === t.key ? 'bg-white border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'items' && items.some(i => i.is_low_stock) && (
        <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800">
          ⚠ {items.filter(i => i.is_low_stock).length} item(s) are below minimum stock level.
        </div>
      )}

      {loading ? (
        <div className="text-center py-10 text-gray-500">Loading...</div>
      ) : (
        <>
          {tab === 'items' && (
            <table className="w-full text-sm border rounded overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {['Item Name', 'Code', 'Unit', 'Current Stock', 'Min Stock', 'Unit Cost', 'Status', 'Action'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr key={item.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium">{item.name}</td>
                    <td className="px-4 py-2 text-gray-500">{item.item_code || '—'}</td>
                    <td className="px-4 py-2">{item.unit}</td>
                    <td className="px-4 py-2">
                      <span className={item.is_low_stock ? 'text-red-600 font-semibold' : ''}>{item.current_stock}</span>
                    </td>
                    <td className="px-4 py-2 text-gray-500">{item.min_stock_level}</td>
                    <td className="px-4 py-2">₹{(item.unit_cost / 100).toFixed(2)}</td>
                    <td className="px-4 py-2">
                      {item.is_low_stock
                        ? <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">Low Stock</span>
                        : <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">OK</span>}
                    </td>
                    <td className="px-4 py-2">
                      <button onClick={() => setIssueForm({ itemId: item.id, qty: '1', to: '' })}
                        className="text-blue-600 hover:underline text-xs">Issue</button>
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No items found.</td></tr>
                )}
              </tbody>
            </table>
          )}

          {tab === 'suppliers' && (
            <table className="w-full text-sm border rounded overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {['Name', 'Contact Person', 'Phone', 'Email', 'Status'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {suppliers.map(s => (
                  <tr key={s.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium">{s.name}</td>
                    <td className="px-4 py-2">{s.contact_person || '—'}</td>
                    <td className="px-4 py-2">{s.phone || '—'}</td>
                    <td className="px-4 py-2">{s.email || '—'}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {s.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
                {suppliers.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No suppliers found.</td></tr>
                )}
              </tbody>
            </table>
          )}

          {tab === 'purchase-orders' && (
            <table className="w-full text-sm border rounded overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {['PO Number', 'Order Date', 'Expected Delivery', 'Total Amount', 'Status'].map(h => (
                    <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pos.map(po => (
                  <tr key={po.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-sm">{po.po_number}</td>
                    <td className="px-4 py-2">{po.order_date}</td>
                    <td className="px-4 py-2">{po.expected_delivery_date || '—'}</td>
                    <td className="px-4 py-2">₹{(po.total_amount / 100).toFixed(2)}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs capitalize
                        ${po.status === 'received' ? 'bg-green-100 text-green-700' :
                          po.status === 'partial_received' ? 'bg-yellow-100 text-yellow-700' :
                          po.status === 'ordered' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-600'}`}>
                        {po.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
                {pos.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No purchase orders found.</td></tr>
                )}
              </tbody>
            </table>
          )}
          {tab === 'categories' && (
            <div className="space-y-4">
              <div className="bg-white rounded-lg border p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Add Category</h3>
                <div className="flex gap-2">
                  <input
                    value={newCatName}
                    onChange={e => setNewCatName(e.target.value)}
                    placeholder="Category name *"
                    className="border rounded px-3 py-2 text-sm flex-1"
                  />
                  <input
                    value={newCatDesc}
                    onChange={e => setNewCatDesc(e.target.value)}
                    placeholder="Description"
                    className="border rounded px-3 py-2 text-sm flex-1"
                  />
                  <button
                    disabled={addingCat || !newCatName.trim()}
                    onClick={async () => {
                      setAddingCat(true);
                      try {
                        await inventoryApi.createCategory({ name: newCatName.trim(), description: newCatDesc.trim() || undefined });
                        setNewCatName(''); setNewCatDesc('');
                        toast.success('Category created');
                        load();
                      } catch { toast.error('Failed to create category'); }
                      finally { setAddingCat(false); }
                    }}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {addingCat ? 'Adding…' : 'Add'}
                  </button>
                </div>
              </div>
              <table className="w-full text-sm border rounded overflow-hidden">
                <thead className="bg-gray-50">
                  <tr>
                    {['Name', 'Description', 'Status'].map(h => (
                      <th key={h} className="text-left px-4 py-2 font-medium text-gray-600">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {categories.map(c => (
                    <tr key={c.id} className="border-t hover:bg-gray-50">
                      <td className="px-4 py-2 font-medium">{c.name}</td>
                      <td className="px-4 py-2 text-gray-500">{c.description || '—'}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${c.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                          {c.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {categories.length === 0 && (
                    <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-400">No categories found.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {showForm && tab === 'items' && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Add New Item</h2>
            <form onSubmit={submitItem} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Item Name *</label>
                <input required value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
                  <input value={form.unit || ''} onChange={e => setForm({ ...form, unit: e.target.value })}
                    placeholder="pcs" className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Min Stock</label>
                  <input type="number" value={form.min_stock_level || ''}
                    onChange={e => setForm({ ...form, min_stock_level: e.target.value })}
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Unit Cost (paise)</label>
                <input type="number" value={form.unit_cost || ''}
                  onChange={e => setForm({ ...form, unit_cost: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border rounded hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                  Add Item
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showForm && tab === 'suppliers' && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Add Supplier</h2>
            <form onSubmit={submitSupplier} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Supplier Name *</label>
                <input required value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input value={form.phone || ''} onChange={e => setForm({ ...form, phone: e.target.value })}
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input type="email" value={form.email || ''} onChange={e => setForm({ ...form, email: e.target.value })}
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border rounded hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                  Add Supplier
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {issueForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm">
            <h2 className="text-lg font-semibold mb-4">Issue Stock</h2>
            <form onSubmit={submitIssue} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label>
                <input required type="number" min="1" value={issueForm.qty}
                  onChange={e => setIssueForm({ ...issueForm, qty: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Issued To</label>
                <input value={issueForm.to}
                  onChange={e => setIssueForm({ ...issueForm, to: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setIssueForm(null)}
                  className="px-4 py-2 text-sm border rounded hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                  Issue
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
