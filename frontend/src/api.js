const API_BASE = "http://localhost:8000";

async function request(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `請求失敗 (${res.status})`);
  }
  return res.json();
}

async function post(path) {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `請求失敗 (${res.status})`);
  }
  return res.json();
}

export function getInstitutionalFlow(stockId) {
  return request(`/api/institutional-flow/${stockId}`);
}

export function getChipData(stockId) {
  return request(`/api/chip-data/${stockId}`);
}

export function fetchInstitutionalFlow(tradeDate) {
  return post(`/api/institutional-flow/fetch?trade_date=${tradeDate}`);
}

export function fetchChipData(tradeDate) {
  return post(`/api/chip-data/fetch?trade_date=${tradeDate}`);
}
