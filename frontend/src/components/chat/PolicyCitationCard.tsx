import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import { PolicyCitation } from '../../types';

interface PolicyCitationCardProps {
  citations: PolicyCitation[];
}

export const PolicyCitationCard: React.FC<PolicyCitationCardProps> = ({ citations }) => {
  const [expanded, setExpanded] = useState(false);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-3 rounded-xl border border-indigo-100 bg-indigo-50/50 p-3.5 text-xs text-slate-800 shadow-xs">
      <div
        className="flex cursor-pointer items-center justify-between"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2 font-semibold text-brand-700">
          <BookOpen className="h-4 w-4 text-brand-600 flex-shrink-0" />
          <span>Verified Policy Sources ({citations.length})</span>
        </div>
        <button
          type="button"
          className="text-slate-400 hover:text-slate-600 focus:outline-none"
        >
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {expanded ? (
        <div className="mt-2.5 space-y-2 border-t border-indigo-100/80 pt-2.5">
          {citations.map((c) => (
            <div
              key={c.policy_id}
              className="rounded-lg bg-white p-2.5 border border-indigo-100/60 shadow-xs"
            >
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="font-semibold text-slate-900">{c.section}</span>
                <span className="rounded-full bg-indigo-50 px-2 py-0.5 font-medium text-brand-700">
                  {Math.round(c.similarity_score * 100)}% Match
                </span>
              </div>
              <p className="text-slate-600 leading-relaxed text-[11px]">{c.snippet}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-1 text-[11px] text-slate-500 truncate">
          Citing {citations.map((c) => c.section).join(', ')}
        </p>
      )}
    </div>
  );
};
