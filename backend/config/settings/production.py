"""Production settings."""
from .base import *  # noqa: F401,F403
from .base import build_databases, env, env_bool, env_list

DEBUG = env_bool('DEBUG', False)
if DEBUG:
    raise ValueError('DEBUG must be False in production')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS')
if not ALLOWED_HOSTS:
    raise ValueError('ALLOWED_HOSTS must be set for production')

DATABASES = build_databases(default_sqlite=False)

SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(env('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
