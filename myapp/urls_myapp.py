from django.urls import path
from . import views


app_name = 'myapp'

urlpatterns = [
    path('users/login/', views.Login.as_view(), name='login'),
    path('accounts/profile/', views.AfterLogin.as_view(), name='after_login'),
    # path('auth/complete/facebook/', views.AfterLogin.as_view(), name='after_login'),
    path("api/v1/alluser/", views.GetPostUser.as_view(), name="get_post"),
    path("api/v1/retrieve/<int:pk>", views.RetrieveUser.as_view(), name="retrieve"),
    path("api/v1/login/", views.LoginView.as_view(), name="login"),
    path("api/v1/logout/", views.LogoutView.as_view(), name="logout"),
    path("api/v1/reactk/", views.ResetAccessToken.as_view(), name="reset_accToken"),
    path("api/v1/user/get_infor/",views.ShowInforUser.as_view(), name="get_information"),
    # path("api/v1/JWTauth/create/",views.TokenObtainPairView.as_view(),name="create_JWT"),
]
