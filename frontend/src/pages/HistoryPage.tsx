import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { StatusBadge } from '../components/shared/StatusBadge';
import { Pagination } from '../components/shared/Pagination';
import { listDocuments } from '../api/documents';
import type { DocumentListItem } from '../types/document';
import type { PaginatedResponse } from '../types/api';

const FILTERS = ['全部', '已完成', '草稿', '解析失败', '审核失败'];

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState<DocumentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [activeFilter, setActiveFilter] = useState('全部');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  const load = async (p: number) => {
    setLoading(true);
    setError('');
    try {
      const statusMap: Record<string, string | undefined> = {
        '已完成': 'COMPLETED',
        '草稿': 'DRAFT',
        '解析失败': 'FAILED',
        '审核失败': 'FAILED',
      };
      const res = await listDocuments({
        page: p,
        size: 20,
        status: activeFilter !== '全部' ? (statusMap[activeFilter] || undefined) : undefined,
      }) as PaginatedResponse<DocumentListItem>;
      setItems(res.data.items.filter(d => {
        if (activeFilter === '审核失败') return false; // Backend doesn't distinguish this yet
        if (search && !d.title.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
      }));
      setTotal(res.data.total);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(page); }, [page, activeFilter]);

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

      <div className="filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: '#fff', borderRadius: 6, border: '1px solid var(--border-color)', width: 300 }}>
          <span>🔍</span>
          <input
            placeholder="关键词搜索..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') load(page); }}
            style={{ border: 'none', outline: 'none', width: '100%', fontSize: 13 }}
          />
        </div>
        {FILTERS.map(f => (
          <button key={f} className={`filter-pill ${f === activeFilter ? 'active' : ''}`} onClick={() => { setActiveFilter(f); setPage(1); }}>{f}</button>
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
        {items.length === 0 && <div className="card-padded"><span style={{ fontSize: 13, color: 'var(--text-muted)' }}>暂无记录</span></div>}
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
