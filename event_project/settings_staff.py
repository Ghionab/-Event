"""
Gate Staff Portal Settings - Port 8002
Restricted settings for gate staff/bouncer check-in portal
"""
from .settings import *

# Override for staff portal
DEBUG = True

# Different secret key for staff portal
SECRET_KEY = 'staff-secret-key-change-in-production'

# Allow all hosts for staff portal
ALLOWED_HOSTS = ['*']

# CSRF settings for browser preview proxies
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8001',
    'http://127.0.0.1:8002',
    'http://127.0.0.1:7282',
    'http://127.0.0.1:7286',
    'http://127.0.0.1:14928',
    'http://127.0.0.1:14929',
    'http://localhost:8000',
    'http://localhost:8001',
    'http://localhost:8002',
]

# Simplified apps for staff portal
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'events',
    'registration',
    'users',
    'advanced',
    'staff',  # New staff app
    'events_api',
]

# Staff-specific middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CSRF settings for staff portal
CSRF_USE_SESSIONS = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Template directories
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.csrf',
            ],
        },
    },
]

# CORS settings for staff portal
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8002",
    "http://127.0.0.1:8002",
]
CORS_ALLOW_CREDENTIALS = True

# URL configuration for staff portal
ROOT_URLCONF = 'event_project.urls_staff'

# Session settings
SESSION_COOKIE_NAME = 'staff_sessionid'
SESSION_COOKIE_AGE = 28800  # 8 hours
SESSION_COOKIE_HTTPONLY = True

# Login/Logout URLs for staff portal
LOGIN_URL = '/staff/login/'
LOGIN_REDIRECT_URL = '/staff/events/'
LOGOUT_REDIRECT_URL = '/staff/login/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
