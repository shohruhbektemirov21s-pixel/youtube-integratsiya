/**
 * Authentication API service.
 */
import { request, setAuthToken, removeAuthToken } from './api';
import type { ApiResponse } from '../types/api';
import type { User, AuthSuccessData, LoginPayload, RegisterPayload } from '../types/auth';

export const authService = {
  async login(payload: LoginPayload): Promise<AuthSuccessData> {
    const res = await request<ApiResponse<AuthSuccessData>>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (res.data?.token) {
      setAuthToken(res.data.token);
    }
    return res.data;
  },

  async register(payload: RegisterPayload): Promise<AuthSuccessData> {
    const res = await request<ApiResponse<AuthSuccessData>>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (res.data?.token) {
      setAuthToken(res.data.token);
    }
    return res.data;
  },

  async logout(): Promise<void> {
    try {
      await request('/auth/logout/', {
        method: 'POST',
      });
    } finally {
      removeAuthToken();
    }
  },

  async getCurrentUser(): Promise<User> {
    const res = await request<ApiResponse<User>>('/auth/me/', {
      method: 'GET',
    });
    return res.data;
  },
};
