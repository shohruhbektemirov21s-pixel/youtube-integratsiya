"""
Django settings for config project.
Configured for YouTube Integration backend with REST API and PostgreSQL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
from django.core.exceptions import ImproperlyConfigured


def _require(name):
    raise ImproperlyConfigured(f"{name} muhit o'zgaruvchisi majburiy (backend/.env).")


load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR.parent / '.env')

# Quick-start development settings - unsuitable for production
# SECRET_KEY majburiy — fallback YO'Q. Kodda turgan kalit bilan hujumchi
# yaroqli session/token imzolay olardi (django.core.signing).
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or ''
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY o'rnatilmagan. backend/.env ga qo'shing: "
        "python -c \"import secrets;print(secrets.token_urlsafe(48))\""
    )

# Default False — .env yo'qolsa tizim xavfsiz holatga tushsin, DEBUG'ga emas.
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

allowed_hosts_str = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_str.split(',') if h.strip()]
if '*' in ALLOWED_HOSTS and not DEBUG:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS='*' production'da taqiqlanadi. "
        "Aniq domenlarni sanang (masalan: localhost,127.0.0.1,.trycloudflare.com)."
    )

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.youtube',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database (PostgreSQL with fallback to SQLite for isolation/testing if needed)
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')

if DB_ENGINE == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'youtube_db'),
            'USER': os.getenv('DB_USER', 'youtube_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD') or _require('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
            'ATOMIC_REQUESTS': False,
            'OPTIONS': {
                'connect_timeout': 10,
            },
            'TEST': {
                'NAME': os.getenv('DB_TEST_NAME', 'youtube_test_db'),
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'ATOMIC_REQUESTS': False,
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    # BrowsableAPIRenderer faqat DEBUG'da: prod'da u tunneldan kirgan har kimga
    # tayyor HTML forma berib, POST/PATCH/DELETE ni bir bosishda qilish imkonini beradi.
    'DEFAULT_RENDERER_CLASSES': (
        ['rest_framework.renderers.JSONRenderer',
         'rest_framework.renderers.BrowsableAPIRenderer']
        if DEBUG else
        ['rest_framework.renderers.JSONRenderer']
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '120/minute',
        'auth': '5/minute',
        # Pul/kvota sarflaydigan amallar (Gemini, Flow AI krediti)
        'generate': '10/hour',
    },
    # nginx — yagona ishonchli proxy. Busiz DRF throttle kaliti sifatida
    # mijoz yuborgan butun X-Forwarded-For satrini oladi va limit chetlab o'tiladi.
    'NUM_PROXIES': 1,
}

# Throttle hisoblagichi barcha gunicorn worker'lari uchun UMUMIY bo'lishi shart.
# LocMemCache (default) har worker'da alohida bo'lib, limitni worker soniga ko'paytiradi.
_redis_url = os.getenv('REDIS_URL', '')
CACHES = {
    'default': (
        {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': _redis_url}
        if _redis_url else
        # Fallback: bitta jarayonli dev uchun. Ko'p worker'da throttle limiti
        # worker soniga ko'payadi, shuning uchun prod'da REDIS_URL majburiy.
        {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'fallback'}
    )
}

# Google YouTube Data API v3 (Strictly Backend-only Secret)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

# CORS & CSRF configuration
cors_origins_str = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000'
)
CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins_str.split(',') if o.strip()]
CORS_ALLOW_CREDENTIALS = True

csrf_origins_str = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:8000'
)
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins_str.split(',') if o.strip()]

# Security Headers & Cookie Hardening
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# 'ALLOWALL' Django/brauzer tan olmaydigan qiymat edi — noto'g'ri header e'tiborsiz
# qoldirilib, freym himoyasi butunlay yo'q bo'lardi. Telegram Mini App uchun
# ruxsat nginx'dagi CSP `frame-ancestors` orqali beriladi (u X-Frame-Options'dan ustun).
X_FRAME_OPTIONS = os.getenv('DJANGO_X_FRAME_OPTIONS', 'SAMEORIGIN')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Bular endi `if not DEBUG` ichida emas — env bilan boshqariladi.
# Default'lar http://localhost orqali kirishni buzmaydigan qilib tanlangan;
# tizim faqat HTTPS orqali ochilganda .env da True qiling.
def _flag(name, default='False'):
    return os.getenv(name, default).lower() in ('true', '1', 'yes')


SESSION_COOKIE_SECURE = _flag('SESSION_COOKIE_SECURE')
CSRF_COOKIE_SECURE = _flag('CSRF_COOKIE_SECURE')
SECURE_SSL_REDIRECT = _flag('SECURE_SSL_REDIRECT')
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0

# Telegram: bot tokeni va ruxsat etilgan chat'lar (bot va Mini App auth uchun)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ALLOWED_CHAT_IDS = {
    int(x) for x in os.getenv('TELEGRAM_ALLOWED_CHAT_IDS', '').replace(' ', '').split(',') if x
}

# Logging Configuration
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

