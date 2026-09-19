"""
URL routing for YouTube integration API.
"""
from rest_framework.routers import DefaultRouter
from .views import (
    YouTubeChannelViewSet,
    YouTubePlaylistViewSet,
    YouTubeVideoViewSet,
    SyncJobViewSet,
    FlowAIAccountViewSet,
    ChannelNicheViewSet,
    VideoGenerationTaskViewSet,
    ScheduledUploadViewSet,
    DailyChannelAnalyticsViewSet,
)

router = DefaultRouter()
router.register(r'channels', YouTubeChannelViewSet, basename='youtube-channel')
router.register(r'playlists', YouTubePlaylistViewSet, basename='youtube-playlist')
router.register(r'videos', YouTubeVideoViewSet, basename='youtube-video')
router.register(r'sync-jobs', SyncJobViewSet, basename='sync-job')
router.register(r'flow-accounts', FlowAIAccountViewSet, basename='flow-account')
router.register(r'niches', ChannelNicheViewSet, basename='channel-niche')
router.register(r'generation-tasks', VideoGenerationTaskViewSet, basename='generation-task')
router.register(r'scheduled-uploads', ScheduledUploadViewSet, basename='scheduled-upload')
router.register(r'daily-analytics', DailyChannelAnalyticsViewSet, basename='daily-analytic')

urlpatterns = router.urls
