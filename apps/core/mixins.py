"""
core/mixins.py

Reusable utilities for views across all apps.
"""
from django.core.exceptions import PermissionDenied


def check_ownership(obj, user, owner_field='seller'):
    """
    Raise PermissionDenied if user doesn't own the object.
    Use in views that need explicit ownership checks beyond
    get_object_or_404(..., seller=request.user).

    Example:
        check_ownership(listing, request.user, owner_field='seller')
    """
    owner = getattr(obj, owner_field, None)
    if owner != user:
        raise PermissionDenied
