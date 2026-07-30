import React from 'react';

interface Props {
  percent: number;
  color?: string;
  label?: string;
}

export const ProgressBar: React.FC<Props> = ({ percent, color = 'var(--color-primary)', label }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '100%' }}>
    {label && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</span>}
    <div className="progress-bar" style={{ width: '100%' }}>
      <div className="progress-bar-fill" style={{ width: `${Math.min(100, Math.max(0, percent))}%`, background: color }} />
    </div>
  </div>
);
