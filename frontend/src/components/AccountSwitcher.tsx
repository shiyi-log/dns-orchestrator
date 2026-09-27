import type { ProviderAccountSummary } from '../types'

interface Props {
  accounts: ProviderAccountSummary[]
  selectedAccountId: string
  onSelect: (id: string) => void
  onManage: () => void
}

export default function AccountSwitcher({ accounts, selectedAccountId, onSelect, onManage }: Props) {
  const current = accounts.find((account) => account.id === selectedAccountId)
  return (
    <div className="account-switcher">
      <div className="account-switcher-label">当前账号</div>
      <select value={selectedAccountId} onChange={(event) => onSelect(event.target.value)} aria-label="选择云服务账号">
        {accounts.map((account) => <option key={account.id} value={account.id}>{account.display_name} · {account.provider}</option>)}
      </select>
      {current && <div className={`account-switcher-status status-${current.status}`}><span />{current.status === 'active' ? '已连接' : current.status === 'error' ? '连接异常' : '待验证'} · {current.zone_count} 个 Zone</div>}
      <button className="account-manage-link" type="button" onClick={onManage}>管理账号</button>
    </div>
  )
}
