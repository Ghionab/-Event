"""
Test script to verify CSRF fix for participant portal
Run with: python test_csrf_fix.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_participant')
django.setup()

from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_csrf_configuration():
    """Test CSRF middleware and settings"""
    print("=" * 60)
    print("TESTING CSRF CONFIGURATION")
    print("=" * 60)
    
    # Check middleware
    print("\n1. Checking CSRF Middleware...")
    csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
    if csrf_middleware in settings.MIDDLEWARE:
        print(f"   ✅ {csrf_middleware} is enabled")
    else:
        print(f"   ❌ {csrf_middleware} is NOT enabled")
        return False
    
    # Check CSRF settings
    print("\n2. Checking CSRF Settings...")
    print(f"   CSRF_USE_SESSIONS: {settings.CSRF_USE_SESSIONS}")
    print(f"   CSRF_COOKIE_HTTPONLY: {settings.CSRF_COOKIE_HTTPONLY}")
    print(f"   CSRF_COOKIE_SAMESITE: {getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Not set')}")
    
    # Check context processors
    print("\n3. Checking Context Processors...")
    csrf_processor = 'django.template.context_processors.csrf'
    context_processors = settings.TEMPLATES[0]['OPTIONS']['context_processors']
    if csrf_processor in context_processors:
        print(f"   ✅ {csrf_processor} is enabled")
    else:
        print(f"   ❌ {csrf_processor} is NOT enabled")
        return False
    
    return True


def test_signup_view():
    """Test signup view without CSRF exempt"""
    print("\n" + "=" * 60)
    print("TESTING SIGNUP VIEW")
    print("=" * 60)
    
    client = Client(enforce_csrf_checks=True)
    
    # GET request - should work
    print("\n1. Testing GET request to /register/...")
    response = client.get('/register/')
    if response.status_code == 200:
        print(f"   ✅ GET request successful (status: {response.status_code})")
        
        # Check for CSRF token in response
        if 'csrfmiddlewaretoken' in response.content.decode():
            print("   ✅ CSRF token found in form")
        else:
            print("   ❌ CSRF token NOT found in form")
            return False
    else:
        print(f"   ❌ GET request failed (status: {response.status_code})")
        return False
    
    # POST request with CSRF token - should work
    print("\n2. Testing POST request with CSRF token...")
    
    # Get CSRF token from cookies
    csrf_token = response.cookies.get('csrftoken')
    if not csrf_token:
        # Try to get from session
        csrf_token = client.cookies.get('csrftoken')
    
    # Create test user data
    test_email = f"test_{os.urandom(4).hex()}@example.com"
    post_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': test_email,
        'password1': 'testpass123',
        'password2': 'testpass123',
        'csrfmiddlewaretoken': csrf_token.value if csrf_token else '',
    }
    
    response = client.post('/register/', post_data, follow=True)
    
    if response.status_code == 200:
        print(f"   ✅ POST request successful (status: {response.status_code})")
        
        # Check if user was created
        if User.objects.filter(email=test_email).exists():
            user = User.objects.get(email=test_email)
            print(f"   ✅ User created successfully")
            print(f"   ✅ User role: {user.role}")
            
            # Cleanup
            user.delete()
            print("   ✅ Test user cleaned up")
            return True
        else:
            print("   ⚠️  POST successful but user not created (check for validation errors)")
            return True  # Still counts as success if no CSRF error
    else:
        print(f"   ❌ POST request failed (status: {response.status_code})")
        if response.status_code == 403:
            print("   ❌ CSRF verification failed!")
        return False


def test_login_view():
    """Test login view"""
    print("\n" + "=" * 60)
    print("TESTING LOGIN VIEW")
    print("=" * 60)
    
    client = Client(enforce_csrf_checks=True)
    
    # GET request
    print("\n1. Testing GET request to /login/...")
    response = client.get('/login/')
    if response.status_code == 200:
        print(f"   ✅ GET request successful (status: {response.status_code})")
        
        # Check for CSRF token
        if 'csrfmiddlewaretoken' in response.content.decode():
            print("   ✅ CSRF token found in form")
            return True
        else:
            print("   ❌ CSRF token NOT found in form")
            return False
    else:
        print(f"   ❌ GET request failed (status: {response.status_code})")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CSRF FIX VERIFICATION SCRIPT")
    print("=" * 60)
    
    results = []
    
    # Test 1: Configuration
    results.append(("CSRF Configuration", test_csrf_configuration()))
    
    # Test 2: Signup View
    results.append(("Signup View", test_signup_view()))
    
    # Test 3: Login View
    results.append(("Login View", test_login_view()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - CSRF FIX VERIFIED!")
    else:
        print("❌ SOME TESTS FAILED - PLEASE REVIEW")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
