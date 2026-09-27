import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import Sidebar from './components/Sidebar'
import RecordDrawer from './components/RecordDrawer'
import RecordTable from './components/RecordTable'
import type { DNSRecord, DomainSummary, RecordDraft } from './types'

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

  const loadDomains = async () => {
    const result = await api.listDomains()
    setDomains(result)
    if (!selectedDomain && result[0]) setSelectedDomain(result[0].domain)
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
    loadDomains()
      .then((result) => result[0] && loadRecords(result[0].domain))
      .catch((loadError) => setError(loadError instanceof Error ? loadError.message : '读取域名失败'))
  }, [])

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
    if (editingRecord) {
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
      await api.deleteRecord(selectedDomain, record.id)
      setNotice('解析记录已删除')
      await Promise.all([loadRecords(selectedDomain), loadDomains()])
      window.setTimeout(() => setNotice(''), 2600)
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : '删除失败')
    }
  }

  const selectedSummary = domains.find((domain) => domain.domain === selectedDomain)

  return (
    <div className="app-shell">
      <Sidebar domains={domains} selectedDomain={selectedDomain} onSelectDomain={setSelectedDomain} />
      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs"><span>解析记录</span><span>/</span><strong>DNS 管理</strong></div>
          <div className="account"><span>演示账户</span><span className="avatar">S</span></div>
        </header>

        <section className="page-heading">
          <div><h1>DNS 解析</h1><p>集中管理域名的 A、CNAME、MX、TXT 和其他解析记录。</p></div>
          <button className="primary-button" type="button" onClick={openCreate}>＋ 新增记录</button>
        </section>

        <section className="stats-grid">
          <div className="stat-card"><span>已连接域名</span><strong>{domains.length}</strong></div>
          <div className="stat-card"><span>解析记录</span><strong>{records.length}</strong></div>
          <div className="stat-card"><span>同步状态</span><strong className="green">正常</strong></div>
          <div className="stat-card"><span>最近同步</span><strong>刚刚</strong></div>
        </section>

        <section className="records-card">
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
        </section>
      </main>
      <RecordDrawer open={drawerOpen} record={editingRecord} onClose={() => setDrawerOpen(false)} onSubmit={saveRecord} />
    </div>
  )
}
