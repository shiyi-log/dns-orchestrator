export type RecordType = 'A' | 'AAAA' | 'CNAME' | 'MX' | 'TXT' | 'NS' | 'SRV' | 'CAA'
export type RecordStatus = 'active' | 'pending' | 'error'

export interface DomainSummary {
  domain: string
  status: string
  expires_at?: string | null
  auto_renew?: boolean | null
  record_count: number
}

export interface DNSRecord {
  id: string
  type: RecordType
  name: string
  data: string
  ttl: number
  priority?: number | null
  weight?: number | null
  port?: number | null
  service?: string | null
  protocol?: string | null
  flags?: number | null
  tag?: string | null
  status: RecordStatus
}

export type RecordDraft = Omit<DNSRecord, 'id' | 'status'>

export interface ActivityEntry {
  id: string
  action: 'create' | 'update' | 'delete'
  domain: string
  record_id?: string | null
  summary: string
  status: 'success' | 'error'
  created_at: string
}
