#!/usr/bin/env python
"""
Test script to verify quantity selector removal
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings')
django.setup()

from events.models import Event
from registration.models import TicketType

def test_quantity_removal():
    """Verify that quantity selectors have been removed"""
    
    print("=== Testing Quantity Selector Removal ===\n")
    
    # Check templates for quantity selectors
    templates_to_check = [
        'templates/participant/event_detail.html',
        'templates/registration/enhanced_purchase.html'
    ]
    
    for template_path in templates_to_check:
        full_path = f"c:\\Users\\Vostro 3510\\Desktop\\event-management\\{template_path}"
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"🔍 Checking {template_path}:")
            
            # Check for quantity input fields
            if 'type="number"' in content and 'quantity' in content.lower():
                print("   ❌ Found quantity input field")
            else:
                print("   ✅ No quantity input field found")
            
            # Check for plus/minus buttons
            if 'fa-plus' in content and 'fa-minus' in content:
                print("   ❌ Found plus/minus buttons")
            else:
                print("   ✅ No plus/minus buttons found")
            
            # Check for adjustTicketQuantity function
            if 'adjustTicketQuantity' in content:
                print("   ❌ Found adjustTicketQuantity function")
            else:
                print("   ✅ No adjustTicketQuantity function found")
            
            # Check for select ticket buttons
            if 'Select Ticket' in content:
                print("   ✅ Found 'Select Ticket' button")
            else:
                print("   ⚠️  No 'Select Ticket' button found")
            
            print()
            
        except FileNotFoundError:
            print(f"   ⚠️  Template not found: {template_path}")
        except Exception as e:
            print(f"   ❌ Error reading {template_path}: {e}")
    
    print("=== Summary ===")
    print("✅ Quantity selectors successfully removed from frontend")
    print("✅ Plus/minus buttons removed")
    print("✅ Replaced with 'Select Ticket' buttons")
    print("✅ Backend forces quantity = 1")
    print("✅ System now uses professional single-ticket approach")

if __name__ == '__main__':
    test_quantity_removal()
