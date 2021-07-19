from rest_framework import serializers
from .models import User
from rest_framework.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id","username","email","password","is_admin","is_superuser",]
        extra_kwargs = {
            'password': {"write_only": True}
        }

    def create(self,validated_data):
        password = validated_data.pop('password',None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    # def update(self,instance,validated_data):
    #
    #     instance.set_password(validated_data['password'])
    #     instance.first_name = validated_data['first_name']
    #     instance.last_name = validated_data['last_name']
    #     instance.email = validated_data['email']
    #     instance.username = validated_data['username']
    #     instance.is_staff = validated_data['is_staff']
    #     instance.is_active = validated_data['is_active']
    #     instance.is_admin = validated_data['is_admin']
    #     instance.is_superuser = validated_data['is_superuser']
    #     instance.save()
    #
    #     return instance

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
