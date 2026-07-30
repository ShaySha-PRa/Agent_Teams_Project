import React from 'react';
import type { ReviewSummary } from '../../types/review';

interface Props {
  visible: boolean;
  reviewSummary: ReviewSummary;
  isSubmitting: boolean;
  errorMessage: string | null;
  onConfirm: (comment?: string) => void;
  onCancel: () => void;
}

export const SubmitConfirmDialog: React.FC<Props> = ({
  visible,
  reviewSummary,
  isSubmitting,
  errorMessage,
  onConfirm,
  onCancel,
}) => {
  const [comment, setComment] = React.useState('');

  if (!visible) return null;

  const s = reviewSummary;
  const totalItems = s.total_high_risk + s.total_medium_risk + s.low_risk_auto_passed + s.manual_added;

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000 }}>
      <div className="card card-padded" style={{ width: 480, maxHeight: '90vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>提交审阅确认</h3>
          <button className="btn btn-ghost" onClick={onCancel} style={{ fontSize: 18, padding: '2px 8px' }}>×</button>
        </div>

        {/* Review Summary */}
        <div>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 10 }}>审阅摘要</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '12px 16px', background: 'var(--bg-page)', borderRadius: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span>高风险 — 已确认 (APPROVE)</span>
              <span style={{ fontWeight: 600, color: 'var(--risk-high)' }}>{s.approved_high_risk}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ paddingLeft: 12 }}>其中已审批</span>
              <span style={{ fontWeight: 600, color: 'var(--color-success)' }}>{s.approved_high_risk}</span>
            </div>
            <div style={{ height: 1, background: 'var(--border-color)' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span>中风险 — 总计</span>
              <span style={{ fontWeight: 600, color: 'var(--risk-medium)' }}>{s.total_medium_risk}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ paddingLeft: 12 }}>已人工审核</span>
              <span style={{ fontWeight: 600 }}>{s.reviewed_medium_risk}</span>
            </div>
            <div style={{ height: 1, background: 'var(--border-color)' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span>低风险 — 自动通过</span>
              <span style={{ fontWeight: 600, color: 'var(--risk-low)' }}>{s.low_risk_auto_passed}</span>
            </div>
            <div style={{ height: 1, background: 'var(--border-color)' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span>手动补充标记</span>
              <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{s.manual_added}</span>
            </div>
            <div style={{ height: 1, background: 'var(--color-primary)' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, fontWeight: 700 }}>
              <span>总计审核项</span>
              <span>{totalItems}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span>完成率</span>
              <span style={{ fontWeight: 600, color: 'var(--color-success)' }}>{s.completion_rate_pct}%</span>
            </div>
          </div>
        </div>

        {/* Optional comment */}
        <div>
          <span style={{ fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>附加备注（可选）</span>
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            rows={2}
            placeholder="可选：添加提交备注..."
            style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12, resize: 'vertical', fontFamily: 'inherit' }}
          />
        </div>

        {/* Warning */}
        <div style={{ padding: '10px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6 }}>
          <span style={{ fontSize: 12, color: '#dc2626' }}>提交后将生成最终审阅报告，无法再修改审批决策</span>
        </div>

        {/* Error */}
        {errorMessage && (
          <div style={{ padding: '10px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6 }}>
            <span style={{ fontSize: 12, color: '#dc2626' }}>{errorMessage}</span>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button className="btn btn-outline" onClick={onCancel} disabled={isSubmitting}>取消，继续审阅</button>
          <button className="btn btn-primary" onClick={() => onConfirm(comment || undefined)} disabled={isSubmitting}>
            {isSubmitting ? '提交中...' : '确认提交'}
          </button>
        </div>
      </div>
    </div>
  );
};
