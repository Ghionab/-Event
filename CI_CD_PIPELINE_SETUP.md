# CI/CD Pipeline Setup Instructions

## Overview

This guide covers setting up a complete CI/CD pipeline for the EventAxis application with:

- GitHub Actions for automation
- Docker for containerization
- **Automatic CD deployment** on merge to main branch (no manual setup required)
- Nginx for reverse proxy and load balancing
- Redis for caching and message broker
- Celery for async task processing
- Multi-domain routing (Eventaxiss.com and organizer.Eventaxiss.com)
- Cloudflare integration

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLOUDFLARE                              │
│                     (Eventaxiss.com)                               │
│                  (organizer.Eventaxiss.com)                       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────┐
│                              NGINX                                 │
│                   (Reverse Proxy + SSL Termination)                │
│         Port 80/443 → Route to respective backends              │
└────────────────────────────────┬──────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌─────────────────────────┐      ┌─────────────────────────────────┐
│   Attendee App (Django)  │      │   Organizer App (Django)         │
│      :8001               │      │        :8002                   │
└─────────────────────────┘      └─────────────────────────────────┘
                    │                         │
         ┌──────────┴──────────┐        │
         ▼                     ▼        ▼
┌────────────────┐    ┌────────────┐    ┌──────────┐
│     Redis       │    │  Celery    │    │  Celery  │
│   (Cache)      │    │  Worker   │    │  Beat    │
└────────────────┘    └───────────┘    └──────────┘
```

---

## Step 1: Server Setup

**Note:** This is a one-time server setup. Most directory creation is handled automatically by the CD pipeline.

### 1.1 Initial Server Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl git vim gcc python3 python3-pip nginx certbot python3-certbot-nginx software-properties-common

# Add Docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 1.2 Configure Firewall

```bash
# Configure UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 6379/tcp   # Redis
sudo ufw allow 6379/udp  # Redis

sudo ufw enable
sudo ufw status
```

---

## Step 2: Initial Server Setup (One-Time)

### 2.1 Create Base Directory

The CD pipeline will automatically create the required directory structure on the server. However, you need to create the base directory and set ownership:

```bash
# Create base directory
sudo mkdir -p /opt/eventaxis

# Set ownership (adjust username as needed)
sudo chown -R ubuntu:ubuntu /opt/eventaxis
```

**Note:** The CD workflow will automatically create all subdirectories (app, nginx, redis, celery, logs, services) when deploying.

---

## Step 3: Docker Configuration

### 3.1 Create Dockerfile

Create file: `app/Dockerfile`

```dockerfile
# EventAxis Django Application Dockerfile

# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBACKE=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose ports
EXPOSE 8001 8002

# Start application
CMD ["sh", "start.sh"]
```

### 3.2 Create Docker Compose Files

Create file: `app/docker-compose.yml`

```yaml
version: '3.9'

