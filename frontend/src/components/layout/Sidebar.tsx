import React, { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  RotateCcw,
  Search,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { api } from '../../services/api';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  isMobileOpen,
  setIsMobileOpen,
}) => {
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const checkBackend = async () => {
      try {
        const res = await api.getHealth();
        if (mounted) setIsBackendHealthy(res.status === 'healthy');
      } catch {
        if (mounted) setIsBackendHealthy(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      badge: undefined,
    },
    {
      id: 'start-return',
      label: 'Start a Return',
      icon: RotateCcw,
      badge: 'Action',
    },
    {
      id: 'tracking',
      label: 'Return Tracking',
      icon: Search,
      badge: undefined,
    },
  ];

  const handleNavClick = (id: string) => {
    setCurrentTab(id);
    setIsMobileOpen(false);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-white border-r border-slate-200/80 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center text-white shadow-sm shadow-brand-500/30">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-slate-900 block leading-tight">
              ReturnPilot<span className="text-brand-600">.ai</span>
            </span>
            <span className="text-[11px] font-medium text-slate-400 block tracking-wide uppercase">
              Resolution Suite
            </span>
          </div>
        </div>

        {/* Navigation list */}
        <div className="flex-1 px-3 py-6 space-y-1">
          <p className="px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase mb-2">
            Workspace
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 group relative ${
                  isActive
                    ? 'bg-brand-50/80 text-brand-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-brand-600' : 'text-slate-400 group-hover:text-slate-600'
                  }`}
                />
                <span className="flex-1 text-left">{item.label}</span>
                {item.badge && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-brand-100 text-brand-700">
                    {item.badge}
                  </span>
                )}
                {isActive && (
                  <span className="absolute left-0 top-2 bottom-2 w-1 bg-brand-600 rounded-r" />
                )}
              </button>
            );
          })}
        </div>

        {/* System & Documentation Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/40 space-y-3">
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between text-xs font-medium text-slate-500 hover:text-brand-600 transition-colors p-2 rounded-lg hover:bg-slate-100/70"
          >
            <span>FastAPI OpenAPI Docs</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          {/* Backend Health Badge */}
          <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-white border border-slate-200/80 shadow-xs text-xs">
            <span className="text-slate-500 font-medium">FastAPI Engine</span>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isBackendHealthy === null
                    ? 'bg-slate-300'
                    : isBackendHealthy
                    ? 'bg-emerald-500 animate-pulse'
                    : 'bg-rose-500'
                }`}
              />
              <span
                className={`font-semibold ${
                  isBackendHealthy === null
                    ? 'text-slate-400'
                    : isBackendHealthy
                    ? 'text-emerald-700'
                    : 'text-rose-600'
                }`}
              >
                {isBackendHealthy === null
                  ? 'Checking...'
                  : isBackendHealthy
                  ? 'Online'
                  : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
