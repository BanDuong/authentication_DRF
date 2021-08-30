import binascii
import base64
from django.contrib.auth.backends import ModelBackend
from .models import User
from django.contrib.auth import get_user_model, authenticate
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
import jwt
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()  # C2: from django.conf import settings   User = settings.AUTH_USER_MODEL
HTTP_HEADER_ENCODING = 'iso-8859-1'


class CustomeBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.EMAIL_FIELD)
        if username is None or password is None:
            raise exceptions.ValidationError(detail="check email or password again", code="ErrorEntity")
        try:
            user = UserModel._default_manager.get_by_natural_key(username)  # xử lý ngôn ngữ tự nhiên với email
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):  # Reject users with is_active=False
                return user

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise exceptions.ValidationError(detail="User not exist", code="UserNotExist")
        return user if self.user_can_authenticate(user) else None


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason


def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.

    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if isinstance(auth, str):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


class JWTAuthentication(BaseAuthentication):
    # authentication_header_prefix = 'Token'

    def authenticate(self, request):
        authorization_header = get_authorization_header(request).split()

        if not authorization_header:
            return None
        try:
            # header = 'Token xxxxxxxxxxxxxxxxxxxxxxxx'
            access_token = authorization_header[1]
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('access_token expired')
        except IndexError:
            raise exceptions.AuthenticationFailed('Token prefix missing')

        user = UserModel.objects.filter(id=payload['id']).first()
        if user is None:
            raise exceptions.AuthenticationFailed('User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('user is inactive')

        # self.enforce_csrf(request)
        return (user, None)

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation
        """
        check = CSRFCheck()
        # populates request.META['CSRF_COOKIE'], which is used in process_view()
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        print(reason)
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)
