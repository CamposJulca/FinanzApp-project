"""
Django settings for finanzapp project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# =====================================================
# SEGURIDAD
# =====================================================

SECRET_KEY = "django-insecure-&u=1#e1azv@2@+7!_x8mu!o1e)@yujij^v$c4=*p5xf=pmyfqo"

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "192.168.0.101",
    "finanzapp.ngrok.io",
    "finanzapp-dev.ngrok.io",
]


# =====================================================
# APLICACIONES
# =====================================================

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "transactions",
    "core",
]


# =====================================================
# MIDDLEWARE
# =====================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ← correcto aquí
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "finanzapp.middleware.LoginRequiredMiddleware",
]


LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"


# =====================================================
# URLS / TEMPLATES
# =====================================================

ROOT_URLCONF = "finanzapp.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "frontend" / "dist",
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "finanzapp.wsgi.application"


# =====================================================
# BASE DE DATOS
# =====================================================

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}


# =====================================================
# INTERNACIONALIZACIÓN
# =====================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"

USE_I18N = True
USE_TZ = True


# =====================================================
# ARCHIVOS ESTÁTICOS (VITE + WHITENOISE)
# =====================================================

# URL pública
STATIC_URL = "/assets/"

# Carpeta donde Vite genera los archivos hash
STATICFILES_DIRS = [
    BASE_DIR / "frontend" / "dist" / "assets",
]

# Carpeta donde collectstatic copia todo
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# =====================================================
# SEGURIDAD ADICIONAL
# =====================================================

CSRF_TRUSTED_ORIGINS = [
    "https://finanzapp.ngrok.io",
    "https://finanzapp-dev.ngrok.io",
]
