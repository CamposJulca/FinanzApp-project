"""
Django settings for finanzapp project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent


# =====================================================
# SEGURIDAD
# =====================================================

DEBUG = os.getenv("DEBUG", "False") == "True"

# La clave vive en .env (ignorado por git). En desarrollo se admite un valor
# de relleno; en producción se exige, porque firmar sesiones y CSRF con una
# clave conocida equivale a no firmarlas.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-solo-para-desarrollo-local"
    else:
        raise RuntimeError(
            "Falta DJANGO_SECRET_KEY en el entorno (.env) y DEBUG=False."
        )

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
    "django.contrib.postgres",
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
LOGIN_REDIRECT_URL = "/transacciones/"
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
            PROJECT_ROOT / "frontend" / "dist",
            BASE_DIR / "templates",
            PROJECT_ROOT / "templates",
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
TIME_ZONE = "America/Bogota"

USE_I18N = True
USE_TZ = True


# =====================================================
# ARCHIVOS ESTÁTICOS (VITE + WHITENOISE)
# =====================================================

# URL pública
STATIC_URL = "/assets/"

# Carpeta donde Vite genera los archivos hash
STATICFILES_DIRS = [
    path
    for path in [
        BASE_DIR / "frontend" / "dist" / "assets",
        PROJECT_ROOT / "frontend" / "dist" / "assets",
    ]
    if path.exists()
]

# Carpeta donde collectstatic copia todo
STATIC_ROOT = BASE_DIR / "staticfiles"

# STATICFILES_STORAGE desapareció en Django 5.1; en 6.x se configura aquí.
# Con el nombre antiguo la compresión de WhiteNoise se ignoraba en silencio.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# =====================================================
# SEGURIDAD ADICIONAL
# =====================================================

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8029",
    "http://127.0.0.1:8029",
    "https://finanzapp.ngrok.io",
    "https://finanzapp-dev.ngrok.io",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8029",
    "http://127.0.0.1:8029",
]

CORS_ALLOW_CREDENTIALS = True


# =====================================================
# ENDURECIMIENTO PARA PRODUCCIÓN
# =====================================================

# ngrok termina el TLS y reenvía en claro a gunicorn. Sin esto Django cree
# que la petición es http y genera URLs absolutas equivocadas.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Cookies restringidas a HTTPS. Se controla por entorno porque la app también
# se abre por http en la LAN; con True, ese acceso deja de poder iniciar sesión.
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "False") == "True"
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES

SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# =====================================================
# LOGGING
# =====================================================

# Con DEBUG=False Django deja de mostrar la traza al visitante; sin logging
# explícito tampoco quedaría registrada en ningún sitio.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
