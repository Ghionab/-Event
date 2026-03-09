#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create test organizer
if not User.objects.filter(email='organizer@test.com').exists():
    user = User.objects.create_user(
        email='organizer@test.com',
        password='test123',
        first_name='Test',
        last_name='Organizer',
        is_staff=True,
        is_superuser=True
    )
    print("Test organizer created!")
else:
    print("Test organizer already exists!")

# List all users
print("\nAll users in database:")
for user in User.objects.all():
    print(f"Email: {user.email}, Staff: {user.is_staff}, Superuser: {user.is_superuser}")

# Test authentication
from django.contrib.auth import authenticate
user = authenticate(username='organizer@test.com', password='test123')
if user:
    print(f"\nAuthentication successful for: {user.email}")
else:
    print("\nAuthentication failed!")
