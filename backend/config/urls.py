"""
URL configuration for YouTube Integration project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls')),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/youtube/', include('apps.youtube.urls')),
]
