import React from 'react';
import { Menu, Plus, RefreshCw } from 'lucide-react';

interface HeaderProps {
  currentTab: string;
  onNewReturnClick: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  setIsMobileOpen: (open: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onNewReturnClick,
  onRefresh,
  isRefreshing,
  setIsMobileOpen,
}) => {
  const getTabTitle = (tab: string) => {
    switch (tab) {
      case 'dashboard':
        return { title: 'Operations Dashboard', subtitle: 'Overview of return metrics, policy status and recent activity' };
      case 'start-return':
        return { title: 'Start a Return Request', subtitle: 'Verify customer credentials and item eligibility before submission' };
      case 'tracking':
        return { title: 'Return Request Tracking', subtitle: 'Audit, search, and monitor return statuses across orders' };
      default:
        return { title: 'ReturnPilot AI', subtitle: 'E-commerce Return Management' };
    }
  };

  const { title, subtitle } = getTabTitle(currentTab);

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-8 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {/* Mobile menu button */}
        <button
          onClick={() => setIsMobileOpen(true)}
          className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Breadcrumb / Title */}
        <div>
          <h1 className="text-sm sm:text-base font-semibold text-slate-900 tracking-tight leading-none">
            {title}
          </h1>
          <p className="hidden md:block text-xs text-slate-500 mt-1">
            {subtitle}
          </p>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2.5">
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-xl border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors disabled:opacity-50"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-brand-600' : ''}`} />
          </button>
        )}

        {currentTab !== 'start-return' && (
          <button
            onClick={onNewReturnClick}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs sm:text-sm shadow-sm shadow-brand-600/30 transition-all hover:shadow-md hover:shadow-brand-600/20 active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span>Start a Return</span>
          </button>
        )}
      </div>
    </header>
  );
};
