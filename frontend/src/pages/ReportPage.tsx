import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getReport, exportReport, signReport } from '../api/reports';
import { getAuditLogs } from '../api/documents';
import type { ReviewReport } from '../types/report';
import type { ApiResponse } from '../types/api';

export const ReportPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<ReviewReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [signing, setSigning] = useState(false);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const res = await getReport(id) as ApiResponse<ReviewReport>;
        setReport(res.data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleSign = async () => {
    if (!id) return;
    setSigning(true);
    try {
      await signReport(id);
      const res = await getReport(id) as ApiResponse<ReviewReport>;
      setReport(res.data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSigning(false);
    }
  };

  const handleExport = async () => {
    if (!id) return;
    const blob = await exportReport(id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <div className="page"><h1 className="page-title">加载报告中...</h1></div>;
  if (error && !report) return <div className="page"><h1 className="page-title">报告加载失败</h1><p style={{ color: 'var(--color-danger)' }}>{error}</p></div>;
  if (!report) return <div className="page"><h1 className="page-title">无报告数据</h1></div>;

  const agg = report.risk_aggregation;
  const isSigned = report.sign_status === 'SIGNED';

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">审阅报告: 文档 #{id?.slice(0,8)}</h1>
        <span className={`badge ${isSigned ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: 13, padding: '6px 14px' }}>
          {isSigned ? '📋 已签署' : '📋 待签署'}
        </span>
      </div>

      <div className="card card-padded" style={{ display: 'flex', gap: 24 }}>
        <div className="stat-card" style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: 'var(--risk-high)' }}>{agg.high_confirmed + agg.high_amended}</span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>🔴 高风险已处理</span>
        </div>
        <div className="stat-card" style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: 'var(--risk-medium)' }}>{agg.medium_auto_passed + agg.medium_reviewed}</span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>🟡 中风险已处理</span>
        </div>
        <div className="stat-card" style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: 'var(--risk-low)' }}>{agg.low_auto_passed}</span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>🟢 低风险自动通过</span>
        </div>
        <div className="stat-card" style={{ textAlign: 'center' }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: 'var(--color-primary)' }}>{agg.manual_added}</span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>✋ 手动补充</span>
        </div>
      </div>

      {report.high_risk_details && report.high_risk_details.length > 0 && (
        <div className="card card-padded">
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 10 }}>高风险条款清单</h3>
          {report.high_risk_details.map((d, i) => (
            <div key={i} className="validation-row" style={{ marginBottom: i < report.high_risk_details.length - 1 ? 8 : 0 }}>
              <span style={{ fontSize: 13, fontWeight: 600, width: 120 }}>{d.clause_type}</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)', width: 160 }}>{d.risk_category} ({(d.ai_confidence * 100).toFixed(0)}%)</span>
              <span style={{ fontSize: 12, color: 'var(--color-primary)', width: 200 }}>{d.final_decision}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-success)' }}>{d.final_status}</span>
            </div>
          ))}
        </div>
      )}

      {report.generated_at && (
        <div className="card card-padded">
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 10 }}>报告信息</h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>生成时间: {report.generated_at}</p>
          <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>签署状态: {isSigned ? `已签署 (${report.signer_name})` : '待签署'}</p>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button className="btn btn-primary" onClick={handleSign} disabled={signing || isSigned}>
          {isSigned ? '已签署' : signing ? '签署中...' : '确认签署'}
        </button>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-outline" onClick={handleExport}>导出 PDF 报告</button>
        </div>
      </div>
    </div>
  );
};
