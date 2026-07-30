import React, { useState } from 'react';
import type { RiskFlag } from '../../types/risk';

interface Props {
  visible: boolean;
  riskFlag: RiskFlag | null;
  onConfirm: (newLevel: string, reason: string) => void;
  onCancel: () => void;
}

export const EscalateDialog: React.FC<Props> = ({ visible, riskFlag, onConfirm, onCancel }) => {
  const [reason, setReason] = useState('');

  if (!visible || !riskFlag) return null;

  const levelLabel = riskFlag.risk_level === 'MEDIUM' ? '中风险' : '低风险';
  const levelColor = riskFlag.risk_level === 'MEDIUM' ? 'var(--risk-medium)' : 'var(--risk-low)';
  const isValid = reason.length >= 10;

  const handleConfirm = () => {
    if (!isValid) return;
    onConfirm('HIGH', reason);
    setReason('');
  };

  const handleCancel = () => {
    setReason('');
    onCancel();
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000 }}>
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: 24, width: 460, maxWidth: '90vw', display: 'flex', flexDirection: 'column', gap: 16, boxShadow: '0 8px 30px rgba(0,0,0,0.15)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 28 }}>⚠️</span>
          <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--color-danger)' }}>升级风险等级</h3>
        </div>

        {/* Summary */}
        <div style={{ padding: '12px 14px', background: 'var(--bg-page)', borderRadius: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>条款类型</span>
            <span style={{ fontSize: 13, fontWeight: 600 }}>{riskFlag.risk_category}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>当前等级</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: levelColor }}>{levelLabel}</span>
          </div>
          <div style={{ height: 1, background: 'var(--border-color)' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>升级后</span>
            <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--risk-high)' }}>🔴 高风险</span>
          </div>
          {riskFlag.clause_location && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>位置</span>
              <span style={{ fontSize: 12 }}>第 {riskFlag.clause_location.page_number} 页</span>
            </div>
          )}
        </div>

        {/* Warnings */}
        <div style={{ padding: '10px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 12, color: '#dc2626' }}>升级后该标记将：</span>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: 11, color: '#dc2626' }}>
            <li>进入高风险强制审批队列</li>
            <li>需要逐条审批（approve / edit / reject）</li>
            <li>在审批完成前无法提交审阅</li>
            <li>操作不可逆</li>
          </ul>
        </div>

        {/* Reason */}
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>升级原因（必填，≥10字符）</label>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder="请说明为什么需要升级此条款的风险等级..."
            rows={3}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 8,
              border: `2px solid ${isValid ? 'var(--color-success)' : reason.length > 0 ? 'var(--color-danger)' : 'var(--border-color)'}`,
              fontSize: 13, resize: 'vertical', fontFamily: 'inherit',
              outline: 'none', background: 'var(--bg-page)',
            }}
            autoFocus
          />
          <span style={{ fontSize: 11, color: isValid ? 'var(--color-success)' : 'var(--text-muted)', marginTop: 4, display: 'block' }}>
            已输入 {reason.length}/10 字符
          </span>
        </div>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button className="btn btn-outline" onClick={handleCancel}>取消</button>
          <button className="btn btn-danger" disabled={!isValid} onClick={handleConfirm}>确认升级为高风险</button>
        </div>
      </div>
    </div>
  );
};
