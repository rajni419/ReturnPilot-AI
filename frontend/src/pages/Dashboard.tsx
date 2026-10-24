import React, { useEffect, useState } from 'react';
import {
  RotateCcw,
  Clock,
  CheckCircle,
  PackageCheck,
  ArrowRight,
  ShieldCheck,
  ShoppingBag,
} from 'lucide-react';

import { api } from '../services/api';
import { ReturnRequest, Order } from '../types';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';

interface DashboardProps {
  onNavigate: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const { showToast } = useToast();

  const loadData = async () => {
    setLoading(true);
    try {
      const [returnsData, ordersData] = await Promise.all([
        api.listReturnRequests({ limit: 10 }),
        api.listOrders(0, 10),
      ]);
      setReturns(returnsData);
      setOrders(ordersData);
    } catch (err: any) {
      showToast(err?.message || 'Failed to fetch dashboard data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSeedDemo = async () => {
    setSeeding(true);
    try {
      const newOrder = await api.seedDemoOrder(user?.email, user?.full_name);
      showToast(`Sample order created: ${newOrder.order_number}`, 'success');
      loadData();
    } catch (err: any) {
      showToast(err?.message || 'Failed to create sample order', 'error');
    } finally {
      setSeeding(false);
    }
  };

  const totalReturns = returns.length;
  const pendingReturns = returns.filter((r) => r.status === 'PENDING').length;
  const approvedReturns = returns.filter((r) => r.status === 'APPROVED').length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Returns
            </span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-brand-600 flex items-center justify-center">
              <RotateCcw className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-2xl font-bold text-slate-900 tracking-tight">{totalReturns}</p>
            )}
            <p className="text-xs text-slate-400 mt-1">Recorded in SQLite database</p>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Pending Review
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-2xl font-bold text-amber-700 tracking-tight">{pendingReturns}</p>
            )}
            <p className="text-xs text-slate-400 mt-1">Awaiting merchant action</p>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Resolved / Approved
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-2xl font-bold text-emerald-700 tracking-tight">{approvedReturns}</p>
            )}
            <p className="text-xs text-slate-400 mt-1">Approved return resolutions</p>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Policy Window
            </span>
            <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
              <PackageCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-2xl font-bold text-slate-900 tracking-tight">7 Days</p>
            <p className="text-xs text-slate-400 mt-1">From order delivery timestamp</p>
          </div>
        </div>
      </div>

      {/* Primary Action Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-8 shadow-md">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-medium text-indigo-200 mb-3 border border-white/10">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-300" />
            <span>Automated Resolution Engine</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            Customer Self-Service Return Portal
          </h2>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            Verify order authenticity, evaluate the 7-day policy window, and submit structured return requests instantly with automated duplicate prevention.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('start-return')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm shadow-sm transition-all hover:shadow-md active:scale-[0.98]"
            >
              <span>Start a Return</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={handleSeedDemo}
              disabled={seeding}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white text-xs sm:text-sm font-medium border border-white/10 transition-colors disabled:opacity-50"
            >
              <ShoppingBag className="w-4 h-4 text-indigo-300" />
              <span>{seeding ? 'Generating Order...' : 'Generate Sample Order for Testing'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Returns Table Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-6 py-4.5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900 text-sm sm:text-base">Recent Return Requests</h3>
            <p className="text-xs text-slate-500 mt-0.5">Most recent customer submissions requiring review</p>
          </div>
          <button
            onClick={() => onNavigate('tracking')}
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition-colors"
          >
            <span>View all</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {loading ? (
          <div className="p-6 space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : returns.length === 0 ? (
          <div className="py-12 px-4 text-center">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
              <RotateCcw className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-slate-900">No Return Requests Found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Start by submitting your first return request or create a sample order to test the pipeline.
            </p>
            <div className="mt-4 flex justify-center gap-2">
              <button
                onClick={() => onNavigate('start-return')}
                className="px-4 py-2 text-xs font-medium rounded-xl bg-brand-600 text-white hover:bg-brand-700 transition-colors"
              >
                Create Return
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/75 border-b border-slate-100 text-slate-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-6">Return Number</th>
                  <th className="py-3 px-6">Order</th>
                  <th className="py-3 px-6">Customer Email</th>
                  <th className="py-3 px-6">SKU</th>
                  <th className="py-3 px-6">Status</th>
                  <th className="py-3 px-6">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {returns.slice(0, 5).map((ret) => (
                  <tr
                    key={ret.id}
                    onClick={() => onNavigate('tracking')}
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                  >
                    <td className="py-3.5 px-6 font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                      {ret.return_number}
                    </td>
                    <td className="py-3.5 px-6 font-medium text-slate-600">{ret.order_number}</td>
                    <td className="py-3.5 px-6 text-slate-500">{ret.customer_email}</td>
                    <td className="py-3.5 px-6 font-mono text-[11px] text-slate-600">{ret.sku}</td>
                    <td className="py-3.5 px-6">
                      <Badge status={ret.status} size="sm" />
                    </td>
                    <td className="py-3.5 px-6 text-slate-400">
                      {new Date(ret.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Available Orders Section */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-slate-900 text-sm sm:text-base">Orders in System</h3>
            <p className="text-xs text-slate-500">Orders available to check for return eligibility</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
            {orders.length} Orders
          </span>
        </div>

        {orders.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No orders found. Click "Generate Sample Order" above to create one.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {orders.slice(0, 6).map((ord) => (
              <div
                key={ord.id}
                className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors text-xs"
              >
                <div className="flex items-center justify-between font-semibold text-slate-900">
                  <span>{ord.order_number}</span>
                  <Badge status={ord.shipping_status} size="sm" />
                </div>
                <p className="text-slate-500 mt-1">{ord.customer_name} ({ord.customer_email})</p>
                <div className="mt-2 text-[11px] text-slate-400">
                  {ord.items.length} items • ${ord.total_amount.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
