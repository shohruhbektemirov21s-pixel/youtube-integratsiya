"""
Serializers for YouTube Channels, Playlists, Videos, and Sync Jobs.
Enforces strict input validation and field security.
"""
from rest_framework import serializers
from .models import YouTubeChannel, YouTubePlaylist, YouTubeVideo, SyncJob


class YouTubeChannelSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    playlists_count = serializers.IntegerField(read_only=True, default=0)
    total_videos = serializers.IntegerField(read_only=True, default=0)
    api_key = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = YouTubeChannel
        fields = [
            'id',
            'channel_id',
            'title',
            'description',
            'custom_url',
            'published_at',
            'subscriber_count',
            'video_count',
            'view_count',
            'thumbnail_url',
            'is_active',
            'api_key',
            'owner_username',
            'playlists_count',
            'total_videos',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_username']

    def validate_channel_id(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Kanal ID bo'sh bo'lishi mumkin emas.")
        if len(cleaned) < 10:
            raise serializers.ValidationError("Kanal ID uzunligi kamida 10 ta belgidan iborat bo'lishi kerak.")
        return cleaned

    def validate_title(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Kanal sarlavhasi bo'sh bo'lishi mumkin emas.")
        return cleaned


class YouTubePlaylistSerializer(serializers.ModelSerializer):
    channel_title = serializers.ReadOnlyField(source='channel.title')
    videos_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = YouTubePlaylist
        fields = [
            'id',
            'channel',
            'channel_title',
            'playlist_id',
            'title',
            'description',
            'published_at',
            'item_count',
            'videos_count',
            'thumbnail_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'channel_title']

    def validate_playlist_id(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Playlist ID bo'sh bo'lishi mumkin emas.")
        return cleaned


class YouTubeVideoSerializer(serializers.ModelSerializer):
    channel_title = serializers.ReadOnlyField(source='channel.title')
    playlist_title = serializers.ReadOnlyField(source='playlist.title')
    formatted_duration = serializers.SerializerMethodField()

    class Meta:
        model = YouTubeVideo
        fields = [
            'id',
            'channel',
            'channel_title',
            'playlist',
            'playlist_title',
            'video_id',
            'title',
            'description',
            'published_at',
            'duration_seconds',
            'formatted_duration',
            'view_count',
            'like_count',
            'comment_count',
            'thumbnail_url',
            'privacy_status',
            'tags',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'channel_title', 'playlist_title']

    def get_formatted_duration(self, obj) -> str:
        total_seconds = obj.duration_seconds or 0
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def validate_video_id(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Video ID bo'sh bo'lishi mumkin emas.")
        if len(cleaned) != 11:
            raise serializers.ValidationError("YouTube Video ID odatda 11 ta belgidan iborat bo'ladi.")
        return cleaned


class SyncJobSerializer(serializers.ModelSerializer):
    channel_title = serializers.ReadOnlyField(source='channel.title')

    class Meta:
        model = SyncJob
        fields = [
            'id',
            'channel',
            'channel_title',
            'status',
            'items_synced',
            'error_message',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'items_synced',
            'error_message',
            'completed_at',
            'created_at',
            'updated_at',
            'channel_title',
        ]
