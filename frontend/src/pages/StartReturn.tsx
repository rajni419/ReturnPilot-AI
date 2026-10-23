import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Search,
  Package,
  Copy,
  Check,
} from 'lucide-react';

import { api } from '../services/api';
import { Order, ReturnCheckResponse, ReturnRequest } from '../types';
import { Badge } from '../components/ui/Badge';
import { useToast } from '../context/ToastContext';

interface StartReturnProps {
  onSuccessNavigate: (tab: string) => void;
}

const COMMON_REASONS = [
  'Item is defective or not functioning as expected',
  'Incorrect size or fit',
  'Received incorrect item or SKU',
  'Item does not match website description or photos',
  'Arrived damaged during shipment',
  'No longer needed / Changed mind',
];

export const StartReturn: React.FC<StartReturnProps> = ({ onSuccessNavigate }) => {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Form State
  const [orderNumber, setOrderNumber] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [selectedSku, setSelectedSku] = useState('');
  const [returnReason, setReturnReason] = useState('');
  const [customReasonDetails, setCustomReasonDetails] = useState('');

  // Processing states
  const [lookingUpOrder, setLookingUpOrder] = useState(false);
  const [loadedOrder, setLoadedOrder] = useState<Order | null>(null);
  const [checkingEligibility, setCheckingEligibility] = useState(false);
  const [eligibilityResult, setEligibilityResult] = useState<ReturnCheckResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [createdReturn, setCreatedReturn] = useState<ReturnRequest | null>(null);
  const [copied, setCopied] = useState(false);

  const { showToast } = useToast();

  // Step 1: Lookup order
  const handleLookupOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderNumber.trim() || !customerEmail.trim()) {
      showToast('Please enter both Order Number and Customer Email', 'error');
      return;
    }

    setLookingUpOrder(true);
    try {
      const order = await api.lookupOrder(orderNumber.trim());
      // Verify email matching client-side preview
      if (order.customer_email.toLowerCase() !== customerEmail.trim().toLowerCase()) {
        showToast('Email address does not match this order records', 'error');
        setLoadedOrder(null);
        return;
      }
      setLoadedOrder(order);
      setStep(2);
      showToast('Order verified successfully', 'success');
    } catch (err: any) {
      showToast(err?.message || 'Order not found. Please check order number.', 'error');
      setLoadedOrder(null);
    } finally {
      setLookingUpOrder(false);
    }
  };

  // Step 2: Check Eligibility for SKU
  const handleCheckSkuEligibility = async (sku: string) => {
    setSelectedSku(sku);
    setCheckingEligibility(true);
    setEligibilityResult(null);

    try {
      const result = await api.checkEligibility({
        order_number: orderNumber.trim(),
        customer_email: customerEmail.trim(),
        sku: sku.trim(),
      });
      setEligibilityResult(result);
      if (result.eligible) {
        showToast('Item is eligible for return!', 'success');
      } else {
        showToast(result.reason, 'info');
      }
    } catch (err: any) {
      showToast(err?.message || 'Failed to check eligibility', 'error');
    } finally {
      setCheckingEligibility(false);
    }
  };

  // Step 3: Submit Return Request
  const handleSubmitReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!eligibilityResult || !eligibilityResult.eligible) {
      showToast('Cannot submit: Item is not eligible for return.', 'error');
      return;
    }

    const finalReason = customReasonDetails
      ? `${returnReason}: ${customReasonDetails}`
      : returnReason;

    if (!finalReason.trim()) {
      showToast('Please select or specify a reason for return', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.createReturnRequest({
        order_number: orderNumber.trim(),
        customer_email: customerEmail.trim(),
        sku: selectedSku.trim(),
        return_reason: finalReason.trim(),
      });
      setCreatedReturn(res);
      setStep(4);
      showToast(`Return request ${res.return_number} created!`, 'success');
    } catch (err: any) {
      showToast(err?.message || 'Failed to create return request', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyReturnNumber = () => {
    if (createdReturn) {
      navigator.clipboard.writeText(createdReturn.return_number);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      showToast('Return number copied to clipboard', 'info');
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      {/* Stepper Header */}
      {step < 4 && (
        <div className="bg-white rounded-2xl p-4 sm:p-6 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            {/* Step 1 Pill */}
            <div className="flex items-center gap-2">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                  step === 1
                    ? 'bg-brand-600 text-white'
                    : step > 1
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {step > 1 ? <Check className="w-4 h-4" /> : '1'}
              </div>
              <span
                className={`text-xs font-semibold hidden sm:inline ${
                  step === 1 ? 'text-slate-900' : 'text-slate-500'
                }`}
              >
                Verify Order
              </span>
            </div>

            <div className="w-8 sm:w-16 h-0.5 bg-slate-200" />

            {/* Step 2 Pill */}
            <div className="flex items-center gap-2">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                  step === 2
                    ? 'bg-brand-600 text-white'
                    : step > 2
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {step > 2 ? <Check className="w-4 h-4" /> : '2'}
              </div>
              <span
                className={`text-xs font-semibold hidden sm:inline ${
                  step === 2 ? 'text-slate-900' : 'text-slate-500'
                }`}
              >
                Item & Eligibility
              </span>
            </div>

            <div className="w-8 sm:w-16 h-0.5 bg-slate-200" />

            {/* Step 3 Pill */}
            <div className="flex items-center gap-2">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                  step === 3 ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-400'
                }`}
              >
                3
              </div>
              <span
                className={`text-xs font-semibold hidden sm:inline ${
                  step === 3 ? 'text-slate-900' : 'text-slate-500'
                }`}
              >
                Reason & Submit
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 1: ORDER CREDENTIALS */}
      {/* ========================================================================= */}
      {step === 1 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-8">
          <div className="max-w-md mx-auto">
            <div className="text-center mb-6">
              <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-3">
                <Search className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">Look Up Your Order</h2>
              <p className="text-xs text-slate-500 mt-1">
                Enter your order number and the email address used during checkout
              </p>
            </div>

            <form onSubmit={handleLookupOrder} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Order Number
                </label>
                <input
                  type="text"
                  placeholder="e.g. ORD-1001"
                  value={orderNumber}
                  onChange={(e) => setOrderNumber(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Customer Email
                </label>
                <input
                  type="email"
                  placeholder="name@example.com"
                  value={customerEmail}
                  onChange={(e) => setCustomerEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={lookingUpOrder}
                className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm shadow-xs transition-all disabled:opacity-50"
              >
                <span>{lookingUpOrder ? 'Verifying Order...' : 'Verify Order & Select Item'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 2: SELECT ITEM & CHECK ELIGIBILITY */}
      {/* ========================================================================= */}
      {step === 2 && loadedOrder && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Order Reference
              </span>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 mt-0.5">
                <span>{loadedOrder.order_number}</span>
                <Badge status={loadedOrder.shipping_status} size="sm" />
              </h2>
            </div>
            <button
              onClick={() => {
                setStep(1);
                setEligibilityResult(null);
              }}
              className="text-xs font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Change Order</span>
            </button>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-1">Select an Item to Return</h3>
            <p className="text-xs text-slate-500 mb-4">
              Click an item to check return policy eligibility against the 7-day window.
            </p>

            <div className="space-y-2.5">
              {loadedOrder.items.map((item) => {
                const isSelected = selectedSku === item.sku;
                return (
                  <div
                    key={item.id}
                    onClick={() => item.sku && handleCheckSkuEligibility(item.sku)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-4 ${
                      isSelected
                        ? 'border-brand-500 bg-brand-50/50 shadow-xs ring-1 ring-brand-500/20'
                        : 'border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/60'
                    }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                          isSelected ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        <Package className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-xs sm:text-sm font-semibold text-slate-900">
                          {item.product_name}
                        </h4>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
                          <span className="font-mono text-[11px] text-slate-600">SKU: {item.sku}</span>
                          <span>•</span>
                          <span>Qty: {item.quantity}</span>
                          <span>•</span>
                          <span className="font-medium text-slate-800">${item.price.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {!item.is_returnable && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 border border-rose-200/80">
                          Final Sale
                        </span>
                      )}
                      <button
                        type="button"
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                          isSelected
                            ? 'bg-brand-600 text-white'
                            : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                        }`}
                      >
                        {isSelected ? 'Selected' : 'Select'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Loading Eligibility */}
          {checkingEligibility && (
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-brand-600 border-t-transparent rounded-full animate-spin shrink-0" />
              <p className="text-xs text-slate-600 font-medium">
                Evaluating return window and item eligibility...
              </p>
            </div>
          )}

          {/* Eligibility Result Card */}
          {eligibilityResult && !checkingEligibility && (
            <div
              className={`p-5 rounded-2xl border transition-all animate-fade-in ${
                eligibilityResult.eligible
                  ? 'bg-emerald-50/90 border-emerald-200 text-emerald-950'
                  : 'bg-rose-50/90 border-rose-200 text-rose-950'
              }`}
            >
              <div className="flex items-start gap-3.5">
                {eligibilityResult.eligible ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider">
                      {eligibilityResult.eligible ? 'Eligible for Return' : 'Ineligible for Return'}
                    </span>
                    <Badge
                      status={eligibilityResult.eligible ? 'ELIGIBLE' : 'INELIGIBLE'}
                      size="sm"
                    />
                  </div>
                  <p className="text-xs sm:text-sm mt-1.5 leading-relaxed font-medium">
                    {eligibilityResult.reason}
                  </p>
                </div>
              </div>

              {eligibilityResult.eligible && (
                <div className="mt-4 pt-3.5 border-t border-emerald-200/80 flex justify-end">
                  <button
                    onClick={() => {
                      setReturnReason(COMMON_REASONS[0]);
                      setStep(3);
                    }}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs sm:text-sm font-semibold shadow-xs transition-colors"
                  >
                    <span>Proceed to Reason & Submit</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 3: REASON & SUBMIT */}
      {/* ========================================================================= */}
      {step === 3 && loadedOrder && eligibilityResult && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                Step 3 of 3
              </span>
              <h2 className="text-base font-bold text-slate-900 mt-0.5">
                Reason for Return
              </h2>
            </div>
            <button
              onClick={() => setStep(2)}
              className="text-xs font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Item Selection</span>
            </button>
          </div>

          {/* Selected Item Summary */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs">
            <div>
              <span className="text-slate-500">Order:</span>{' '}
              <span className="font-semibold text-slate-900">{orderNumber}</span>
            </div>
            <div>
              <span className="text-slate-500">SKU:</span>{' '}
              <span className="font-mono font-semibold text-slate-900">{selectedSku}</span>
            </div>
            <div>
              <span className="text-slate-500">Policy:</span>{' '}
              <span className="text-emerald-700 font-semibold">Eligible (7-Day Window)</span>
            </div>
          </div>

          <form onSubmit={handleSubmitReturn} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Primary Return Reason
              </label>
              <select
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all bg-white"
                required
              >
                {COMMON_REASONS.map((r, i) => (
                  <option key={i} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Additional Details (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="Provide any additional context or details about the issue..."
                value={customReasonDetails}
                onChange={(e) => setCustomReasonDetails(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
              />
            </div>

            <div className="pt-2 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 font-medium text-xs sm:text-sm transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs sm:text-sm shadow-xs transition-all disabled:opacity-50"
              >
                <span>{submitting ? 'Submitting Request...' : 'Confirm & Submit Return'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 4: SUCCESS CONFIRMATION */}
      {/* ========================================================================= */}
      {step === 4 && createdReturn && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-10 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
            Return Request Submitted!
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto mt-1.5">
            Your return request has been registered in the database with status{' '}
            <span className="font-semibold text-amber-700">PENDING</span>. Keep your reference number handy.
          </p>

          {/* Reference badge */}
          <div className="my-6 inline-flex items-center gap-3 px-5 py-3 rounded-2xl bg-slate-50 border border-slate-200/80">
            <div>
              <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                Return Reference
              </span>
              <span className="text-xl sm:text-2xl font-mono font-bold text-brand-700 tracking-wider">
                {createdReturn.return_number}
              </span>
            </div>
            <button
              onClick={handleCopyReturnNumber}
              className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              title="Copy Return Number"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>

          {/* Detail card */}
          <div className="max-w-md mx-auto p-4 rounded-xl bg-slate-50/50 border border-slate-100 text-left text-xs space-y-2 mb-6">
            <div className="flex justify-between">
              <span className="text-slate-400">Order Number:</span>
              <span className="font-semibold text-slate-800">{createdReturn.order_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Item SKU:</span>
              <span className="font-mono text-slate-800">{createdReturn.sku}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Customer:</span>
              <span className="text-slate-800">{createdReturn.customer_email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Status:</span>
              <Badge status={createdReturn.status} size="sm" />
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => onSuccessNavigate('tracking')}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs sm:text-sm shadow-xs transition-colors"
            >
              View in Return Tracking
            </button>
            <button
              onClick={() => {
                setStep(1);
                setOrderNumber('');
                setCustomerEmail('');
                setSelectedSku('');
                setReturnReason('');
                setLoadedOrder(null);
                setEligibilityResult(null);
                setCreatedReturn(null);
              }}
              className="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-700 hover:text-slate-900 hover:bg-slate-50 font-medium text-xs sm:text-sm transition-colors"
            >
              Start Another Return
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
