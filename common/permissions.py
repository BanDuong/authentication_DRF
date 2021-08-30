from rest_framework.permissions import BasePermission, SAFE_METHODS
import jwt
from django.conf import settings
from myapp.models import User

class IsAuthenticate(BasePermission):
    message = "Authenticate account"

    def has_permission(self, request, view):
        user = request.user

        if user:
            instance = User.objects.filter(id=user.id).first()
            if instance:
                return True
            else:
                return False
        else:
            return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user

