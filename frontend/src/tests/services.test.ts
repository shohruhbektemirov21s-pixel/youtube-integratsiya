import { describe, it, expect, beforeEach, vi } from 'vitest';
import { youtubeService } from '../services/youtubeService';
import { authService } from '../services/authService';
import { getAuthToken, setAuthToken } from '../services/api';

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

  it('createChannel sends payload strictly without API key', async () => {
    let capturedBody: string | undefined;

    globalThis.fetch = vi.fn().mockImplementation(async (_url, options) => {
      capturedBody = options?.body as string;
      return {
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          id: 2,
          channel_id: 'UC_new_channel_123',
          title: 'New Channel',
          custom_url: '@newchan',
          subscriber_count: 0,
          video_count: 0,
          view_count: 0,
        }),
      } as Response;
    });

    const payload = {
      channel_id: 'UC_new_channel_123',
      title: 'New Channel',
      custom_url: '@newchan',
    };

    const res = await youtubeService.createChannel(payload);
    expect(res.id).toBe(2);
    expect(res.title).toBe('New Channel');

    // CRITICAL: Ensure no api_key was included in the request body
    expect(capturedBody).toBeDefined();
    const parsed = JSON.parse(capturedBody!);
    expect(parsed).not.toHaveProperty('api_key');
    expect(parsed.channel_id).toBe('UC_new_channel_123');
  });

  it('deleteChannel calls DELETE endpoint properly', async () => {
    let capturedMethod: string | undefined;

    globalThis.fetch = vi.fn().mockImplementation(async (_url, options) => {
      capturedMethod = options?.method;
      return {
        ok: true,
        status: 204,
        headers: new Headers(),
      } as Response;
    });

    await expect(youtubeService.deleteChannel(1)).resolves.not.toThrow();
    expect(capturedMethod).toBe('DELETE');
  });

  it('triggerSync triggers backend channel sync job', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        success: true,
        message: 'Sinxronizatsiya muvaffaqiyatli',
        data: { id: 1, status: 'completed', items_synced: 10 },
      }),
    } as Response);

    const res = await youtubeService.triggerSync(1);
    expect(res.success).toBe(true);
    expect(res.data.status).toBe('completed');
  });

  it('getVideoStatistics returns aggregated video analytics', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        success: true,
        data: {
          total_videos: 50,
          total_views: 1200000,
          total_likes: 45000,
          total_comments: 3200,
          avg_duration_seconds: 420.5,
        },
      }),
    } as Response);

    const stats = await youtubeService.getVideoStatistics();
    expect(stats.success).toBe(true);
    expect(stats.data.total_videos).toBe(50);
    expect(stats.data.total_views).toBe(1200000);
  });

  it('checkHealth calls backend health endpoint', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({
        status: 'online',
        service: 'youtube-integratsiya-backend',
        database: 'ok',
        version: '1.0.0',
      }),
    } as Response);

    const health = await youtubeService.checkHealth();
    expect(health.status).toBe('online');
    expect(health.database).toBe('ok');
  });

  it('authService.logout clears token and calls backend logout', async () => {
    setAuthToken('token-to-delete');
    expect(getAuthToken()).toBe('token-to-delete');

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ success: true, message: 'Chiqildi' }),
    } as Response);

    await authService.logout();
    expect(getAuthToken()).toBeNull();
  });
});
