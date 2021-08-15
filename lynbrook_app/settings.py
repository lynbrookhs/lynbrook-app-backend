from google.oauth2.service_account import Credentials

"""
Django settings for lynbrook_app project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "t", "1")

ALLOWED_HOSTS = ["*"] if DEBUG else ["lynbrookasb.org", "www.lynbrookasb.org"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_better_admin_arrayfield",
    "social_django",
    "rest_framework",
    "corsheaders",
    "djoser",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lynbrook_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "lynbrook_app.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USERNAME"],
        "PASSWORD": os.environ["DATABASE_PASSWORD"],
        "HOST": os.environ["DATABASE_HOST"],
        "PORT": os.environ["DATABASE_PORT"],
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/Los_Angeles"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom things

AUTH_USER_MODEL = "core.User"
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "core.auth.SchoologyOAuth",
    "core.auth.GoogleOAuth",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


class AllList(list):
    def __contains__(self, o: object) -> bool:
        return True


DJOSER = {
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": AllList(),
    "SERIALIZERS": {
        "user": "core.serializers.UserSerializer",
        "current_user": "core.serializers.UserSerializer",
    },
}

SOCIAL_AUTH_GOOGLE_WHITELISTED_DOMAINS = ["fuhsd.org", "student.fuhsd.org"]
SOCIAL_AUTH_USER_FIELDS = ["email", "type"]
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

SOCIAL_AUTH_GOOGLE_KEY = os.environ["GOOGLE_API_KEY"]
SOCIAL_AUTH_GOOGLE_SECRET = os.environ["GOOGLE_API_SECRET"]
SOCIAL_AUTH_SCHOOLOGY_KEY = os.environ["SCHOOLOGY_API_KEY"]
SOCIAL_AUTH_SCHOOLOGY_SECRET = os.environ["SCHOOLOGY_API_SECRET"]

SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(weeks=4)}

CORS_ALLOW_ALL_ORIGINS = True

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

LOGIN_REDIRECT_URL = "/admin/"

DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_BUCKET_NAME = "lynbrook-app"
GS_PROJECT_ID = "lynbrook-high"
GS_CREDENTIALS = Credentials.from_service_account_file(os.environ["GCS_CREDS"])
GS_DEFAULT_ACL = "authenticatedRead"
GS_FILE_OVERWRITE = False

DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
