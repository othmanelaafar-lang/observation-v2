const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

function toQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return;
    }
    query.set(key, String(value));
  });
  const rendered = query.toString();
  return rendered ? `?${rendered}` : '';
}

async function request(path, params) {
  const response = await fetch(`${API_BASE_URL}${path}${toQuery(params)}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text || response.statusText}`);
  }
  return response.json();
}

export function getTalents(params) {
  return request('/talents', params);
}

export function getTalentById(id) {
  return request(`/talents/${id}`);
}

export function searchTalents(query, limit = 50) {
  return request('/search', { q: query, limit });
}

export function getStats(top = 10) {
  return request('/stats', { top });
}
