import api from './axios';

export interface InventoryCategory {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Supplier {
  id: string;
  name: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  address?: string;
  is_active: boolean;
}

export interface Store {
  id: string;
  name: string;
  description?: string;
  location?: string;
  is_active: boolean;
}

export interface Item {
  id: string;
  name: string;
  item_code?: string;
  category_id?: string;
  store_id?: string;
  unit: string;
  description?: string;
  min_stock_level: number;
  current_stock: number;
  unit_cost: number;
  is_active: boolean;
  is_low_stock: boolean;
}

export interface PurchaseOrder {
  id: string;
  supplier_id: string;
  po_number: string;
  status: string;
  order_date: string;
  expected_delivery_date?: string;
  total_amount: number;
  notes?: string;
}

export interface StockEntry {
  id: string;
  item_id: string;
  store_id?: string;
  po_id?: string;
  quantity: number;
  unit_cost: number;
  entry_date: string;
  notes?: string;
}

export interface StockIssue {
  id: string;
  item_id: string;
  issued_to?: string;
  issued_to_dept?: string;
  quantity: number;
  issue_date: string;
  purpose?: string;
}

const unwrap = (r: any) => Array.isArray(r) ? r : (r?.data ?? r);

export const inventoryApi = {
  // Categories
  listCategories: (): Promise<InventoryCategory[]> => api.get('/inventory/categories').then(unwrap),
  createCategory: (data: Partial<InventoryCategory>) => api.post('/inventory/categories', data),

  // Suppliers
  listSuppliers: (): Promise<Supplier[]> => api.get('/inventory/suppliers').then(unwrap),
  createSupplier: (data: Partial<Supplier>) => api.post('/inventory/suppliers', data),
  updateSupplier: (id: string, data: Partial<Supplier>) => api.put(`/inventory/suppliers/${id}`, data),

  // Stores
  listStores: (): Promise<Store[]> => api.get('/inventory/stores').then(unwrap),
  createStore: (data: Partial<Store>) => api.post('/inventory/stores', data),

  // Items
  listItems: (filters?: { category_id?: string; low_stock?: boolean }): Promise<Item[]> =>
    api.get('/inventory/items', { params: filters }).then(unwrap),
  getItem: (id: string) => api.get(`/inventory/items/${id}`),
  createItem: (data: Partial<Item>) => api.post('/inventory/items', data),
  updateItem: (id: string, data: Partial<Item>) => api.put(`/inventory/items/${id}`, data),
  addStockEntry: (itemId: string, data: Partial<StockEntry>) =>
    api.post(`/inventory/items/${itemId}/stock-entries`, data),
  issueStock: (itemId: string, data: Partial<StockIssue>) =>
    api.post(`/inventory/items/${itemId}/stock-issues`, data),
  getItemHistory: (itemId: string): Promise<any[]> =>
    api.get(`/inventory/items/${itemId}/history`).then(unwrap),

  // Purchase Orders
  listPOs: (): Promise<PurchaseOrder[]> => api.get('/inventory/purchase-orders').then(unwrap),
  createPO: (data: any) => api.post('/inventory/purchase-orders', data),
  updatePO: (id: string, data: any) => api.put(`/inventory/purchase-orders/${id}`, data),
};
