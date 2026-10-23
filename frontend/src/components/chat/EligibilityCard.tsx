import React from 'react';
import { CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';
import { EligibilityEvaluation } from '../../types';

interface EligibilityCardProps {
  eligibility: EligibilityEvaluation;
}

export const EligibilityCard: React.FC<EligibilityCardProps> = ({ eligibility }) => {
  const {
    eligible,
    product_name,
    order_number,
    policy_reference,
    reason,
    detailed_explanation,
    return_window_days,
    days_since_delivery,
    requires_human_review,
    active_return_number,
  } = eligibility;

  return (
    <div
      className={`mt-3 rounded-2xl border p-4 shadow-xs transition-all ${
        eligible
          ? 'border-emerald-200 bg-emerald-50/40 text-emerald-950'
          : 'border-rose-200 bg-rose-50/40 text-rose-950'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          {eligible ? (
            <div className="rounded-xl bg-emerald-100 p-1.5 text-emerald-700">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          ) : (
            <div className="rounded-xl bg-rose-100 p-1.5 text-rose-700">
              <XCircle className="h-5 w-5" />
            </div>
          )}
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold tracking-tight">
                {eligible ? 'Eligible for Return / Exchange' : 'Return Ineligible'}
              </h4>
              {requires_human_review && (
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-800">
                  Human Review Required
                </span>
              )}
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              Order <span className="font-semibold text-slate-800">{order_number}</span> &bull; {product_name}
            </p>
          </div>
        </div>

        {/* Policy reference badge */}
        <span className="hidden sm:inline-block rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 shadow-2xs">
          {policy_reference}
        </span>
      </div>

      {/* Body */}
      <div className="mt-3 text-xs leading-relaxed space-y-1.5">
        <p className="font-semibold text-slate-800">{reason}</p>
        <p className="text-slate-600">{detailed_explanation}</p>
      </div>

      {/* Return window progress & Active return status */}
      <div className="mt-3 pt-3 border-t border-slate-200/60 flex flex-wrap items-center justify-between text-[11px] text-slate-500 gap-2">
        <div className="flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5 text-slate-400" />
          <span>
            Window: <strong className="text-slate-700">{return_window_days} Days</strong>
            {days_since_delivery !== null && days_since_delivery !== undefined && (
              <> ({days_since_delivery} days elapsed)</>
            )}
          </span>
        </div>

        {active_return_number && (
          <div className="flex items-center gap-1 text-amber-700 font-semibold">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>Active Request: {active_return_number}</span>
          </div>
        )}
      </div>
    </div>
  );
};
