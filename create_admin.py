#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create admin user
if not User.objects.filter(email='admin@eventmanager.com').exists():
    admin_user = User.objects.create_user(
        email='admin@eventmanager.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )
    print("Admin user created successfully!")
    print("Email: admin@eventmanager.com")
    print("Password: admin123")
else:
    print("Admin user already exists!")
    print("Email: admin@eventmanager.com")
    print("Password: admin123")
