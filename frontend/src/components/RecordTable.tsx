import type { DNSRecord, RecordType } from '../types'

interface RecordTableProps {
  records: DNSRecord[]
  onEdit: (record: DNSRecord) => void
  onDelete: (record: DNSRecord) => void
}

export default function RecordTable({ records, onEdit, onDelete }: RecordTableProps) {
  return (
    <div className="table-shell">
      <table>
        <thead>
          <tr>
            <th>类型</th>
            <th>主机记录</th>
            <th>记录值</th>
            <th>TTL</th>
            <th>状态</th>
            <th className="actions-heading">操作</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id}>
              <td><span className={`record-type type-${record.type.toLowerCase() as Lowercase<RecordType>}`}>{record.type}</span></td>
              <td className="host">{record.name}</td>
              <td className="value" title={record.data}>{record.data}</td>
              <td>{record.ttl} 秒</td>
              <td>
                <span className={`status status-${record.status}`}>
                  <span className="status-dot" />
                  {record.status === 'pending' ? '同步中' : record.status === 'error' ? '异常' : '生效中'}
                </span>
              </td>
              <td>
                <div className="actions">
                  <button className="icon-button" type="button" onClick={() => onEdit(record)} aria-label={`编辑 ${record.name}`}>✎</button>
                  <button className="icon-button danger-hover" type="button" onClick={() => onDelete(record)} aria-label={`删除 ${record.name}`}>⌫</button>
                </div>
              </td>
            </tr>
          ))}
          {records.length === 0 && (
            <tr><td className="empty-cell" colSpan={6}>没有符合筛选条件的解析记录。</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
