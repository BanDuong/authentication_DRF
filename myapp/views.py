from django.shortcuts import render
from django.views import View
from .models import Questions,Answers,User
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from common.errors import *
from .serializers import UserSerializer
from rest_framework.exceptions import AuthenticationFailed,ValidationError
import datetime
import jwt
from rest_framework import status
from rest_framework.permissions import AllowAny

class index(View):
    def get(self,request):
        qss = Questions.objects.all()
        content = {'qs':qss}
        return render(request,'myapp/index.html',context=content)

    def post(self,request):
        qs_id = request.POST.get('questions')
        obj_qs = Questions.objects.get(pk=qs_id)
        qs = obj_qs.question
        img = request.FILES.get('image')
        ans = Answers(question=obj_qs,answer=request.POST.get('answer'),image=img)
        ans.save()
        content = {'qs_id':qs_id,'ans': ans.answer,'image':ans.image,'qs':qs}
        return render(request,'myapp/save.html',context=content)

#----------------------------------------User-----------------------------------------#

class GetPostUser(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = (AllowAny,)

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
            raise ErrCannotListEntity(entity="User",err=e)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            # data['password'] = jwt.encode(data['password'], 'secret', algorithm='HS256')
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            raise ErrCannotCreateEntity(entity="User",err=e)


class RetrieveUser(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            raise ErrCannotGetEntity(entity="User",err=e)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)
        except Exception as e:
            raise ErrCannotUpdateEntity(entity="User",err=e)

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise ErrCannotDeleteEntity(entity="User",err=e)

class LoginView(APIView):

    def post(self, request, *args, **kwargs):
        try:
            email = request.data['email']
            password = request.data['password']

            user = User.objects.filter(email=email).first()

            if user is None:
                raise AuthenticationFailed("User not found")
            if not user.check_password(password):
                raise AuthenticationFailed("InCorrect password")

            payload ={
                "id" : user.id,
                "username" : user.username,
                "email" : user.email,
                "is_admin" : user.is_admin,
                "is_superuser" : user.is_superuser,
                "iat" : datetime.datetime.utcnow(),
            }

            token = jwt.encode(payload,'secret',algorithm='HS256')
            response = Response()
            response.set_cookie(key='token',value=token,httponly=True)
            response.data = {
                "token":token,
            }
            return response

        except Exception as e:
            raise ErrLogin(entity="User",err=e)

    def get(self,request,*args, **kwargs):
        try:
            token = request.COOKIES.get('token')

            if not token:
                raise AuthenticationFailed("Unauthenticated!")

            try:
                payload = jwt.decode(token,key="secret",algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                raise AuthenticationFailed("Unauthenticated")

            user = User.objects.filter(id=payload['id']).first()
            serializer = UserSerializer(user)

            return Response(serializer.data)

        except Exception as e:
            raise ErrLogin(entity="User",err=e)

class LogoutView(APIView):

    def post(self, request, *args, **kwargs):
        response = Response()
        response.delete_cookie(key="token")
        response.data = {
            "result" : "Log out successful"
        }
        return response







