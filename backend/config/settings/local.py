"""Local development settings."""
from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS as BASE_ALLOWED_HOSTS
from .base import build_databases, env_bool

DEBUG = env_bool('DEBUG', True)

# Django test client uses Host: testserver
ALLOWED_HOSTS = list({*BASE_ALLOWED_HOSTS, 'testserver', 'localhost', '127.0.0.1'})

DATABASES = build_databases(default_sqlite=True)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
