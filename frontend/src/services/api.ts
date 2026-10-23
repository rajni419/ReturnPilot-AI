import {
  AuthResponse,
  ForgotPasswordRequest,
  HealthStatus,
  MessageResponse,
  Order,
  ResendVerificationRequest,
  ResetPasswordRequest,
  ReturnCheckRequest,
  ReturnCheckResponse,
  ReturnCreateRequest,
  ReturnRequest,
  UserLoginRequest,
  UserProfile,
  UserRegisterRequest,
  VerifyEmailRequest,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';
const TOKEN_KEY = 'rp_auth_token';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Ignore storage errors in restricted iframe/private mode
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Ignore storage errors
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const fullUrl = `${API_BASE}${url}`;
  const token = getStoredToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers as Record<string, string> || {}),
  };

  try {
    const response = await fetch(fullUrl, {
      ...options,
      credentials: 'include', // Support HttpOnly cookies across origin
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            // Pydantic 422 validation errors
            errorMessage = errorData.detail
              .map((err: any) => err.msg || err.message || JSON.stringify(err))
              .join('; ');
          } else {
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
      } catch {
        // Fallback to text status
      }
      throw new ApiError(errorMessage, response.status);
    }

    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json();

    // Check for dev token headers (in non-SMTP environments)
    const devVerifyToken = response.headers.get('x-dev-verification-token');
    const devResetToken = response.headers.get('x-dev-reset-token');

    if (data && typeof data === 'object') {
      if (devVerifyToken && !data.dev_token) {
        data.dev_token = devVerifyToken;
      }
      if (devResetToken && !data.dev_token) {
        data.dev_token = devResetToken;
      }
    }

    return data;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err?.message || 'Network error connecting to ReturnPilot AI backend', 0);
  }
}

export const api = {
  // Authentication
  async register(payload: UserRegisterRequest): Promise<UserProfile & { dev_token?: string }> {
    return fetchJson<UserProfile & { dev_token?: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async login(payload: UserLoginRequest): Promise<AuthResponse> {
    const res = await fetchJson<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (res.access_token) {
      setStoredToken(res.access_token);
    }
    return res;
  },

  async getMe(): Promise<UserProfile> {
    return fetchJson<UserProfile>('/api/auth/me');
  },

  async logout(): Promise<MessageResponse> {
    try {
      const res = await fetchJson<MessageResponse>('/api/auth/logout', {
        method: 'POST',
      });
      clearStoredToken();
      return res;
    } catch (err) {
      clearStoredToken();
      throw err;
    }
  },

  async verifyEmail(payload: VerifyEmailRequest): Promise<MessageResponse> {
    return fetchJson<MessageResponse>('/api/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async resendVerification(payload: ResendVerificationRequest): Promise<MessageResponse> {
    return fetchJson<MessageResponse>('/api/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async forgotPassword(payload: ForgotPasswordRequest): Promise<MessageResponse> {
    return fetchJson<MessageResponse>('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async resetPassword(payload: ResetPasswordRequest): Promise<MessageResponse> {
    return fetchJson<MessageResponse>('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Token Helpers
  getToken: getStoredToken,
  setToken: setStoredToken,
  clearToken: clearStoredToken,

  // System Health
  async getHealth(): Promise<HealthStatus> {
    return fetchJson<HealthStatus>('/health');
  },

  // Orders
  async listOrders(skip = 0, limit = 50): Promise<Order[]> {
    return fetchJson<Order[]>(`/api/orders/?skip=${skip}&limit=${limit}`);
  },

  async lookupOrder(orderNumber: string): Promise<Order> {
    return fetchJson<Order>(`/api/orders/lookup/${encodeURIComponent(orderNumber.trim())}`);
  },

  async createOrder(payload: Partial<Order>): Promise<Order> {
    return fetchJson<Order>('/api/orders/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Returns
  async checkEligibility(payload: ReturnCheckRequest): Promise<ReturnCheckResponse> {
    return fetchJson<ReturnCheckResponse>('/returns/check', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async createReturnRequest(payload: ReturnCreateRequest): Promise<ReturnRequest> {
    return fetchJson<ReturnRequest>('/returns', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listReturnRequests(params?: {
    order_number?: string;
    customer_email?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<ReturnRequest[]> {
    const searchParams = new URLSearchParams();
    if (params?.order_number) searchParams.append('order_number', params.order_number);
    if (params?.customer_email) searchParams.append('customer_email', params.customer_email);
    if (params?.status && params.status !== 'ALL') searchParams.append('status', params.status);
    if (params?.skip) searchParams.append('skip', String(params.skip));
    if (params?.limit) searchParams.append('limit', String(params.limit));

    const qs = searchParams.toString();
    return fetchJson<ReturnRequest[]>(`/returns${qs ? `?${qs}` : ''}`);
  },

  async getReturnRequest(returnId: number): Promise<ReturnRequest> {
    return fetchJson<ReturnRequest>(`/returns/${returnId}`);
  },

  // Demo order generator to test easily
  async seedDemoOrder(): Promise<Order> {
    const rand = Math.floor(1000 + Math.random() * 9000);
    const demoPayload = {
      order_number: `ORD-DEMO-${rand}`,
      customer_name: 'Sarah Connor',
      customer_email: 'sarah.connor@example.com',
      shipping_status: 'DELIVERED',
      delivery_date: new Date().toISOString(),
      items: [
        {
          product_name: 'Studio Pro Wireless Headphones',
          sku: `HEADPHONE-${rand}`,
          quantity: 1,
          price: 199.99,
          is_returnable: true,
        },
        {
          product_name: 'Hardshell Protective Case',
          sku: `CASE-${rand}`,
          quantity: 1,
          price: 29.99,
          is_returnable: true,
        },
        {
          product_name: 'Custom Engraved Nameplate (Final Sale)',
          sku: `ENGRAVE-${rand}`,
          quantity: 1,
          price: 15.00,
          is_returnable: false,
        },
      ],
    };
    return fetchJson<Order>('/api/orders/', {
      method: 'POST',
      body: JSON.stringify(demoPayload),
    });
  },
};
