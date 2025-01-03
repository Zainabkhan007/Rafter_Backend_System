"""
Django settings for rafters_food project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import environ

import os
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)
ROOT_URLCONF = 'rafters_food.urls'
ADMIN_PASSWORD = 'password123'
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-td7slw974l-a6!kd1txk2+4f7r-voiiy&uzcc9g^1uraniz5kz'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_rest_passwordreset',
    'admin_section',
    'whitenoise.runserver_nostatic',
    'corsheaders',

]

MIDDLEWARE = [
    # 'django.middleware.security.SecurityMiddleware',

    'corsheaders.middleware.CorsMiddleware',

     'corsheaders.middleware.CorsMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

   
    'django.middleware.csrf.CsrfViewMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
   
]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'accept',
    'x-requested-with',
]


# Allow methods
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'OPTIONS',
]
CORS_ALLOW_CREDENTIALS = True


# Allow methods
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'OPTIONS',
]
CORS_ALLOW_CREDENTIALS = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rafters_food.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGES =  "whitenoise.storage.CompressedManifestStaticFilesStorage"
    

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' 


EMAIL_PORT = 587  
EMAIL_USE_TLS = True 
EMAIL_HOST = 'smtp.gmail.com' 
EMAIL_HOST_USER = 'testingsites247365@gmail.com'  
EMAIL_HOST_PASSWORD="djbsfnkdbvfvihrt"

MAIL_DEFAULT_SENDER = 'testingsites247365@gmail.com'

STRIPE_PUBLIC_KEY=env('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY=env('STRIPE_SECRET_KEY')