from rest_framework.permissions import BasePermission


class UserNotAuthenticatedOnly(BasePermission):
    message = _(
        'It is required to logout before making this request')

    def has_permission(self, request, view):
        return not (request.user and request.user.is_authenticated)
