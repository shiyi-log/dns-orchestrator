import type { AccountCreate, AccountUpdate, ActivityEntry, DNSRecord, DomainSummary, ProviderAccountSummary, ProviderMetadata, RecordDraft, Zone } from './types'

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
  listProviders: () => request<ProviderMetadata[]>('/providers'),
  listAccounts: () => request<ProviderAccountSummary[]>('/accounts'),
  createAccount: (payload: AccountCreate) => request<ProviderAccountSummary>('/accounts', { method: 'POST', body: JSON.stringify(payload) }),
  updateAccount: (id: string, payload: AccountUpdate) => request<ProviderAccountSummary>(`/accounts/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteAccount: (id: string) => request<void>(`/accounts/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  verifyAccount: (id: string) => request<ProviderAccountSummary>(`/accounts/${encodeURIComponent(id)}/verify`, { method: 'POST' }),
  setDefaultAccount: (id: string) => request<ProviderAccountSummary>(`/accounts/${encodeURIComponent(id)}/set-default`, { method: 'POST' }),
  listZones: (accountId: string) => request<Zone[]>(`/accounts/${encodeURIComponent(accountId)}/zones`),
  listAccountRecords: async (accountId: string, zone: string) => {
    const records = await request<Array<DNSRecord & { content?: string }>>(`/accounts/${encodeURIComponent(accountId)}/zones/${encodeURIComponent(zone)}/records`)
    return records.map((record) => ({ ...record, data: record.data ?? record.content ?? '' }))
  },
  createAccountRecord: (accountId: string, zone: string, payload: RecordDraft) => request<DNSRecord>(`/accounts/${encodeURIComponent(accountId)}/zones/${encodeURIComponent(zone)}/records`, { method: 'POST', body: JSON.stringify({ type: payload.type, name: payload.name, content: payload.data, ttl: payload.ttl, priority: payload.priority }) }),
  updateAccountRecord: (accountId: string, zone: string, id: string, payload: RecordDraft) => request<DNSRecord>(`/accounts/${encodeURIComponent(accountId)}/zones/${encodeURIComponent(zone)}/records/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify({ type: payload.type, name: payload.name, content: payload.data, ttl: payload.ttl, priority: payload.priority }) }),
  deleteAccountRecord: (accountId: string, zone: string, id: string) => request<void>(`/accounts/${encodeURIComponent(accountId)}/zones/${encodeURIComponent(zone)}/records/${encodeURIComponent(id)}`, { method: 'DELETE' }),
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
