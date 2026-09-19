"""
URL routing for YouTube integration API.
"""
from rest_framework.routers import DefaultRouter
from .views import (
    YouTubeChannelViewSet,
    YouTubePlaylistViewSet,
    YouTubeVideoViewSet,
    SyncJobViewSet,
)

router = DefaultRouter()
router.register(r'channels', YouTubeChannelViewSet, basename='youtube-channel')
router.register(r'playlists', YouTubePlaylistViewSet, basename='youtube-playlist')
router.register(r'videos', YouTubeVideoViewSet, basename='youtube-video')
router.register(r'sync-jobs', SyncJobViewSet, basename='sync-job')

urlpatterns = router.urls
