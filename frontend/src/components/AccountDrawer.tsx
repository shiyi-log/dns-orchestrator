import { useEffect, useState } from 'react'
import type { AccountCreate, ProviderMetadata } from '../types'

interface Props {
  open: boolean
  providers: ProviderMetadata[]
  onClose: () => void
  onSubmit: (payload: AccountCreate) => Promise<void>
}

export default function AccountDrawer({ open, providers, onClose, onSubmit }: Props) {
  const [provider, setProvider] = useState<'godaddy' | 'cloudflare' | 'aliyun' | 'tencent'>('godaddy')
  const [displayName, setDisplayName] = useState('')
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  useEffect(() => { if (open) { setDisplayName(''); setToken(''); setError('') } }, [open])
  if (!open) return null
  const selectedProvider = providers.find((item) => item.id === provider)
  const supported = selectedProvider?.implemented === true
  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!displayName.trim() || !token.trim()) { setError('账号名称和 PAT 不能为空。'); return }
    setSaving(true); setError('')
    try { await onSubmit({ provider, display_name: displayName.trim(), credential: { token } }); onClose() }
    catch (submitError) { setError(submitError instanceof Error ? submitError.message : '保存账号失败') }
    finally { setSaving(false) }
  }
  return <div className="drawer-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section className="drawer" role="dialog" aria-modal="true" aria-labelledby="account-drawer-title">
      <div className="drawer-head"><div><div className="drawer-kicker">账号管理</div><h3 id="account-drawer-title">添加云服务账号</h3></div><button className="close-button" type="button" onClick={onClose} aria-label="关闭">×</button></div>
      <form onSubmit={submit}>
        <label>提供商<select value={provider} onChange={(event) => setProvider(event.target.value as typeof provider)}>{providers.map((item) => <option key={item.id} value={item.id}>{item.name}{item.implemented ? '' : '（即将支持）'}</option>)}</select></label>
        <label>账号名称<input value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="例如：生产 GoDaddy" /></label>
        <label>PAT<input type="password" value={token} onChange={(event) => setToken(event.target.value)} placeholder="只保存在后端加密存储" /></label>
        {!supported && <div className="form-error">该提供商将在后续阶段支持，当前不会提交凭证。</div>}
        {error && <div className="form-error">{error}</div>}
        <div className="drawer-summary"><span>安全提示</span><strong>PAT 只发送到 Django 后端，不会返回浏览器。</strong></div>
        <div className="drawer-actions"><button className="secondary-button" type="button" onClick={onClose}>取消</button><button className="primary-button" type="submit" disabled={saving || !supported}>{saving ? '验证中…' : '验证并保存'}</button></div>
      </form>
    </section>
  </div>
}