services:
  # Main Django Application - Attendee Portal
  app-attendee:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: eventaxis_attendee
    ports:
      - "8001:8001"
    environment:
      - DEBUG=0
      - DOMAIN=Eventaxiss.com
      - PORT=8001
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DATABASE_URL=postgresql://user:password@db:5432/eventaxis
      - SECRET_KEY=your-secret-key-here
      - ALLOWED_HOSTS=Eventaxiss.com,www.Eventaxiss.com
    volumes:
      - ./media:/app/media
      - ./static:/app/static
      - ./logs:/app/logs
    depends_on:
      - redis
      - db
    restart: unless-stopped
    networks:
      - eventaxis_network

  # Organizer Portal
  app-organizer:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: eventaxis_organizer
    ports:
      - "8002:8002"
    environment:
      - DEBUG=0
      - DOMAIN=organizer.Eventaxiss.com
      - PORT=8002
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DATABASE_URL=postgresql://user:password@db:5432/eventaxis
      - SECRET_KEY=your-secret-key-here
      - ALLOWED_HOSTS=organizer.Eventaxiss.com,www.organizer.Eventaxiss.com
    volumes:
      - ./media:/app/media
      - ./static:/app/static
      - ./logs:/app/logs
    depends_on:
      - redis
      - db
    restart: unless-stopped
    networks:
      - eventaxis_network

  # Redis Cache and Message Broker
  redis:
    image: redis:7-alpine
    container_name: eventaxis_redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - ./redis/data:/data
      - ./redis/conf/redis.conf:/usr/local/etc/redis/redis.conf
    restart: unless-stopped
    networks:
      - eventaxis_network

  # Celery Worker for Attendee Portal
  celery-attendee:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: eventaxis_celery_attendee
    command: celery -A event_project worker -l info --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DATABASE_URL=postgresql://user:password@db:5432/eventaxis
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs
    depends_on:
      - redis
      - db
      - app-attendee
    restart: unless-stopped
    networks:
      - eventaxis_network

  # Celery Worker for Organizer Portal
  celery-organizer:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: eventaxis_celery_organizer
    command: celery -A event_project worker -l info --concurrency=4 -Q organizer
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DATABASE_URL=postgresql://user:password@db:5432/eventaxis
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs
    depends_on:
      - redis
      - db
      - app-organizer
    restart: unless-stopped
    networks:
      - eventaxis_network

  # Celery Beat (Scheduler)
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: eventaxis_celery_beat
    command: celery -A event_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - DATABASE_URL=postgresql://user:password@db:5432/eventaxis
    volumes:
      - ./media:/app/media
    depends_on:
      - redis
      - db
    restart: unless-stopped
    networks:
      - eventaxis_network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: eventaxis_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
      - ./static:/usr/share/nginx/html/static
      - ./media:/usr/share/nginx/html/media
    depends_on:
      - app-attendee
      - app-organizer
    restart: unless-stopped
    networks:
      - eventaxis_network

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: eventaxis_db
    environment:
      - POSTGRES_DB=eventaxis
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - ./db/data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - eventaxis_network

networks:
  eventaxis_network:
    driver: bridge
```

### 3.3 Create Entry Point Script

Create file: `app/start.sh`

```bash
#!/bin/bash

# Wait for database
echo "Waiting for database..."
while ! nc -z $DJANGO_DB_HOST 5432; do
  sleep 1
done

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 1
done

echo "Database and Redis are ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn event_project.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --worker-class=sync \
    --worker-connections=1000 \
    --max-requests=10000 \
    --max-requests-jitter=1000 \
    --timeout=120 \
    --access-logfile /app/logs/gunicorn_access.log \
    --error-logfile /app/logs/gunicorn_error.log \
    --log-level info
```

### 3.4 Create Requirements for Docker

Create file: `app/requirements.txt`

```
Django>=4.2,<5.0
gunicorn>=21.0
celery>=5.3
redis>=5.0
django-redis>=5.4
psycopg2-binary>=2.9
dj-database-url>=2.1
dj-static>=0.0.7
Whitenoise>=6.6
django-cors-headers>=4.3
django-celery-beat>=2.5
Pillow>=10.0
python-magic>=0.4
reportlab>=4.0
qrcode>=7.4
Pillow>=10.0
cryptography>=41.0
PyJWT>=2.8
requests>=2.31
habanero>=3.1
markdown>=3.5
bleach>=6.1
channels>=4.0
daphne>=4.0
channels-redis>=4.0
django-storages>=1.14
boto3>=1.34
python-dateutil>=2.8
pytz>=2024.1
django-widget-tweaks>=1.5
django-phonenumber-field>=8.0
phonenumbers>=8.13
openpyxl>=3.1
```

---

## Step 4: Nginx Configuration

### 4.1 Main Nginx Configuration

Create file: `nginx/conf.d/eventaxis.conf`

```nginx
# Main Nginx Configuration for EventAxis

# Upstream backends
upstream attendee_backend {
    server app-attendee:8001;
    keepalive 32;
}

