"""
Django settings for the Wonderland Diorama ERP project.
"""

import sys
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# Local apps live under apps/<name> with name='<name>' (see apps/*/apps.py),
# so the apps/ directory is added to the import path instead of nesting
# everything under an 'apps' package.
sys.path.insert(0, str(BASE_DIR / "apps"))

SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key-change-me")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
# Django rejects cross-origin POSTs (any form submit) unless the exact origin
# (scheme+host+port) is trusted - matters here since Unraid is reached via
# "http://<host-ip>:<port>/", not just a bare hostname. Empty by default (dev
# server on 127.0.0.1 doesn't need it); must be set explicitly in production.
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "django_filters",
    "import_export",
    "django_htmx",
    # local apps
    "core",
    "accounts",
    "catalog",
    "wishlist",
    "orders",
    "finance",
    "contacts",
    "dashboard",
    "knowledge",
    "tasks",
    "settings_hub",
    "data_import",
    "appointments",
    "lexikon",
    "documents",
    "reports",
    "messaging",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.notifications",
                "messaging.context_processors.unread_messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# SQLite is the deliberate choice for this project's scale (single/few users,
# a few thousand rows/year) - see wonderland-diorama-erp-konzept.md section 4.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": config("DB_PATH", default=str(BASE_DIR / "data" / "db.sqlite3")),
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL;",
        },
    },
    # Self-contained/portable Heilstein-Lexikon dataset - kept in its own
    # file on purpose so it could be reused standalone in other projects.
    "lexikon": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": config("LEXIKON_DB_PATH", default=str(BASE_DIR / "data" / "lexikon.sqlite3")),
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL;",
        },
    },
}

DATABASE_ROUTERS = ["lexikon.router.LexikonRouter"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = config("MEDIA_ROOT", default=str(BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "login"

# Map to Bootstrap's contextual color names (text-bg-*) so message.tags can be
# used directly as a CSS class in the toast markup.
from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}
