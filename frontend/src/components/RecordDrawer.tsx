import { useEffect, useState } from 'react'
import type { DNSRecord, RecordDraft, RecordType } from '../types'

interface RecordDrawerProps {
  open: boolean
  record: DNSRecord | null
  onClose: () => void
  onSubmit: (draft: RecordDraft) => Promise<void>
}

const recordTypes: RecordType[] = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA']

const emptyDraft: RecordDraft = { type: 'A', name: '@', data: '', ttl: 600, priority: null }

export default function RecordDrawer({ open, record, onClose, onSubmit }: RecordDrawerProps) {
  const [draft, setDraft] = useState<RecordDraft>(emptyDraft)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setDraft(record ? {
      type: record.type,
      name: record.name,
      data: record.data,
      ttl: record.ttl,
      priority: record.priority ?? null,
      weight: record.weight ?? null,
      port: record.port ?? null,
      service: record.service ?? null,
      protocol: record.protocol ?? null,
      flags: record.flags ?? null,
      tag: record.tag ?? null,
    } : emptyDraft)
    setError('')
  }, [record, open])

  if (!open) return null

  const update = <K extends keyof RecordDraft>(key: K, value: RecordDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }))
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!draft.name.trim() || !draft.data.trim()) {
      setError('主机记录和记录值不能为空。')
      return
    }
    setSaving(true)
    setError('')
    try {
      await onSubmit(draft)
      onClose()
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="drawer-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
        <div className="drawer-head">
          <div>
            <div className="drawer-kicker">{record ? '编辑解析记录' : '新增解析记录'}</div>
            <h3 id="drawer-title">{record ? `${record.type} · ${record.name}` : '添加 DNS 记录'}</h3>
          </div>
          <button className="close-button" type="button" onClick={onClose} aria-label="关闭">×</button>
        </div>
        <form onSubmit={submit}>
          <div className="form-grid two">
            <label>记录类型
              <select value={draft.type} onChange={(event) => update('type', event.target.value as RecordType)}>
                {recordTypes.map((type) => <option key={type}>{type}</option>)}
              </select>
            </label>
            <label>TTL（秒）
              <input type="number" min={60} value={draft.ttl} onChange={(event) => update('ttl', Number(event.target.value))} />
            </label>
          </div>
          <label>主机记录
            <input value={draft.name} onChange={(event) => update('name', event.target.value)} placeholder="例如：@" />
          </label>
          <label>记录值
            <textarea rows={3} value={draft.data} onChange={(event) => update('data', event.target.value)} placeholder="例如：3.0.3.205" />
          </label>
          {draft.type === 'MX' && (
            <label>优先级
              <input type="number" min={0} value={draft.priority ?? 10} onChange={(event) => update('priority', Number(event.target.value))} />
            </label>
          )}
          {error && <div className="form-error">{error}</div>}
          <div className="drawer-summary">
            <span>提交前预览</span>
            <strong>{draft.type} {draft.name || '—'} → {draft.data || '—'}</strong>
          </div>
          <div className="drawer-actions">
            <button className="secondary-button" type="button" onClick={onClose}>取消</button>
            <button className="primary-button" type="submit" disabled={saving}>{saving ? '保存中…' : '确认保存'}</button>
          </div>
        </form>
      </section>
    </div>
  )
}
