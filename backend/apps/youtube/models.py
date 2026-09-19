"""
YouTube Integration Models.
Defines Channel, Playlist, Video, and SyncJob models with PostgreSQL constraints.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel


class YouTubeChannel(TimeStampedModel):
    """
    Represents an integrated YouTube Channel.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='youtube_channels',
        help_text="Egasi bo'lgan foydalanuvchi"
    )
    channel_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="YouTube tomonidan berilgan noyob kanal ID (masalan: UC...)"
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, default='')
    custom_url = models.CharField(max_length=128, blank=True, default='')
    published_at = models.DateTimeField(null=True, blank=True)
    subscriber_count = models.BigIntegerField(default=0)
    video_count = models.PositiveIntegerField(default=0)
    view_count = models.BigIntegerField(default=0)
    thumbnail_url = models.URLField(max_length=500, blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True)
    api_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Kanal uchun maxsus YouTube API kaliti (ixtiyoriy)"
    )

    class Meta:
        verbose_name = 'YouTube Kanal'
        verbose_name_plural = 'YouTube Kanallar'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'channel_id'],
                name='unique_owner_channel'
            ),
            models.CheckConstraint(
                condition=models.Q(subscriber_count__gte=0),
                name='subscriber_count_non_negative'
            ),
            models.CheckConstraint(
                condition=models.Q(view_count__gte=0),
                name='channel_view_count_non_negative'
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.channel_id})"


class YouTubePlaylist(TimeStampedModel):
    """
    Represents a Playlist belonging to a YouTube Channel.
    """
    channel = models.ForeignKey(
        YouTubeChannel,
        on_delete=models.CASCADE,
        related_name='playlists'
    )
    playlist_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    published_at = models.DateTimeField(null=True, blank=True)
    item_count = models.PositiveIntegerField(default=0)
    thumbnail_url = models.URLField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name = 'YouTube Playlist'
        verbose_name_plural = 'YouTube Playlistlar'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.channel.title}"


class YouTubeVideo(TimeStampedModel):
    """
    Represents a Video belonging to a Channel and optionally a Playlist.
    """
    class PrivacyStatus(models.TextChoices):
        PUBLIC = 'public', 'Public'
        UNLISTED = 'unlisted', 'Unlisted'
        PRIVATE = 'private', 'Private'

    channel = models.ForeignKey(
        YouTubeChannel,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    playlist = models.ForeignKey(
        YouTubePlaylist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='videos'
    )
    video_id = models.CharField(
        max_length=32,
        unique=True,
        db_index=True
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, default='')
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    view_count = models.BigIntegerField(default=0, db_index=True)
    like_count = models.BigIntegerField(default=0)
    comment_count = models.BigIntegerField(default=0)
    thumbnail_url = models.URLField(max_length=500, blank=True, default='')
    privacy_status = models.CharField(
        max_length=20,
        choices=PrivacyStatus.choices,
        default=PrivacyStatus.PUBLIC,
        db_index=True
    )
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = 'YouTube Video'
        verbose_name_plural = 'YouTube Videolar'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['channel', '-published_at']),
            models.Index(fields=['channel', '-view_count']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(view_count__gte=0),
                name='video_view_count_non_negative'
            ),
            models.CheckConstraint(
                condition=models.Q(like_count__gte=0),
                name='video_like_count_non_negative'
            ),
            models.CheckConstraint(
                condition=models.Q(comment_count__gte=0),
                name='video_comment_count_non_negative'
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.video_id})"


class SyncJob(TimeStampedModel):
    """
    Audit log for YouTube API synchronization tasks.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    channel = models.ForeignKey(
        YouTubeChannel,
        on_delete=models.CASCADE,
        related_name='sync_jobs'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    items_synced = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default='')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Sinxronizatsiya Vazifasi'
        verbose_name_plural = 'Sinxronizatsiya Vazifalari'
        ordering = ['-created_at']

    def __str__(self):
        return f"Sync for {self.channel.title} - {self.status}"
