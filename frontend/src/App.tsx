import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate, useParams, useNavigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { ToastProvider } from './context/ToastContext';
import { Dashboard } from './pages/Dashboard';
import { UploadPage } from './pages/UploadPage';
import { ParsingPage } from './pages/ParsingPage';
import { ReviewProgressPage } from './pages/ReviewProgressPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { ReportPage } from './pages/ReportPage';
import { HistoryPage } from './pages/HistoryPage';

// Skeleton loading component
const PageLoading: React.FC = () => (
  <div className="page">
    <div className="page-header">
      <div style={{ width: 200, height: 28, background: 'var(--border-color)', borderRadius: 4, animation: 'pulse 1.5s ease-in-out infinite' }} />
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ width: '100%', height: 120, background: 'var(--border-color)', borderRadius: 8, opacity: 0.5, animation: 'pulse 1.5s ease-in-out infinite' }} />
      <div style={{ width: '80%', height: 200, background: 'var(--border-color)', borderRadius: 8, opacity: 0.3, animation: 'pulse 1.5s ease-in-out infinite' }} />
    </div>
    <style>{`@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }`}</style>
  </div>
);

// Simple 404 page
const NotFoundPage: React.FC = () => (
  <div className="page" style={{ textAlign: 'center', paddingTop: 80 }}>
    <span style={{ fontSize: 64, display: 'block', marginBottom: 16 }}>🔍</span>
    <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>404 — 页面未找到</h1>
    <p style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 24 }}>您访问的页面不存在或已被移除</p>
    <a href="/dashboard" className="btn btn-primary" style={{ textDecoration: 'none' }}>返回工作台</a>
  </div>
);

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <ToastProvider>
        <AppLayout />
      </ToastProvider>
    ),
    errorElement: <NotFoundPage />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'review/new', element: <UploadPage /> },
      { path: 'review/history', element: <HistoryPage /> },
      { path: 'review/:id/parsing', element: <ParsingPage /> },
      { path: 'review/:id/reviewing', element: <ReviewProgressPage /> },
      { path: 'review/:id/workspace', element: <WorkspacePage /> },
      { path: 'review/:id/report', element: <ReportPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);

export const App: React.FC = () => <RouterProvider router={router} fallbackElement={<PageLoading />} />;
