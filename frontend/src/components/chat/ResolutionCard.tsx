import React from 'react';
import { RefreshCw, RotateCcw, Wrench, CheckCircle, ArrowRight } from 'lucide-react';
import { ResolutionOption } from '../../types';

interface ResolutionCardProps {
  resolutions: ResolutionOption[];
  onSelectResolution: (resolutionId: string) => void;
  selectedResolution?: string | null;
}

export const ResolutionCard: React.FC<ResolutionCardProps> = ({
  resolutions,
  onSelectResolution,
  selectedResolution,
}) => {
  if (!resolutions || resolutions.length === 0) return null;

  const getIcon = (id: string) => {
    switch (id) {
      case 'EXCHANGE_SIZE':
        return RefreshCw;
      case 'REPLACEMENT_DAMAGED':
        return RefreshCw;
      case 'PRODUCT_SUPPORT':
        return Wrench;
      case 'RETURN_REFUND':
      default:
        return RotateCcw;
    }
  };

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Available Resolution Options ({resolutions.length})
        </p>
        <span className="text-[11px] text-slate-400">Select your preferred outcome</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {resolutions.map((res) => {
          const Icon = getIcon(res.id);
          const isSelected = selectedResolution === res.id;

          return (
            <div
              key={res.id}
              onClick={() => onSelectResolution(res.id)}
              className={`group cursor-pointer rounded-2xl border p-4 transition-all duration-150 relative flex flex-col justify-between ${
                isSelected
                  ? 'border-brand-500 bg-brand-50/40 ring-2 ring-brand-500/20 shadow-sm'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-xs'
              }`}
            >
              <div>
                {/* Header & Badges */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <div
                      className={`p-2 rounded-xl transition-colors ${
                        isSelected
                          ? 'bg-brand-600 text-white'
                          : 'bg-slate-100 text-slate-600 group-hover:bg-brand-50 group-hover:text-brand-600'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <h5 className="text-xs font-bold text-slate-900 group-hover:text-brand-600 transition-colors">
                        {res.title}
                      </h5>
                      <p className="text-[10px] text-slate-500 mt-0.5">{res.timeline}</p>
                    </div>
                  </div>

                  {res.badge && (
                    <span className="rounded-full bg-brand-100 px-2 py-0.5 text-[9px] font-bold text-brand-700 tracking-wide uppercase">
                      {res.badge}
                    </span>
                  )}
                </div>

                {/* Description */}
                <p className="text-xs text-slate-600 leading-relaxed mb-3">{res.description}</p>

                {/* Pros list */}
                {res.pros && res.pros.length > 0 && (
                  <div className="space-y-1 mb-3">
                    {res.pros.map((pro, idx) => (
                      <div key={idx} className="flex items-center gap-1.5 text-[11px] text-emerald-700">
                        <CheckCircle className="h-3 w-3 flex-shrink-0" />
                        <span>{pro}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Action Button */}
              <button
                type="button"
                className={`w-full py-1.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                  isSelected
                    ? 'bg-brand-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-700 group-hover:bg-slate-200'
                }`}
              >
                <span>{isSelected ? 'Selected' : 'Choose This Option'}</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
