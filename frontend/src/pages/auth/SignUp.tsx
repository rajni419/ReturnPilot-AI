import React, { useMemo, useState } from 'react';
import {
  Sparkles,
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Check,
  X,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';

interface SignUpProps {
  onNavigate: (view: string, email?: string) => void;
}

export const SignUp: React.FC<SignUpProps> = ({ onNavigate }) => {
  const { register } = useAuth();
  const { showToast } = useToast();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Password rules validation
  const rules = useMemo(() => {
    return {
      minLength: password.length >= 8,
      hasUpper: /[A-Z]/.test(password),
      hasLower: /[a-z]/.test(password),
      hasDigit: /[0-9]/.test(password),
      hasSpecial: /[^A-Za-z0-9]/.test(password),
      matches: password.length > 0 && password === confirmPassword,
    };
  }, [password, confirmPassword]);

  const strengthScore = useMemo(() => {
    let score = 0;
    if (rules.minLength) score += 20;
    if (rules.hasUpper) score += 20;
    if (rules.hasLower) score += 20;
    if (rules.hasDigit) score += 20;
    if (rules.hasSpecial) score += 20;
    return score;
  }, [rules]);

  const strengthColor = () => {
    if (strengthScore < 40) return 'bg-rose-500';
    if (strengthScore < 80) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  const strengthLabel = () => {
    if (password.length === 0) return '';
    if (strengthScore < 40) return 'Weak';
    if (strengthScore < 80) return 'Moderate';
    return 'Strong';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmedName = fullName.trim();
    const trimmedEmail = email.trim();

    if (!trimmedName) {
      setErrorMessage('Please provide your full name.');
      return;
    }
    if (!trimmedEmail) {
      setErrorMessage('Please provide your email address.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }
    if (strengthScore < 100) {
      setErrorMessage('Password must satisfy all security requirements listed below.');
      return;
    }
    if (!acceptTerms) {
      setErrorMessage('You must accept the terms of service and privacy policy to continue.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await register({
        full_name: trimmedName,
        email: trimmedEmail,
        password,
        confirm_password: confirmPassword,
      });

      showToast('Registration successful! Please check your email for verification code.', 'success');
      if (res.dev_token) {
        showToast(`Dev Token: ${res.dev_token}`, 'info');
      }

      onNavigate('verify-email', trimmedEmail);
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please check your information.');
    } finally {
      setIsLoading(false);
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
          Create your account
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Join ReturnPilot AI to streamline returns and policy enforcement
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm border border-slate-200/80 rounded-2xl">
          {/* Error Message */}
          {errorMessage && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
              <span className="leading-snug">{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name */}
            <div>
              <label
                htmlFor="name"
                className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
              >
                Full Name
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <User className="h-4 w-4" />
                </div>
                <input
                  id="name"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                  className="block w-full pl-10 pr-3.5 py-2.5 text-sm rounded-xl border border-slate-200 bg-slate-50/50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                />
              </div>
            </div>

            {/* Email Address */}
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
              >
                Email Address
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jane@company.com"
                  className="block w-full pl-10 pr-3.5 py-2.5 text-sm rounded-xl border border-slate-200 bg-slate-50/50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
              >
                Password
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-10 py-2.5 text-sm rounded-xl border border-slate-200 bg-slate-50/50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              {/* Strength Meter Bar */}
              {password.length > 0 && (
                <div className="mt-2 space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-500 font-medium">Password Strength</span>
                    <span className="font-semibold text-slate-700">{strengthLabel()}</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${strengthColor()}`}
                      style={{ width: `${strengthScore}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirm-password"
                className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
              >
                Confirm Password
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-10 py-2.5 text-sm rounded-xl border border-slate-200 bg-slate-50/50 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Password Requirements Checklist */}
            <div className="p-3 bg-slate-50/80 rounded-xl border border-slate-200/60 space-y-1.5 text-xs">
              <span className="font-semibold text-slate-600 block mb-1">
                Password Requirements:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <div className="flex items-center gap-1.5">
                  {rules.minLength ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <X className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  )}
                  <span className={rules.minLength ? 'text-emerald-700' : 'text-slate-500'}>
                    8+ characters
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {rules.hasUpper ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <X className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  )}
                  <span className={rules.hasUpper ? 'text-emerald-700' : 'text-slate-500'}>
                    Uppercase letter
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {rules.hasLower ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <X className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  )}
                  <span className={rules.hasLower ? 'text-emerald-700' : 'text-slate-500'}>
                    Lowercase letter
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {rules.hasDigit ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <X className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  )}
                  <span className={rules.hasDigit ? 'text-emerald-700' : 'text-slate-500'}>
                    Number (0-9)
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {rules.hasSpecial ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <X className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  )}
                  <span className={rules.hasSpecial ? 'text-emerald-700' : 'text-slate-500'}>
                    Special character
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {rules.matches ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <X className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  )}
                  <span className={rules.matches ? 'text-emerald-700' : 'text-slate-500'}>
                    Passwords match
                  </span>
                </div>
              </div>
            </div>

            {/* Terms acceptance */}
            <div className="flex items-start pt-1">
              <input
                id="terms"
                type="checkbox"
                required
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
                className="h-4 w-4 text-brand-600 focus:ring-brand-500 border-slate-300 rounded mt-0.5 cursor-pointer"
              />
              <label htmlFor="terms" className="ml-2 block text-xs text-slate-600 cursor-pointer">
                I agree to the{' '}
                <span className="text-brand-600 hover:underline">Terms of Service</span> and{' '}
                <span className="text-brand-600 hover:underline">Privacy Policy</span>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl shadow-sm text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Create Account</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Switch to Sign In */}
          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-500">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => onNavigate('signin')}
                className="font-semibold text-brand-600 hover:text-brand-700 hover:underline transition-colors"
              >
                Sign in
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
