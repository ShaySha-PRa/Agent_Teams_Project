import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { StatusBadge } from '../components/shared/StatusBadge';
import { Pagination } from '../components/shared/Pagination';
import { listDocuments } from '../api/documents';
import type { DocumentListItem } from '../types/document';
import type { PaginatedResponse } from '../types/api';

const STATUS_FILTERS = [
  { label: '全部', value: undefined },
  { label: '已完成', value: 'COMPLETED' },
  { label: '草稿', value: 'DRAFT' },
  { label: '解析失败', value: 'FAILED_PARSE' },
  { label: '审核失败', value: 'FAILED_REVIEW' },
  { label: '已取消', value: 'CANCELLED' },
];

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState<DocumentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [activeFilter, setActiveFilter] = useState('全部');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const load = async (p: number) => {
    setLoading(true);
    setError('');
    try {
      const filterItem = STATUS_FILTERS.find(f => f.label === activeFilter);
      const statusParam = filterItem?.value;

      const res = await listDocuments({ page: p, size: 20, status: statusParam }) as PaginatedResponse<DocumentListItem>;

      // Apply client-side filters that backend doesn't support
      let filtered = res.data.items;

      // Text search (client-side for MVP)
      if (search) {
        filtered = filtered.filter(d => d.title.toLowerCase().includes(search.toLowerCase()));
      }

      // Date range filter
      if (dateFrom) {
        const from = new Date(dateFrom);
        filtered = filtered.filter(d => d.uploaded_at && new Date(d.uploaded_at) >= from);
      }
      if (dateTo) {
        const to = new Date(dateTo);
        to.setHours(23, 59, 59);
        filtered = filtered.filter(d => d.uploaded_at && new Date(d.uploaded_at) <= to);
      }

      // "审核失败" filter: show failed documents that reached review stage
      if (activeFilter === '审核失败') {
        // Backend doesn't distinguish FAILED_PARSE vs FAILED_REVIEW yet
        // In MVP, show all FAILED + CANCELLED as "审核失败"
        filtered = res.data.items.filter(d => d.status === 'FAILED' || d.status === 'CANCELLED');
      }

      setItems(filtered);
      setTotal(filtered.length > 0 ? res.data.total : 0);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(page); }, [page, activeFilter, dateFrom, dateTo]);

  const handleSearch = () => load(page);

  const handleRowClick = (doc: DocumentListItem) => {
    if (doc.status === 'COMPLETED') navigate(`/review/${doc.document_id}/report`);
    else if (doc.status === 'DRAFT' || doc.status === 'HUMAN_REVIEW') navigate(`/review/${doc.document_id}/workspace`);
    else if (doc.status === 'REVIEWING') navigate(`/review/${doc.document_id}/reviewing`);
    else navigate(`/review/${doc.document_id}/parsing`);
  };

  if (loading && items.length === 0) return <div className="page"><h1>历史审阅</h1><p>加载中...</p></div>;

  return (
    <div className="page">
      <h1 className="page-title">历史审阅</h1>

      {/* Search + Date Filter Bar */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: '#fff', borderRadius: 6, border: '1px solid var(--border-color)', width: 280 }}>
          <span>🔍</span>
          <input
            placeholder="关键词搜索..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
            style={{ border: 'none', outline: 'none', width: '100%', fontSize: 13 }}
          />
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>日期:</span>
          <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} style={{ padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 11, fontFamily: 'inherit' }} />
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>至</span>
          <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} style={{ padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 11, fontFamily: 'inherit' }} />
          {(dateFrom || dateTo) && <button className="btn btn-ghost" style={{ fontSize: 11 }} onClick={() => { setDateFrom(''); setDateTo(''); }}>清除</button>}
        </div>
      </div>

      {/* Status Filter Pills */}
      <div className="filter-bar">
        {STATUS_FILTERS.map(f => (
          <button key={f.label} className={`filter-pill ${f.label === activeFilter ? 'active' : ''}`} onClick={() => { setActiveFilter(f.label); setPage(1); }}>{f.label}</button>
        ))}
      </div>

      <div className="card">
        <div className="table-header">
          <div className="table-cell" style={{ width: 260 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>文档标题</span></div>
          <div className="table-cell" style={{ width: 70 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>类型</span></div>
          <div className="table-cell" style={{ width: 160 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>风险统计</span></div>
          <div className="table-cell" style={{ width: 120 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>时间</span></div>
          <div className="table-cell" style={{ width: 100 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>状态</span></div>
          <div className="table-cell" style={{ width: 100 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>操作</span></div>
        </div>

        {error && <div className="card-padded"><span style={{ color: 'var(--color-danger)', fontSize: 12 }}>{error}</span></div>}
        {items.length === 0 && !error && <div className="card-padded"><span style={{ fontSize: 13, color: 'var(--text-muted)' }}>暂无记录</span></div>}

        {items.map(d => (
          <div key={d.document_id} className="table-row" onClick={() => handleRowClick(d)} style={{ cursor: 'pointer' }}>
            <div className="table-cell" style={{ width: 260 }}><span style={{ fontSize: 13, fontWeight: 500 }}>{d.title}</span></div>
            <div className="table-cell" style={{ width: 70 }}><span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{d.document_type}</span></div>
            <div className="table-cell" style={{ width: 160 }}>
              <span style={{ fontSize: 12 }}>
                {d.risk_summary ? `🔴${d.risk_summary.high} 🟡${d.risk_summary.medium} 🟢${d.risk_summary.low}` : '—'}
              </span>
            </div>
            <div className="table-cell" style={{ width: 120 }}><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : ''}</span></div>
            <div className="table-cell" style={{ width: 100 }}><StatusBadge status={d.status} /></div>
            <div className="table-cell" style={{ width: 100 }}>
              <span style={{ fontSize: 12, color: 'var(--color-primary)', fontWeight: 500 }}>
                {d.status === 'COMPLETED' ? '查看报告' : d.status === 'DRAFT' || d.status === 'HUMAN_REVIEW' ? '继续审阅' : '查看'}
              </span>
            </div>
          </div>
        ))}
        <Pagination page={page} total={total} size={20} onChange={(p) => setPage(p)} />
      </div>
    </div>
  );
};
