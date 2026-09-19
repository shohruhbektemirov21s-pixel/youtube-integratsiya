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
