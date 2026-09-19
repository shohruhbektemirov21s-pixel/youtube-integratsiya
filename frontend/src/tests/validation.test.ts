import { describe, it, expect } from 'vitest';

describe('Validation Rules', () => {
  it('validates YouTube Channel ID format', () => {
    const isValidChannelId = (id: string) => id.trim().length >= 10;

    expect(isValidChannelId('UC_x5XG1OV2P6uZZ5FSM9Ttw')).toBe(true);
    expect(isValidChannelId('UC123456789')).toBe(true);
    expect(isValidChannelId('short')).toBe(false);
    expect(isValidChannelId('')).toBe(false);
  });

  it('validates email format', () => {
    const isValidEmail = (email: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    expect(isValidEmail('user@example.com')).toBe(true);
    expect(isValidEmail('test.user+tag@domain.co.uk')).toBe(true);
    expect(isValidEmail('invalid-email')).toBe(false);
    expect(isValidEmail('@domain.com')).toBe(false);
  });

  it('validates password matching', () => {
    const checkPasswordMatch = (p1: string, p2: string) => p1.length >= 8 && p1 === p2;

    expect(checkPasswordMatch('StrongPass123!', 'StrongPass123!')).toBe(true);
    expect(checkPasswordMatch('Short1!', 'Short1!')).toBe(false);
    expect(checkPasswordMatch('Password123', 'Password456')).toBe(false);
  });
});
