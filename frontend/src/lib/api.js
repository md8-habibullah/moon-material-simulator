// Optional live backend (local development). The hosted site works without it.
const BASE = import.meta.env.VITE_API_URL ?? `${import.meta.env.BASE_URL}api`.replace(/\/{2,}/g, '/');

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, { headers: { Accept: 'application/json' }, ...options });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

export async function apiAvailable(signal) {
  try {
    const health = await request('/health', { signal });
    return health.status === 'ok';
  } catch {
    return false;
  }
}

export const searchNtrs = (q, signal) => request(`/research?q=${encodeURIComponent(q)}`, { signal });
