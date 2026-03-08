"""
Participant Portal Settings - Port 8001
Restricted settings for public participant-facing portal
"""
from .settings import *

# Override for participant portal
DEBUG = True

# Different secret key for participant portal
SECRET_KEY = 'participant-secret-key-change-in-production'

# Allow all hosts for participant portal
ALLOWED_HOSTS = ['*']

# Simplified apps for participants
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'events',
    'registration',
    'users',
    'advanced',
    'events_api',
]

# Participant-specific middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Custom middleware to disable CSRF for registration API
    'event_project.middleware.DisableCSRFMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Enable CSRF for participant portal (except for API endpoints handled by middleware)
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_AGE = 31449600  # 1 year
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_TRUSTED_ORIGINS = []
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Template directories
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

# CORS settings for participant portal
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8001",
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True

# URL configuration for participant portal
ROOT_URLCONF = 'event_project.urls_participant'

# Session settings
SESSION_COOKIE_NAME = 'participant_sessionid'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True

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
