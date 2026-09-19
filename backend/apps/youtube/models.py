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


class FlowAIAccount(TimeStampedModel):
    """
    Tracks browser-authenticated Flow AI accounts and credit quotas.
    """
    name = models.CharField(max_length=100, help_text="Akkaunt nomi (masalan: Flow AI Akkaunt 1)")
    email = models.EmailField(blank=True, default='', help_text="Akkaunt emaili (agar mavjud bo'lsa)")
    profile_dir = models.CharField(
        max_length=255,
        default="Default",
        help_text="Chrome profil katalogi (masalan: Default, Profile 1, Profile 3, Profile 4, Profile 6)"
    )
    has_flow_credits = models.BooleanField(default=True, help_text="Ushbu akkauntda Flow AI kreditlari bormi")
    credits_remaining = models.IntegerField(default=1000, help_text="Qolgan kreditlar miqdori")
    initial_credits = models.IntegerField(default=1000, help_text="Dastlabki kredit miqdori")

    has_youtube_channel = models.BooleanField(default=False, help_text="Ushbu akkauntda YouTube kanal bormi")
    youtube_channel_name = models.CharField(max_length=255, blank=True, default='', help_text="YouTube kanal nomi")
    youtube_channel_id = models.CharField(max_length=100, blank=True, default='', help_text="YouTube kanal ID")
    youtube_subscribers = models.BigIntegerField(default=0, help_text="YouTube obunachilar soni")

    is_active = models.BooleanField(default=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_inspected_at = models.DateTimeField(null=True, blank=True, help_text="Oxirgi marta brauzer orqali tekshirilgan vaqt")
    inspection_status = models.CharField(max_length=50, default="verified", help_text="Holat: verified, pending, not_found")

    class Meta:
        verbose_name = 'Flow AI Akkaunt'
        verbose_name_plural = 'Flow AI Akkauntlar'
        ordering = ['-credits_remaining', 'id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(credits_remaining__gte=0),
                name='flow_ai_credits_non_negative'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.credits_remaining}/{self.initial_credits} kredit)"


class ChannelNiche(TimeStampedModel):
    """
    Defines the single topic/niche strategy for the channel.
    """
    channel = models.OneToOneField(
        YouTubeChannel,
        on_delete=models.CASCADE,
        related_name='niche_strategy'
    )
    niche_name = models.CharField(max_length=255, help_text="Asosiy kanal mavzusi (masalan: Sun'iy Intellekt va Kelajak Texnologiyalari)")
    description = models.TextField(help_text="Mavzuning batafsil tasnifi va maqsadli auditoriya")
    tone = models.CharField(max_length=100, default="informative, engaging, futuristic")
    keywords = models.JSONField(default=list, blank=True, help_text="Asosiy SEO kalit so'zlari")
    prompt_guidelines = models.TextField(
        blank=True,
        default="Har bir video 1ta mavzu doirasida, tomoshabinni jalb qiluvchi sarlavha va qiziqarli vizual prompt bilan yaratilsin."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Kanal Mavzusi (Niche)'
        verbose_name_plural = 'Kanal Mavzulari (Niches)'

    def __str__(self):
        return f"{self.channel.title} - {self.niche_name}"


class VideoGenerationTask(TimeStampedModel):
    """
    Tracks video generation lifecycle through Flow AI.
    """
    class GenerationStatus(models.TextChoices):
        QUEUED = 'queued', 'Navbatda'
        GENERATING = 'generating', 'Generatsiya qilinmoqda'
        COMPLETED = 'completed', 'Tayyor'
        FAILED = 'failed', 'Xatolik'

    account = models.ForeignKey(
        FlowAIAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generation_tasks'
    )
    topic = models.CharField(max_length=255)
    prompt = models.TextField(help_text="Flow AI uchun Gemini tomonidan yaratilgan prompt")
    status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.QUEUED,
        db_index=True
    )
    video_file_path = models.CharField(max_length=500, blank=True, default='')
    video_url = models.URLField(max_length=500, blank=True, default='')
    credits_used = models.PositiveIntegerField(default=10)
    error_message = models.TextField(blank=True, default='')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Video Generatsiya Vazifasi'
        verbose_name_plural = 'Video Generatsiya Vazifalari'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.topic} ({self.status})"


class ScheduledUpload(TimeStampedModel):
    """
    Manages daily video uploads scheduled for 19:00.
    """
    class UploadStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Rejalashtirilgan'
        PROCESSING = 'processing', 'Yuklanmoqda'
        PUBLISHED = 'published', 'Nashr qilindi'
        FAILED = 'failed', 'Xatolik'

    channel = models.ForeignKey(
        YouTubeChannel,
        on_delete=models.CASCADE,
        related_name='scheduled_uploads'
    )
    video_task = models.OneToOneField(
        VideoGenerationTask,
        on_delete=models.CASCADE,
        related_name='upload_schedule'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    tags = models.JSONField(default=list, blank=True)
    scheduled_date = models.DateField(db_index=True)
    scheduled_time = models.TimeField(default="19:00:00")
    status = models.CharField(
        max_length=20,
        choices=UploadStatus.choices,
        default=UploadStatus.SCHEDULED,
        db_index=True
    )
    youtube_video_id = models.CharField(max_length=64, blank=True, default='')
    published_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Rejalashtirilgan Yuklash'
        verbose_name_plural = 'Rejalashtirilgan Yuklashlar'
        ordering = ['scheduled_date', 'scheduled_time']
        constraints = [
            models.UniqueConstraint(
                fields=['channel', 'scheduled_date', 'scheduled_time'],
                name='unique_channel_schedule_slot'
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.scheduled_date} {self.scheduled_time} ({self.status})"


class DailyChannelAnalytics(TimeStampedModel):
    """
    Daily snapshot of channel metrics and growth reporting.
    """
    channel = models.ForeignKey(
        YouTubeChannel,
        on_delete=models.CASCADE,
        related_name='daily_analytics'
    )
    date = models.DateField(db_index=True)
    total_views = models.BigIntegerField(default=0)
    total_subscribers = models.BigIntegerField(default=0)
    total_videos = models.PositiveIntegerField(default=0)
    views_growth_today = models.BigIntegerField(default=0, help_text="Bugungi ko'rishlar o'sishi")
    subscribers_growth_today = models.BigIntegerField(default=0, help_text="Bugungi obunachilar o'sishi")
    growth_rate_percent = models.FloatField(default=0.0, help_text="Foizdagi o'sish darajasi")
    telegram_report_sent = models.BooleanField(default=False)
    telegram_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Kunlik Statistika'
        verbose_name_plural = 'Kunlik Statistikalar'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['channel', 'date'],
                name='unique_channel_daily_analytic'
            )
        ]

    def __str__(self):
        return f"{self.channel.title} - {self.date} (+{self.views_growth_today} ko'rish)"
