import React, { useState } from 'react';
import type { RiskFlag } from '../../types/risk';

interface Props {
  open: boolean;
  riskFlag: RiskFlag | null;
  onClose: () => void;
  onSubmit: (reason: string) => void;
}

export const RejectDialog: React.FC<Props> = ({ open, riskFlag, onClose, onSubmit }) => {
  const [reason, setReason] = useState('');
  if (!open) return null;
  const isValid = reason.trim().length >= 10;

  const handleSubmit = () => {
    if (!isValid) return;
    onSubmit(reason);
    setReason('');
  };

  const handleClose = () => {
    setReason('');
    onClose();
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000 }}>
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 24, width: 460, maxWidth: '90vw', display: 'flex', flexDirection: 'column', gap: 16, boxShadow: '0 8px 30px rgba(0,0,0,0.15)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 28 }}>⚠️</span>
          <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--color-danger)' }}>驳回 AI 风险标记</h3>
        </div>

        {riskFlag && (
          <div style={{ padding: '12px 14px', background: 'var(--bg-page)', borderRadius: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
              <span style={{ color: 'var(--text-muted)' }}>条款类型</span>
              <span style={{ fontWeight: 600 }}>{riskFlag.risk_category}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
              <span style={{ color: 'var(--text-muted)' }}>风险等级</span>
              <span style={{ fontWeight: 600, color: 'var(--risk-high)' }}>高风险</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
              <span style={{ color: 'var(--text-muted)' }}>AI 置信度</span>
              <span style={{ fontWeight: 600 }}>{(riskFlag.ai_confidence * 100).toFixed(0)}%</span>
            </div>
            {riskFlag.clause_location && (
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                <span style={{ color: 'var(--text-muted)' }}>位置</span>
                <span>第 {riskFlag.clause_location.page_number} 页</span>
              </div>
            )}
            <div style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic', marginTop: 2 }}>
              "{riskFlag.rationale_text?.slice(0, 100)}..."
            </div>
          </div>
        )}

        <div style={{ padding: '10px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6 }}>
          <span style={{ fontSize: 12, color: '#dc2626' }}>
            驳回后该标记将被移除，操作不可撤销
          </span>
        </div>

        <div>
          <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>驳回原因（必填，≥10字符）</label>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder="请详细说明驳回此 AI 风险标记的原因..."
            rows={3}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 8,
              border: `2px solid ${isValid ? 'var(--color-success)' : reason.length > 0 ? 'var(--color-danger)' : 'var(--border-color)'}`,
              fontSize: 13, resize: 'vertical', fontFamily: 'inherit',
              outline: 'none', background: 'var(--bg-page)',
            }}
            autoFocus
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
            <span style={{ fontSize: 11, color: isValid ? 'var(--color-success)' : 'var(--text-muted)' }}>
              已输入 {reason.length}/10 字符
            </span>
            {!isValid && reason.length > 0 && (
              <span style={{ fontSize: 11, color: 'var(--color-danger)' }}>至少需要 10 个字符</span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button className="btn btn-outline" onClick={handleClose}>取消</button>
          <button className="btn btn-danger" disabled={!isValid} onClick={handleSubmit}>确认驳回</button>
        </div>
      </div>
    </div>
  );
};
