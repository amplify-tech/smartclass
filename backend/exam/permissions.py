from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Shared question bank: read/patch for any auth user; delete for owner.

    Non-owner PATCH clones via QuestionSerializer instead of mutating.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.method == 'PATCH':
            return True
        owner_id = getattr(obj, 'created_by_id', None)
        return owner_id is not None and owner_id == request.user.id
