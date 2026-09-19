import { describe, it, expect, beforeEach } from 'vitest';
import { ApiError, setAuthToken, getAuthToken, removeAuthToken } from '../services/api';

describe('API Client Utilities', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('ApiError creates instance with code, details, and status', () => {
    const error = new ApiError('Test xatosi', 'ValidationError', { field: ['Required'] }, 400);
    expect(error.message).toBe('Test xatosi');
    expect(error.code).toBe('ValidationError');
    expect(error.details).toEqual({ field: ['Required'] });
    expect(error.status).toBe(400);
    expect(error.name).toBe('ApiError');
  });

  it('manages auth token lifecycle in localStorage', () => {
    expect(getAuthToken()).toBeNull();

    setAuthToken('token-123-abc');
    expect(getAuthToken()).toBe('token-123-abc');

    removeAuthToken();
    expect(getAuthToken()).toBeNull();
  });
});
