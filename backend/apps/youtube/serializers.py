"""
Serializers for YouTube Channels, Playlists, Videos, and Sync Jobs.
Enforces strict input validation, regex sanitization, and IDOR prevention.
"""
import re
from rest_framework import serializers
from .models import (
    YouTubeChannel,
    YouTubePlaylist,
    YouTubeVideo,
    SyncJob,
    FlowAIAccount,
    ChannelNiche,
    VideoGenerationTask,
    ScheduledUpload,
    DailyChannelAnalytics,
)

# YouTube identifier format regex: alphanumeric, underscores, hyphens
YOUTUBE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+$')


class YouTubeChannelSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    playlists_count = serializers.IntegerField(read_only=True, default=0)
    total_videos = serializers.IntegerField(read_only=True, default=0)

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
        if len(cleaned) < 10 or len(cleaned) > 64:
            raise serializers.ValidationError("Kanal ID uzunligi 10 dan 64 gacha belgi bo'lishi kerak.")
        if not YOUTUBE_ID_PATTERN.match(cleaned):
            raise serializers.ValidationError("Kanal ID faqat lotin harflari, sonlar, chiziqcha va pastki chiziqdan iborat bo'lishi kerak.")
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

    def validate_channel(self, value):
        # Prevent IDOR: Ensure caller owns the channel
        request = self.context.get('request')
        if request and request.user and not request.user.is_staff:
            if value.owner != request.user:
                raise serializers.ValidationError("Siz faqat o'zingizga tegishli kanalga playlist qo'sha olasiz.")
        return value

    def validate_playlist_id(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Playlist ID bo'sh bo'lishi mumkin emas.")
        if not YOUTUBE_ID_PATTERN.match(cleaned):
            raise serializers.ValidationError("Playlist ID faqat harflar, sonlar va chiziqchalardan iborat bo'lishi kerak.")
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

    def validate_channel(self, value):
        # Prevent IDOR: Ensure caller owns the channel
        request = self.context.get('request')
        if request and request.user and not request.user.is_staff:
            if value.owner != request.user:
                raise serializers.ValidationError("Siz faqat o'zingizga tegishli kanalga video qo'sha olasiz.")
        return value

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
            raise serializers.ValidationError("YouTube Video ID 11 ta belgidan iborat bo'lishi kerak.")
        if not YOUTUBE_ID_PATTERN.match(cleaned):
            raise serializers.ValidationError("Video ID da ruxsat etilmagan belgilar mavjud.")
        return cleaned

    def validate(self, attrs):
        channel = attrs.get('channel') or (self.instance.channel if self.instance else None)
        playlist = attrs.get('playlist') or (self.instance.playlist if self.instance and 'playlist' not in attrs else None)

        if playlist and channel and playlist.channel_id != channel.id:
            raise serializers.ValidationError({"playlist": "Tanlangan playlist ushbu kanalga tegishli emas."})

        request = self.context.get('request')
        if playlist and request and not request.user.is_staff:
            if playlist.channel.owner != request.user:
                raise serializers.ValidationError({"playlist": "Siz faqat o'zingizga tegishli playlistni tanlashingiz mumkin."})

        return attrs


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


class FlowAIAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for Flow AI and YouTube accounts.
    """
    class Meta:
        model = FlowAIAccount
        fields = [
            'id',
            'name',
            'email',
            'profile_dir',
            'has_flow_credits',
            'credits_remaining',
            'initial_credits',
            'has_youtube_channel',
            'youtube_channel_name',
            'youtube_channel_id',
            'youtube_subscribers',
            'is_active',
            'last_used_at',
            'last_inspected_at',
            'inspection_status',
            'created_at',
            'updated_at',
        ]
        # Kredit balansi va profil yo'li API orqali yozilmaydi: ular faqat
        # haqiqiy generatsiya/tekshiruv natijasida server tomonda o'zgaradi.
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'credits_remaining', 'initial_credits', 'last_used_at',
            'profile_dir', 'inspection_status', 'last_inspected_at',
        ]


class ChannelNicheSerializer(serializers.ModelSerializer):
    """
    Serializer for single-niche strategy configuration.
    """
    channel_title = serializers.ReadOnlyField(source='channel.title')

    class Meta:
        model = ChannelNiche
        fields = [
            'id',
            'channel',
            'channel_title',
            'niche_name',
            'description',
            'tone',
            'keywords',
            'prompt_guidelines',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'channel_title']


class VideoGenerationTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Flow AI video generation tasks.
    """
    account_name = serializers.ReadOnlyField(source='account.name')

    class Meta:
        model = VideoGenerationTask
        fields = [
            'id',
            'account',
            'account_name',
            'topic',
            'prompt',
            'status',
            'video_file_path',
            'video_url',
            'credits_used',
            'error_message',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        # status/credits_used — kredit hisobini chetlab o'tishning to'g'ridan-to'g'ri yo'li edi
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'account_name',
            'status', 'credits_used', 'completed_at', 'video_file_path',
        ]


class ScheduledUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for 19:00 daily YouTube video upload queue.
    """
    channel_title = serializers.ReadOnlyField(source='channel.title')
    video_topic = serializers.ReadOnlyField(source='video_task.topic')

    class Meta:
        model = ScheduledUpload
        fields = [
            'id',
            'channel',
            'channel_title',
            'video_task',
            'video_topic',
            'title',
            'description',
            'tags',
            'scheduled_date',
            'scheduled_time',
            'status',
            'youtube_video_id',
            'published_at',
            'error_message',
            'created_at',
            'updated_at',
        ]
        # status — PATCH bilan to'g'ridan-to'g'ri 'published' qilish mumkin edi,
        # ya'ni tasdiqlash oqimini butunlay aylanib o'tish. Holat faqat
        # confirm_upload/cancel_upload action'lari orqali o'zgaradi.
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'channel_title', 'video_topic',
            'status', 'youtube_video_id', 'published_at', 'error_message',
        ]


class DailyChannelAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for daily metrics and Telegram growth reports.
    """
    channel_title = serializers.ReadOnlyField(source='channel.title')

    class Meta:
        model = DailyChannelAnalytics
        fields = [
            'id',
            'channel',
            'channel_title',
            'date',
            'total_views',
            'total_subscribers',
            'total_videos',
            'views_growth_today',
            'subscribers_growth_today',
            'growth_rate_percent',
            'telegram_report_sent',
            'telegram_sent_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'channel_title']
