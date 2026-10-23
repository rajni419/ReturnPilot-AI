import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Sparkles } from 'lucide-react';

import './index.css';

import { ToastProvider } from './context/ToastContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { StartReturn } from './pages/StartReturn';
import { ReturnTracking } from './pages/ReturnTracking';

import { SignIn } from './pages/auth/SignIn';
import { SignUp } from './pages/auth/SignUp';
import { VerifyEmail } from './pages/auth/VerifyEmail';
import { ForgotPassword } from './pages/auth/ForgotPassword';
import { ResetPassword } from './pages/auth/ResetPassword';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<'dashboard' | 'start-return' | 'tracking'>('dashboard');
  const [authView, setAuthView] = useState<
    'signin' | 'signup' | 'verify-email' | 'forgot-password' | 'reset-password'
  >('signin');
  const [authEmail, setAuthEmail] = useState<string>('');

  const handleNavigateAuth = (view: string, email?: string) => {
    if (email !== undefined) {
      setAuthEmail(email);
    }
    setAuthView(view as any);
  };

  // Loading state while verifying token or restoring session
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-brand-500/25 mb-4 animate-bounce">
          <Sparkles className="w-6 h-6" />
        </div>
        <p className="text-sm font-semibold text-slate-700 tracking-tight">
          Securing ReturnPilot AI Session...
        </p>
        <p className="text-xs text-slate-400 mt-1">Verifying cryptographic credentials</p>
      </div>
    );
  }

  // Unauthenticated / Auth views
  if (!isAuthenticated) {
    switch (authView) {
      case 'signup':
        return <SignUp onNavigate={handleNavigateAuth} />;
      case 'verify-email':
        return <VerifyEmail onNavigate={handleNavigateAuth} initialEmail={authEmail} />;
      case 'forgot-password':
        return <ForgotPassword onNavigate={handleNavigateAuth} initialEmail={authEmail} />;
      case 'reset-password':
        return <ResetPassword onNavigate={handleNavigateAuth} initialEmail={authEmail} />;
      case 'signin':
      default:
        return <SignIn onNavigate={handleNavigateAuth} initialEmail={authEmail} />;
    }
  }

  // Authenticated workspace views
  const renderPage = () => {
    switch (currentTab) {
      case 'dashboard':
        return <Dashboard onNavigate={(tab) => setCurrentTab(tab as any)} />;
      case 'start-return':
        return <StartReturn onSuccessNavigate={(tab) => setCurrentTab(tab as any)} />;
      case 'tracking':
        return <ReturnTracking />;
      default:
        return <Dashboard onNavigate={(tab) => setCurrentTab(tab as any)} />;
    }
  };

  return (
    <Layout currentTab={currentTab} setCurrentTab={(tab) => setCurrentTab(tab as any)}>
      {renderPage()}
    </Layout>
  );
};

export const App: React.FC = () => {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
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
