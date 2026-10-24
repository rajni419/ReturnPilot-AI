import React from 'react';
import { Package, ArrowRight, CheckCircle2, ShieldAlert } from 'lucide-react';

interface OrderCardProps {
  orders: any[];
  onSelectItem: (orderNumber: string, sku: string, productName: string) => void;
}

export const OrderCard: React.FC<OrderCardProps> = ({ orders, onSelectItem }) => {
  if (!orders || orders.length === 0) return null;

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Your Recent Orders ({orders.length})
        </p>
        <span className="text-[11px] text-slate-400">Click an item to check return eligibility</span>
      </div>

      <div className="space-y-3">
        {orders.map((order) => (
          <div
            key={order.order_number}
            className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs hover:border-slate-300 transition-all"
          >
            {/* Order Meta Header */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2.5 mb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-brand-50 text-brand-600">
                  <Package className="h-4 w-4" />
                </div>
                <div>
                  <span className="font-mono text-xs font-bold text-slate-900 block leading-tight">
                    {order.order_number}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    Delivered on: {order.delivery_date || 'Recently'}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="rounded-full bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-700">
                  {order.shipping_status || 'DELIVERED'}
                </span>
                <span className="text-xs font-bold text-slate-900">
                  ${Number(order.total_amount).toFixed(2)}
                </span>
              </div>
            </div>

            {/* Line items list */}
            <div className="space-y-2">
              {order.items?.map((item: any, idx: number) => (
                <div
                  key={idx}
                  className={`p-2.5 rounded-xl border text-xs transition-colors ${
                    item.is_returnable
                      ? 'bg-slate-50 border-slate-100'
                      : 'bg-amber-50/40 border-amber-200/60'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-slate-800 truncate leading-snug">
                        {item.product_name}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5 text-[11px] text-slate-500">
                        <span className="font-mono">SKU: {item.sku}</span>
                        <span>&bull;</span>
                        <span>Qty: {item.quantity}</span>
                        <span>&bull;</span>
                        <span className="font-medium text-slate-700">${Number(item.price).toFixed(2)}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.is_returnable ? (
                        <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 font-medium">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Returnable</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10px] text-amber-700 font-semibold px-2 py-0.5 rounded-md bg-amber-100/70 border border-amber-300">
                          <ShieldAlert className="h-3 w-3 text-amber-600" />
                          <span>Final Sale</span>
                        </span>
                      )}

                      {item.is_returnable ? (
                        <button
                          type="button"
                          onClick={() => onSelectItem(order.order_number, item.sku, item.product_name)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs shadow-xs transition-colors"
                        >
                          <span>Select Item</span>
                          <ArrowRight className="h-3 w-3" />
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => onSelectItem(order.order_number, item.sku, item.product_name)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-amber-100/80 hover:bg-amber-200/80 text-amber-900 border border-amber-300 font-medium text-xs shadow-2xs transition-colors"
                          title="Final Sale item: standard returns prohibited per Policy CUS-05. Click to check transit damage or defect exceptions."
                        >
                          <ShieldAlert className="h-3.5 w-3.5 text-amber-700" />
                          <span>Report Damage</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {!item.is_returnable && (
                    <div className="mt-1.5 pt-1.5 border-t border-amber-200/50 flex items-center gap-1.5 text-[10px] text-amber-800">
                      <span className="font-medium">Policy CUS-05:</span>
                      <span>Clearance & customized items are non-returnable (exceptions for transit damage or error only).</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
