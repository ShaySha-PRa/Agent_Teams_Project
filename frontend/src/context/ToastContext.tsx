import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

type ToastType = 'success' | 'warning' | 'error' | 'info';

interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
  action?: { label: string; onClick: () => void };
  duration?: number;
}

interface ToastContextValue {
  show: (type: ToastType, message: string, opts?: { action?: { label: string; onClick: () => void }; duration?: number }) => void;
}

const ToastContext = createContext<ToastContextValue>({ show: () => {} });

export const useToast = () => useContext(ToastContext);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const counterRef = useRef(0);

  const show = useCallback((type: ToastType, message: string, opts?: { action?: { label: string; onClick: () => void }; duration?: number }) => {
    const id = `toast_${++counterRef.current}`;
    const duration = opts?.duration ?? (type === 'error' || type === 'warning' ? 5000 : 3000);
    const item: ToastItem = { id, type, message, action: opts?.action, duration };
    setToasts(prev => [...prev, item]);

    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const icons: Record<ToastType, string> = { success: '✅', warning: '⚠️', error: '❌', info: 'ℹ️' };
  const colors: Record<ToastType, string> = {
    success: 'var(--color-success)',
    warning: 'var(--color-warning)',
    error: 'var(--color-danger)',
    info: 'var(--color-primary)',
  };
  const backgrounds: Record<ToastType, string> = {
    success: '#f0fdf4',
    warning: '#fffbeb',
    error: '#fef2f2',
    info: '#eff6ff',
  };

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      {/* Toast Container */}
      <div style={{
        position: 'fixed', top: 20, right: 20, zIndex: 10000,
        display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 400,
        pointerEvents: 'none',
      }}>
        {toasts.map(t => (
          <div
            key={t.id}
            style={{
              pointerEvents: 'auto',
              display: 'flex', alignItems: 'flex-start', gap: 10,
              padding: '12px 16px',
              background: backgrounds[t.type],
              border: `1px solid ${colors[t.type]}`,
              borderRadius: 8,
              color: colors[t.type],
              fontSize: 13,
              fontWeight: 500,
              boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
              animation: 'slideInRight 0.3s ease',
              position: 'relative',
            }}
          >
            <span style={{ fontSize: 16, flexShrink: 0 }}>{icons[t.type]}</span>
            <div style={{ flex: 1 }}>
              <span>{t.message}</span>
              {t.action && (
                <div style={{ marginTop: 6 }}>
                  <button
                    className="btn btn-ghost"
                    style={{ fontSize: 11, padding: '2px 8px', color: colors[t.type], border: `1px solid ${colors[t.type]}`, borderRadius: 4, cursor: 'pointer' }}
                    onClick={t.action.onClick}
                  >
                    {t.action.label}
                  </button>
                </div>
              )}
            </div>
            <button
              style={{ background: 'none', border: 'none', color: colors[t.type], cursor: 'pointer', fontSize: 14, padding: 0, lineHeight: 1 }}
              onClick={() => setToasts(prev => prev.filter(to => to.id !== t.id))}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      {/* Keyframe style */}
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </ToastContext.Provider>
  );
};
