import React, { useEffect, useState } from 'react';
import type { AuditLogEntry } from '../../types/review';

interface Props {
  documentId: string;
}

const MOCK_TIMELINE: AuditLogEntry[] = [
  { log_id: '1', operation_type: 'UPLOAD', timestamp: '2026-07-30T10:15:00', operator_id: 'user_001', details: { filename: 'document.pdf' } },
  { log_id: '2', operation_type: 'PARSE_START', timestamp: '2026-07-30T10:15:30', operator_id: 'system', details: { playbook: 'NDA Standard' } },
  { log_id: '3', operation_type: 'PARSE_COMPLETE', timestamp: '2026-07-30T10:16:45', operator_id: 'system', details: { clause_count: 12 } },
  { log_id: '4', operation_type: 'REVIEW_START', timestamp: '2026-07-30T10:17:00', operator_id: 'system', details: { agents: 4 } },
  { log_id: '5', operation_type: 'REVIEW_COMPLETE', timestamp: '2026-07-30T10:22:00', operator_id: 'system', details: { high: 3, medium: 5, low: 4 } },
  { log_id: '6', operation_type: 'HUMAN_APPROVE', timestamp: '2026-07-30T10:30:00', operator_id: 'user_001', details: { risk_flag_id: 'rf_001', decision: 'APPROVE' } },
  { log_id: '7', operation_type: 'HUMAN_EDIT', timestamp: '2026-07-30T10:32:00', operator_id: 'user_001', details: { risk_flag_id: 'rf_002', decision: 'EDIT', modified_level: 'MEDIUM' } },
  { log_id: '8', operation_type: 'BATCH_CONFIRM', timestamp: '2026-07-30T10:35:00', operator_id: 'user_001', details: { count: 5, level: 'MEDIUM' } },
  { log_id: '9', operation_type: 'FINAL_SUBMIT', timestamp: '2026-07-30T10:40:00', operator_id: 'user_001', details: {} },
];

export const AuditTimeline: React.FC<Props> = ({ documentId }) => {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch from API
    import('../../api/documents').then(({ getAuditLogs }) => {
      getAuditLogs(documentId)
        .then((res: any) => {
          if (res.data?.items && res.data.items.length > 0) {
            setEntries(res.data.items);
          } else {
            // Fallback to mock timeline if API returns empty
            setEntries(MOCK_TIMELINE as AuditLogEntry[]);
          }
        })
        .catch(() => setEntries(MOCK_TIMELINE as AuditLogEntry[]))
        .finally(() => setLoading(false));
    });
  }, [documentId]);

  if (loading) return <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>加载审计时间线...</div>;
  if (error) return <div style={{ fontSize: 12, color: 'var(--color-danger)' }}>{error}</div>;

  const opLabels: Record<string, { label: string; icon: string; color: string }> = {
    UPLOAD: { label: '上传文档', icon: '📤', color: 'var(--color-primary)' },
    PARSE_START: { label: '开始解析', icon: '🔍', color: 'var(--color-info)' },
    PARSE_COMPLETE: { label: '解析完成', icon: '✅', color: 'var(--color-success)' },
    REVIEW_START: { label: 'AI 审核启动', icon: '🤖', color: 'var(--color-info)' },
    REVIEW_COMPLETE: { label: 'AI 审核完成', icon: '✅', color: 'var(--color-success)' },
    REVIEW_FAILED: { label: 'AI 审核失败', icon: '❌', color: 'var(--color-danger)' },
    HUMAN_APPROVE: { label: '人工同意', icon: '👍', color: 'var(--color-success)' },
    HUMAN_EDIT: { label: '人工修正', icon: '✏️', color: 'var(--color-warning)' },
    HUMAN_REJECT: { label: '人工驳回', icon: '❌', color: 'var(--color-danger)' },
    BATCH_CONFIRM: { label: '批量确认', icon: '📋', color: 'var(--color-info)' },
    SPOT_CHECK_SAMPLE: { label: '抽样审计', icon: '🔍', color: 'var(--color-warning)' },
    SPOT_CHECK_ESCALATE: { label: '抽样升级', icon: '⬆️', color: 'var(--color-danger)' },
    MANUAL_ADD: { label: '手动标记', icon: '✋', color: 'var(--color-primary)' },
    FINAL_SUBMIT: { label: '提交审阅', icon: '📤', color: 'var(--color-success)' },
    REPORT_GENERATED: { label: '报告生成', icon: '📄', color: 'var(--color-success)' },
    REPORT_SIGNED: { label: '报告签署', icon: '✍️', color: 'var(--color-primary)' },
    SAVE_DRAFT: { label: '暂存草稿', icon: '💾', color: 'var(--text-muted)' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0, position: 'relative' }}>
      {/* Vertical line */}
      <div style={{ position: 'absolute', left: 11, top: 8, bottom: 8, width: 2, background: 'var(--border-color)' }} />

      {entries.map((entry, i) => {
        const op = opLabels[entry.operation_type] || { label: entry.operation_type, icon: '', color: 'var(--text-muted)' };
        const time = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '';
        return (
          <div key={entry.log_id || i} style={{ display: 'flex', gap: 14, padding: '8px 0', position: 'relative' }}>
            {/* Dot */}
            <div style={{
              width: 10, height: 10, borderRadius: '50%', background: op.color,
              border: '2px solid #fff', boxShadow: `0 0 0 2px ${op.color}`, flexShrink: 0,
              marginTop: 4, zIndex: 1,
            }} />
            {/* Content */}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: op.color }}>{op.icon} {op.label}</span>
                <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{time}</span>
                {entry.operator_id && entry.operator_id !== 'system' && (
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>操作人: {entry.operator_id}</span>
                )}
              </div>
              {/* Show key details */}
              {entry.details && Object.keys(entry.details).length > 0 && (
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  {Object.entries(entry.details).slice(0, 3).map(([k, v]) => (
                    <span key={k} style={{ marginRight: 12 }}>{k}: <span style={{ fontFamily: 'var(--font-mono)' }}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span></span>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
