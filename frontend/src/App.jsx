import axios from 'axios';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const emptyItem = { name: '', category_id: '', quantity: 0, price: 0, sku: '', status: 'In Stock' };

// ── Toast hook ──────────────────────────────────────────────────────────────
function useToast() {
  const [toasts, setToasts] = useState([]);
  const push = useCallback((msg, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, msg, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  }, []);
  return { toasts, push };
}

// ── Status badge ────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const cls =
    status === 'In Stock' ? 'badge badge-in-stock' :
    status === 'Low Stock' ? 'badge badge-low-stock' :
    status === 'Out of Stock' ? 'badge badge-out-of-stock' :
    'badge badge-default';
  return <span className={cls}>{status}</span>;
}

// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [editingId, setEditingId] = useState(null);
  const [editingCategoryId, setEditingCategoryId] = useState(null);
  const [form, setForm] = useState(emptyItem);
  const [categoryForm, setCategoryForm] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const { toasts, push } = useToast();
  const formRef = useRef(null);

  // ── Load data ──────────────────────────────────────────────────────────────
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [itemsRes, categoriesRes] = await Promise.all([
        axios.get('/api/items', {
          params: {
            q: query || undefined,
            category_id: selectedCategory === 'all' ? undefined : Number(selectedCategory),
          },
        }),
        axios.get('/api/categories'),
      ]);
      setItems(itemsRes.data);
      setCategories(categoriesRes.data);
    } catch {
      setError('Failed to load data. Check if the backend is running.');
    } finally {
      setLoading(false);
    }
  }, [query, selectedCategory]);

  useEffect(() => { loadData(); }, [loadData]);

  // ── Stats ──────────────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    const totalUnits = items.reduce((s, i) => s + Number(i.quantity || 0), 0);
    const stockValue = items.reduce((s, i) => s + Number(i.quantity || 0) * Number(i.price || 0), 0);
    return { totalUnits, categories: categories.length, stockValue };
  }, [items, categories]);

  // ── Item CRUD ──────────────────────────────────────────────────────────────
  const resetForm = () => { setForm(emptyItem); setEditingId(null); };

  const submitItem = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        ...form,
        category_id: form.category_id ? Number(form.category_id) : null,
        quantity: Number(form.quantity),
        price: Number(form.price),
      };
      if (editingId) {
        await axios.put(`/api/items/${editingId}`, payload);
        push('Item updated successfully');
      } else {
        await axios.post('/api/items', payload);
        push('Item added successfully');
      }
      resetForm();
      await loadData();
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to save item';
      push(detail, 'error');
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setForm({
      name: item.name,
      category_id: item.category_id ? String(item.category_id) : '',
      quantity: item.quantity,
      price: item.price,
      sku: item.sku || '',
      status: item.status || 'In Stock',
    });
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const deleteItem = async (itemId, itemName) => {
    if (!window.confirm(`Delete "${itemName}"?`)) return;
    try {
      await axios.delete(`/api/items/${itemId}`);
      push('Item deleted');
      await loadData();
    } catch {
      push('Failed to delete item', 'error');
    }
  };

  // ── Category CRUD ──────────────────────────────────────────────────────────
  const submitCategory = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingCategoryId) {
        await axios.put(`/api/categories/${editingCategoryId}`, categoryForm);
        push('Category updated');
      } else {
        await axios.post('/api/categories', categoryForm);
        push('Category created');
      }
      setCategoryForm({ name: '', description: '' });
      setEditingCategoryId(null);
      await loadData();
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to save category';
      push(detail, 'error');
    } finally {
      setSaving(false);
    }
  };

  const startCategoryEdit = (cat) => {
    setEditingCategoryId(cat.id);
    setCategoryForm({ name: cat.name, description: cat.description || '' });
  };

  const deleteCategory = async (catId, catName) => {
    if (!window.confirm(`Delete category "${catName}"? Items in this category will become uncategorized.`)) return;
    try {
      await axios.delete(`/api/categories/${catId}`);
      push('Category deleted');
      await loadData();
    } catch {
      push('Failed to delete category', 'error');
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Toast notifications */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>{t.msg}</div>
        ))}
      </div>

      <main className="page">
        {/* ── Left panel: forms ── */}
        <section className="panel">
          <h1 style={{ margin: '0 0 4px 0', fontSize: '1.4rem' }}>Inventory Management</h1>
          <p style={{ margin: '0 0 16px 0', color: '#64748b', fontSize: '0.88rem' }}>
            FastAPI + Supabase + React
          </p>

          {/* Stats */}
          <div className="stats-grid">
            <article className="card stat-card">
              <strong>{stats.totalUnits}</strong>
              <span>Total units</span>
            </article>
            <article className="card stat-card">
              <strong>{stats.categories}</strong>
              <span>Categories</span>
            </article>
            <article className="card stat-card">
              <strong>${stats.stockValue.toFixed(2)}</strong>
              <span>Stock value</span>
            </article>
          </div>

          {/* Category form */}
          <div className="card section-card">
            <h2 style={{ margin: '0 0 10px 0', fontSize: '1rem' }}>
              {editingCategoryId ? 'Edit category' : 'Add category'}
            </h2>
            <form onSubmit={submitCategory} className="form-grid">
              <input
                value={categoryForm.name}
                onChange={e => setCategoryForm({ ...categoryForm, name: e.target.value })}
                placeholder="Category name"
                required
              />
              <input
                value={categoryForm.description}
                onChange={e => setCategoryForm({ ...categoryForm, description: e.target.value })}
                placeholder="Description (optional)"
              />
              <div className="button-row">
                <button type="submit" disabled={saving}>
                  {editingCategoryId ? 'Update category' : 'Create category'}
                </button>
                {editingCategoryId && (
                  <button type="button" className="secondary" onClick={() => { setEditingCategoryId(null); setCategoryForm({ name: '', description: '' }); }}>
                    Cancel
                  </button>
                )}
              </div>
            </form>

            <div className="chip-list">
              {categories.map(cat => (
                <span key={cat.id} className="chip">
                  {cat.name}
                  <button type="button" className="chip-btn" onClick={() => startCategoryEdit(cat)}>Edit</button>
                  <button type="button" className="chip-btn danger" onClick={() => deleteCategory(cat.id, cat.name)}>✕</button>
                </span>
              ))}
            </div>
          </div>

          {/* Item form */}
          <form ref={formRef} onSubmit={submitItem} className="card form-grid section-card">
            <h2 style={{ margin: '0 0 4px 0', fontSize: '1rem' }}>
              {editingId ? 'Edit item' : 'Add item'}
            </h2>
            <input
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="Item name *"
              required
            />
            <input
              value={form.sku}
              onChange={e => setForm({ ...form, sku: e.target.value })}
              placeholder="SKU (optional)"
            />
            <select value={form.category_id} onChange={e => setForm({ ...form, category_id: e.target.value })}>
              <option value="">No category</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
            <input
              type="number"
              min="0"
              value={form.quantity}
              onChange={e => setForm({ ...form, quantity: e.target.value })}
              placeholder="Quantity"
            />
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.price}
              onChange={e => setForm({ ...form, price: e.target.value })}
              placeholder="Price"
            />
            <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
              <option value="In Stock">In Stock</option>
              <option value="Low Stock">Low Stock</option>
              <option value="Out of Stock">Out of Stock</option>
            </select>
            <div className="button-row">
              <button type="submit" disabled={saving}>
                {saving ? 'Saving…' : editingId ? 'Update item' : 'Add item'}
              </button>
              {editingId && (
                <button type="button" className="secondary" onClick={resetForm}>Cancel</button>
              )}
            </div>
          </form>
        </section>

        {/* ── Right panel: items list ── */}
        <section className="panel">
          <div className="toolbar">
            <h2 style={{ margin: 0, fontSize: '1.1rem' }}>
              Inventory items
              <span style={{ marginLeft: 8, fontSize: '0.8rem', color: '#475569', fontWeight: 400 }}>
                {items.length} result{items.length !== 1 ? 's' : ''}
              </span>
            </h2>
            <div className="toolbar-row">
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search by name or SKU…"
              />
              <select value={selectedCategory} onChange={e => setSelectedCategory(e.target.value)}>
                <option value="all">All categories</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <div style={{ background: '#450a0a', border: '1px solid #7f1d1d', borderRadius: 10, padding: 14, color: '#fca5a5', marginBottom: 12 }}>
              ⚠️ {error}
            </div>
          )}

          {loading ? (
            <div className="spinner" />
          ) : items.length === 0 ? (
            <div className="empty-state">
              <svg width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 3H8a2 2 0 00-2 2v2h12V5a2 2 0 00-2-2z" />
              </svg>
              <p>No items found. Add your first item using the form.</p>
            </div>
          ) : (
            <div className="grid">
              {items.map(item => (
                <article key={item.id} className="card item-card">
                  <h3>{item.name}</h3>
                  <StatusBadge status={item.status} />
                  <p style={{ marginTop: 6 }}>SKU: {item.sku || '—'}</p>
                  <p>Category: {item.category_name || <em>Uncategorized</em>}</p>
                  <p>Qty: <strong style={{ color: '#e2e8f0' }}>{item.quantity}</strong></p>
                  <p className="item-price">${Number(item.price).toFixed(2)}</p>
                  <p style={{ color: '#64748b', fontSize: '0.78rem' }}>
                    Value: ${(Number(item.quantity) * Number(item.price)).toFixed(2)}
                  </p>
                  <div className="button-row">
                    <button type="button" className="secondary" onClick={() => startEdit(item)}>Edit</button>
                    <button type="button" className="danger" onClick={() => deleteItem(item.id, item.name)}>Delete</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </>
  );
}
