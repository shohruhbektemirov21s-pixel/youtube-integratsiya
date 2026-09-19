"""
Core reusable permission classes.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request (GET, HEAD or OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

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
