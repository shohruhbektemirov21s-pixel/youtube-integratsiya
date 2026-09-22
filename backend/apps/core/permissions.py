"""
Core reusable permission classes.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        """View darajasidagi tekshiruv.

        Busiz `has_object_permission` faqat MAVJUD obyektlar uchun ishlardi:
        `POST /channels/` obyektga ega emas, shuning uchun ruxsat bosqichini
        umuman chetlab o'tib, anonim so'rov kanal yarata olardi.
        """
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # O'qish: faqat egasi yoki staff (ilgari hamma o'qiy olardi — IDOR)
        owner_obj = getattr(obj, 'owner', None)
        if owner_obj is None:
            channel_obj = getattr(obj, 'channel', None)
            owner_obj = getattr(channel_obj, 'owner', None) if channel_obj else None

        if request.method in permissions.SAFE_METHODS:
            if request.user and request.user.is_staff:
                return True
            return owner_obj is None or owner_obj == request.user

        # Write permissions are only allowed to the owner or staff
        if request.user and request.user.is_staff:
            return True

        owner = getattr(obj, 'owner', None)
        if owner is not None:
            return owner == request.user

        # If object has channel with owner (e.g., Playlist or Video)
        channel = getattr(obj, 'channel', None)
        if channel is not None and getattr(channel, 'owner', None) is not None:
            return channel.owner == request.user

        return False


class IsOwnerOfRelatedChannel(permissions.BasePermission):
    """Avtomatlashtirish resurslari uchun: autentifikatsiya + kanal egaligi.

    FlowAIAccount / VideoGenerationTask / ScheduledUpload / DailyChannelAnalytics
    modellarida `owner` maydoni yo'q, shuning uchun mavjud bo'lsa `channel.owner`
    bo'yicha, bo'lmasa staff bo'yicha tekshiriladi.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        channel = getattr(obj, 'channel', None)
        owner = getattr(channel, 'owner', None) if channel is not None else None
        if owner is not None:
            return owner == request.user
        # Kanalga bog'lanmagan resurs (masalan Flow AI akkaunti) — faqat o'qish
        return request.method in permissions.SAFE_METHODS
