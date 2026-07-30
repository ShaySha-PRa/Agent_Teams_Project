import React, { useState } from 'react';
import type { RiskLevel } from '../../types/api';

interface Props {
  visible: boolean;
  riskLevel: RiskLevel;
  riskCategory: string;
  suggestedWording: string;
  onSave: (data: {
    comment: string;
    modified_risk_level?: string;
    modified_risk_category?: string;
    modified_suggestion?: string;
  }) => void;
  onCancel: () => void;
}

export const EditForm: React.FC<Props> = ({ visible, riskLevel, riskCategory, suggestedWording, onSave, onCancel }) => {
  const [comment, setComment] = useState('');
  const [modifiedLevel, setModifiedLevel] = useState<string>('');
  const [modifiedCategory, setModifiedCategory] = useState<string>('');
  const [modifiedSuggestion, setModifiedSuggestion] = useState(suggestedWording);

  if (!visible) return null;

  const isDowngradeToLow = riskLevel === 'HIGH' && modifiedLevel === 'LOW';
  const isDowngrade = modifiedLevel && modifiedLevel !== riskLevel;
  const isValid = comment.length >= 10;

  const handleSave = () => {
    if (!isValid) return;
    onSave({
      comment,
      modified_risk_level: modifiedLevel || undefined,
      modified_risk_category: modifiedCategory || undefined,
      modified_suggestion: modifiedSuggestion !== suggestedWording ? modifiedSuggestion : undefined,
    });
    setComment('');
    setModifiedLevel('');
    setModifiedCategory('');
    setModifiedSuggestion('');
  };

  return (
    <div className="card card-padded" style={{ display: 'flex', flexDirection: 'column', gap: 10, border: '2px solid var(--color-warning)', background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 14, fontWeight: 700 }}>✏️ 编辑风险标记</span>
        <button className="btn btn-ghost" style={{ fontSize: 14, padding: '2px 6px' }} onClick={onCancel}>×</button>
      </div>

      {/* Risk Level */}
      <div>
        <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>风险等级</label>
        <select
          value={modifiedLevel}
          onChange={e => setModifiedLevel(e.target.value)}
          style={{ width: '100%', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12, fontFamily: 'inherit' }}
        >
          <option value="">保持不变（{riskLevel === 'HIGH' ? '高风险' : riskLevel === 'MEDIUM' ? '中风险' : '低风险'}）</option>
          {riskLevel === 'HIGH' && <option value="MEDIUM">降级为 中风险</option>}
          {riskLevel === 'HIGH' && <option value="LOW">降级为 低风险</option>}
          {riskLevel === 'MEDIUM' && (
            <>
              <option value="HIGH" disabled style={{ color: '#999' }}>升为高风险（请使用"升级"操作）</option>
              <option value="LOW">降级为 低风险</option>
            </>
          )}
          {riskLevel === 'LOW' && (
            <option value="HIGH" disabled style={{ color: '#999' }}>升为高风险（请使用"升级"操作）</option>
          )}
        </select>
        {riskLevel === 'MEDIUM' && modifiedLevel === 'HIGH' && (
          <span style={{ fontSize: 10, color: 'var(--color-danger)' }}>MEDIUM → HIGH 不可通过编辑实现，请使用"升级"操作</span>
        )}
      </div>

      {/* Risk Category */}
      <div>
        <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>风险类别</label>
        <select
          value={modifiedCategory}
          onChange={e => setModifiedCategory(e.target.value)}
          style={{ width: '100%', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12, fontFamily: 'inherit' }}
        >
          <option value="">保持不变（{riskCategory}）</option>
          <option>合规风险</option>
          <option>财务风险</option>
          <option>法律风险</option>
          <option>数据隐私</option>
          <option>保密义务</option>
          <option>保密期限</option>
          <option>例外情形</option>
          <option>违约救济</option>
          <option>存续条款</option>
          <option>管辖法律</option>
          <option>争议解决</option>
          <option>通知条款</option>
        </select>
      </div>

      {/* Modified Suggestion */}
      <div>
        <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>修改建议措辞</label>
        <textarea
          value={modifiedSuggestion}
          onChange={e => setModifiedSuggestion(e.target.value)}
          rows={2}
          style={{ width: '100%', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12, resize: 'vertical', fontFamily: 'inherit' }}
        />
      </div>

      {/* Comment (required) */}
      <div>
        <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>修改原因（必填，≥10字符）</label>
        <textarea
          value={comment}
          onChange={e => setComment(e.target.value)}
          rows={2}
          placeholder="请说明修改原因..."
          style={{ width: '100%', padding: '6px 10px', borderRadius: 6, border: `1px solid ${isValid ? 'var(--color-success)' : comment.length > 0 ? 'var(--color-danger)' : 'var(--border-color)'}`, fontSize: 12, resize: 'vertical', fontFamily: 'inherit' }}
        />
        <span style={{ fontSize: 10, color: isValid ? 'var(--color-success)' : 'var(--text-muted)' }}>{comment.length}/10 字符</span>
      </div>

      {/* Downgrade explanation (conditional: HIGH → LOW) */}
      {isDowngradeToLow && (
        <div style={{ padding: '8px 12px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6 }}>
          <span style={{ fontSize: 11, color: '#dc2626' }}>
            HIGH → LOW 降级需要充分的降级理由。请确保修改原因中已详细说明降级理由。
          </span>
        </div>
      )}

      {isDowngrade && !isDowngradeToLow && (
        <div style={{ padding: '8px 12px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 6 }}>
          <span style={{ fontSize: 11, color: '#92400e' }}>
            降级操作将变更风险等级，请确保修改原因充分。
          </span>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button className="btn btn-outline" style={{ fontSize: 12 }} onClick={onCancel}>取消</button>
        <button className="btn btn-primary" style={{ fontSize: 12 }} disabled={!isValid} onClick={handleSave}>保存修改</button>
      </div>
    </div>
  );
};