upstream organizer_backend {
    server app-organizer:8002;
    keepalive 32;
}

# Main HTTP Server
server {
    listen 80;
    server_name Eventaxiss.com www.Eventaxiss.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Health check endpoint
    location /health/ {
        proxy_pass http://attendee_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files - served directly by Nginx
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files - served directly by Nginx
    location /media/ {
        alias /usr/share/nginx/html/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Main application proxy
    location / {
        proxy_pass http://attendee_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # WebSocket location
    location /ws/ {
        proxy_pass http://attendee_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Organizer Portal HTTP Server
server {
    listen 80;
    server_name organizer.Eventaxiss.com www.organizer.Eventaxiss.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Health check endpoint
    location /health/ {
        proxy_pass http://organizer_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Charset "UTF-8;
    }

    # Media files
    location /media/ {
        alias /usr/share/nginx/html/media/;
        expires 7d;
    }

    # Main application proxy
    location / {
        proxy_pass http://organizer_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4.2 SSL Configuration (with Let's Encrypt)

Create SSL certificates after DNS setup:

```bash
# Stop Nginx temporarily
docker-compose stop nginx

# Get SSL certificates for both domains
sudo certbot --nginx -d Eventaxiss.com -d www.Eventaxiss.com --non-interactive --agree-tos --email your-email@example.com

sudo certbot --nginx -d organizer.Eventaxiss.com -d www.organizer.Eventaxiss.com --non-interactive --agree-tos --email your-email@example.com

# Copy certificates to nginx ssl directory
sudo cp /etc/letsencrypt/live/Eventaxiss.com/fullchain.pem /opt/eventaxis/nginx/ssl/
sudo cp /etc/letsencrypt/live/Eventaxiss.com/privkey.pem /opt/eventaxis/nginx/ssl/
sudo cp /etc/letsencrypt/live/organizer.Eventaxiss.com/fullchain.pem /opt/eventaxis/nginx/ssl/
sudo cp /etc/letsencrypt/live/organizer.Eventaxiss.com/privkey.pem /opt/eventaxis/nginx/ssl/

# Set permissions
sudo chmod 600 /opt/eventaxis/nginx/ssl/*.pem
```

### 4.3 SSL-Enabled Nginx Config

Update `nginx/conf.d/eventaxis.conf` to include SSL:

```nginx
# HTTPS Server for Attendee Portal
server {
    listen 443 ssl http2;
    server_name Eventaxiss.com www.Eventaxiss.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name Eventaxiss.com www.Eventaxiss.com organizer.Eventaxiss.com www.organizer.Eventaxiss.com;
    return 301 https://$host$request_uri;
}
```

---

## Step 5: Django Settings

### 5.1 Create Production Settings

Create file: `app/event_project/settings_production.py`

```python
"""
Production Settings for EventAxis
"""

from .settings import *
import os

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# HSTS settings
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Allowed hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'eventaxis'),
        'USER': os.environ.get('POSTGRES_USER', 'user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'password'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

# Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.environ.get('REDIS_HOST', 'redis')}:{os.environ.get('REDIS_PORT', '6379')}/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

# Celery configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 270

# Static and media files
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATIC_ROOT = '/app/static'
MEDIA_ROOT = '/app/media'

# Whitenoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

---

## Step 6: GitHub Actions Workflow

### 6.1 Create Workflow Directory

```bash
mkdir -p .github/workflows
```

### 6.2 CI Workflow

Create file: `.github/workflows/ci.yml`

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: eventaxis_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6373

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run migrations
        run: |
          python manage.py makemigrations --check --noinput || exit 1

      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml --cov-report=html

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: eventaxis

  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install flake8 black isort

      - name: Run flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Check formatting with Black
        run: |
          black --check .

      - name: Check import order
        run: |
          isort --check-only .

  build:
    runs-on: ubuntu-latest
    needs: [test, lint]
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: eventaxis:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 6.3 CD Workflow

Create file: `.github/workflows/cd.yml`

```yaml
name: CD Pipeline

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ghcr.io/${{ github.repository }}
            eventaxis/${{ github.repository.name }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{ branch }}-
            type=raw,value=latest,enable={{ branch == 'main' }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Update deployment timestamp
        run: |
          echo "Deployment initiated at $(date)" >> deployment_log.txt

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Connect to staging server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USERNAME }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            # Create directory structure if not exists (first-time setup)
            mkdir -p /opt/eventaxis/{app,nginx,redis,celery,logs,services}
            mkdir -p /opt/eventaxis/app/{media,static,logs}
            mkdir -p /opt/eventaxis/nginx/{conf.d,ssl}
            mkdir -p /opt/eventaxis/redis/{data,conf}

            cd /opt/eventaxis

            # Pull latest image
            docker-compose -f docker-compose.staging.yml pull

            # Restart services
            docker-compose -f docker-compose.staging.yml up -d

            # Verify deployment
            docker-compose -f docker-compose.staging.yml ps

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Connect to production server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USERNAME }}
          key: ${{ secrets.PRODUCTION_SSH_KEY }}
          script: |
            # Create directory structure if not exists (first-time setup)
            mkdir -p /opt/eventaxis/{app,nginx,redis,celery,logs,services}
            mkdir -p /opt/eventaxis/app/{media,static,logs}
            mkdir -p /opt/eventaxis/nginx/{conf.d,ssl}
            mkdir -p /opt/eventaxis/redis/{data,conf}
            mkdir -p /opt/eventaxis/celery/{logs,data}

            cd /opt/eventaxis

            # Pull latest image
            docker-compose pull

            # Restart services with zero-downtime
            docker-compose up -d --force-recreate

            # Verify deployment
            docker-compose ps
            docker-compose logs --tail=30
```

### 6.4 Docker Compose for Staging

Create file: `docker-compose.staging.yml`

```yaml
version: '3.9'

services:
  app-attendee:
    image: ghcr.io/nextgen-technologies-p-l-c/eventaxis:latest
    environment:
      - DEBUG=0
      - DOMAIN=staging.Eventaxiss.com
      - PORT=8001
    ports:
      - "8001:8001"

  app-organizer:
    image: ghcr.io/nextgen-technologies-p-l-c/eventaxis:latest
    environment:
      - DEBUG=0
      - DOMAIN=staging.organizer.Eventaxiss.com
      - PORT=8002
    ports:
      - "8002:8002"

  # Use existing services from main compose
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
```

---

## Step 7: Cloudflare Configuration

### 7.1 DNS Setup

In Cloudflare Dashboard:

1. **Attendee Portal Domain (Eventaxiss.com)**:
   - A Record: `@` → Your Server IP
   - A Record: `www` → Your Server IP (optional)

2. **Organizer Portal Domain (organizer.Eventaxiss.com)**:
   - A Record: `organizer` → Your Server IP

Both domains route to the same server - Nginx handles routing based on domain name.

### 7.2 SSL/TLS Settings

1. Go to SSL/TLS Overview
2. Set mode to **Full (Strict)**
3. Enable **Always Use HTTPS**
4. Enable **Automatic HTTPS Rewrites**

### 7.3 Performance Settings

1. Enable **Rocket Loader** (optional)
2. Enable **Brotli** compression
3. Set **Cache Level** to Cache Everything for static files

### 7.4 Security Settings

1. Enable **WAF** rules for protection
2. Set up **Rate Limiting** if needed
3. Configure **Page Rules** for caching static content

---

## Step 8: Environment Variables

Create file: `.env.production`

```env
# Django Settings
DEBUG=0
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=Eventaxiss.com,www.Eventaxiss.com,organizer.Eventaxiss.com,www.organizer.Eventaxiss.com

# Database
POSTGRES_DB=eventaxis
POSTGRES_USER=eventaxis_user
POSTGRES_PASSWORD=strong-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Email (SMTP)
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@Eventaxiss.com
EMAIL_HOST_PASSWORD=email-password
DEFAULT_FROM_EMAIL=noreply@Eventaxiss.com

# Domain Settings
MAIN_DOMAIN=Eventaxiss.com
ORGANIZER_DOMAIN=organizer.Eventaxiss.com

# Security
CSRF_TRUSTED_ORIGINS=https://Eventaxiss.com,https://organizer.Eventaxiss.com
```

---

## Step 9: Deployment

### 9.1 Automatic Deployment (CD)

When code is merged into the `main` branch, the CD pipeline automatically handles deployment:

1. **CI tests** run automatically
2. **Docker image** is built and pushed to container registry
3. **Production server** receives updated image via SSH
4. **Services** are restarted with zero-downtime (rolling update)

```bash
# Simply merge to main branch
# CD pipeline runs automatically
git checkout main
git merge feature-branch
git push origin main
```

### 9.2 Manual Rollback (If Needed)

```bash
# SSH into production server
ssh user@production-server

# Navigate to project directory
cd /opt/eventaxis

# Rollback to previous image version
docker-compose pull
docker-compose up -d --force-recreate

# Check status
docker-compose logs --tail=50
```

---

## Step 10: Monitoring and Health Checks

### 10.1 Docker Health Checks

Add to `docker-compose.yml`:

```yaml
services:
  app-attendee:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 10.2 Create Health Check View

Create file: `app/health/views.py`

```python
from django.http import JsonResponse
from django.views import View
import sys

class HealthCheckView(View):
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'python_version': sys.version,
        })
```

Add to urls:

```python
path('health/', HealthCheckView.as_view(), name='health'),
```

---

## Step 11: SSL Certificate Renewal

### 11.1 Auto-Renewal

```bash
# Add to crontab
sudo crontab -e

# Add this line to auto-renew every month
0 0 * * * certbot renew --quiet --deploy-hook "docker-compose restart nginx"
```

---

## Step 12: Backup Strategy

### 12.1 Database Backup Script

Create file: `backup.sh`

```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/opt/eventaxis/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker exec eventaxis_db pg_dump -U eventaxis_user eventaxis > $BACKUP_DIR/db_$DATE.sql

# Compress
gzip $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

---

## Step 13: Quick Reference Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart a specific service
docker-compose restart app-attendee

# Scale services
docker-compose up -d --scale app-attendee=3

# Update and restart
docker-compose up -d --build

# SSH into container
docker exec -it eventaxis_attendee bash

# View service status
docker-compose ps

# Check resource usage
docker stats

# Prune unused resources
docker system prune -f
```

---

## File Structure Summary

```
/opt/eventaxis/                    # Base directory (created once)
├── app/                        # Created by CD on first deploy
│   ├── Dockerfile
│   ├── start.sh
│   ├── requirements.txt
│   ├── docker-compose.yml
│   ├── media/
│   ├── static/
│   └── logs/
├── nginx/                      # Created by CD on first deploy
│   ├── conf.d/
│   │   └── eventaxis.conf
│   └── ssl/
│       ├── fullchain.pem
│       └── privkey.pem
├── redis/                      # Created by CD on first deploy
│   ├── data/
│   └── conf/
│       └── redis.conf
├── db/                         # Created by CD on first deploy
│   └── data/
├── docker-compose.staging.yml
├── .env                        # Created from secrets
└── backup.sh
```

**Note:** All subdirectories are automatically created by the CD pipeline on the first deployment. You only need to create the base `/opt/eventaxis` directory manually.

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Set up SSH key authentication
- [ ] Configure firewall rules
- [ ] Enable SSL/TLS
- [ ] Set up automatic security updates
- [ ] Configure backup schedule
- [ ] Enable monitoring and alerts
- [ ] Set up log rotation
- [ ] Configure rate limiting
- [ ] Set up WAF rules in Cloudflare