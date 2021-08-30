from django.urls import path
from . import views

urlpatterns = [
    path('djoser/login/', views.LoginUsingJWTDjoser.as_view()),
]