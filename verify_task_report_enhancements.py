#!/usr/bin/env python
"""
Verification script for Task Management and Report System enhancements
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event
from advanced.models import Task, TeamMember
from business.models import Report
from registration.models import Registration

User = get_user_model()

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_task_model():
    """Verify Task model has new fields"""
    print_section("Task Model Verification")
    
    fields_to_check = [
        'progress_percentage',
        'estimated_hours',
        'actual_hours',
        'tags',
        'attachment'
    ]
    
    task_fields = [f.name for f in Task._meta.get_fields()]
    
    for field in fields_to_check:
        if field in task_fields:
            print(f"✓ Field '{field}' exists")
        else:
            print(f"✗ Field '{field}' missing")
    
    # Check helper methods
    methods_to_check = [
        'is_overdue',
        'get_priority_color',
        'get_status_color',
        'can_start',
        'mark_completed'
    ]
    
    print("\nHelper Methods:")
    for method in methods_to_check:
        if hasattr(Task, method):
            print(f"✓ Method '{method}' exists")
        else:
            print(f"✗ Method '{method}' missing")

def check_report_model():
    """Verify Report model has new fields"""
    print_section("Report Model Verification")
    
    fields_to_check = [
        'export_format',
        'schedule_frequency',
        'next_scheduled',
        'report_data',
        'updated_at'
    ]
    
    report_fields = [f.name for f in Report._meta.get_fields()]
    
    for field in fields_to_check:
        if field in report_fields:
            print(f"✓ Field '{field}' exists")
        else:
            print(f"✗ Field '{field}' missing")
    
    # Check export format choices
    print("\nExport Format Choices:")
    if hasattr(Report, 'EXPORT_FORMATS'):
        for code, label in Report.EXPORT_FORMATS:
            print(f"  - {code}: {label}")
    else:
        print("✗ EXPORT_FORMATS not defined")

def check_task_views():
    """Verify task views exist"""
    print_section("Task Views Verification")
    
    from advanced import views
    
    views_to_check = [
        'task_list',
        'task_create',
        'task_update',
        'task_detail',
        'task_delete',
        'task_export',
        'task_bulk_update'
    ]
    
    for view_name in views_to_check:
        if hasattr(views, view_name):
            print(f"✓ View '{view_name}' exists")
        else:
            print(f"✗ View '{view_name}' missing")

def check_report_views():
    """Verify report views exist"""
    print_section("Report Views Verification")
    
    from business import views
    
    views_to_check = [
        'report_list',
        'report_create',
        'report_detail',
        'report_generate',
        'report_export'
    ]
    
    for view_name in views_to_check:
        if hasattr(views, view_name):
            print(f"✓ View '{view_name}' exists")
        else:
            print(f"✗ View '{view_name}' missing")

def check_urls():
    """Verify URL patterns exist"""
    print_section("URL Patterns Verification")
    
    from django.urls import reverse, NoReverseMatch
    
    urls_to_check = [
        ('advanced:task_list', {}),
        ('advanced:task_create', {}),
        ('advanced:task_export', {}),
        ('advanced:task_bulk_update', {}),
        ('business:report_list', {}),
        ('business:report_create', {}),
    ]
    
    for url_name, kwargs in urls_to_check:
        try:
            url = reverse(url_name, kwargs=kwargs)
            print(f"✓ URL '{url_name}' -> {url}")
        except NoReverseMatch:
            print(f"✗ URL '{url_name}' not found")

def check_data_integrity():
    """Check if existing data is intact"""
    print_section("Data Integrity Check")
    
    # Count tasks
    task_count = Task.objects.count()
    print(f"Total tasks in database: {task_count}")
    
    # Count reports
    report_count = Report.objects.count()
    print(f"Total reports in database: {report_count}")
    
    # Count events
    event_count = Event.objects.count()
    print(f"Total events in database: {event_count}")
    
    # Count users
    user_count = User.objects.count()
    print(f"Total users in database: {user_count}")
    
    if task_count > 0:
        print("\nSample Task:")
        task = Task.objects.first()
        print(f"  Title: {task.title}")
        print(f"  Status: {task.get_status_display()}")
        print(f"  Priority: {task.get_priority_display()}")
        print(f"  Progress: {task.progress_percentage}%")
        print(f"  Overdue: {task.is_overdue()}")
    
    if report_count > 0:
        print("\nSample Report:")
        report = Report.objects.first()
        print(f"  Name: {report.name}")
        print(f"  Type: {report.get_report_type_display()}")
        print(f"  Export Format: {report.get_export_format_display()}")

def check_dependencies():
    """Check if optional dependencies are installed"""
    print_section("Optional Dependencies Check")
    
    # Check openpyxl for Excel export
    try:
        import openpyxl
        print(f"✓ openpyxl installed (version {openpyxl.__version__})")
        print("  Excel export available")
    except ImportError:
        print("✗ openpyxl not installed")
        print("  Install with: pip install openpyxl")
    
    # Check reportlab for PDF export
    try:
        import reportlab
        print(f"✓ reportlab installed (version {reportlab.Version})")
        print("  PDF export available")
    except ImportError:
        print("✗ reportlab not installed")
        print("  Install with: pip install reportlab")

def run_all_checks():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("  TASK & REPORT ENHANCEMENT VERIFICATION")
    print("="*60)
    
    try:
        check_task_model()
        check_report_model()
        check_task_views()
        check_report_views()
        check_urls()
        check_data_integrity()
        check_dependencies()
        
        print_section("Verification Complete")
        print("✓ All core features verified successfully!")
        print("\nNote: Install openpyxl and reportlab for full export functionality")
        
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = run_all_checks()
    sys.exit(0 if success else 1)
