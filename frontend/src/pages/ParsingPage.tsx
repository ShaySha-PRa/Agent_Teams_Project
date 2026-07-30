import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CircularProgress } from '../components/shared/CircularProgress';
import { ProgressBar } from '../components/shared/ProgressBar';
import { connectSSE, type SSEEventHandler } from '../api/sse';

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

  useEffect(() => {
    if (!id) return;

    const handlers: SSEEventHandler = {
      onParseProgress: (data) => {
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
        setAgents(prev => prev.map(a => ({ ...a, pct: 100, detail: '已完成' })));
        setStatus('解析完成');
        setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), agent: '系统', msg: `解析完成，提取 ${data.clause_count} 条条款` }]);
        // Auto-navigate to review after a short delay
        setTimeout(() => {
          if (id) navigate(`/review/${id}/reviewing`);
        }, 2000);
      },
      onParseFailed: (data) => {
        setStatus('解析失败');
        setError(data.error_message || '解析失败');
      },
    };

    const sse = connectSSE(id, handlers);
    return () => sse.close();
  }, [id, navigate]);

  return (
    <div className="page">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 className="page-title">{docTitle}</h1>
          <span className={`badge ${status === '解析完成' ? 'badge-success' : status === '解析失败' ? 'badge-danger' : 'badge-info'}`}>{status}</span>
        </div>
      </div>

      {error && <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, color: '#dc2626', marginBottom: 16 }}>{error}</div>}

      <div style={{ display: 'flex', gap: 24 }}>
        <div className="card card-padded" style={{ width: 220, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>整体进度</span>
          <CircularProgress percent={overallPct} />
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{overallPct}%</span>
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

      <div className="card card-padded" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>实时操作日志</span>
        {logs.length === 0 && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>等待 SSE 事件...</span>}
        {logs.map((l, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>[{l.time}]</span>
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-primary)', width: 70 }}>{l.agent}</span>
            <span style={{ fontSize: 12 }}>{l.msg}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
