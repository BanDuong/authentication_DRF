import json
import os
import random

from django.shortcuts import render, redirect
from django.views import View
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.http import HttpResponse
from myapp.models import *
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from common.errors import *
from common.permissions import IsAuthenticate
from .serializers import UserSerializer, LoginSerializer, TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed, ValidationError
import datetime
import jwt
from rest_framework import status
from rest_framework.permissions import *
from .token import generate_access_token, generate_fresh_token
from django.conf import settings
# from .backends import JWTAuthentication
from django.core.cache.backends.base import DEFAULT_TIMEOUT
# from django.views.decorators.cache import cache_page
from django.core.cache import cache
import redis
from django.contrib.auth import authenticate

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


class Login(View):

    def get(self, request):
        list_img_cc = MakeImageCaptcha.objects.all()
        img_cc = random.choice(list_img_cc)
        list_audio_cc = MakeAudioCaptcha.objects.all()
        audio_cc = random.choice(list_audio_cc)
        return render(request, template_name="login.html", context={'img_cc': img_cc, 'audio_cc': audio_cc})

    def post(self, request):
        data ='img_captcha/' + request.POST.get('captcha') + '.png'
        if MakeImageCaptcha.objects.filter(image_captcha=data):
            return render(request, template_name="notice.html")
        else:
            return redirect('/users/login/')


class AfterLogin(View):

    def get(self, request):
        user = request.user
        return render(request, template_name="profile.html", context={'user': user})

    # def post(self, request):
    #     qs_id = request.POST.get('questions')
    #     obj_qs = Questions.objects.get(pk=qs_id)
    #     qs = obj_qs.question
    #     img = request.FILES.get('image')
    #     ans = Answers(question=obj_qs, answer=request.POST.get('answer'), image=img)
    #     ans.save()
    #     content = {'qs_id': qs_id, 'ans': ans.answer, 'image': ans.image, 'qs': qs}
    #     return render(request, 'myapp/save.html', context=content)


# ----------------------------------------User-----------------------------------------#

rd = redis.StrictRedis(host="redis")


def check_token_user(request, access_token, refresh_token):
    get_refresh_token = cache.get(refresh_token)
    get_access_token = request.COOKIES.get(access_token)
    if not get_access_token or not get_refresh_token:
        raise ValidationError(detail="Please Login", code="DontLogin")
    else:
        response = Response()
        try:
            payload = jwt.decode(get_access_token, key=settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload.get('id'))
            return response, user
        except Exception as e:
            if type(e) == jwt.exceptions.ExpiredSignatureError:
                payload = jwt.decode(get_refresh_token, key=settings.REFRESH_KEY, algorithms=["HS256"])
                user = User.objects.get(id=payload.get('id'))
                access_token_ck = generate_access_token(user)
                response.set_cookie(key=access_token, value=access_token_ck, httponly=True)
                return response, user
            else:
                raise ValidationError(detail=e)


class GetPostUser(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    # template_name = "myapp/test.html"

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            # raise ValueError(serializer.data)
            return Response(serializer.data)
            # return render(request, template_name="myapp/test.html", context={'context': serializer.data})
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
    # permission_classes = [AllowAny]

    # rd = redis.Redis(host="redis")

    # authentication_classes

    def post(self, request, *args, **kwargs):
        try:
            email = request.data.get('email')
            user = User.objects.get(email=email)
            password = request.data['password']

            if user is None:
                raise AuthenticationFailed("User not found")
            if not user.check_password(password):
                raise AuthenticationFailed("InCorrect password")

            # authenticate(email,password)

            access_token = generate_access_token(user)
            refresh_token = generate_fresh_token(user)

            response = Response()
            response.set_cookie(key='access_token', value=access_token, httponly=True)
            #
            # if self.rd.get("refresh_token"):
            #     self.rd.delete("refresh_token")
            # self.rd.set("refresh_token", refresh_token)

            cache.set("refresh_token", refresh_token, CACHE_TTL)
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
        # if request.user.id is not None:
        #     return Response(request.user)
        # else:
        return Response()
    #
    #     # user = request.user
    #     # if user.id is not None:
    #     #     serializer = UserSerializer(user)
    #     #     return Response(data={
    #     #         'user': serializer.data
    #     #     })
    #     # else:
    #     #     raise ValidationError("Time out Login", code="TimeOutLogin")
    #
    #     coockie_refresh_token = request.COOKIES.get('refresh_token')
    #     redis_refresh_token = self.rd.get("refresh_token")
    #     if coockie_refresh_token == redis_refresh_token:
    #         payload = jwt.decode(redis_refresh_token, key=settings.REFRESH_KEY, algorithms=["HS256"])
    #         user = User.objects.get(id=payload.get('id'))
    #         serializer = UserSerializer(user)
    #         return Response(data={"user": serializer.data})
    #     else:
    #         raise ValidationError("Error Connection", code="ErrConnection")


from rest_framework_csv import renderers as r
from rest_framework.settings import api_settings


class ShowInforUser(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    # renderer_classes = (r.CSVRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    http_method_names = ['get', 'post']

    # def get(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         # return self.get_paginated_response(serializer.data)
    #         return Response(data={"data": serializer.data}, template_name="myapp/test.html")
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(data={"data": serializer.data}, template_name="myapp/test.html")


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
    # permission_classes = [IsAuthenticated]
    # renderer_classes = [TemplateHTMLRenderer]

    def post(self, request, *args, **kwargs):
        response = Response()
        token_ck = request.COOKIES.get('access_token')
        if token_ck:
            response.delete_cookie(key="access_token")
            # request.COOKIES['access_token'].delete()
            cache.delete("refresh_token")
            response.data = {
                "result": "Log out successful"
            }
            response.template_name = "myapp/test.html"
            return response
            # return redirect('/api/v1/login/')
        else:
            raise ValidationError("Don't account logging. Please login!")

    def get(self, request):
        return Response()


from rest_framework_simplejwt.views import TokenViewBase


class LoginUsingJWTDjoser(generics.ListCreateAPIView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = Response()
        response.set_cookie(key="access_token", value=serializer.validated_data['access'], httponly=True)
        cache.set("refresh_token", serializer.validated_data['refresh'], CACHE_TTL)
        response.data = serializer.validated_data
        return response
