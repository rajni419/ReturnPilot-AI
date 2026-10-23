
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';

import './index.css';

import { ToastProvider } from './context/ToastContext';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { StartReturn } from './pages/StartReturn';

const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState('dashboard');

  const renderPage = () => {
    switch (currentTab) {
      case 'dashboard':
        return (
          <Dashboard
            onNavigate={setCurrentTab}
          />
        );

      case 'start-return':
        return (
          <StartReturn
            onSuccessNavigate={setCurrentTab}
          />
        );

      case 'tracking':
        return (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="text-xl font-bold text-slate-900">
              Return Tracking
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Return tracking page integration is the next step.
            </p>
          </div>
        );

      default:
        return (
          <Dashboard
            onNavigate={setCurrentTab}
          />
        );
    }
  };

  return (
    <ToastProvider>
      <Layout
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
      >
        {renderPage()}
      </Layout>
    </ToastProvider>
  );
};

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found in index.html');
}

createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
