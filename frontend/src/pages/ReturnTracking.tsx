import React, { useEffect, useState } from 'react';
import {
  Search,
  RefreshCw,
  Package,
  CalendarDays,
  Mail,
  ArrowUpRight,
  RotateCcw,
  X,
} from 'lucide-react';

import { api } from '../services/api';
import { ReturnRequest } from '../types';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';

const statusStyles: Record<string, string> = {
  PENDING: 'bg-amber-50 text-amber-700 border-amber-200',
  APPROVED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  REJECTED: 'bg-rose-50 text-rose-700 border-rose-200',
  PROCESSING: 'bg-blue-50 text-blue-700 border-blue-200',
};

export const ReturnTracking: React.FC = () => {
  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('ALL');
  const [selected, setSelected] = useState<ReturnRequest | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const { showToast } = useToast();

  const loadReturns = async (refresh = false) => {
    if (refresh) setRefreshing(true);
    else setLoading(true);

    try {
      const data = await api.listReturnRequests({ limit: 100 });
      setReturns(data);
    } catch (error: any) {
      showToast(error?.message || 'Could not load return requests.', 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadReturns();
  }, []);

  const filteredReturns = returns.filter((item) => {
    const query = search.trim().toLowerCase();

    const matchesSearch =
      !query ||
      item.return_number.toLowerCase().includes(query) ||
      item.order_number.toLowerCase().includes(query) ||
      item.customer_email.toLowerCase().includes(query) ||
      item.sku.toLowerCase().includes(query);

    const matchesStatus = status === 'ALL' || item.status === status;

    return matchesSearch && matchesStatus;
  });

  const counts = {
    total: returns.length,
    pending: returns.filter((r) => r.status === 'PENDING').length,
    processing: returns.filter((r) => r.status === 'PROCESSING').length,
    resolved: returns.filter(
      (r) => r.status === 'APPROVED' || r.status === 'REJECTED'
    ).length,
  };

  const formatDate = (value: string) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? '—'
      : date.toLocaleDateString('en-IN', {
          day: '2-digit',
          month: 'short',
          year: 'numeric',
        });
  };

  return (
    <div className="space-y-7 animate-fade-in">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-600">
            Returns management
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
            Return Tracking
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Search requests, review their status and inspect return details.
          </p>
        </div>

        <button
          onClick={() => loadReturns(true)}
          disabled={refreshing}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-60"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: 'Total requests', value: counts.total, color: 'text-slate-900' },
          { label: 'Pending review', value: counts.pending, color: 'text-amber-600' },
          { label: 'Processing', value: counts.processing, color: 'text-blue-600' },
          { label: 'Resolved', value: counts.resolved, color: 'text-emerald-600' },
        ].map((metric) => (
          <div
            key={metric.label}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <p className="text-sm font-medium text-slate-500">{metric.label}</p>
            <p className={`mt-3 text-3xl font-bold ${metric.color}`}>
              {loading ? '—' : metric.value}
            </p>
          </div>
        ))}
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 p-5 sm:p-6">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="font-bold text-slate-900">All return requests</h2>
              <p className="mt-1 text-sm text-slate-500">
                Showing {filteredReturns.length} of {returns.length} loaded requests
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search return, order, email, SKU"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-brand-400 focus:bg-white focus:ring-4 focus:ring-brand-100 sm:w-72"
                />
              </div>

              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
              >
                <option value="ALL">All statuses</option>
                <option value="PENDING">Pending</option>
                <option value="APPROVED">Approved</option>
                <option value="PROCESSING">Processing</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-6 py-4 font-semibold">Return request</th>
                <th className="px-6 py-4 font-semibold">Order / SKU</th>
                <th className="px-6 py-4 font-semibold">Customer</th>
                <th className="px-6 py-4 font-semibold">Submitted</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 text-right font-semibold">Details</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 6 }).map((__, j) => (
                      <td key={j} className="px-6 py-5">
                        <Skeleton className="h-4 w-24" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : filteredReturns.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
                      <Package className="h-6 w-6" />
                    </div>
                    <p className="mt-4 font-semibold text-slate-800">
                      No matching return requests
                    </p>
                    <p className="mt-1 text-sm text-slate-500">
                      Try another search or status filter.
                    </p>
                    {(search || status !== 'ALL') && (
                      <button
                        onClick={() => {
                          setSearch('');
                          setStatus('ALL');
                        }}
                        className="mt-3 text-sm font-semibold text-brand-600 hover:text-brand-700"
                      >
                        Clear filters
                      </button>
                    )}
                  </td>
                </tr>
              ) : (
                filteredReturns.map((item) => (
                  <tr key={item.id} className="transition hover:bg-slate-50/80">
                    <td className="px-6 py-4">
                      <p className="font-semibold text-slate-900">{item.return_number}</p>
                      <p className="mt-1 text-xs text-slate-400">ID: {item.id}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-800">{item.order_number}</p>
                      <p className="mt-1 font-mono text-xs text-slate-500">{item.sku}</p>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-slate-600">
                        <Mail className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                        <span>{item.customer_email}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      <span className="inline-flex items-center gap-2">
                        <CalendarDays className="h-4 w-4 text-slate-400" />
                        {formatDate(item.created_at)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${
                          statusStyles[item.status] ||
                          'border-slate-200 bg-slate-50 text-slate-600'
                        }`}
                      >
                        <span className="mr-1.5">●</span>
                        {item.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelected(item)}
                        className="inline-flex items-center gap-1 rounded-lg px-3 py-2 font-semibold text-brand-600 transition hover:bg-brand-50"
                      >
                        View <ArrowUpRight className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setSelected(null);
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="return-detail-title"
            className="w-full max-w-xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
          >
            <header className="flex items-start justify-between border-b border-slate-100 p-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">
                  Return details
                </p>
                <h2 id="return-detail-title" className="mt-2 text-xl font-bold text-slate-900">
                  {selected.return_number}
                </h2>
              </div>
              <button
                aria-label="Close details"
                onClick={() => setSelected(null)}
                className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </header>

            <div className="space-y-5 p-6">
              <div className="flex items-center justify-between rounded-xl bg-slate-50 p-4">
                <div>
                  <p className="text-xs text-slate-500">Current status</p>
                  <p className="mt-1 font-semibold text-slate-900">{selected.status}</p>
                </div>
                <RotateCcw className="h-5 w-5 text-brand-600" />
              </div>

              {[
                ['Order number', selected.order_number],
                ['Customer email', selected.customer_email],
                ['SKU', selected.sku],
                ['Return reason', selected.return_reason],
                ['Created on', formatDate(selected.created_at)],
                ['Last updated', formatDate(selected.updated_at)],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex flex-col gap-1 border-b border-slate-100 pb-3 sm:flex-row sm:items-start sm:justify-between"
                >
                  <span className="text-sm text-slate-500">{label}</span>
                  <span className="max-w-sm break-words text-sm font-medium text-slate-800 sm:text-right">
                    {value}
                  </span>
                </div>
              ))}
            </div>

            <footer className="border-t border-slate-100 bg-slate-50 px-6 py-4 text-right">
              <button
                onClick={() => setSelected(null)}
                className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
              >
                Close
              </button>
            </footer>
          </section>
        </div>
      )}
    </div>
  );
};
