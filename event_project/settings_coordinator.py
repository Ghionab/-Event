"""
Coordinator Portal Settings - Port 8003
Restricted settings for event coordinators
"""
from .settings import *

# Override for coordinator portal
DEBUG = True

# Different secret key for coordinator portal
SECRET_KEY = 'coordinator-secret-key-change-in-production'

# Allow all hosts for coordinator portal
ALLOWED_HOSTS = ['*']

# CSRF settings for coordinator portal
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8001',
    'http://127.0.0.1:8002',
    'http://127.0.0.1:8003',
    'http://localhost:8000',
    'http://localhost:8001',
    'http://localhost:8002',
    'http://localhost:8003',
]

# Simplified apps for coordinator portal
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
    'coordinators',  # Coordinator app
    'communication',
    'business',
]

# Coordinator-specific middleware
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

ROOT_URLCONF = 'event_project.urls_coordinator'

# Session settings to avoid conflicts with other portals
SESSION_COOKIE_NAME = 'coordinator_sessionid'
SESSION_COOKIE_AGE = 28800  # 8 hours
SESSION_COOKIE_HTTPONLY = True

# Login/Logout URLs for coordinator portal
LOGIN_URL = '/coordinators/login/'
LOGIN_REDIRECT_URL = '/coordinators/dashboard/'
LOGOUT_REDIRECT_URL = '/coordinators/login/'

# Template settings
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

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8003",
    "http://127.0.0.1:8003",
]
CORS_ALLOW_CREDENTIALS = True
