"""
Settings package.

Select environment with DJANGO_ENV: local | staging | production (default: local).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

_ENV = os.getenv('DJANGO_ENV', 'local').lower()

if _ENV == 'production':
    from .production import *  # noqa: F401,F403
elif _ENV == 'staging':
    from .staging import *  # noqa: F401,F403
else:
    from .local import *  # noqa: F401,F403
