import React from 'react';

interface DiffItem { field: string; standard_value: string; actual_value: string; deviation_type: string; }

interface Props { standardText: string; actualText: string; diffItems: DiffItem[]; }

export const PlaybookDiff: React.FC<Props> = ({ standardText, actualText, diffItems }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>Playbook 对比</div>
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
      <div style={{ padding: 8, background: '#f0faf0', borderRadius: 6, fontSize: 11 }}><strong>标准条款:</strong><br/>{standardText}</div>
      <div style={{ padding: 8, background: '#fff0f0', borderRadius: 6, fontSize: 11 }}><strong>实际条款:</strong><br/>{actualText}</div>
    </div>
    {diffItems.length > 0 && (
      <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
        {diffItems.map((d, i) => <div key={i}>{d.field}: {d.standard_value} to {d.actual_value} [{d.deviation_type}]</div>)}
      </div>
    )}
  </div>
);
