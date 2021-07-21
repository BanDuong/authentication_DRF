from django.contrib.auth.backends import ModelBackend
from .models import User
from common.errors import *
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

UserModel = get_user_model()  # C2: from django.conf import settings   User = settings.AUTH_USER_MODEL


class CustomeBackend(ModelBackend):

    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None:
            email = kwargs.get(UserModel.EMAIL_FIELD)
        if email is None or password is None:
            raise ValidationError(detail="check email or password again", code="ErrorEntity")
        try:
            user = UserModel._default_manager.get_by_natural_key(email)  # xử lý ngôn ngữ tự nhiên với email
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):  # Reject users with is_active=False
                return user

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError(detail="User not exist", code="UserNotExist")
        return user if self.user_can_authenticate(user) else None
