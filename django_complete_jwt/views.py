from functools import wraps
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import generics
from django.contrib.auth.models import update_last_login
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase
from social_core.exceptions import MissingBackend, AuthException
from social_core.utils import user_is_active
from social_django.utils import load_strategy, load_backend
from .permissions import UserNotAuthenticatedOnly
from .serializers import (fill_token, TokenLogoutSerializer,
                          TokenObtainPairCustomSerializer, OAuthTokenObtainSerializer)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairCustomSerializer


class TokenLogoutView(TokenViewBase):
    serializer_class = TokenLogoutSerializer


def psa(func):
    @wraps(func)
    def wrapper(view, request, backend, *args, **kwargs):
        request.social_strategy = load_strategy(request)
        # backward compatibility in attribute name, only if not already
        # defined
        if not hasattr(request, 'strategy'):
            request.strategy = request.social_strategy

        try:
            request.backend = load_backend(request.social_strategy,
                                           backend, '')
        except MissingBackend:
            raise Http404('Backend not found')
        return func(view, request, backend, *args, **kwargs)
    return wrapper


def do_complete(backend, data, *args, request=None, **kwargs):

    user = backend.do_auth(data['token'], *args, request=request, **kwargs)

    if user_is_active(user) or backend.setting('INACTIVE_USER_LOGIN', False):
        return user
    else:
        raise InvalidToken


class OAuthLogin(generics.GenericAPIView):
    serializer_class = OAuthTokenObtainSerializer
    token_class = RefreshToken
    permission_classes = (UserNotAuthenticatedOnly,)

    default_error_messages = {
        "token_invalid": _("No active account found with the given credentials")
    }

    @psa
    def post(self, request, backend):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = do_complete(request.backend, serializer.data, request=request)
        except AuthException:
            raise InvalidToken

        refresh = fill_token(user, self.get_token(user))
        is_new = getattr(user, 'is_brand_new', False)

        data = {"is_new": is_new, "refresh": str(refresh), "access": str(refresh.access_token)}

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        return Response(data, status=status.HTTP_200_OK)

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)
