from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "is_admin", "is_superuser", ]
        extra_kwargs = {
            'password': {"write_only": True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    #
    # def validate(self, attrs):
    #     email = attrs.get('email',None)
    #     return super().validate(attrs)

    def validate_username(self, username):
        try:
            User.objects.get(username=username)
            raise ValidationError(detail="Username đã tồn tại", code="Username exist")
        except User.MultipleObjectsReturned:
            raise ValidationError(detail="Đã tồn tại nhiều username", code="Multi Username exist")
        except User.DoesNotExist:
            return username
        except Exception as e:
            raise e


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "is_admin", "is_superuser", ]
        extra_kwargs = {
            'password': {"write_only": True}
        }

    def validate(self, attrs):
        email = attrs.get('email', None)
        password = attrs.get('password', None)
        username = attrs.get('username', None)

        if email is None:
            raise ValidationError(detail="An email address is required to log in", code="EmailLoginError")

        if password is None:
            raise ValidationError(detail="A password address is required to log in", code="PasswordLoginError")

        user = authenticate(username=(email or username), password=password)

        if user is None:
            raise ValidationError(detail="A user with this email and password was not found",
                                  code="AuthenticateLoginError")

        if not user.is_active:
            raise ValidationError(detail="This user has been deactivated", code="ActivateAccountError")

        return {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'password': user.password,
            'is_admin': user.is_admin,
            'is_superuser': user.is_superuser
        }

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.serializers import TokenObtainSerializer

class TokenObtainPairSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data
