import React from 'react';

interface Props {
  level: 'HIGH' | 'MEDIUM' | 'LOW';
  count?: number;
}

export const RiskBadge: React.FC<Props> = ({ level, count }) => {
  const config: Record<string, { icon: string; label: string }> = {
    HIGH: { icon: '🔴', label: '高风险' },
    MEDIUM: { icon: '🟡', label: '中风险' },
    LOW: { icon: '🟢', label: '低风险' },
  };
  const c = config[level];
  const text = count !== undefined ? `${c.icon} ${c.label} ${count}项` : `${c.icon} ${c.label}`;
  return <span className={`risk-badge risk-badge-${level.toLowerCase()}`}>{text}</span>;
};
