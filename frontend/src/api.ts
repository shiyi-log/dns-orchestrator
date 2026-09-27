import type { ActivityEntry, DNSRecord, DomainSummary, RecordDraft } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
    ...options,
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail ?? `请求失败（HTTP ${response.status}）`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  listDomains: () => request<DomainSummary[]>('/domains'),
  listRecords: (domain: string) => request<DNSRecord[]>(`/domains/${encodeURIComponent(domain)}/records`),
  listActivity: () => request<ActivityEntry[]>('/activity'),
  createRecord: (domain: string, payload: RecordDraft) =>
    request<DNSRecord>(`/domains/${encodeURIComponent(domain)}/records`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateRecord: (domain: string, id: string, payload: RecordDraft) =>
    request<DNSRecord>(`/domains/${encodeURIComponent(domain)}/records/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteRecord: (domain: string, id: string) =>
    request<void>(`/domains/${encodeURIComponent(domain)}/records/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),
}
