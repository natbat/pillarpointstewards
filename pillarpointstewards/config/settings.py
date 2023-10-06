"""
Django settings for pillarpointstewards project.

Generated by 'django-admin startproject' using Django 4.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import dj_database_url
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

AUTH0_DOMAIN = "pillarpointstewards.us.auth0.com"
AUTH0_CLIENT_ID = "DLXBMPbtamC2STUyV7R6OFJFDsSTHqEA"
AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET")

# For AUTH0 forwarding in development environments
AUTH0_FORWARD_URL = os.environ.get("AUTH0_FORWARD_URL", None)
AUTH0_FORWARD_SECRET = os.environ.get("AUTH0_FORWARD_SECRET", None)

# Allow inactive users to sign in:
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]

SHIFTS_ICS_SECRET = os.environ.get("SHIFTS_ICS_SECRET") or ""

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-iy$k84$=%68trrc_idv@@(n3gs00_!%jf%ymi52yzv91#ejs5^"

BACKUP_SECRET = os.environ.get("BACKUP_SECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get("DJANGO_DEBUG"))

USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = bool(os.environ.get("SECURE_SSL_REDIRECT"))
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ALLOWED_HOSTS = [
    "pillarpointstewards.fly.dev",
    "0.0.0.0",
    "127.0.0.1",
    "dev.pillarpointstewards.com",
    "www.pillarpointstewards.com",
    "pillarpointstewards.com",
]
if os.environ.get("ALLOWED_HOSTS_STAR"):
    ALLOWED_HOSTS.append("*")

CSRF_TRUSTED_ORIGINS = ["https://www.pillarpointstewards.com", "http://localhost:8000"]

LOGIN_URL = "/login/"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_sql_dashboard",
    "django_extensions",
    "django_htmx",
    "homepage",
    "shifts",
    "auth0_login",
    "weather",
    "tides",
    "teams",
]
if not DEBUG:
    INSTALLED_APPS.insert(0, "whitenoise.runserver_nostatic")

MIDDLEWARE = (
    [
        "django.middleware.security.SecurityMiddleware",
    ]
    + (["whitenoise.middleware.WhiteNoiseMiddleware"] if not DEBUG else [])
    + [
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "django_htmx.middleware.HtmxMiddleware",
    ]
)

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
    )
    ignore_logger("django.security.DisallowedHost")

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
DATABASES = {}
DATABASES["default"] = dj_database_url.config()
DATABASES["dashboard"] = dj_database_url.config()
# https://django-sql-dashboard.datasette.io/en/stable/setup.html#danger-mode-configuration-without-a-read-only-database-user
DATABASES["dashboard"]["OPTIONS"] = {
    "options": "-c default_transaction_read_only=on -c statement_timeout=3000"
}
DASHBOARD_ENABLE_FULL_EXPORT = True


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

if DEBUG:
    pass
else:
    STATIC_ROOT = BASE_DIR / "static-root"
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Don't let non-existent static references, including in commented-out CSS blocks,
# cause Django to throw errors:
WHITENOISE_MANIFEST_STRICT = False

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
