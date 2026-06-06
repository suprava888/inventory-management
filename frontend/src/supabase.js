// Supabase REST API client — no SDK needed
const SUPABASE_URL = 'https://peoltjjwevcvwinuyqqa.supabase.co';
const SUPABASE_KEY = 'sb_publishable_reksooLnuYhZelKKrXg2wg_74u-8Ly9';

const headers = {
  'apikey': SUPABASE_KEY,
  'Authorization': `Bearer ${SUPABASE_KEY}`,
  'Content-Type': 'application/json',
  'Prefer': 'return=representation',
};

async function sbFetch(path, options = {}) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || `HTTP ${res.status}`);
  }
  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

// ── Categories ────────────────────────────────────────────────────────────────
export const getCategories = () =>
  sbFetch('/categories?select=*&order=name.asc');

export const createCategory = (data) =>
  sbFetch('/categories', { method: 'POST', body: JSON.stringify(data) })
    .then(r => Array.isArray(r) ? r[0] : r);

export const updateCategory = (id, data) =>
  sbFetch(`/categories?id=eq.${id}`, { method: 'PATCH', body: JSON.stringify(data) })
    .then(r => Array.isArray(r) ? r[0] : r);

export const deleteCategory = (id) =>
  sbFetch(`/categories?id=eq.${id}`, { method: 'DELETE', headers: { 'Prefer': '' } });

// ── Items ─────────────────────────────────────────────────────────────────────
export const getItems = (q, category_id) => {
  let path = '/inventory_items?select=*,categories(name)&order=created_at.desc';
  if (q) path += `&or=(name.ilike.*${encodeURIComponent(q)}*,sku.ilike.*${encodeURIComponent(q)}*)`;
  if (category_id) path += `&category_id=eq.${category_id}`;
  return sbFetch(path);
};

export const createItem = (data) =>
  sbFetch('/inventory_items', { method: 'POST', body: JSON.stringify(data) })
    .then(r => Array.isArray(r) ? r[0] : r);

export const updateItem = (id, data) =>
  sbFetch(`/inventory_items?id=eq.${id}`, { method: 'PATCH', body: JSON.stringify(data) })
    .then(r => Array.isArray(r) ? r[0] : r);

export const deleteItem = (id) =>
  sbFetch(`/inventory_items?id=eq.${id}`, { method: 'DELETE', headers: { 'Prefer': '' } });
