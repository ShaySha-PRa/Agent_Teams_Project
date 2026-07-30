import React from 'react';

interface Props {
  confidence: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
}

export const ConfidenceRing: React.FC<Props> = ({ confidence, size = 48, strokeWidth = 4, showLabel = true }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const dash = confidence * circumference;
  const color = confidence >= 0.8 ? 'var(--color-success)' : confidence >= 0.6 ? 'var(--color-warning)' : 'var(--color-danger)';

  return (
    <div style={{ position: 'relative', width: size, height: size, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--border-color)" strokeWidth={strokeWidth} />
        <circle
          cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeDasharray={`${dash} ${circumference - dash}`} strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.5s ease' }}
        />
      </svg>
      {showLabel && (
        <span style={{ position: 'absolute', fontSize: Math.max(10, size / 5), fontWeight: 700, color, fontFamily: 'var(--font-mono)' }}>
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
};
