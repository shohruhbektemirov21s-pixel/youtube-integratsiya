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

  async getFlowAccounts(): Promise<PaginatedResponse<import('../types/youtube').FlowAIAccount>> {
    return request<PaginatedResponse<import('../types/youtube').FlowAIAccount>>('/youtube/flow-accounts/', {
      method: 'GET',
    });
  },

  async createFlowAccount(data: Partial<import('../types/youtube').FlowAIAccount>): Promise<import('../types/youtube').FlowAIAccount> {
    return request<import('../types/youtube').FlowAIAccount>('/youtube/flow-accounts/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateFlowAccount(id: number, data: Partial<import('../types/youtube').FlowAIAccount>): Promise<import('../types/youtube').FlowAIAccount> {
    return request<import('../types/youtube').FlowAIAccount>(`/youtube/flow-accounts/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async deleteFlowAccount(id: number): Promise<void> {
    return request<void>(`/youtube/flow-accounts/${id}/`, {
      method: 'DELETE',
    });
  },

  async getDetectedChromeProfiles(): Promise<{ success: boolean; profiles: import('../types/youtube').DetectedProfile[] }> {
    return request<{ success: boolean; profiles: import('../types/youtube').DetectedProfile[] }>('/youtube/flow-accounts/detected_chrome_profiles/', {
      method: 'GET',
    });
  },

  async inspectAccount(id: number, data?: Partial<import('../types/youtube').FlowAIAccount>): Promise<ApiResponse<import('../types/youtube').FlowAIAccount>> {
    return request<ApiResponse<import('../types/youtube').FlowAIAccount>>(`/youtube/flow-accounts/${id}/inspect_account/`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });
  },

  async getNiches(): Promise<PaginatedResponse<import('../types/youtube').ChannelNiche>> {
    return request<PaginatedResponse<import('../types/youtube').ChannelNiche>>('/youtube/niches/', {
      method: 'GET',
    });
  },

  async getGenerationTasks(): Promise<PaginatedResponse<import('../types/youtube').VideoGenerationTask>> {
    return request<PaginatedResponse<import('../types/youtube').VideoGenerationTask>>('/youtube/generation-tasks/', {
      method: 'GET',
    });
  },

  async generateNextVideo(topic?: string): Promise<ApiResponse<import('../types/youtube').VideoGenerationTask>> {
    return request<ApiResponse<import('../types/youtube').VideoGenerationTask>>('/youtube/generation-tasks/generate_next/', {
      method: 'POST',
      body: JSON.stringify({ topic }),
    });
  },

  async getScheduledUploads(): Promise<PaginatedResponse<import('../types/youtube').ScheduledUpload>> {
    return request<PaginatedResponse<import('../types/youtube').ScheduledUpload>>('/youtube/scheduled-uploads/', {
      method: 'GET',
    });
  },

  async getDailyAnalytics(): Promise<PaginatedResponse<import('../types/youtube').DailyChannelAnalytics>> {
    return request<PaginatedResponse<import('../types/youtube').DailyChannelAnalytics>>('/youtube/daily-analytics/', {
      method: 'GET',
    });
  },

  async generateImageFromPrompt(prompt: string): Promise<ApiResponse<{ image_url: string; prompt: string; title: string }>> {
    return request<ApiResponse<{ image_url: string; prompt: string; title: string }>>('/youtube/generation-tasks/generate_image/', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  },

  async generateVideoFromPrompt(prompt: string, topic?: string): Promise<ApiResponse<import('../types/youtube').VideoGenerationTask & { upload_id?: number }>> {
    return request<ApiResponse<import('../types/youtube').VideoGenerationTask & { upload_id?: number }>>('/youtube/generation-tasks/generate_video_from_prompt/', {
      method: 'POST',
      body: JSON.stringify({ prompt, topic }),
    });
  },

  async confirmUpload(uploadId: number): Promise<ApiResponse<import('../types/youtube').ScheduledUpload>> {
    return request<ApiResponse<import('../types/youtube').ScheduledUpload>>(`/youtube/scheduled-uploads/${uploadId}/confirm_upload/`, {
      method: 'POST',
    });
  },

  async cancelUpload(uploadId: number): Promise<ApiResponse<import('../types/youtube').ScheduledUpload>> {
    return request<ApiResponse<import('../types/youtube').ScheduledUpload>>(`/youtube/scheduled-uploads/${uploadId}/cancel_upload/`, {
      method: 'POST',
    });
  },

  async sendDailyReport(chatId?: string): Promise<ApiResponse<{ report_text: string; telegram_sent: boolean; chat_id: string | null }>> {
    return request<ApiResponse<{ report_text: string; telegram_sent: boolean; chat_id: string | null }>>('/youtube/daily-analytics/send_daily_report/', {
      method: 'POST',
      body: JSON.stringify({ chat_id: chatId }),
    });
  },
};

