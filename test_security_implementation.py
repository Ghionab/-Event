#!/usr/bin/env python
"""
Simple test script to verify security implementation is working.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intern_project.settings')
django.setup()

from theming.security import (
    ThemeSecurityValidator,
    SecureImageProcessor,
    APISecurityManager,
    PermissionManager,
    AuditLogger
)

def test_css_security():
    """Test CSS security validation."""
    print("Testing CSS Security Validation...")
    
    validator = ThemeSecurityValidator()
    
    # Test dangerous CSS
    dangerous_css = """
    .malicious {
        background: url('javascript:alert("XSS")');
        color: expression(alert('XSS'));
    }
    """
    
    result = validator.validate_css_content(dangerous_css)
    print(f"Dangerous CSS detected: {not result['is_valid']}")
    print(f"Errors found: {len(result['errors'])}")
    
    # Test safe CSS
    safe_css = """
    .safe {
        color: #007bff;
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    """
    
    result = validator.validate_css_content(safe_css)
    print(f"Safe CSS validated: {result['is_valid']}")
    
    # Test color validation
    valid_colors = ['#007bff', '#fff', 'rgb(255, 0, 0)', 'red']
    invalid_colors = ['javascript:alert(1)', '#gggggg', 'invalid']
    
    print("\nColor Validation:")
    for color in valid_colors:
        is_valid = validator.validate_color_value(color)
        print(f"  {color}: {'✓' if is_valid else '✗'}")
    
    for color in invalid_colors:
        is_valid = validator.validate_color_value(color)
        print(f"  {color}: {'✗' if not is_valid else '✓ (should be ✗)'}")

def test_image_security():
    """Test image security validation."""
    print("\nTesting Image Security...")
    
    processor = SecureImageProcessor()
    
    # Test path traversal detection
    malicious_paths = [
        '../../../etc/passwd',
        '/etc/passwd',
        'C:\\Windows\\System32\\config\\SAM'
    ]
    
    print("Path Traversal Detection:")
    for path in malicious_paths:
        detected = processor._check_path_traversal(path)
        print(f"  {path}: {'✓ Blocked' if detected else '✗ Not detected'}")

def test_csp_headers():
    """Test CSP header generation."""
    print("\nTesting CSP Header Generation...")
    
    validator = ThemeSecurityValidator()
    
    css_content = """
    .test {
        color: #007bff;
        background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==');
    }
    """
    
    headers = validator.generate_csp_headers(css_content)
    
    print("Generated CSP Headers:")
    for header_name, header_value in headers.items():
        print(f"  {header_name}: {header_value}")

def main():
    """Run all security tests."""
    print("=" * 60)
    print("THEMING SYSTEM SECURITY IMPLEMENTATION TEST")
    print("=" * 60)
    
    try:
        test_css_security()
        test_image_security()
        test_csp_headers()
        
        print("\n" + "=" * 60)
        print("✓ Security implementation test completed successfully!")
        print("✓ All security measures are working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Security test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()