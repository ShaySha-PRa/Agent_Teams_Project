import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CircularProgress } from '../components/shared/CircularProgress';
import { ProgressBar } from '../components/shared/ProgressBar';
import { StatusBadge } from '../components/shared/StatusBadge';
import { connectSSE, type SSEEventHandler } from '../api/sse';
import { retryParse } from '../api/documents';
import type { ApiResponse } from '../types/api';

interface AgentState { name: string; pct: number; detail: string; color: string }
interface LogEntry { time: string; agent: string; msg: string }

export const ParsingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [docTitle] = useState('文档解析中...');
  const [overallPct, setOverallPct] = useState(0);
  const [agents, setAgents] = useState<AgentState[]>([
    { name: '条款提取 Agent', pct: 0, detail: '等待中...', color: 'var(--color-primary)' },
    { name: '风控 Agent', pct: 0, detail: '等待中...', color: 'var(--color-warning)' },
    { name: '合规 Agent', pct: 0, detail: '等待中...', color: 'var(--color-success)' },
    { name: '报告 Agent', pct: 0, detail: '等待上游完成...', color: 'var(--text-disabled)' },
  ]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState('解析中');
  const [error, setError] = useState('');
  const [errorType, setErrorType] = useState('');
  const [recoverable, setRecoverable] = useState(false);
  const [percent, setPercent] = useState(0);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (!id) return;

    const handlers: SSEEventHandler = {
      onParseProgress: (data) => {
        setStatus('解析中');
        setAgents(prev => prev.map(a => {
          if (a.name.includes('条款') && data.agent_name === 'clause_extraction') return { ...a, pct: Math.round(data.progress_pct * 100), detail: data.current_clause_type || '提取中' };
          if (a.name.includes('风控') && data.agent_name === 'risk_control') return { ...a, pct: Math.round(data.progress_pct * 100), detail: data.current_dimension || '分析中' };
          if (a.name.includes('合规') && data.agent_name === 'compliance') return { ...a, pct: Math.round(data.progress_pct * 100), detail: data.current_dimension || '检查中' };
          return a;
        }));
        setOverallPct(prev => Math.max(prev, Math.round(data.progress_pct * 100)));
      },
      onParseComplete: (data) => {
        setOverallPct(100);
        setPercent(100);
        setAgents(prev => prev.map(a => ({ ...a, pct: 100, detail: '已完成' })));
        setStatus('解析完成');
        setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), agent: '系统', msg: `解析完成，提取 ${data.clause_count} 条条款` }]);
        setTimeout(() => { if (id) navigate(`/review/${id}/reviewing`); }, 2000);
      },
      onParseFailed: (data) => {
        setStatus('解析失败');
        setError(data.error_message || '解析失败');
        setErrorType(data.error_type || 'UNKNOWN');
        setRecoverable(data.recoverable ?? false);
      },
    };

    const sse = connectSSE(id, handlers);
    return () => sse.close();
  }, [id, navigate]);

  const handleRetry = async () => {
    if (!id) return;
    setRetrying(true);
    setError('');
    try {
      await retryParse(id) as ApiResponse<any>;
      // SSE will update the UI
      setStatus('解析中');
      setOverallPct(0);
    } catch (e: any) {
      setError(e.message || '重试失败');
    } finally {
      setRetrying(false);
    }
  };

  const handleReupload = () => {
    navigate('/review/new');
  };

  const handleCancel = () => {
    navigate('/dashboard');
  };

  const isFailed = status === '解析失败';
  const isComplete = status === '解析完成';

  return (
    <div className="page">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 className="page-title">{docTitle}</h1>
          <StatusBadge status={status} />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {!isComplete && !isFailed && (
            <button className="btn btn-outline" style={{ fontSize: 12 }} onClick={handleCancel}>取消解析</button>
          )}
          {isComplete && (
            <button className="btn btn-primary" style={{ fontSize: 12 }} onClick={() => navigate(`/review/${id}/reviewing`)}>进入 AI 审核 →</button>
          )}
        </div>
      </div>

      {/* Failure Panel */}
      {isFailed && (
        <div style={{ padding: '20px 24px', background: '#fef2f2', border: '2px solid #fecaca', borderRadius: 12, marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 28 }}>{recoverable ? '⚠️' : '❌'}</span>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#dc2626', margin: 0 }}>
                {recoverable ? '解析失败（可恢复）' : '解析失败（不可恢复）'}
              </h3>
              <p style={{ fontSize: 13, color: '#dc2626', margin: '4px 0 0' }}>
                {error}
              </p>
            </div>
          </div>

          {recoverable ? (
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-primary" onClick={handleRetry} disabled={retrying}>
                {retrying ? '重试中...' : '断点续传 — 从失败点恢复'}
              </button>
              <button className="btn btn-outline" onClick={handleReupload}>重新上传</button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-primary" onClick={handleReupload}>重新上传新文件</button>
            </div>
          )}
        </div>
      )}

      {/* Normal / Streaming progress */}
      <div style={{ display: 'flex', gap: 24 }}>
        <div className="card card-padded" style={{ width: 220, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>整体进度</span>
          <CircularProgress percent={overallPct} />
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{overallPct}%</span>
          {!isFailed && !isComplete && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>预估剩余约 30 秒</span>}
        </div>

        <div className="card card-padded" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <span style={{ fontSize: 14, fontWeight: 600 }}>分 Agent 进度</span>
          {agents.map((a, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{a.name}</span>
                <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: a.color }}>{a.pct}%</span>
              </div>
              <ProgressBar percent={a.pct} color={a.color} />
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.detail}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Log Stream */}
      <div className="card card-padded" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>实时操作日志</span>
        {logs.length === 0 && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>等待 SSE 事件...</span>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 200, overflowY: 'auto' }}>
          {logs.map((l, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', flexShrink: 0 }}>[{l.time}]</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-primary)', flexShrink: 0, width: 80 }}>{l.agent}</span>
              <span style={{ fontSize: 12 }}>{l.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
