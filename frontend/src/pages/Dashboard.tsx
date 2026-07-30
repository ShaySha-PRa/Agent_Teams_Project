import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { StatusBadge } from '../components/shared/StatusBadge';
import { Pagination } from '../components/shared/Pagination';
import { getDashboardStats } from '../api/documents';
import { listDocuments } from '../api/documents';
import type { DashboardStats } from '../types/report';
import type { DocumentListItem } from '../types/document';
import type { ApiResponse, PaginatedResponse } from '../types/api';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [docs, setDocs] = useState<DocumentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const [statsRes, docsRes] = await Promise.all([
          getDashboardStats() as Promise<ApiResponse<DashboardStats>>,
          listDocuments({ page: 1, size: 20 }) as Promise<PaginatedResponse<DocumentListItem>>,
        ]);
        setStats(statsRes.data);
        setDocs(docsRes.data.items);
        setTotal(docsRes.data.total);
      } catch (e: any) {
        setError(e.message || 'Failed to load');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const loadPage = async (p: number) => {
    setPage(p);
    try {
      const res = await listDocuments({ page: p, size: 20 }) as PaginatedResponse<DocumentListItem>;
      setDocs(res.data.items);
      setTotal(res.data.total);
    } catch {}
  };

  const handleRowClick = (doc: DocumentListItem) => {
    if (doc.status === 'COMPLETED') navigate(`/review/${doc.document_id}/report`);
    else if (doc.status === 'HUMAN_REVIEW' || doc.status === 'DRAFT') navigate(`/review/${doc.document_id}/workspace`);
    else if (doc.status === 'REVIEWING') navigate(`/review/${doc.document_id}/reviewing`);
    else if (doc.status === 'PARSING') navigate(`/review/${doc.document_id}/parsing`);
    else navigate(`/review/${doc.document_id}/parsing`);
  };

  if (loading) return <div className="page"><div className="page-header"><h1>工作台</h1></div><p>加载中...</p></div>;
  if (error) return <div className="page"><div className="page-header"><h1>工作台</h1></div><p style={{ color: 'var(--color-danger)' }}>加载失败: {error}</p></div>;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">工作台</h1>
        <Link to="/review/new" className="btn btn-primary" style={{ textDecoration: 'none' }}>+ 新建审阅</Link>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        <div className="stat-card">
          <span className="stat-label">待处理审阅</span>
          <span className="stat-value">{stats?.pending_reviews ?? '--'}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">本周完成</span>
          <span className="stat-value">{stats?.completed_this_week ?? '--'}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">平均耗时</span>
          <span className="stat-value">{stats?.avg_review_time_minutes ? `${stats.avg_review_time_minutes}min` : '--'}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">AI发现风险</span>
          <span className="stat-value">{stats?.total_risks_found ?? '--'}</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        <div className="card" style={{ flex: 1 }}>
          <div className="card-padded">
            <span style={{ fontSize: 15, fontWeight: 600 }}>最近审阅</span>
            {docs.slice(0, 3).map((d, i) => (
              <div key={d.document_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <span style={{ fontSize: 13 }}>{d.title}</span>
                <StatusBadge status={d.status} />
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : ''}</span>
              </div>
            ))}
            {docs.length === 0 && <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>暂无审阅记录</p>}
          </div>
        </div>
        <Link to="/review/new" className="card" style={{ width: 280, textDecoration: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, padding: 20 }}>
          <span style={{ fontSize: 32 }}>📤</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>上传新文档</span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>支持 PDF / DOCX 格式</span>
        </Link>
      </div>

      <div className="card">
        <div className="card-padded" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)' }}>
          <span style={{ fontSize: 15, fontWeight: 600 }}>审阅任务列表</span>
        </div>
        <div className="table-header">
          <div className="table-cell" style={{ width: 280 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>文档标题</span></div>
          <div className="table-cell" style={{ width: 80 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>类型</span></div>
          <div className="table-cell" style={{ width: 100 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>状态</span></div>
          <div className="table-cell" style={{ width: 180 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>风险摘要</span></div>
          <div className="table-cell" style={{ width: 140 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>提交时间</span></div>
          <div className="table-cell" style={{ width: 80 }}><span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>操作</span></div>
        </div>
        {docs.map(d => (
          <div key={d.document_id} className="table-row" onClick={() => handleRowClick(d)} style={{ cursor: 'pointer' }}>
            <div className="table-cell" style={{ width: 280 }}><span style={{ fontSize: 13, fontWeight: 500 }}>{d.title}</span></div>
            <div className="table-cell" style={{ width: 80 }}><span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{d.document_type}</span></div>
            <div className="table-cell" style={{ width: 100 }}><StatusBadge status={d.status} /></div>
            <div className="table-cell" style={{ width: 180 }}>
              <span style={{ fontSize: 12 }}>
                {d.risk_summary ? `🔴${d.risk_summary.high} 🟡${d.risk_summary.medium} 🟢${d.risk_summary.low}` : '—'}
              </span>
            </div>
            <div className="table-cell" style={{ width: 140 }}><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : ''}</span></div>
            <div className="table-cell" style={{ width: 80 }}><span style={{ fontSize: 12, color: 'var(--color-primary)', fontWeight: 500 }}>查看</span></div>
          </div>
        ))}
        <Pagination page={page} total={total} size={20} onChange={loadPage} />
      </div>
    </div>
  );
};
