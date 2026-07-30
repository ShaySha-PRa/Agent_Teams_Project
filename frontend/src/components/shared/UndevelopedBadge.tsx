import React from 'react';

interface Props {
  endpoint?: string;
}

export const UndevelopedBadge: React.FC<Props> = ({ endpoint }) => (
  <span className="undeveloped-badge" title={endpoint ? `${endpoint} — 未开发` : undefined}>
    ⚠️ 未开发
  </span>
);
