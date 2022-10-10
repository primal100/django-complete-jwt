from django.contrib.auth import get_user_model
from rest_framework_simplejwt.models import TokenUser
from functools import cached_property


User = get_user_model()


class CompleteTokenUser(TokenUser):

    def __getattr__(self, item):
        return getattr(self.user, item)

    @cached_property
    def user(self):
        return User.objects.get(id=self.id)

    def save(self, *args, **kwargs):
        return self.user.save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.user.delete(*args, **kwargs)

    def set_password(self, raw_password):
        return self.user.set_password(raw_password)

    def check_password(self, raw_password):
        raise self.user.check_password(raw_password)

    @cached_property
    def email(self):
        return self.token.get('email', '')

    def has_perm(self, *args, **kwargs):
        return self.user.has_perm(*args, **kwargs)
