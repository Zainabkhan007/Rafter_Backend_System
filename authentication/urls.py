from django.urls import path, include
from . import views

urlpatterns = [

      path("register/",views.register,name='register'),
      path('login/', views.login,name='login'),
      path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
      path('admin_login/', views.admin_login,name='admin_login'),
]