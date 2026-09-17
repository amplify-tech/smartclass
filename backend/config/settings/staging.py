"""Staging settings."""
from .base import *  # noqa: F401,F403
from .base import build_databases, env_bool, env_list

DEBUG = env_bool('DEBUG', False)
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS')
if not ALLOWED_HOSTS:
    raise ValueError('ALLOWED_HOSTS must be set for staging')

DATABASES = build_databases(default_sqlite=False)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
