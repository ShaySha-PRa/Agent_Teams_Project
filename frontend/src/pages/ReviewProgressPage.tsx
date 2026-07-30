import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { StatusBadge } from '../components/shared/StatusBadge';
import { connectSSE, type SSEEventHandler } from '../api/sse';
import { startReview, pauseReview, resumeReview, cancelReview, retryReview } from '../api/documents';
import type { ApiResponse } from '../types/api';

interface LogEntry { time: string; agent: string; msg: string }
interface PartialResult { name: string; completed: number; total: number }

export const ReviewProgressPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState('启动中...');
  const [agents, setAgents] = useState([
    { name: '条款提取 Agent', progress: '等待中', status: 'waiting', current: '—', completed: 0, total: 0 },
    { name: '风控 Agent', progress: '等待中', status: 'waiting', current: '—', completed: 0, total: 0 },
    { name: '合规 Agent', progress: '等待中', status: 'waiting', current: '—', completed: 0, total: 0 },
    { name: '报告 Agent', progress: '等待中', status: 'waiting', current: '—', completed: 0, total: 0 },
  ]);
  const [summary, setSummary] = useState<{ high: number; medium: number; low: number } | null>(null);
  const [threadId, setThreadId] = useState('');
  const [paused, setPaused] = useState(false);
  const [error, setError] = useState('');
  const [failCategory, setFailCategory] = useState('');
  const [partialResults, setPartialResults] = useState<PartialResult[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [timeout, setTimeoutInfo] = useState<{ completedCount: number; totalCount: number } | null>(null);

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
          if (a.name.includes('风控') && data.agent_name === 'risk_control') return { ...a, status: 'active', progress: `${data.clauses_processed}/${data.total_clauses}`, current: data.current_dimension || '', completed: data.clauses_processed, total: data.total_clauses };
          if (a.name.includes('合规') && data.agent_name === 'compliance') return { ...a, status: 'active', progress: `${data.clauses_processed}/${data.total_clauses}`, current: data.current_dimension || '', completed: data.clauses_processed, total: data.total_clauses };
          if (a.name.includes('条款') && data.agent_name === 'clause_extraction') return { ...a, status: 'active', progress: `${data.clauses_processed}/${data.total_clauses}`, current: '提取完成', completed: data.clauses_processed, total: data.total_clauses };
          if (a.name.includes('报告') && data.agent_name === 'report') return { ...a, status: 'active', progress: '生成中', current: data.current_dimension || '' };
          return a;
        }));
      },
      onReviewLog: (data) => {
        setLogs(prev => [...prev, { time: data.timestamp || new Date().toLocaleTimeString(), agent: data.agent_name, msg: data.message }]);
      },
      onReviewComplete: (data) => {
        setStatus('审核完成');
        setSummary(data.summary);
        setAgents(prev => prev.map(a => ({ ...a, status: 'done', current: '完成' })));
        setTimeout(() => { if (id) navigate(`/review/${id}/workspace`); }, 2500);
      },
      onReviewFailed: (data) => {
        setStatus('审核失败');
        setError(data.message || 'AI 审核失败');
        setFailCategory(data.fail_category || 'UNKNOWN');
        if (data.partial_results_available) {
          setPartialResults(agents.filter(a => a.completed > 0).map(a => ({ name: a.name, completed: a.completed, total: a.total || 0 })));
        }
      },
      onReviewTimeout: (data) => {
        setStatus('审核超时');
        setTimeoutInfo({ completedCount: data.completed_count, totalCount: data.total_count });
        setError('审核超时，但已完成条款的风险数据保留可用');
      },
      onInterruptReady: (_data) => {
        if (id) navigate(`/review/${id}/workspace`);
      },
    };

    const sse = connectSSE(id, handlers);
    return () => sse.close();
  }, [id, agents]);

  useEffect(() => { startReviewAndListen(); }, [startReviewAndListen]);

  const handlePause = async () => { if (!id) return; await pauseReview(id); setPaused(true); };
  const handleResume = async () => { if (!id) return; await resumeReview(id); setPaused(false); };
  const handleCancel = async () => { if (!id) return; await cancelReview(id); navigate(`/review/${id}/parsing`); };
  const handleRetry = async () => { if (!id) return; await retryReview(id); setError(''); setStatus('重试中...'); };

  const isRunning = (!summary && status !== '审核失败' && status !== '审核超时');
  const isFailed = status === '审核失败';
  const isTimeout = status === '审核超时';

  return (
    <div className="page">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 className="page-title">文档 #{id?.slice(0,8)} — AI 审核</h1>
          <StatusBadge status={status} />
        </div>
      </div>

      {/* Failure Panel */}
      {isFailed && (
        <div style={{ padding: '20px 24px', background: '#fef2f2', border: '2px solid #fecaca', borderRadius: 12, marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <span style={{ fontSize: 28 }}>❌</span>
            <div style={{ flex: 1 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#dc2626', margin: 0 }}>
                AI 审核失败 — {failCategory === 'SERVICE_UNAVAILABLE' ? 'AI 服务不可用' : failCategory === 'PARSE_ERROR' ? '解析残留错误' : '未知错误'}
              </h3>
              <p style={{ fontSize: 13, color: '#dc2626', margin: '4px 0 0' }}>{error}</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            {failCategory === 'SERVICE_UNAVAILABLE' && <button className="btn btn-primary" onClick={handleRetry}>重试</button>}
            {failCategory === 'SERVICE_UNAVAILABLE' && <button className="btn btn-outline">人工接管</button>}
            {failCategory === 'PARSE_ERROR' && <button className="btn btn-outline" onClick={() => navigate(`/review/${id}/parsing`)}>重新上传</button>}
          </div>
        </div>
      )}

      {/* Timeout Panel */}
      {isTimeout && timeout && (
        <div style={{ padding: '16px 20px', background: '#fffbeb', border: '2px solid #fde68a', borderRadius: 12, marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <span style={{ fontSize: 28 }}>⏱️</span>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#92400e', margin: 0 }}>审核超时</h3>
              <p style={{ fontSize: 13, color: '#92400e', margin: '4px 0 0' }}>
                {error}（已完成 {timeout.completedCount}/{timeout.totalCount} 条款）
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={handleRetry}>重试</button>
            <button className="btn btn-outline" onClick={() => id && navigate(`/review/${id}/workspace`)}>查看已完成条款</button>
          </div>
        </div>
      )}

      {/* Partial Success Panel */}
      {partialResults.length > 0 && (
        <div style={{ padding: '16px 20px', background: '#f0fdf4', border: '2px solid #bbf7d0', borderRadius: 12, marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <span style={{ fontSize: 28 }}>⚠️</span>
            <div style={{ flex: 1 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#166534', margin: 0 }}>部分成功 — 已完成审阅的条款数据可用</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                {partialResults.map((p, i) => (
                  <span key={i} style={{ fontSize: 11, padding: '4px 10px', background: '#dcfce7', border: '1px solid #86efac', borderRadius: 6, fontFamily: 'var(--font-mono)' }}>
                    {p.name}: {p.completed}/{p.total} 完成
                  </span>
                ))}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={() => id && navigate(`/review/${id}/workspace`)}>进入人工接管工作台</button>
            <button className="btn btn-outline" onClick={handleRetry}>重试未完成条款</button>
          </div>
        </div>
      )}

      {/* Supervisor info bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 16px', background: 'var(--color-primary-light)', borderRadius: 8, border: '1px solid var(--color-primary)' }}>
        <span style={{ fontSize: 18 }}>{isRunning ? '🔄' : '✅'}</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>
          {isRunning ? `Supervisor: 已编排 4 个 Agent，正在并行执行${threadId ? ` | Thread: ${threadId}` : ''}` : 'Supervisor: 执行完毕'}
        </span>
      </div>

      {/* Agent Cards */}
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

      {/* Review Log Stream */}
      <div className="card card-padded" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>实时审核日志</span>
        {logs.length === 0 && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>等待 Agent 输出...</span>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 200, overflowY: 'auto' }}>
          {logs.map((l, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', flexShrink: 0 }}>[{l.time}]</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-warning)', flexShrink: 0, width: 90 }}>{l.agent}</span>
              <span style={{ fontSize: 12 }}>{l.msg}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Completion Summary */}
      {summary && (
        <div className="card card-padded" style={{ background: 'var(--color-success-bg)', border: '1px solid var(--color-success)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-success)', marginBottom: 12 }}>AI 审核完成 — 风险统计摘要</h3>
          <div style={{ display: 'flex', gap: 24, marginBottom: 16 }}>
            <div className="stat-card" style={{ textAlign: 'center' }}><span style={{ fontSize: 24, fontWeight: 700, color: 'var(--risk-high)' }}>{summary.high}</span><span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>高风险</span></div>
            <div className="stat-card" style={{ textAlign: 'center' }}><span style={{ fontSize: 24, fontWeight: 700, color: 'var(--risk-medium)' }}>{summary.medium}</span><span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>中风险</span></div>
            <div className="stat-card" style={{ textAlign: 'center' }}><span style={{ fontSize: 24, fontWeight: 700, color: 'var(--risk-low)' }}>{summary.low}</span><span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block' }}>低风险</span></div>
          </div>
          <button className="btn btn-primary" onClick={() => navigate(`/review/${id}/workspace`)}>进入人工审批工作台 →</button>
        </div>
      )}

      {/* Control Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {isRunning && (
            paused
              ? <button className="btn btn-primary" onClick={handleResume}>▶ 恢复审核</button>
              : <button className="btn btn-outline" onClick={handlePause}>⏸ 暂停审核</button>
          )}
          {isRunning && <button className="btn btn-ghost" onClick={handleCancel}>✕ 取消</button>}
        </div>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>生命周期: 已创建 → 排队 → 执行中 → ...</span>
      </div>
    </div>
  );
};
