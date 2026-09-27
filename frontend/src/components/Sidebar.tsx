import type { DomainSummary } from '../types'
import type { ProviderAccountSummary } from '../types'
import AccountSwitcher from './AccountSwitcher'

interface SidebarProps {
  domains: DomainSummary[]
  selectedDomain: string
  onSelectDomain: (domain: string) => void
  accounts: ProviderAccountSummary[]
  selectedAccountId: string
  onSelectAccount: (id: string) => void
  onManageAccounts: () => void
  onShowDns: () => void
}

export default function Sidebar({ domains, selectedDomain, onSelectDomain, accounts, selectedAccountId, onSelectAccount, onManageAccounts, onShowDns }: SidebarProps) {
  const currentDomain = domains.find((domain) => domain.domain === selectedDomain)

  return (
    <aside className="sidebar">
      <div className="brand">
        go<span>daddy</span> <small>/ dns</small>
      </div>
      <AccountSwitcher accounts={accounts} selectedAccountId={selectedAccountId} onSelect={onSelectAccount} onManage={onManageAccounts} />
      <div className="nav-label">管理</div>
      <button className="nav-item" type="button"><span className="nav-icon">⌂</span><span>概览</span></button>
      <button className="nav-item" type="button"><span className="nav-icon">◇</span><span>域名</span><span className="nav-meta">{domains.length}</span></button>
      <button className="nav-item active" type="button" onClick={onShowDns}><span className="nav-icon">≋</span><span>解析记录</span></button>
      <button className="nav-item" type="button"><span className="nav-icon">◷</span><span>变更记录</span><span className="nav-meta">2</span></button>

      <div className="nav-context">
        <div className="nav-context-label">当前域名</div>
        <select
          className="nav-domain-select"
          value={selectedDomain}
          onChange={(event) => onSelectDomain(event.target.value)}
          aria-label="选择当前域名"
        >
          {domains.map((domain) => <option key={domain.domain} value={domain.domain}>{domain.domain}</option>)}
        </select>
        <div className="nav-context-status"><span />同步正常</div>
        <div className="nav-context-count">{currentDomain?.record_count ?? 0} 条解析记录</div>
      </div>

      <div className="nav-label nav-label-system">系统</div>
      <button className="nav-item" type="button"><span className="nav-icon">⚙</span><span>设置</span></button>
      <div className="sidebar-foot">GoDaddy API<br /><span>服务运行正常</span></div>
    </aside>
  )
}
