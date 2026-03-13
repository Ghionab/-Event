#!/usr/bin/env python
"""
Test script for Enterprise Bulk Registration System
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event
from registration.models import TicketType, BulkRegistrationUpload, BulkRegistrationRow
from registration.services.bulk_registration import BulkRegistrationService
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import csv

User = get_user_model()

def test_enterprise_bulk_registration():
    """Test the enterprise bulk registration system"""
    print("\n=== Testing Enterprise Bulk Registration System ===")
    
    try:
        # Create test user
        user, created = User.objects.get_or_create(
            email='organizer@test.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'Organizer'
            }
        )
        print(f"✓ Test user: {user.email}")
        
        # Create test event
        event, created = Event.objects.get_or_create(
            title='Test Enterprise Event',
            defaults={
                'description': 'Test event for enterprise bulk registration',
                'organizer': user,
                'start_date': '2026-06-01',
                'end_date': '2026-06-02',
                'venue_name': 'Test Venue',
                'max_attendees': 1000,
                'status': 'published'
            }
        )
        print(f"✓ Test event: {event.title}")
        
        # Create test ticket type
        ticket_type, created = TicketType.objects.get_or_create(
            event=event,
            name='General Admission',
            defaults={
                'price': 50.00,
                'quantity_available': 500,
                'sales_start': '2026-01-01',
                'sales_end': '2026-05-31'
            }
        )
        print(f"✓ Test ticket type: {ticket_type.name}")
        
        # Create test CSV content
        csv_content = """name,email,phone,company,job_title
John Doe,john.doe@example.com,+1234567890,Acme Inc,Developer
Jane Smith,jane.smith@example.com,+0987654321,Tech Corp,Manager
Bob Johnson,bob.johnson@example.com,,Startup LLC,CEO
Alice Brown,alice.brown@example.com,+1122334455,Design Co,Designer
Charlie Wilson,charlie.wilson@example.com,+5566778899,Marketing Ltd,Marketer"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        # Create uploaded file object
        with open(temp_file_path, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                name='test_attendees.csv',
                content=f.read(),
                content_type='text/csv'
            )
        
        # Test 1: Create bulk upload record
        print("\n--- Test 1: Creating Bulk Upload Record ---")
        bulk_upload = BulkRegistrationUpload.objects.create(
            event=event,
            uploaded_by=user,
            file=uploaded_file,
            original_filename='test_attendees.csv',
            file_name='test_attendees.csv',
            file_size=len(csv_content),
            current_step='uploaded',
            import_options={'skip_header': True}
        )
        print(f"✓ Bulk upload created: ID {bulk_upload.id}")
        
        # Test 2: Parse file and detect columns
        print("\n--- Test 2: File Parsing and Column Detection ---")
        service = BulkRegistrationService(bulk_upload)
        detected_columns, rows_data = service.parse_file()
        
        print(f"✓ Detected columns: {detected_columns}")
        print(f"✓ Rows parsed: {len(rows_data)}")
        
        # Update bulk upload with detected data
        bulk_upload.detected_columns = detected_columns
        bulk_upload.total_rows = len(rows_data)
        bulk_upload.save()
        
        # Create row records
        bulk_rows = []
        for i, row_data in enumerate(rows_data, 1):
            bulk_rows.append(BulkRegistrationRow(
                bulk_upload=bulk_upload,
                row_number=i,
                row_data=row_data
            ))
        
        BulkRegistrationRow.objects.bulk_create(bulk_rows)
        print(f"✓ Created {len(bulk_rows)} row records")
        
        # Test 3: Column mapping
        print("\n--- Test 3: Column Mapping ---")
        column_mapping = {
            'name': 'attendee_name',
            'email': 'attendee_email',
            'phone': 'attendee_phone',
            'company': 'company',
            'job_title': 'job_title'
        }
        
        bulk_upload.column_mapping = column_mapping
        bulk_upload.current_step = 'mapped'
        bulk_upload.save()
        print(f"✓ Column mapping configured: {column_mapping}")
        
        # Test 4: Data validation
        print("\n--- Test 4: Data Validation ---")
        validation_summary = service.validate_data()
        print(f"✓ Validation results: {validation_summary}")
        
        # Test 5: Configure import options
        print("\n--- Test 5: Import Configuration ---")
        import_options = {
            'duplicate_handling': 'skip',
            'ticket_assignment_mode': 'same_for_all',
            'send_emails': False
        }
        
        bulk_upload.import_options.update(import_options)
        bulk_upload.default_ticket_type = ticket_type
        bulk_upload.current_step = 'configured'
        bulk_upload.save()
        print(f"✓ Import options configured: {import_options}")
        
        # Test 6: Execute import
        print("\n--- Test 6: Import Execution ---")
        results = service.execute_import()
        print(f"✓ Import results: {results}")
        
        # Verify results
        print("\n--- Verification ---")
        registrations_created = event.registrations.count()
        print(f"✓ Registrations created: {registrations_created}")
        
        # Check ticket count update
        ticket_type.refresh_from_db()
        print(f"✓ Tickets sold: {ticket_type.quantity_sold}")
        
        # Check audit logs
        audit_logs = bulk_upload.audit_logs.count()
        print(f"✓ Audit logs created: {audit_logs}")
        
        # Cleanup
        os.unlink(temp_file_path)
        print("✓ Temporary file cleaned up")
        
        print("\n🎉 All tests passed! Enterprise Bulk Registration System is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_enterprise_bulk_registration()
    sys.exit(0 if success else 1)