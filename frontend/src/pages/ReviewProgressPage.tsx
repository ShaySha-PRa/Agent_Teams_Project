import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { StatusBadge } from '../components/shared/StatusBadge';
import { connectSSE, type SSEEventHandler } from '../api/sse';
import { startReview, pauseReview, resumeReview } from '../api/documents';
import type { ApiResponse } from '../types/api';

export const ReviewProgressPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState('启动中...');
  const [agents, setAgents] = useState([
    { name: '条款提取 Agent', progress: '等待中', status: 'waiting', current: '—' },
    { name: '风控 Agent', progress: '等待中', status: 'waiting', current: '—' },
    { name: '合规 Agent', progress: '等待中', status: 'waiting', current: '—' },
    { name: '报告 Agent', progress: '等待中', status: 'waiting', current: '—' },
  ]);
  const [summary, setSummary] = useState<{ high: number; medium: number; low: number } | null>(null);
  const [threadId, setThreadId] = useState('');
  const [paused, setPaused] = useState(false);
  const [error, setError] = useState('');

  const startReviewAndListen = useCallback(async () => {
    if (!id) return;
    try {
      const res = await startReview(id) as ApiResponse<any>;
      setThreadId(res.data.thread_id || '');
    } catch (e: any) {
      setError(e.message);
      return;
    }

    const handlers: SSEEventHandler = {
      onReviewProgress: (data) => {
        setStatus('AI 审核中');
        setAgents(prev => prev.map(a => {
          if (a.name.includes('风控') && data.agent_name === 'risk_control') return { ...a, status: 'active', progress: `${data.clauses_processed}/${data.total_clauses}`, current: data.current_dimension || '' };
          if (a.name.includes('合规') && data.agent_name === 'compliance') return { ...a, status: 'active', progress: `${data.clauses_processed}/${data.total_clauses}`, current: data.current_dimension || '' };
          if (a.name.includes('条款') && data.agent_name === 'clause_extraction') return { ...a, status: 'active', progress: `${data.clauses_processed}/${data.total_clauses}`, current: '提取完成' };
          if (a.name.includes('报告') && data.agent_name === 'report') return { ...a, status: 'active', progress: '生成中', current: data.current_dimension || '' };
          return a;
        }));
      },
      onReviewComplete: (data) => {
        setStatus('审核完成');
        setSummary(data.summary);
        setAgents(prev => prev.map(a => ({ ...a, status: 'done', current: '完成' })));
        // Auto-navigate to workspace after review completes
        setTimeout(() => {
          if (id) navigate(`/review/${id}/workspace`);
        }, 2000);
      },
      onReviewFailed: (data) => setError(data.message),
      onReviewTimeout: () => setError('审核超时'),
      onInterruptReady: (_data) => {
        // HITL interrupt is ready — navigate to workspace for human review
        if (id) navigate(`/review/${id}/workspace`);
      },
    };

    const sse = connectSSE(id, handlers);
    return () => sse.close();
  }, [id]);

  useEffect(() => { startReviewAndListen(); }, [startReviewAndListen]);

  const handlePause = async () => {
    if (!id) return;
    await pauseReview(id);
    setPaused(true);
  };

  const handleResume = async () => {
    if (!id) return;
    await resumeReview(id);
    setPaused(false);
  };

  return (
    <div className="page">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 className="page-title">文档 #{id?.slice(0,8)} — AI 审核</h1>
          <StatusBadge status={status} />
        </div>
      </div>

      {error && <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, color: '#dc2626', marginBottom: 16 }}>{error}</div>}

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: 'var(--color-primary-light)', borderRadius: 8, border: '1px solid var(--color-primary)' }}>
        <span style={{ fontSize: 18 }}>🧠</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>Supervisor: 已编排 4 个 Agent，正在并行执行{threadId ? ` | Thread: ${threadId}` : ''}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {agents.map((a, i) => (
          <div key={i} className={`agent-card ${a.status}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 14, fontWeight: 700 }}>{a.name}</span>
              <span className={`badge ${a.status === 'done' ? 'badge-success' : a.status === 'active' ? 'badge-info' : 'badge-muted'}`}>
                {a.status === 'done' ? '✅' : a.status === 'active' ? '⏳' : '⏸'} {a.status === 'done' ? '完成' : a.status === 'active' ? '执行中' : '等待'}
              </span>
            </div>
            <span style={{ fontSize: 13, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{a.progress}</span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.current}</span>
          </div>
        ))}
      </div>

      {summary && (
        <div className="card card-padded" style={{ background: 'var(--color-success-bg)', border: '1px solid var(--color-success)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-success)', marginBottom: 12 }}>✅ AI 审核完成 — 风险统计摘要</h3>
          <div style={{ display: 'flex', gap: 24, marginBottom: 16 }}>
            <div className="stat-card" style={{ textAlign: 'center' }}><span style={{ fontSize: 24, fontWeight: 700, color: 'var(--risk-high)' }}>{summary.high}</span><span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>🔴 高风险</span></div>
            <div className="stat-card" style={{ textAlign: 'center' }}><span style={{ fontSize: 24, fontWeight: 700, color: 'var(--risk-medium)' }}>{summary.medium}</span><span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>🟡 中风险</span></div>
            <div className="stat-card" style={{ textAlign: 'center' }}><span style={{ fontSize: 24, fontWeight: 700, color: 'var(--risk-low)' }}>{summary.low}</span><span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>🟢 低风险</span></div>
          </div>
          <button className="btn btn-primary" onClick={() => navigate(`/review/${id}/workspace`)}>进入人工审批工作台 →</button>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {paused
          ? <button className="btn btn-primary" onClick={handleResume}>▶ 恢复审核</button>
          : <button className="btn btn-outline" onClick={handlePause} disabled={!!summary}>⏸ 暂停审核</button>
        }
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>生命周期: 已创建 → 排队 → 执行中 → ...</span>
      </div>
    </div>
  );
};
