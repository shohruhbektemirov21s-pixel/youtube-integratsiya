/**
 * Core HTTP API Client with token handling, error normalization, and strict typing.
 */
import type { ApiErrorResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const TOKEN_STORAGE_KEY = 'youtube_auth_token';

export class ApiError extends Error {
  readonly code: string;
  readonly details: unknown;
  readonly status: number;

  constructor(message: string, code: string = 'ApiError', details: unknown = null, status: number = 400) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function removeAuthToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...restOptions } = options;

  let url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, val] of Object.entries(params)) {
      if (val !== undefined && val !== '') {
        searchParams.append(key, String(val));
      }
    }
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  const token = getAuthToken();
  const requestHeaders: HeadersInit = {
    'Accept': 'application/json',
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { 'Authorization': `Token ${token}` } : {}),
    ...headers,
  };

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
    });

    if (response.status === 204) {
      return {} as T;
    }

    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    const data = isJson ? await response.json() : null;

    if (!response.ok) {
      if (data && typeof data === 'object' && 'error' in data) {
        const errPayload = data as ApiErrorResponse;
        throw new ApiError(
          errPayload.error.message || 'Server xatosi yuz berdi',
          errPayload.error.code || 'ServerError',
          errPayload.error.details,
          response.status
        );
      }

      const errorMessage = data?.detail || response.statusText || 'So‘rovni bajarishda xatolik yuz berdi';
      throw new ApiError(errorMessage, 'HttpError', data, response.status);
    }

    return data as T;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err instanceof Error ? err.message : 'Tarmoqqa ulanishda xatolik yuz berdi',
      'NetworkError',
      null,
      0
    );
  }
}
