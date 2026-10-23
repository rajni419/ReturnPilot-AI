import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  Mail,
  KeyRound,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Send,
  ArrowLeft,
  Copy,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';

interface VerifyEmailProps {
  onNavigate: (view: string, email?: string) => void;
  initialEmail?: string;
  initialToken?: string;
}

export const VerifyEmail: React.FC<VerifyEmailProps> = ({
  onNavigate,
  initialEmail = '',
  initialToken = '',
}) => {
  const { verifyEmail, resendVerification } = useAuth();
  const { showToast } = useToast();

  const [email, setEmail] = useState(initialEmail);
  const [token, setToken] = useState(initialToken);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Resend state & cooldown
  const [isResending, setIsResending] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [devTokenHint, setDevTokenHint] = useState<string | null>(null);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const trimmedEmail = email.trim();
    const trimmedToken = token.trim();

    if (!trimmedEmail) {
      setErrorMessage('Please provide the account email address.');
      return;
    }
    if (!trimmedToken) {
      setErrorMessage('Please enter the verification code received.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await verifyEmail({
        email: trimmedEmail,
        token: trimmedToken,
      });

      setSuccessMessage(res.message || 'Email verified successfully! You can now sign in.');
      showToast('Account verified! Please sign in.', 'success');

      setTimeout(() => {
        onNavigate('signin', trimmedEmail);
      }, 1500);
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid or expired verification token.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setErrorMessage('Please provide your email address to receive a new verification code.');
      return;
    }

    setIsResending(true);
    setErrorMessage(null);

    try {
      const res = await resendVerification({ email: trimmedEmail });
      setCooldown(60);
      showToast('A fresh verification token has been generated.', 'success');

      if (res.dev_token) {
        setDevTokenHint(res.dev_token);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to resend verification code.');
    } finally {
      setIsResending(false);
    }
  };

  const handleApplyDevToken = () => {
    if (devTokenHint) {
      setToken(devTokenHint);
      showToast('Applied test verification token.', 'info');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-violet-600 text-white shadow-lg shadow-brand-500/25 mb-4">
          <Sparkles className="w-6 h-6" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Verify your email address
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Enter the secure verification token sent to your email inbox
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm border border-slate-200/80 rounded-2xl">
          {/* Dev Token Assistant */}
          {devTokenHint && (
            <div className="mb-6 p-3.5 rounded-xl bg-violet-50 border border-violet-200 text-violet-900 text-xs">
              <div className="flex items-center justify-between font-semibold mb-1">
                <span>Dev / SMTP Outbox Token:</span>
                <button
                  type="button"
                  onClick={handleApplyDevToken}
                  className="inline-flex items-center gap-1 text-violet-700 hover:text-violet-900 underline font-medium"
                >
                  <Copy className="w-3 h-3" />
                  Auto-fill Token
                </button>
              </div>
              <p className="font-mono bg-white p-2 rounded-lg border border-violet-200 text-slate-800 break-all select-all">
                {devTokenHint}
              </p>
            </div>
          )}

          {/* Success Notification */}
          {successMessage && (
            <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Email Verified!</p>
                <p className="mt-0.5 text-xs text-emerald-700">{successMessage}</p>
              </div>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
              <span className="leading-snug">{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Address */}
            <div>
              <label
                htmlFor="verify-email"
                className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
              >
                Account Email
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  id="verify-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="block w-full pl-10 pr-3.5 py-2.5 text-sm rounded-xl border border-slate-200 bg-slate-50/50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                />
              </div>
            </div>

            {/* Verification Token */}
            <div>
              <label
                htmlFor="verify-token"
                className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
              >
                Verification Token / Code
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <KeyRound className="h-4 w-4" />
                </div>
                <input
                  id="verify-token"
                  type="text"
                  required
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Paste your 64-character token"
                  className="block w-full pl-10 pr-3.5 py-2.5 text-sm font-mono rounded-xl border border-slate-200 bg-slate-50/50 text-slate-900 placeholder:text-slate-400 placeholder:font-sans focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                />
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                Check your inbox or backend logs for the secure token.
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || !!successMessage}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl shadow-sm text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Verify Email</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Resend Action */}
          <div className="mt-6 pt-6 border-t border-slate-100 flex items-center justify-between text-xs">
            <button
              type="button"
              onClick={() => onNavigate('signin', email)}
              className="inline-flex items-center gap-1.5 font-medium text-slate-600 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </button>

            <button
              type="button"
              disabled={isResending || cooldown > 0}
              onClick={handleResend}
              className="inline-flex items-center gap-1.5 font-semibold text-brand-600 hover:text-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-3.5 h-3.5" />
              <span>
                {cooldown > 0 ? `Resend in ${cooldown}s` : isResending ? 'Sending...' : 'Resend Code'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
