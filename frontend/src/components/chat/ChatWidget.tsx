import React, { useState } from 'react';
import { Sparkles, X, Maximize2 } from 'lucide-react';
import { ChatContainer } from './ChatContainer';

interface ChatWidgetProps {
  onNavigateTab: (tab: string) => void;
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({ onNavigateTab }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-40 flex flex-col items-end">
      {/* Widget Popover Panel */}
      {isOpen && (
        <div className="mb-3 w-[360px] sm:w-[420px] rounded-2xl shadow-2xl overflow-hidden border border-slate-200/90 animate-in fade-in slide-in-from-bottom-5 duration-200 bg-white">
          <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 text-white">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-400" />
              <span className="font-semibold text-xs tracking-tight">ReturnPilot AI Assistant</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  onNavigateTab('advisor');
                }}
                title="Open Dedicated Fullscreen Advisor"
                className="p-1 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <ChatContainer isWidget={true} onNavigateTab={onNavigateTab} />
        </div>
      )}

      {/* Floating Action Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="group flex items-center gap-2 px-4 py-3 rounded-full bg-slate-900 hover:bg-brand-600 text-white shadow-lg shadow-slate-900/20 hover:shadow-brand-600/30 transition-all duration-200 cursor-pointer active:scale-95"
      >
        <div className="relative">
          <Sparkles className="w-5 h-5 text-brand-400 group-hover:text-white transition-colors animate-pulse" />
          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400" />
        </div>
        <span className="font-semibold text-xs pr-1">
          {isOpen ? 'Close Assistant' : 'Ask AI Return Advisor'}
        </span>
      </button>
    </div>
  );
};
