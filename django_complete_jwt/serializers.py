from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed


User = get_user_model()
default_token_attrs = ("email", "first_name", "last_name", "is_staff")


def fill_token(user, token):
    token_attrs = settings.get("JWT_COMPLETE_TOKEN_ATTRS", default_token_attrs)
    for attr in token_attrs:
        token[attr] = getattr(user, attr)
    return token


class TokenObtainPairCustomSerializer(TokenObtainPairSerializer):

    default_error_messages = {
        'account_not_confirmed': _(
            'Authentication was successful but this account is not active yet. Please check your email for a confirmation email. It may be in your spam or junk folder.')
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return fill_token(user, token)

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except AuthenticationFailed:
            user_filter_kwargs = {
                self.username_field: attrs[self.username_field]
            }
            try:
                user = User.objects.get(**user_filter_kwargs)
                if not user.is_active and user.check_password(attrs['password']):
                    raise AuthenticationFailed(
                        self.error_messages['account_not_confirmed'],
                        'account_not_confirmed',)
            except User.DoesNotExist:
                pass
            raise


class TokenLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
            refresh.blacklist()
        except TokenError:
            pass    # Token invalid or already blacklisted
        return {}


class OAuthTokenObtainSerializer(serializers.Serializer):
    token_class = None

    token = serializers.CharField(required=True)

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)
