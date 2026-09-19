import { describe, it, expect, beforeEach, vi } from 'vitest';
import { youtubeService } from '../services/youtubeService';
import { authService } from '../services/authService';
import { getAuthToken } from '../services/api';

describe('Frontend Services with API Contracts', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('fetches channels and matches PaginatedResponse schema', async () => {
    const mockChannelResponse = {
      success: true,
      count: 1,
      total_pages: 1,
      current_page: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          channel_id: 'UC_x5XG1OV2P6uZZ5FSM9Ttw',
          title: 'Google Developers',
          description: 'Official channel',
          custom_url: '@googledevs',
          published_at: '2026-01-01T00:00:00Z',
          subscriber_count: 2300000,
          video_count: 5400,
          view_count: 180000000,
          thumbnail_url: 'https://example.com/thumb.jpg',
          is_active: true,
          owner_username: 'creator1',
          playlists_count: 3,
          total_videos: 5400,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockChannelResponse,
    } as Response);

    const data = await youtubeService.getChannels();
    expect(data.success).toBe(true);
    expect(data.count).toBe(1);
    expect(data.results[0].channel_id).toBe('UC_x5XG1OV2P6uZZ5FSM9Ttw');
    expect(data.results[0].subscriber_count).toBe(2300000);
  });

  it('login stores token in localStorage and returns user info', async () => {
    const mockLoginResponse = {
      success: true,
      data: {
        token: 'auth-token-xyz-789',
        user: {
          id: 42,
          username: 'shohruh',
          email: 'shohruh@example.com',
          first_name: 'Shohruh',
          last_name: 'Temirov',
          date_joined: '2026-01-01T00:00:00Z',
        },
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockLoginResponse,
    } as Response);

    const res = await authService.login({ username: 'shohruh', password: 'SecretPassword1!' });
    expect(res.user.username).toBe('shohruh');
    expect(getAuthToken()).toBe('auth-token-xyz-789');
  });
});
