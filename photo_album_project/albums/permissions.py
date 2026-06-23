from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    """Разрешает изменение только владельцу объекта или администратору"""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        return obj.user == request.user