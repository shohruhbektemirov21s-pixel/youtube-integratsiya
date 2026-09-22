/**
 * YouTube domain types matching apps.youtube models and serializers.
 */

export interface YouTubeChannel {
  id: number;
  channel_id: string;
  title: string;
  description: string;
  custom_url: string;
  published_at: string | null;
  subscriber_count: number;
  video_count: number;
  view_count: number;
  thumbnail_url: string;
  is_active: boolean;
  owner_username: string;
  playlists_count: number;
  total_videos: number;
  created_at: string;
  updated_at: string;
}

export interface ChannelCreatePayload {
  channel_id: string;
  title: string;
  description?: string;
  custom_url?: string;
}

export interface YouTubePlaylist {
  id: number;
  channel: number;
  channel_title: string;
  playlist_id: string;
  title: string;
  description: string;
  published_at: string | null;
  item_count: number;
  videos_count: number;
  thumbnail_url: string;
  created_at: string;
  updated_at: string;
}

export interface YouTubeVideo {
  id: number;
  channel: number;
  channel_title: string;
  playlist: number | null;
  playlist_title: string | null;
  video_id: string;
  title: string;
  description: string;
  published_at: string | null;
  duration_seconds: number;
  formatted_duration: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  thumbnail_url: string;
  privacy_status: 'public' | 'unlisted' | 'private';
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface SyncJob {
  id: number;
  channel: number;
  channel_title: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  items_synced: number;
  error_message: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface VideoStatistics {
  total_videos: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  avg_duration_seconds: number;
}

export interface FlowAIAccount {
  id: number;
  name: string;
  email: string;
  profile_dir: string;
  has_flow_credits: boolean;
  credits_remaining: number;
  initial_credits: number;
  has_youtube_channel: boolean;
  youtube_channel_name: string;
  youtube_channel_id: string;
  youtube_subscribers: number;
  is_active: boolean;
  last_used_at: string | null;
  last_inspected_at: string | null;
  inspection_status: string;
  created_at: string;
  updated_at: string;
}

export interface DetectedProfile {
  profile_dir: string;
  name: string;
  email: string;
}

export interface ChannelNiche {
  id: number;
  channel: number;
  channel_title: string;
  niche_name: string;
  description: string;
  tone: string;
  keywords: string[];
  prompt_guidelines: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VideoGenerationTask {
  id: number;
  account: number | null;
  account_name: string;
  topic: string;
  prompt: string;
  status: 'queued' | 'generating' | 'completed' | 'failed';
  video_file_path: string;
  video_url: string;
  credits_used: number;
  error_message: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduledUpload {
  id: number;
  channel: number;
  channel_title: string;
  video_task: number;
  video_topic: string;
  title: string;
  description: string;
  tags: string[];
  scheduled_date: string;
  scheduled_time: string;
  status: 'pending_confirmation' | 'scheduled' | 'processing' | 'published' | 'failed';
  youtube_video_id: string;
  published_at: string | null;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface DailyChannelAnalytics {
  id: number;
  channel: number;
  channel_title: string;
  date: string;
  total_views: number;
  total_subscribers: number;
  total_videos: number;
  views_growth_today: number;
  subscribers_growth_today: number;
  growth_rate_percent: number;
  telegram_report_sent: boolean;
  telegram_sent_at: string | null;
  created_at: string;
  updated_at: string;
}
