const BASE = '/api'

async function request(url, options = {}) {
  const res = await fetch(BASE + url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      detail = await res.text().catch(() => '')
    }
    throw new Error(detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  listContracts: () => request('/contracts'),
  createContract: (data) =>
    request('/contracts', { method: 'POST', body: JSON.stringify(data) }),
  getContract: (id) => request(`/contracts/${id}`),
  autoRun: () => request('/contract-deduction/auto-run', { method: 'POST' }),
  listDeductions: () => request('/deductions'),
  listRates: () => request('/exchange-rates'),
  todayRate: (currency) =>
    request(`/exchange-rates/today?currency=${currency}`),
  listOffsets: () => request('/exchange-offsets'),
  summary: () => request('/exchange-offsets/summary'),
}
