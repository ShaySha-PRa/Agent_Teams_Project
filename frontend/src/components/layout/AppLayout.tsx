import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export const AppLayout: React.FC = () => (
  <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
    <Sidebar />
    <main style={{ flex: 1, overflowY: 'auto', minWidth: 0 }}>
      <Outlet />
    </main>
  </div>
);
