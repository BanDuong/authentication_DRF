from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id","username","email","password","is_admin","is_superuser",]
        extra_kwargs = {
            "password" : {"write_only": True}
        }

    def validate_username(self,username):
        try:
            User.objects.get(username=username)
            raise ValidationError(detail="Username đã tồn tại",code="Username exist")
        except User.MultipleObjectsReturned:
            raise ValidationError(detail="Đã tồn tại nhiều username",code="Multi Username exist")
        except User.DoesNotExist:
            return username
        except Exception as e:
            raise e

    def create(self, validated_data):
        password = validated_data.pop("password",None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance