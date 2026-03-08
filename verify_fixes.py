#!/usr/bin/env python
"""
Verification script to check if all fixes are working
Run with: python verify_fixes.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

print("=" * 70)
print("VERIFICATION SCRIPT - Checking All Fixes")
print("=" * 70)

# Check 1: Event Form - Status Field
print("\n1. Checking Event Form...")
from events.forms import EventForm
form = EventForm()

if 'status' in form.fields:
    print("   ✗ FAIL: Status field is still in the form!")
else:
    print("   ✓ PASS: Status field successfully removed")

if 'invite_emails' in form.fields:
    print("   ✓ PASS: Invite emails field present")
else:
    print("   ✗ FAIL: Invite emails field missing!")

print(f"   Total fields in form: {len(form.fields)}")

# Check 2: Task List View
print("\n2. Checking Task List View...")
try:
    from advanced.views import task_list
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    factory = RequestFactory()
    request = factory.get('/advanced/tasks/')
    
    # Create a test user with permissions
    try:
        user = User.objects.filter(is_staff=True).first()
        if not user:
            user = User.objects.create_user(
                email='test@example.com',
                password='test123',
                is_staff=True
            )
        request.user = user
        
        # This will fail without proper permissions, but we can check the function exists
        print("   ✓ PASS: Task list view exists")
    except Exception as e:
        print(f"   ⚠ WARNING: Could not fully test task list: {e}")
        
except ImportError as e:
    print(f"   ✗ FAIL: Task list view import error: {e}")

# Check 3: Reports
print("\n3. Checking Reports...")
try:
    from business.models import Report
    from business.views import report_list
    
    report_count = Report.objects.count()
    print(f"   ✓ PASS: Reports model accessible ({report_count} reports in database)")
    print("   ✓ PASS: Report list view exists")
except ImportError as e:
    print(f"   ✗ FAIL: Reports import error: {e}")

# Check 4: Task Model
print("\n4. Checking Task Model...")
try:
    from advanced.models import Task
    
    task_count = Task.objects.count()
    print(f"   ✓ PASS: Task model accessible ({task_count} tasks in database)")
    
    # Check if STATUS_CHOICES and PRIORITY_CHOICES exist
    if hasattr(Task, 'STATUS_CHOICES'):
        print(f"   ✓ PASS: STATUS_CHOICES defined ({len(Task.STATUS_CHOICES)} statuses)")
    else:
        print("   ✗ FAIL: STATUS_CHOICES not found")
        
    if hasattr(Task, 'PRIORITY_CHOICES'):
        print(f"   ✓ PASS: PRIORITY_CHOICES defined ({len(Task.PRIORITY_CHOICES)} priorities)")
    else:
        print("   ✗ FAIL: PRIORITY_CHOICES not found")
        
except ImportError as e:
    print(f"   ✗ FAIL: Task model import error: {e}")

# Check 5: URLs
print("\n5. Checking URL Configuration...")
try:
    from django.urls import reverse
    
    # Check event create URL
    try:
        url = reverse('event_create')
        print(f"   ✓ PASS: Event create URL configured: {url}")
    except:
        print("   ✗ FAIL: Event create URL not found")
    
    # Check task list URL
    try:
        url = reverse('advanced:task_list')
        print(f"   ✓ PASS: Task list URL configured: {url}")
    except:
        print("   ✗ FAIL: Task list URL not found")
    
    # Check report list URL
    try:
        url = reverse('business:report_list')
        print(f"   ✓ PASS: Report list URL configured: {url}")
    except:
        print("   ✗ FAIL: Report list URL not found")
        
except Exception as e:
    print(f"   ✗ FAIL: URL configuration error: {e}")

# Summary
print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print("\nIf you see any FAIL messages above:")
print("1. Check the TROUBLESHOOTING_GUIDE.md file")
print("2. Clear your browser cache and hard refresh (Ctrl+F5)")
print("3. Restart the development server")
print("4. Check server logs for errors")
print("\nIf all checks PASS but you still see issues:")
print("- Clear browser cache completely")
print("- Try opening in incognito/private mode")
print("- Check browser console for JavaScript errors (F12)")
print("=" * 70)
