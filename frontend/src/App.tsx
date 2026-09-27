import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import Sidebar from './components/Sidebar'
import RecordDrawer from './components/RecordDrawer'
import RecordTable from './components/RecordTable'
import AccountDrawer from './components/AccountDrawer'
import AccountTable from './components/AccountTable'
import type { DNSRecord, DomainSummary, ProviderAccountSummary, ProviderMetadata, RecordDraft, Zone } from './types'

export default function App() {
  const [domains, setDomains] = useState<DomainSummary[]>([])
  const [selectedDomain, setSelectedDomain] = useState('')
  const [records, setRecords] = useState<DNSRecord[]>([])
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<DNSRecord | null>(null)
  const [accounts, setAccounts] = useState<ProviderAccountSummary[]>([])
  const [providers, setProviders] = useState<ProviderMetadata[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState('')
  const [zones, setZones] = useState<Zone[]>([])
  const [selectedZone, setSelectedZone] = useState('')
  const [accountDrawerOpen, setAccountDrawerOpen] = useState(false)
  const [accountView, setAccountView] = useState(false)

  const loadDomains = async () => {
    const result = await api.listDomains()
    setDomains(result)
    if (!selectedDomain && result[0]) setSelectedDomain(result[0].domain)
    return result
  }

  const loadAccounts = async () => {
    const [accountResult, providerResult] = await Promise.all([api.listAccounts(), api.listProviders()])
    setAccounts(accountResult)
    setProviders(providerResult)
    const next = accountResult.find((account) => account.is_default) ?? accountResult[0]
    if (!selectedAccountId && next) setSelectedAccountId(next.id)
    return accountResult
  }

  const loadAccountZones = async (accountId: string) => {
    if (!accountId) return
    const result = await api.listZones(accountId)
    setZones(result)
    setDomains(result.map((zone) => ({ domain: zone.name, status: zone.status, record_count: zone.record_count })))
    if (!selectedZone && result[0]) {
      setSelectedZone(result[0].name)
      setSelectedDomain(result[0].name)
    }
    return result
  }

  const loadRecords = async (domain = selectedDomain) => {
    if (!domain) return
    setLoading(true)
    setError('')
    try {
      setRecords(await api.listRecords(domain))
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : '读取解析记录失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAccounts()
      .then((result) => {
        const next = result.find((account) => account.is_default) ?? result[0]
        if (next) return loadAccountZones(next.id).then(() => undefined)
        return loadDomains().then((domains) => { if (domains[0]) return loadRecords(domains[0].domain) })
      })
      .catch((loadError) => setError(loadError instanceof Error ? loadError.message : '读取域名失败'))
  }, [])

  useEffect(() => {
    if (selectedAccountId) {
      setSelectedZone('')
      setZones([])
      setRecords([])
      loadAccountZones(selectedAccountId).catch((loadError) => setError(loadError instanceof Error ? loadError.message : '读取 Zone 失败'))
    }
  }, [selectedAccountId])

  useEffect(() => {
    if (selectedAccountId && selectedZone) {
      setLoading(true)
      api.listAccountRecords(selectedAccountId, selectedZone).then(setRecords).catch((loadError) => setError(loadError instanceof Error ? loadError.message : '读取解析记录失败')).finally(() => setLoading(false))
    }
  }, [selectedAccountId, selectedZone])

  useEffect(() => {
    if (selectedDomain) loadRecords(selectedDomain)
  }, [selectedDomain])

  const filteredRecords = useMemo(() => records.filter((record) => {
    const matchesSearch = `${record.name} ${record.data}`.toLowerCase().includes(search.toLowerCase())
    return matchesSearch && (typeFilter === 'ALL' || record.type === typeFilter)
  }), [records, search, typeFilter])

  const openCreate = () => {
    setEditingRecord(null)
    setDrawerOpen(true)
  }

  const saveRecord = async (draft: RecordDraft) => {
    if (selectedAccountId && selectedZone) {
      if (editingRecord) await api.updateAccountRecord(selectedAccountId, selectedZone, editingRecord.id, draft)
      else await api.createAccountRecord(selectedAccountId, selectedZone, draft)
      setNotice(editingRecord ? '解析记录已更新' : '解析记录已新增')
      const refreshed = await api.listAccountRecords(selectedAccountId, selectedZone)
      setRecords(refreshed)
    } else if (editingRecord) {
      await api.updateRecord(selectedDomain, editingRecord.id, draft)
      setNotice('解析记录已更新')
    } else {
      await api.createRecord(selectedDomain, draft)
      setNotice('解析记录已新增')
    }
    await Promise.all([loadRecords(selectedDomain), loadDomains()])
    window.setTimeout(() => setNotice(''), 2600)
  }

  const deleteRecord = async (record: DNSRecord) => {
    if (!window.confirm(`确定删除 ${record.type} ${record.name} → ${record.data} 吗？`)) return
    try {
      if (selectedAccountId && selectedZone) await api.deleteAccountRecord(selectedAccountId, selectedZone, record.id)
      else await api.deleteRecord(selectedDomain, record.id)
      setNotice('解析记录已删除')
      await Promise.all([loadRecords(selectedDomain), loadDomains()])
      window.setTimeout(() => setNotice(''), 2600)
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : '删除失败')
    }
  }

  const selectedSummary = domains.find((domain) => domain.domain === selectedDomain)

  const refreshAccounts = async () => {
    const result = await api.listAccounts()
    setAccounts(result)
    if (!selectedAccountId && result[0]) setSelectedAccountId(result[0].id)
  }

  const createAccount = async (payload: Parameters<typeof api.createAccount>[0]) => {
    await api.createAccount(payload)
    await refreshAccounts()
    setNotice('账号已验证并保存')
    window.setTimeout(() => setNotice(''), 2600)
  }

  const verifyAccount = async (account: ProviderAccountSummary) => { setAccounts((items) => items); const updated = await api.verifyAccount(account.id); setAccounts((items) => items.map((item) => item.id === updated.id ? updated : item)) }
  const setDefaultAccount = async (account: ProviderAccountSummary) => { const updated = await api.setDefaultAccount(account.id); setAccounts((items) => items.map((item) => ({ ...item, is_default: item.id === updated.id }))); setSelectedAccountId(updated.id) }
  const deleteAccount = async (account: ProviderAccountSummary) => { if (!window.confirm(`确定删除本地账号“${account.display_name}”吗？不会删除云端 DNS 数据。`)) return; await api.deleteAccount(account.id); const result = await api.listAccounts(); setAccounts(result); if (selectedAccountId === account.id) setSelectedAccountId(result[0]?.id ?? '') }

  return (
    <div className="app-shell">
      <Sidebar domains={domains} selectedDomain={selectedDomain} onSelectDomain={setSelectedDomain} accounts={accounts} selectedAccountId={selectedAccountId} onSelectAccount={setSelectedAccountId} onManageAccounts={() => setAccountView(true)} onShowDns={() => setAccountView(false)} />
      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs"><span>解析记录</span><span>/</span><strong>DNS 管理</strong></div>
          <div className="account"><span>演示账户</span><span className="avatar">S</span></div>
        </header>

        {accountView ? <section className="page-heading"><div><h1>账号管理</h1><p>管理 GoDaddy 连接，并为未来的多云 DNS 适配器预留统一入口。</p></div><button className="primary-button" type="button" onClick={() => setAccountDrawerOpen(true)}>＋ 添加账号</button></section> : <section className="page-heading">
          <div><h1>DNS 解析</h1><p>集中管理域名的 A、CNAME、MX、TXT 和其他解析记录。</p></div>
          <button className="primary-button" type="button" onClick={openCreate}>＋ 新增记录</button>
        </section>}

        {accountView ? <section className="records-card account-view-card"><AccountTable accounts={accounts} providers={providers} onVerify={verifyAccount} onSetDefault={setDefaultAccount} onDelete={deleteAccount} /></section> : null}

        {!accountView && <section className="stats-grid">
          <div className="stat-card"><span>已连接域名</span><strong>{domains.length}</strong></div>
          <div className="stat-card"><span>解析记录</span><strong>{records.length}</strong></div>
          <div className="stat-card"><span>同步状态</span><strong className="green">正常</strong></div>
          <div className="stat-card"><span>最近同步</span><strong>刚刚</strong></div>
        </section>}

        {!accountView && <section className="records-card">
          <div className="toolbar">
            <div className="toolbar-left">
              <select className="domain-select" value={selectedDomain} onChange={(event) => setSelectedDomain(event.target.value)} aria-label="选择域名">
                {domains.map((domain) => <option key={domain.domain}>{domain.domain}</option>)}
              </select>
              <input className="search-input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="⌕  搜索主机记录或值" />
              <select className="filter-select" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} aria-label="筛选记录类型">
                <option value="ALL">类型：全部</option>
                <option value="A">A</option><option value="AAAA">AAAA</option><option value="CNAME">CNAME</option>
                <option value="MX">MX</option><option value="TXT">TXT</option><option value="NS">NS</option>
              </select>
            </div>
            <div className="toolbar-right"><span className="sync-pill"><span />已同步</span><button className="icon-button" type="button" onClick={() => loadRecords()}>↻</button></div>
          </div>
          {error && <div className="alert error">{error}</div>}
          {notice && <div className="alert success">{notice}</div>}
          {loading ? <div className="loading">正在读取 {selectedDomain || '域名'} 的解析记录…</div> : <RecordTable records={filteredRecords} onEdit={(record) => { setEditingRecord(record); setDrawerOpen(true) }} onDelete={deleteRecord} />}
          <div className="table-footer"><span>显示 <strong>{filteredRecords.length}</strong> / 共 {records.length} 条记录</span><span>数据来自 {selectedSummary?.domain ?? 'GoDaddy'}</span></div>
        </section>}
      </main>
      <RecordDrawer open={drawerOpen} record={editingRecord} onClose={() => setDrawerOpen(false)} onSubmit={saveRecord} />
      <AccountDrawer open={accountDrawerOpen} providers={providers} onClose={() => setAccountDrawerOpen(false)} onSubmit={createAccount} />
    </div>
  )
}
