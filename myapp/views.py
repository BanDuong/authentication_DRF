from django.shortcuts import render, redirect
from django.views import View
from .models import Questions, Answers, User
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from common.errors import *
from .serializers import UserSerializer, LoginSerializer
from rest_framework.exceptions import AuthenticationFailed, ValidationError
import datetime
import jwt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from .token import generate_access_token, generate_fresh_token
from django.conf import settings
from .backends import JWTAuthentication
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page
from django.core.cache import cache

CACHE_TTL = getattr(settings,"CACHE_TTL",DEFAULT_TIMEOUT)

class index(View):
    def get(self, request):
        qss = Questions.objects.all()
        content = {'qs': qss}
        return render(request, 'myapp/index.html', context=content)

    def post(self, request):
        qs_id = request.POST.get('questions')
        obj_qs = Questions.objects.get(pk=qs_id)
        qs = obj_qs.question
        img = request.FILES.get('image')
        ans = Answers(question=obj_qs, answer=request.POST.get('answer'), image=img)
        ans.save()
        content = {'qs_id': qs_id, 'ans': ans.answer, 'image': ans.image, 'qs': qs}
        return render(request, 'myapp/save.html', context=content)


# ----------------------------------------User-----------------------------------------#

class GetPostUser(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            raise ErrCannotListEntity(entity="User", err=e)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            raise ErrCannotCreateEntity(entity="User", err=e)


class RetrieveUser(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data,
                            status=status.HTTP_200_OK)  # render(request,"myapp/test.html",{'context':serializer.data})
        except Exception as e:
            raise ErrCannotGetEntity(entity="User", err=e)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            instance.set_password(serializer.data.get('password'))
            instance.save()

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)
        except Exception as e:
            raise ErrCannotUpdateEntity(entity="User", err=e)

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise ErrCannotDeleteEntity(entity="User", err=e)


class LoginView(APIView):
    permission_classes = [AllowAny]

    # authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        try:
            username = request.data.get('username')
            user = User.objects.get(email=username)
            password = request.data['password']

            if user is None:
                raise AuthenticationFailed("User not found")
            if not user.check_password(password):
                raise AuthenticationFailed("InCorrect password")

            access_token = generate_access_token(user)
            refresh_token = generate_fresh_token(user)

            response = Response()
            response.set_cookie(key='refresh_token', value=refresh_token, httponly=True)

            serializer = UserSerializer(instance=user)

            response.data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": serializer.data,
            }
            return response

        except Exception as e:
            raise ErrLogin(entity="User", err=e)

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.id is not None:
            serializer = UserSerializer(user)
            return Response(data={
                'user': serializer.data
            })
        else:
            raise ValidationError("Time out Login", code="TimeOutLogin")


class ResetAccessToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            raise AuthenticationFailed("Authentication credentials were not provided")
        try:
            payload = jwt.decode(refresh_token, key=settings.REFRESH_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("expired refresh token, please login again")

        user = User.objects.get(id=payload.get('id'))

        if user is None:
            raise AuthenticationFailed('User not found')

        if not user.is_active:
            raise AuthenticationFailed('user is inactive')

        new_access_token = generate_access_token(user)

        return Response(data={
            'new_access_token': new_access_token
        })


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response()
        response.delete_cookie(key="refresh_token")
        response.data = {
            "result": "Log out successful"
        }
        return response
