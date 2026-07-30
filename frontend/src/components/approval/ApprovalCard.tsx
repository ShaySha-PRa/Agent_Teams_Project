import React from 'react';
import { RiskBadge } from '../shared/RiskBadge';
import type { RiskFlag } from '../../types/risk';

interface Props {
  riskFlag: RiskFlag;
  onApprove?: () => void;
  onEdit?: () => void;
  onReject?: () => void;
  index?: number;
  total?: number;
}

export const ApprovalCard: React.FC<Props> = ({ riskFlag, onApprove, onEdit, onReject, index, total }) => {
  const handleAction = (action: string) => {
    if (action === 'approve') onApprove?.();
    else if (action === 'edit') onEdit?.();
    else if (action === 'reject') onReject?.();
  };

  const idx = index ?? 0;
  const tot = total ?? 0;

  return (
    <div className="approval-card">
      <div>
        <div className="zone-label">① 条款定位: {riskFlag.risk_category} — 第 {riskFlag.clause_location.page_number} 页第 {riskFlag.clause_location.paragraph_number || '?'} 段</div>
        <div className="zone-ref">&quot;{riskFlag.rationale_text?.substring(0, 80)}...&quot;</div>
      </div>
      <div className="zone-judgment">
        ② AI 判定: <RiskBadge level={riskFlag.risk_level} /> · {riskFlag.risk_category} · AI 置信度 {(riskFlag.ai_confidence * 100).toFixed(0)}%
      </div>
      <div className="zone-diff">
        <strong>③ Playbook 对比:</strong>{'\n'}{riskFlag.playbook_diff_text}
      </div>
      <div className="zone-suggestion">
        ④ 修改建议: {riskFlag.suggested_wording}
      </div>
      <div className="zone-history">
        ⑤ 审批历史: 无历史相似条款审阅记录
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {tot > 0 && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>审批进度: 第 {idx + 1}/{tot} 项</span>}
        <div className="zone-actions">
          <button className="btn btn-success" onClick={() => handleAction('approve')}>✅ 同意</button>
          <button className="btn btn-outline" onClick={() => handleAction('edit')}>✏️ 编辑</button>
          <button className="btn btn-danger" onClick={() => handleAction('reject')}>❌ 驳回</button>
        </div>
      </div>
    </div>
  );
};
