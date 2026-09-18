from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Authenticated users may read; only the creator may update/delete."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner_id = getattr(obj, 'created_by_id', None)
        return owner_id is not None and owner_id == request.user.id
