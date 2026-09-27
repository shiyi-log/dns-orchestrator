import type { ProviderAccountSummary, ProviderMetadata } from '../types'

interface Props {
  accounts: ProviderAccountSummary[]
  providers: ProviderMetadata[]
  onVerify: (account: ProviderAccountSummary) => void
  onSetDefault: (account: ProviderAccountSummary) => void
  onDelete: (account: ProviderAccountSummary) => void
}

export default function AccountTable({ accounts, providers, onVerify, onSetDefault, onDelete }: Props) {
  const providerName = (id: string) => providers.find((provider) => provider.id === id)?.name ?? id
  return (
    <div className="account-table-shell">
      <table>
        <thead><tr><th>账号名称</th><th>提供商</th><th>状态</th><th>Zone</th><th>默认</th><th>最近验证</th><th>操作</th></tr></thead>
        <tbody>
          {accounts.map((account) => (
            <tr key={account.id}>
              <td className="host">{account.display_name}</td>
              <td>{providerName(account.provider)}</td>
              <td><span className={`status status-${account.status}`}><span className="status-dot" />{account.status === 'active' ? '已连接' : account.status === 'error' ? '异常' : '待验证'}</span></td>
              <td>{account.zone_count}</td>
              <td>{account.is_default ? <span className="default-mark">默认</span> : <button className="text-button" type="button" onClick={() => onSetDefault(account)}>设为默认</button>}</td>
              <td>{account.last_verified_at ? new Date(account.last_verified_at).toLocaleString() : '未验证'}</td>
              <td><div className="actions"><button className="text-button" type="button" onClick={() => onVerify(account)}>验证</button><button className="text-button danger-text" type="button" onClick={() => onDelete(account)}>删除</button></div></td>
            </tr>
          ))}
          {accounts.length === 0 && <tr><td className="empty-cell" colSpan={7}>还没有连接账号。</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
