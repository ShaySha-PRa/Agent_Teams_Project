import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { UploadPage } from './pages/UploadPage';
import { ParsingPage } from './pages/ParsingPage';
import { ReviewProgressPage } from './pages/ReviewProgressPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { ReportPage } from './pages/ReportPage';
import { HistoryPage } from './pages/HistoryPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'review/new', element: <UploadPage /> },
      { path: 'review/history', element: <HistoryPage /> },
      { path: 'review/:id/parsing', element: <ParsingPage /> },
      { path: 'review/:id/reviewing', element: <ReviewProgressPage /> },
      { path: 'review/:id/workspace', element: <WorkspacePage /> },
      { path: 'review/:id/report', element: <ReportPage /> },
    ],
  },
]);

export const App: React.FC = () => <RouterProvider router={router} />;
