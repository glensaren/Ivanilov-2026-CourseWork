from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request


class IsOwnerOrAdmin(BasePermission):
    """Разрешает изменение только владельцу объекта или администратору."""

    def has_object_permission(self, request: Request, view, obj) -> bool:
        """
        Проверяет право доступа к конкретному объекту.

        Args:
            request: объект запроса
            view: текущий ViewSet
            obj: объект модели

        Returns:
            True если доступ разрешён, иначе False
        """
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        return obj.user == request.user