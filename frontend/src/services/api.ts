import {
  HealthStatus,
  Order,
  ReturnCheckRequest,
  ReturnCheckResponse,
  ReturnCreateRequest,
  ReturnRequest,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const fullUrl = `${API_BASE}${url}`;
  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to text status
      }
      throw new ApiError(errorMessage, response.status);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err?.message || 'Network error connecting to ReturnPilot AI backend', 0);
  }
}

export const api = {
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
