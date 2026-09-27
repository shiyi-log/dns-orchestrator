import os
from pathlib import Path

from backend.app.config import get_settings


BASE_DIR = Path(__file__).resolve().parents[2]
settings = get_settings()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")]
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")
ROOT_URLCONF = "backend.config.urls"
WSGI_APPLICATION = "backend.config.wsgi.application"
ASGI_APPLICATION = "backend.config.asgi.application"

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "backend.accounts",
    "backend.dns_api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "backend" / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "zh-hans"
ROOT_URLCONF = "backend.config.urls"
STATIC_URL = "static/"
CORS_ALLOWED_ORIGINS = settings.cors_origin_list
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "UNAUTHENTICATED_USER": None,
}
