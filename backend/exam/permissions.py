from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Read/update for any auth user; delete only for the creator.

    Non-owner updates clone the question (handled in the serializer).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.method in ('PUT', 'PATCH'):
            return True
        owner_id = getattr(obj, 'created_by_id', None)
        return owner_id is not None and owner_id == request.user.id
