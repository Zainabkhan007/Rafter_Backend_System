"""
URL configuration for rafters_food project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path("admin_details/",include("admin_section.urls")),
    # path('auth/', include('dj_rest_auth.urls')),  # Login, logout, password reset, etc.
    
    # # DJ Rest Auth Registration routes (for user registration)
    # path('auth/registration/', include('dj_rest_auth.registration.urls')),  # For user registration
    
    # # Allauth's URLs for password reset and other features
    # path('accounts/', include('allauth.urls')),  
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
