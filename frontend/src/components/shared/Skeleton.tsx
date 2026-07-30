import React from 'react';

const SKELETON = {
  background: 'linear-gradient(90deg, var(--border-color) 25%, #e8eaed 50%, var(--border-color) 75%)',
  backgroundSize: '200% 100%',
  animation: 'skeleton 1.5s ease-in-out infinite',
  borderRadius: 6,
};

const styleTag = `
@keyframes skeleton {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}`;

export const SkeletonText: React.FC<{ width?: string | number; lines?: number; fontSize?: number }> = ({ width = '100%', lines = 1, fontSize = 13 }) => (
  <>
    <style>{styleTag}</style>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} style={{ ...SKELETON, width: typeof width === 'number' ? width : i === lines - 1 ? '60%' : width, height: fontSize * 1.5, opacity: 1 - i * 0.1 }} />
      ))}
    </div>
  </>
);

export const SkeletonCard: React.FC<{ lines?: number }> = ({ lines = 4 }) => (
  <>
    <style>{styleTag}</style>
    <div className="card card-padded" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ ...SKELETON, width: '40%', height: 16 }} />
      <SkeletonText lines={lines} />
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <div style={{ ...SKELETON, width: 60, height: 32, borderRadius: 6 }} />
        <div style={{ ...SKELETON, width: 60, height: 32, borderRadius: 6 }} />
      </div>
    </div>
  </>
);

export const SkeletonRow: React.FC<{ cols?: number }> = ({ cols = 5 }) => (
  <>
    <style>{styleTag}</style>
    <div style={{ display: 'flex', gap: 16, padding: '10px 20px', borderBottom: '1px solid var(--border-color)' }}>
      {Array.from({ length: cols }).map((_, i) => (
        <div key={i} style={{ ...SKELETON, flex: 1, height: 14, opacity: 1 - i * 0.1 }} />
      ))}
    </div>
  </>
);

export const SkeletonStatCards: React.FC = () => (
  <>
    <style>{styleTag}</style>
    <div style={{ display: 'flex', gap: 16 }}>
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="card card-padded" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ ...SKELETON, width: '60%', height: 12 }} />
          <div style={{ ...SKELETON, width: '40%', height: 28 }} />
        </div>
      ))}
    </div>
  </>
);
