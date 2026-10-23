import React, { useState } from 'react';
import { ShieldCheck, ArrowRight, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { useToast } from '../../context/ToastContext';

interface ConfirmationCardProps {
  payload: {
    order_number: string;
    customer_email: string;
    sku: string;
    product_name: string;
    resolution: string;
    return_reason: string;
  };
  sessionId: string;
  onSuccess: (returnNumber: string, status: string) => void;
  onCancel?: () => void;
}

export const ConfirmationCard: React.FC<ConfirmationCardProps> = ({
  payload,
  sessionId,
  onSuccess,
  onCancel,
}) => {
  const { showToast } = useToast();
  const [reason, setReason] = useState(payload.return_reason || 'Item return/exchange request');
  const [resolution, setResolution] = useState(payload.resolution || 'RETURN_REFUND');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmedNumber, setConfirmedNumber] = useState<string | null>(null);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    try {
      const res = await api.confirmReturnAction({
        session_id: sessionId,
        order_number: payload.order_number,
        sku: payload.sku,
        resolution: resolution,
        return_reason: reason.trim(),
      });

      setConfirmedNumber(res.return_number);
      showToast(`Return request ${res.return_number} confirmed!`, 'success');
      onSuccess(res.return_number, res.status);
    } catch (err: any) {
      showToast(err.message || 'Failed to submit return request', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (confirmedNumber) {
    return (
      <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 text-xs text-emerald-950 shadow-xs">
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-emerald-100 p-2 text-emerald-700">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div className="flex-1 space-y-1">
            <h4 className="font-bold text-sm text-emerald-900">
              Return Request Created: {confirmedNumber}
            </h4>
            <p className="text-emerald-800 leading-relaxed">
              Your request has been officially recorded with status <strong>PENDING</strong>.
              Free reverse courier pickup has been scheduled for your address.
            </p>
            <div className="pt-2 flex items-center gap-2">
              <span className="font-mono text-xs bg-white px-2.5 py-1 rounded-lg border border-emerald-200 font-bold">
                {confirmedNumber}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-2xl border border-indigo-200 bg-gradient-to-b from-indigo-50/70 to-white p-4 shadow-sm text-xs">
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1.5 rounded-lg bg-brand-600 text-white">
          <ShieldCheck className="h-4 w-4" />
        </div>
        <div>
          <h4 className="font-bold text-slate-900 text-sm">Review & Explicitly Confirm Request</h4>
          <p className="text-[11px] text-slate-500">
            Please confirm your resolution choice before submission
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-3 space-y-2 mb-3 shadow-2xs">
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <span className="text-slate-400 block font-medium">Order Number:</span>
            <span className="font-mono font-semibold text-slate-800">{payload.order_number}</span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Product SKU:</span>
            <span className="font-mono font-semibold text-slate-800">{payload.sku}</span>
          </div>
        </div>

        <div>
          <span className="text-slate-400 block font-medium text-[11px]">Item:</span>
          <span className="font-semibold text-slate-800">{payload.product_name}</span>
        </div>

        <div>
          <label className="text-slate-400 block font-medium text-[11px] mb-1">
            Selected Resolution:
          </label>
          <select
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-200 bg-slate-50 py-1.5 px-2.5 text-slate-800 font-medium focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="RETURN_REFUND">Return for 100% Refund (Doorstep Reverse Pickup)</option>
            <option value="EXCHANGE_SIZE">Exchange for Alternate Size/Fit</option>
            <option value="REPLACEMENT_DAMAGED">Brand New Unit Replacement (Defect/Damage)</option>
          </select>
        </div>

        <div>
          <label className="text-slate-400 block font-medium text-[11px] mb-1">
            Reason for Return / Details:
          </label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Brief description of the issue"
            className="w-full text-xs rounded-lg border border-slate-200 bg-slate-50 py-1.5 px-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
      </div>

      <div className="flex items-center justify-end gap-2">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 font-medium text-xs transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          type="button"
          onClick={handleConfirm}
          disabled={isSubmitting || !reason.trim()}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-xs transition-all flex items-center gap-1.5 disabled:opacity-50"
        >
          {isSubmitting ? (
            <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <>
              <span>Confirm & Submit Return</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
