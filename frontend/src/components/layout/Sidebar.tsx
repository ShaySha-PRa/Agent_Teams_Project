import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/dashboard', icon: '📊', label: '工作台' },
  { to: '/review/history', icon: '📋', label: '历史审阅' },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <aside style={{
      width: 240, height: '100vh', background: '#0d1117',
      display: 'flex', flexDirection: 'column', padding: 24, gap: 24,
      flexShrink: 0, overflowY: 'auto',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 28, height: 28, borderRadius: 6, background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 16 }}>N</div>
        <span style={{ color: '#c9d1d9', fontSize: 16, fontWeight: 600 }}>NDA Review</span>
      </div>
      <div style={{ height: 1, background: '#21262d', flexShrink: 0 }} />
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV_ITEMS.map(item => {
          const isActive = location.pathname.startsWith(item.to);
          return (
            <NavLink key={item.to} to={item.to} style={{
              display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px',
              borderRadius: 6, textDecoration: 'none', fontSize: 14, fontWeight: 500,
              background: isActive ? 'rgba(47, 129, 247, 0.15)' : 'transparent',
              color: isActive ? '#ffffff' : '#8b949e',
            }}>
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
      <div style={{ flex: 1 }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingTop: 12, borderTop: '1px solid #21262d' }}>
        <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#30363d' }} />
        <span style={{ color: '#c9d1d9', fontSize: 13 }}>企业法务</span>
      </div>
    </aside>
  );
};
