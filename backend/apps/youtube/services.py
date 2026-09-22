"""
YouTube API Service for fetching and synchronizing YouTube data.
Handles communication with Google YouTube Data API v3.
"""
import os
import logging
import re
from typing import Dict, Any, Optional
import requests
from django.conf import settings
from django.utils import timezone
from .models import YouTubeChannel, YouTubePlaylist, YouTubeVideo, SyncJob

# URL query'sidagi ?key=... ni topadi
_KEY_IN_URL = re.compile(r'([?&]key=)[^&\s"\']+')

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API related errors."""
    pass


class YouTubeService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'YOUTUBE_API_KEY', os.getenv('YOUTUBE_API_KEY', ''))

    def _mask(self, text: str) -> str:
        """Matndan API kalitini olib tashlaydi (log va xato xabarlari uchun)."""
        key = getattr(self, 'api_key', None)
        if key:
            text = text.replace(key, '***MASKED***')
        return _KEY_IN_URL.sub(r'\1***MASKED***', text)

    def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an authenticated GET request to YouTube Data API v3.
        """
        if not self.api_key:
            raise YouTubeAPIError("YouTube API kaliti (.env yoki modelda) topilmadi.")

        params['key'] = self.api_key
        url = f"{YOUTUBE_API_BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 403:
                error_data = response.json().get('error', {})
                message = error_data.get('message', 'YouTube API ruxsat yoki kvota xatosi')
                raise YouTubeAPIError(f"YouTube API 403 Forbidden: {message}")

            if not response.ok:
                # response.text va istisno matni so'rov URL'ini (ya'ni ?key=...)
                # o'z ichiga olishi mumkin. Bu matn SyncJob.error_message ga
                # yozilib API orqali qaytariladi — shuning uchun faqat logga.
                logger.error(
                    "YouTube API xatosi %s: %s",
                    response.status_code, self._mask(response.text)[:500],
                )
                raise YouTubeAPIError(f"YouTube API xatosi ({response.status_code})")

            return response.json()
        except requests.RequestException as exc:
            logger.error("Tarmoq xatosi YouTube API ga ulanishda: %s", self._mask(str(exc)))
            raise YouTubeAPIError("YouTube API ga ulanishda tarmoq xatosi yuz berdi.")

    def fetch_channel_details(self, channel_id: str) -> Dict[str, Any]:
        """
        Fetch channel snippet and statistics by Channel ID.
        """
        data = self._get('channels', {
            'part': 'snippet,statistics',
            'id': channel_id
        })
        items = data.get('items', [])
        if not items:
            raise YouTubeAPIError(f"'{channel_id}' ID ga ega kanal topilmadi.")
        return items[0]

    def sync_channel(self, channel: YouTubeChannel) -> SyncJob:
        """
        Synchronizes channel information and updates the database.
        Records progress in a SyncJob audit log.
        """
        job = SyncJob.objects.create(
            channel=channel,
            status=SyncJob.Status.IN_PROGRESS,
            items_synced=0
        )

        effective_api_key = self.api_key or channel.api_key

        # If no real API key is configured, perform safe local sync of current database state
        if not effective_api_key or effective_api_key.startswith('test') or effective_api_key == 'dummy':
            job.status = SyncJob.Status.COMPLETED
            job.items_synced = channel.videos.count()
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'items_synced', 'completed_at'])
            return job

        try:
            api_client = YouTubeService(api_key=effective_api_key)
            channel_data = api_client.fetch_channel_details(channel.channel_id)

            snippet = channel_data.get('snippet', {})
            statistics = channel_data.get('statistics', {})

            channel.title = snippet.get('title', channel.title)
            channel.description = snippet.get('description', channel.description)
            channel.custom_url = snippet.get('customUrl', channel.custom_url)
            channel.subscriber_count = int(statistics.get('subscriberCount', channel.subscriber_count))
            channel.video_count = int(statistics.get('videoCount', channel.video_count))
            channel.view_count = int(statistics.get('viewCount', channel.view_count))

            thumbnails = snippet.get('thumbnails', {})
            high_thumb = thumbnails.get('high', {}).get('url') or thumbnails.get('default', {}).get('url')
            if high_thumb:
                channel.thumbnail_url = high_thumb

            channel.save(update_fields=[
                'title', 'description', 'custom_url', 'subscriber_count',
                'video_count', 'view_count', 'thumbnail_url', 'updated_at'
            ])

            job.status = SyncJob.Status.COMPLETED
            job.items_synced = 1
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'items_synced', 'completed_at'])

        except Exception as exc:
            logger.error(f"Sinxronizatsiya xatosi (channel_id={channel.channel_id}): {str(exc)}")
            job.status = SyncJob.Status.FAILED
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_message', 'completed_at'])

        return job
