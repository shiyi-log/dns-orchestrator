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

export type ProviderId = 'godaddy' | 'cloudflare' | 'aliyun' | 'tencent'

export interface ProviderMetadata {
  id: ProviderId
  name: string
  implemented: boolean
  credential_fields: string[]
}

export interface ProviderAccountSummary {
  id: string
  provider: ProviderId
  display_name: string
  status: 'unknown' | 'active' | 'error' | 'disabled'
  is_default: boolean
  zone_count: number
  last_verified_at?: string | null
  last_error?: string | null
}

export interface AccountCreate {
  provider: ProviderId
  display_name: string
  credential: Record<string, string>
}

export interface AccountUpdate {
  display_name?: string
  is_enabled?: boolean
  credential?: Record<string, string>
}

export interface Zone {
  id: string
  name: string
  status: string
  record_count: number
}
