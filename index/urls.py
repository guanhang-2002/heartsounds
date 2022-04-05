from django.urls import path

from . import views
from .views import *
app_name = 'index'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/',LogoutView.as_view(),name='logout'),
    path('passwordforget/',ForgetPasswordView.as_view(),name='forgetpassword'),
    path('pfcode/',ForgetPasswordEmailCodeView.as_view(),name='forgetpasswordcode'),
    path('uploade/',login_required(UploadView.as_view()),name='upload'),
    path('file_detail/<int:id>/',login_required(HeartSoundsDemonstrate.as_view()),name='file_detail'),
    path('file_list/<int:page>/',HeartSoundsList.as_view(),name='file_list'),
    path('file_download/<int:id>',views.download,name='file_download')
]
