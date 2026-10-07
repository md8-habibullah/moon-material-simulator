const BASE = import.meta.env.VITE_API_URL ?? '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

export const getModelInfo = (signal) => request('/model', { signal });

export const compare = (items, signal) =>
  request('/compare', { method: 'POST', body: JSON.stringify({ items }), signal });
