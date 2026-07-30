import React from 'react';

interface Props {
  onApprove: () => void;
  onEdit: () => void;
  onReject: () => void;
  disabled?: boolean;
}

export const ActionBar: React.FC<Props> = ({ onApprove, onEdit, onReject, disabled = false }) => (
  <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
    <button className="btn btn-success" disabled={disabled} onClick={onApprove}>同意</button>
    <button className="btn btn-outline" disabled={disabled} onClick={onEdit}>编辑</button>
    <button className="btn btn-danger" disabled={disabled} onClick={onReject}>驳回</button>
  </div>
);
