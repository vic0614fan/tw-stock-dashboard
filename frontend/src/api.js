const API_BASE = "http://localhost:8000";

async function throwForStatus(res) {
  const body = await res.json().catch(() => ({}));
  const err = new Error(body.detail || `請求失敗 (${res.status})`);
  err.status = res.status;
  throw err;
}

async function request(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) await throwForStatus(res);
  return res.json();
}

async function post(path) {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST" });
  if (!res.ok) await throwForStatus(res);
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

export function getOpinions(stockId) {
  return request(`/api/opinions?stock_id=${stockId}`);
}

export function getNews(stockId) {
  return request(`/api/news?stock_id=${stockId}`);
}

export function listInfluencers() {
  return request(`/api/influencers`);
}

export function scrapeInfluencer(influencerId) {
  return post(`/api/influencers/${influencerId}/scrape`);
}

export function fetchNews() {
  return post(`/api/news/fetch`);
}

export function getShareholding(stockId) {
  return request(`/api/shareholding/${stockId}`);
}

export function fetchShareholding() {
  return post(`/api/shareholding/fetch`);
}

export function getConsensus(windowDays = 7) {
  return request(`/api/consensus?window_days=${windowDays}`);
}

export function fetchIndustry() {
  return post(`/api/stocks/industry/fetch`);
}
