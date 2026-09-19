"""
ViewSets for YouTube Channels, Playlists, Videos, and Sync Jobs.
Optimized with select_related, prefetch_related, and aggregations to prevent N+1 query problems.
"""
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsOwnerOrReadOnly
from .models import YouTubeChannel, YouTubePlaylist, YouTubeVideo, SyncJob
from .serializers import (
    YouTubeChannelSerializer,
    YouTubePlaylistSerializer,
    YouTubeVideoSerializer,
    SyncJobSerializer,
)


class YouTubeChannelViewSet(viewsets.ModelViewSet):
    """
    CRUD for YouTube Channels with N+1 query optimization.
    """
    serializer_class = YouTubeChannelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'channel_id', 'custom_url']
    ordering_fields = ['created_at', 'subscriber_count', 'video_count', 'view_count']
    ordering = ['-created_at']

    def get_queryset(self):
        # Prevent N+1 queries using select_related and Count annotations
        return YouTubeChannel.objects.select_related('owner').annotate(
            playlists_count=Count('playlists', distinct=True),
            total_videos=Count('videos', distinct=True)
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrReadOnly])
    def trigger_sync(self, request, pk=None):
        """
        Manually trigger a sync job for a specific YouTube channel using YouTubeService.
        """
        from .services import YouTubeService
        channel = self.get_object()
        service = YouTubeService()
        job = service.sync_channel(channel)

        return Response(
            {
                "success": job.status != SyncJob.Status.FAILED,
                "message": f"'{channel.title}' kanali uchun sinxronizatsiya {job.status}.",
                "data": SyncJobSerializer(job).data
            },
            status=status.HTTP_200_OK if job.status != SyncJob.Status.FAILED else status.HTTP_400_BAD_REQUEST
        )


class YouTubePlaylistViewSet(viewsets.ModelViewSet):
    """
    CRUD for YouTube Playlists with channel relationship optimization.
    """
    serializer_class = YouTubePlaylistSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'playlist_id']
    ordering_fields = ['published_at', 'created_at', 'item_count']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = YouTubePlaylist.objects.select_related('channel', 'channel__owner').annotate(
            videos_count=Count('videos', distinct=True)
        )
        channel_id = self.request.query_params.get('channel_id')
        if channel_id:
            queryset = queryset.filter(channel__channel_id=channel_id)
        return queryset


class YouTubeVideoViewSet(viewsets.ModelViewSet):
    """
    CRUD for YouTube Videos with optimized queries and analytics.
    """
    serializer_class = YouTubeVideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'video_id']
    ordering_fields = ['published_at', 'view_count', 'like_count', 'duration_seconds', 'created_at']
    ordering = ['-published_at', '-created_at']

    def get_queryset(self):
        # select_related channel and playlist to eliminate N+1 queries on nested fields
        queryset = YouTubeVideo.objects.select_related('channel', 'playlist', 'channel__owner')

        # URL Query param filtering
        channel_id = self.request.query_params.get('channel_id')
        playlist_id = self.request.query_params.get('playlist_id')
        privacy = self.request.query_params.get('privacy_status')

        if channel_id:
            queryset = queryset.filter(channel__channel_id=channel_id)
        if playlist_id:
            queryset = queryset.filter(playlist__playlist_id=playlist_id)
        if privacy:
            queryset = queryset.filter(privacy_status=privacy)

        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Calculates aggregated video analytics across all filtered videos.
        """
        qs = self.get_queryset()
        stats = qs.aggregate(
            total_videos=Count('id'),
            total_views=Sum('view_count'),
            total_likes=Sum('like_count'),
            total_comments=Sum('comment_count'),
            avg_duration=Avg('duration_seconds')
        )

        return Response({
            "success": True,
            "data": {
                "total_videos": stats['total_videos'] or 0,
                "total_views": stats['total_views'] or 0,
                "total_likes": stats['total_likes'] or 0,
                "total_comments": stats['total_comments'] or 0,
                "avg_duration_seconds": round(stats['avg_duration'] or 0, 1),
            }
        })


class SyncJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only audit log for synchronization jobs.
    """
    serializer_class = SyncJobSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = SyncJob.objects.select_related('channel', 'channel__owner')
        channel_id = self.request.query_params.get('channel_id')
        if channel_id:
            queryset = queryset.filter(channel__channel_id=channel_id)
        return queryset
