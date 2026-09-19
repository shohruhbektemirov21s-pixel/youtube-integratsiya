/**
 * Common API responses and generic contracts matching the Django REST Framework backend.
 */

export interface PaginatedResponse<T> {
  success: boolean;
  count: number;
  total_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiErrorDetails {
  [key: string]: string[] | string | Record<string, unknown>;
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: ApiErrorDetails | string | null;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
}

export interface HealthResponse {
  status: string;
  service: string;
  database: string;
  version: string;
}
