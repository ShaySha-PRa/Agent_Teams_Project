import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/dashboard', icon: '📊', label: '工作台' },
  { to: '/review/history', icon: '📋', label: '历史审阅' },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const [darkMode, setDarkMode] = React.useState(() => localStorage.getItem('theme') !== 'light');

  const toggleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    document.documentElement.setAttribute('data-theme', next ? 'dark' : 'light');
    localStorage.setItem('theme', next ? 'dark' : 'light');
  };

  return (
    <aside style={{
      width: 240, height: '100vh', background: 'var(--sidebar-bg)',
      display: 'flex', flexDirection: 'column', padding: 24, gap: 24,
      flexShrink: 0, overflowY: 'auto',
      transition: 'background 0.3s ease',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 28, height: 28, borderRadius: 6, background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 16 }}>N</div>
        <span style={{ color: 'var(--sidebar-text)', fontSize: 16, fontWeight: 600 }}>NDA Review</span>
      </div>
      <div style={{ height: 1, background: 'var(--sidebar-divider)', flexShrink: 0 }} />
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV_ITEMS.map(item => {
          const isActive = location.pathname.startsWith(item.to);
          return (
            <NavLink key={item.to} to={item.to} style={{
              display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px',
              borderRadius: 6, textDecoration: 'none', fontSize: 14, fontWeight: 500,
              background: isActive ? 'var(--sidebar-active)' : 'transparent',
              color: isActive ? 'var(--sidebar-text-active)' : 'var(--sidebar-text)',
              transition: 'background 0.15s ease',
            }}>
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
      <div style={{ flex: 1 }} />
      {/* Dark mode toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0' }}>
        <button
          onClick={toggleTheme}
          style={{
            width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
            background: darkMode ? 'var(--color-primary)' : 'var(--border-color)',
            position: 'relative', transition: 'background 0.3s ease',
            padding: 0,
          }}
          title={darkMode ? '切换到浅色模式' : '切换到深色模式'}
        >
          <span style={{
            position: 'absolute', top: 2, left: darkMode ? 22 : 2,
            width: 20, height: 20, borderRadius: '50%', background: '#fff',
            transition: 'left 0.3s ease', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
          }} />
        </button>
        <span style={{ color: 'var(--sidebar-text)', fontSize: 12 }}>
          {darkMode ? '🌙 深色' : '☀️ 浅色'}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingTop: 12, borderTop: '1px solid var(--sidebar-divider)' }}>
        <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--avatar-bg)' }} />
        <span style={{ color: 'var(--sidebar-text)', fontSize: 13 }}>企业法务</span>
      </div>
    </aside>
  );
};
