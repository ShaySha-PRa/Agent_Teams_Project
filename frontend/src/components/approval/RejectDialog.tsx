import React, { useState } from 'react';

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (reason: string) => void;
}

export const RejectDialog: React.FC<Props> = ({ open, onClose, onSubmit }) => {
  const [reason, setReason] = useState('');
  if (!open) return null;
  const isValid = reason.trim().length >= 10;
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: 'var(--bg-card)', borderRadius: 8, padding: 24, width: 420, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700 }}>驳回 AI 标记</h3>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>请填写驳回原因（至少 10 个字符）</p>
        <textarea value={reason} onChange={e => setReason(e.target.value)} placeholder="填写驳回原因..." rows={4}
          style={{ padding: 10, borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 13, resize: 'vertical', fontFamily: 'inherit' }} />
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button className="btn btn-outline" onClick={onClose}>取消</button>
          <button className="btn btn-danger" disabled={!isValid} onClick={() => { onSubmit(reason); setReason(''); }}>确认驳回</button>
        </div>
      </div>
    </div>
  );
};
