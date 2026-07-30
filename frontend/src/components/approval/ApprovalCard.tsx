import React, { useEffect, useState } from 'react';
import { RiskBadge } from '../shared/RiskBadge';
import { getPlaybookDiff, getDecisions } from '../../api/riskFlags';
import type { RiskFlag, PlaybookDiff as PlaybookDiffType } from '../../types/risk';
import type { ReviewDecision } from '../../types/review';
import type { ApiResponse } from '../../types/api';

interface Props {
  riskFlag: RiskFlag;
  onApprove?: () => void;
  onEdit?: () => void;
  onReject?: () => void;
  index?: number;
  total?: number;
  sourceLabel?: string;
}

export const ApprovalCard: React.FC<Props> = ({ riskFlag, onApprove, onEdit, onReject, index, total, sourceLabel }) => {
  const [expanded, setExpanded] = useState(false);
  const [diffData, setDiffData] = useState<PlaybookDiffType | null>(null);
  const [decisions, setDecisions] = useState<ReviewDecision[]>([]);
  const [loadingDiff, setLoadingDiff] = useState(false);
  const [loadingDecisions, setLoadingDecisions] = useState(false);

  const isManual = riskFlag.source === 'MANUALLY_ADDED';
  const idx = index ?? 0;
  const tot = total ?? 0;

  // Lazy load diff and history when expanded
  useEffect(() => {
    if (!expanded) return;
    if (!isManual && !diffData && !loadingDiff) {
      setLoadingDiff(true);
      getPlaybookDiff(riskFlag.risk_flag_id)
        .then((res: unknown) => {
          const r = res as ApiResponse<PlaybookDiffType>;
          setDiffData(r.data);
        })
        .catch(() => {})
        .finally(() => setLoadingDiff(false));
    }
    if (!loadingDecisions && decisions.length === 0) {
      setLoadingDecisions(true);
      getDecisions(riskFlag.risk_flag_id)
        .then((res: unknown) => {
          const r = res as ApiResponse<{ decisions: ReviewDecision[] }>;
          setDecisions(r.data.decisions);
        })
        .catch(() => {})
        .finally(() => setLoadingDecisions(false));
    }
  }, [expanded, riskFlag.risk_flag_id, isManual, diffData, decisions.length, loadingDiff, loadingDecisions]);

  return (
    <div className="approval-card" style={{ border: expanded ? '2px solid var(--color-primary)' : undefined }}>
      {/* Zone 1: Clause Location */}
      <div>
        <div className="zone-label">
          ① 条款定位: {riskFlag.risk_category}
          {riskFlag.clause_location && ` — 第 ${riskFlag.clause_location.page_number} 页第 ${riskFlag.clause_location.paragraph_number || '?'} 段`}
        </div>
        <div className="zone-ref">"{riskFlag.rationale_text?.substring(0, 80)}..."</div>
      </div>

      {/* Zone 2: AI Judgment */}
      <div className="zone-judgment">
        ② AI 判定: <RiskBadge level={riskFlag.risk_level} /> · {riskFlag.risk_category}
        {!isManual && <> · AI 置信度 {(riskFlag.ai_confidence * 100).toFixed(0)}%</>}
        {isManual && <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--color-warning)', fontWeight: 600 }}>👤 人工标记</span>}
      </div>

      {/* Zone 3: Playbook Diff */}
      {isManual ? (
        <div className="zone-diff" style={{ opacity: 0.6 }}>
          <strong>③ Playbook 对比:</strong>{'\n'}无 Playbook 对比 — 人工标记
        </div>
      ) : (
        <div className="zone-diff">
          <strong>③ Playbook 对比:</strong>
          {loadingDiff ? (
            <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8 }}>加载中...</span>
          ) : diffData ? (
            <div style={{ marginTop: 4, display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                <div style={{ padding: '6px 8px', background: '#f0faf0', borderRadius: 4, fontSize: 10 }}>
                  <span style={{ fontWeight: 600 }}>标准条款:</span> {diffData.playbook_rule.standard_clause_text?.slice(0, 80)}
                </div>
                <div style={{ padding: '6px 8px', background: '#fff0f0', borderRadius: 4, fontSize: 10 }}>
                  <span style={{ fontWeight: 600 }}>实际条款:</span> {riskFlag.clause_text?.slice(0, 80) || '见原文'}
                </div>
              </div>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                相似度: {(diffData.match.similarity_score * 100).toFixed(0)}%
                {diffData.match.diff_items?.map((d, i) => (
                  <span key={i} style={{ marginLeft: 8 }}>{d.field}: {d.standard_value} → {d.actual_value} [{d.deviation_type}]</span>
                ))}
              </span>
            </div>
          ) : (
            <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 8, fontStyle: 'italic' }}>点击展开加载对比数据</span>
          )}
        </div>
      )}

      {/* Zone 4: Suggestion */}
      <div className="zone-suggestion">
        ④ 修改建议: {riskFlag.suggested_wording || (isManual ? '—' : riskFlag.suggested_wording || '按实际情况调整')}
      </div>

      {/* Zone 5: Decision History */}
      <div className="zone-history">
        ⑤ 审批历史:{' '}
        {loadingDecisions ? (
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>加载中...</span>
        ) : decisions.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4 }}>
            {decisions.slice(0, 3).map((d) => (
              <div key={d.decision_id} style={{ fontSize: 11, display: 'flex', gap: 6, alignItems: 'center' }}>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{d.timestamp ? new Date(d.timestamp).toLocaleDateString() : ''}</span>
                <span style={{ fontWeight: 600, color: d.decision_type === 'APPROVE' ? 'var(--color-success)' : d.decision_type === 'REJECT' ? 'var(--color-danger)' : 'var(--color-warning)' }}>
                  {d.decision_type === 'APPROVE' ? '同意' : d.decision_type === 'EDIT' ? '编辑' : d.decision_type === 'REJECT' ? '驳回' : d.decision_type}
                </span>
                <span style={{ color: 'var(--text-muted)' }}>{d.comment?.slice(0, 50)}</span>
                {d.modified_risk_level && <span style={{ fontSize: 10, color: 'var(--color-warning)' }}>→{d.modified_risk_level}</span>}
              </div>
            ))}
            {decisions.length > 3 && <span style={{ fontSize: 10, color: 'var(--color-primary)' }}>查看全部 {decisions.length} 条记录</span>}
          </div>
        ) : (
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>无历史相似条款审阅记录</span>
        )}
      </div>

      {/* Zone 6: Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {tot > 0 && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>审批进度: 第 {idx + 1}/{tot} 项</span>}
        <div className="zone-actions" style={{ marginLeft: 'auto' }}>
          <button className="btn btn-success" onClick={onApprove}>✅ 同意</button>
          <button className="btn btn-outline" onClick={onEdit}>✏️ 编辑</button>
          <button className="btn btn-danger" onClick={onReject}>❌ 驳回</button>
        </div>
      </div>

      {/* Expand toggle */}
      <div style={{ textAlign: 'center', marginTop: 4 }}>
        <button
          className="btn btn-ghost"
          style={{ fontSize: 10, padding: '2px 8px' }}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? '收起详情 ▲' : '展开更多 ▼'}
        </button>
      </div>
    </div>
  );
};
