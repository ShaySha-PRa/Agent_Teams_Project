import React, { useState } from 'react';

interface Props {
  visible: boolean;
  documentId: string;
  position: { x: number; y: number };
  onClose: () => void;
  onSubmit: (data: { risk_level: string; risk_category: string; description: string; clause_text: string; page: number; para: number }) => void;
}

export const ManualFlagForm: React.FC<Props> = ({ visible, documentId, position, onClose, onSubmit }) => {
  const [level, setLevel] = useState('HIGH');
  const [category, setCategory] = useState('合规风险');
  const [description, setDescription] = useState('');
  const [clauseText, setClauseText] = useState('');
  const [page, setPage] = useState(1);
  const [para, setPara] = useState(1);

  if (!visible) return null;

  const handleSubmit = () => {
    if (description.length < 10) return;
    onSubmit({
      risk_level: level,
      risk_category: category,
      description,
      clause_text: clauseText,
      page,
      para,
    });
  };

  return (
    <div style={{ position: 'fixed', left: position.x, top: position.y, zIndex: 500, background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, padding: 14, width: 340, display: 'flex', flexDirection: 'column', gap: 10, boxShadow: '0 4px 12px rgba(0,0,0,0.12)' }}>
      <div style={{ fontSize: 13, fontWeight: 600 }}>手动补充标记</div>
      <div style={{ display: 'flex', gap: 8 }}>
        <select value={level} onChange={e => setLevel(e.target.value)} style={{ flex: 1, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }}>
          <option value="HIGH">高风险</option><option value="MEDIUM">中风险</option><option value="LOW">低风险</option>
        </select>
        <select value={category} onChange={e => setCategory(e.target.value)} style={{ flex: 1, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }}>
          <option>合规风险</option><option>财务风险</option><option>法律风险</option><option>数据隐私</option>
          <option>保密义务</option><option>保密期限</option><option>违约救济</option>
        </select>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input type="number" value={page} onChange={e => setPage(parseInt(e.target.value) || 1)} placeholder="页码" style={{ width: 80, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }} />
        <input type="number" value={para} onChange={e => setPara(parseInt(e.target.value) || 1)} placeholder="段落" style={{ width: 80, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }} />
        <input value={clauseText} onChange={e => setClauseText(e.target.value)} placeholder="条款原文 (可选)" style={{ flex: 1, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }} />
      </div>
      <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="说明 (≥10字符)" rows={3}
        style={{ padding: 8, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12, resize: 'vertical', fontFamily: 'inherit' }} />
      <span style={{ fontSize: 10, color: description.length >= 10 ? 'var(--color-success)' : 'var(--text-muted)' }}>{description.length}/10 字符</span>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button className="btn btn-ghost" onClick={onClose} style={{ fontSize: 12 }}>取消</button>
        <button className="btn btn-primary" disabled={description.length < 10} onClick={handleSubmit} style={{ fontSize: 12 }}>提交标记</button>
      </div>
    </div>
  );
};
