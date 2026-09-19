/**
 * YouTube API service connecting to apps.youtube endpoints.
 */
import { request } from './api';
import type { PaginatedResponse, ApiResponse, HealthResponse } from '../types/api';
import type {
  YouTubeChannel,
  ChannelCreatePayload,
  YouTubePlaylist,
  YouTubeVideo,
  SyncJob,
  VideoStatistics,
} from '../types/youtube';

export const youtubeService = {
  async checkHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health/', { method: 'GET' });
  },

  async getChannels(page: number = 1): Promise<PaginatedResponse<YouTubeChannel>> {
    return request<PaginatedResponse<YouTubeChannel>>('/youtube/channels/', {
      method: 'GET',
      params: { page },
    });
  },

  async createChannel(payload: ChannelCreatePayload): Promise<YouTubeChannel> {
    return request<YouTubeChannel>('/youtube/channels/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async deleteChannel(id: number): Promise<void> {
    return request<void>(`/youtube/channels/${id}/`, {
      method: 'DELETE',
    });
  },

  async triggerSync(channelId: number): Promise<ApiResponse<SyncJob>> {
    return request<ApiResponse<SyncJob>>(`/youtube/channels/${channelId}/trigger_sync/`, {
      method: 'POST',
    });
  },

  async getPlaylists(channelId?: string): Promise<PaginatedResponse<YouTubePlaylist>> {
    return request<PaginatedResponse<YouTubePlaylist>>('/youtube/playlists/', {
      method: 'GET',
      params: { channel_id: channelId },
    });
  },

  async getVideos(params?: {
    search?: string;
    channel_id?: string;
    ordering?: string;
    page?: number;
  }): Promise<PaginatedResponse<YouTubeVideo>> {
    return request<PaginatedResponse<YouTubeVideo>>('/youtube/videos/', {
      method: 'GET',
      params,
    });
  },

  async getVideoStatistics(): Promise<ApiResponse<VideoStatistics>> {
    return request<ApiResponse<VideoStatistics>>('/youtube/videos/statistics/', {
      method: 'GET',
    });
  },

  async getSyncJobs(channelId?: string): Promise<PaginatedResponse<SyncJob>> {
    return request<PaginatedResponse<SyncJob>>('/youtube/sync-jobs/', {
      method: 'GET',
      params: { channel_id: channelId },
    });
  },
};
