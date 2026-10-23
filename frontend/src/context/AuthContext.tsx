import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, clearStoredToken, getStoredToken } from '../services/api';
import {
  ForgotPasswordRequest,
  MessageResponse,
  ResendVerificationRequest,
  ResetPasswordRequest,
  UserLoginRequest,
  UserProfile,
  UserRegisterRequest,
  VerifyEmailRequest,
} from '../types';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: UserLoginRequest) => Promise<UserProfile>;
  register: (payload: UserRegisterRequest) => Promise<UserProfile & { dev_token?: string }>;
  verifyEmail: (payload: VerifyEmailRequest) => Promise<MessageResponse>;
  resendVerification: (payload: ResendVerificationRequest) => Promise<MessageResponse>;
  forgotPassword: (payload: ForgotPasswordRequest) => Promise<MessageResponse>;
  resetPassword: (payload: ResetPasswordRequest) => Promise<MessageResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<UserProfile | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setTokenState] = useState<string | null>(getStoredToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Restore authenticated session on initial mount
  useEffect(() => {
    let mounted = true;

    const restoreSession = async () => {
      try {
        const userProfile = await api.getMe();
        if (mounted) {
          setUser(userProfile);
          setTokenState(getStoredToken());
        }
      } catch {
        // If not authenticated or token expired, clear local state
        if (mounted) {
          setUser(null);
          clearStoredToken();
          setTokenState(null);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    restoreSession();

    return () => {
      mounted = false;
    };
  }, []);

  const login = async (payload: UserLoginRequest): Promise<UserProfile> => {
    const authRes = await api.login(payload);
    setUser(authRes.user);
    setTokenState(authRes.access_token);
    return authRes.user;
  };

  const register = async (payload: UserRegisterRequest): Promise<UserProfile & { dev_token?: string }> => {
    return await api.register(payload);
  };

  const verifyEmail = async (payload: VerifyEmailRequest): Promise<MessageResponse> => {
    return await api.verifyEmail(payload);
  };

  const resendVerification = async (payload: ResendVerificationRequest): Promise<MessageResponse> => {
    return await api.resendVerification(payload);
  };

  const forgotPassword = async (payload: ForgotPasswordRequest): Promise<MessageResponse> => {
    return await api.forgotPassword(payload);
  };

  const resetPassword = async (payload: ResetPasswordRequest): Promise<MessageResponse> => {
    return await api.resetPassword(payload);
  };

  const logout = async (): Promise<void> => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      setTokenState(null);
      clearStoredToken();
    }
  };

  const refreshUser = async (): Promise<UserProfile | null> => {
    try {
      const userProfile = await api.getMe();
      setUser(userProfile);
      return userProfile;
    } catch {
      setUser(null);
      clearStoredToken();
      setTokenState(null);
      return null;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && user.is_verified,
        isLoading,
        login,
        register,
        verifyEmail,
        resendVerification,
        forgotPassword,
        resetPassword,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
