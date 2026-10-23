import React, { useEffect, useState } from 'react';
import { Sparkles, Package, BookOpen, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { Order } from '../types';
import { ChatContainer } from '../components/chat/ChatContainer';

interface AiAdvisorProps {
  onNavigate: (tab: string) => void;
}

export const AiAdvisor: React.FC<AiAdvisorProps> = ({ onNavigate }) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loadingOrders, setLoadingOrders] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchOrders = async () => {
      try {
        const data = await api.getChatOrders();
        if (mounted) setOrders(data);
      } catch {
        // Handled silently
      } finally {
        if (mounted) setLoadingOrders(false);
      }
    };
    fetchOrders();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-[11px] font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Multilingual RAG Intelligence</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
            AI Return & Exchange Advisor
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Explain your issue in English, Hindi, or Hinglish for instant policy verification and automated resolution
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onNavigate('tracking')}
            className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors flex items-center gap-1.5"
          >
            <span>View Return Tracking</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Left Panel: Verified Policies & Quick Orders */}
        <div className="lg:col-span-1 space-y-4">
          {/* Policy Guidelines Summary Card */}
          <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs space-y-3 text-xs">
            <div className="flex items-center gap-2 font-bold text-slate-900">
              <BookOpen className="w-4 h-4 text-brand-600" />
              <span>Return Policy Windows</span>
            </div>
            <ul className="space-y-2 text-slate-600 text-[11px]">
              <li className="flex items-center justify-between py-1 border-b border-slate-100">
                <span>Apparel & Footwear:</span>
                <strong className="text-emerald-700">14 Days</strong>
              </li>
              <li className="flex items-center justify-between py-1 border-b border-slate-100">
                <span>Electronics (Defects):</span>
                <strong className="text-emerald-700">7 Days</strong>
              </li>
              <li className="flex items-center justify-between py-1 border-b border-slate-100">
                <span>Cosmetics & Hygiene:</span>
                <span className="text-slate-500 font-medium">Final Sale / 48h Transit</span>
              </li>
              <li className="flex items-center justify-between py-1 border-b border-slate-100">
                <span>Custom Engravings:</span>
                <span className="text-rose-600 font-medium">Non-Returnable</span>
              </li>
              <li className="flex items-center justify-between py-1">
                <span>Doorstep Pickup:</span>
                <strong className="text-brand-600">Free Reverse Pickup</strong>
              </li>
            </ul>
          </div>

          {/* Quick Order Selector Card */}
          <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-slate-900">
                <Package className="w-4 h-4 text-slate-600" />
                <span>Your Orders</span>
              </div>
              <span className="text-[10px] rounded-full bg-slate-100 px-2 py-0.5 font-bold text-slate-600">
                {orders.length}
              </span>
            </div>

            {loadingOrders ? (
              <div className="py-4 text-center text-slate-400 text-xs animate-pulse">
                Loading order history...
              </div>
            ) : orders.length === 0 ? (
              <p className="text-slate-400 text-[11px]">No delivered orders found.</p>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {orders.map((o) => (
                  <div
                    key={o.order_number}
                    className="p-2.5 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-brand-50/30 hover:border-brand-200 transition-colors"
                  >
                    <div className="flex items-center justify-between text-[11px] font-bold text-slate-900 mb-0.5">
                      <span className="font-mono">{o.order_number}</span>
                      <span className="text-emerald-700 font-semibold text-[10px]">
                        {o.shipping_status}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 truncate">
                      {o.items?.map((it) => it.product_name).join(', ')}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right / Center: Unified Chat Container */}
        <div className="lg:col-span-3">
          <ChatContainer onNavigateTab={onNavigate} />
        </div>
      </div>
    </div>
  );
};
