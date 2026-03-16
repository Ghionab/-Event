#!/usr/bin/env python
"""
UI Compatibility and Validation Demo

This script demonstrates the UI compatibility and validation system
for the Dynamic Event Theming System.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_management.settings')
django.setup()

from theming.services.ui_compatibility import UICompatibilityValidator
from theming.services.theme_generator import ThemeGenerator
from django.contrib.auth import get_user_model
from django.utils import timezone
from events.models import Event
from theming.models import EventTheme
import uuid

User = get_user_model()


def create_demo_data():
    """Create demo data for the compatibility test."""
    unique_id = str(uuid.uuid4())[:8]
    
    user = User.objects.create_user(
        email=f'demo-user-{unique_id}@example.com',
        password='demopass123',
        first_name='Demo',
        last_name='User'
    )
    
    event = Event.objects.create(
        title=f'Demo Event {unique_id}',
        description='Demo event for UI compatibility testing',
        start_date=timezone.now() + timezone.timedelta(days=30),
        end_date=timezone.now() + timezone.timedelta(days=31),
        organizer=user
    )
    
    return user, event


def demo_good_theme_validation():
    """Demonstrate validation of a well-designed theme."""
    print("=" * 60)
    print("DEMO: Good Theme Validation")
    print("=" * 60)
    
    validator = UICompatibilityValidator()
    theme_generator = ThemeGenerator()
    
    # Create a good theme with proper contrast and colors
    good_theme_colors = {
        'primary': '#007bff',      # Blue
        'secondary': '#6c757d',    # Gray
        'accent': '#28a745',       # Green
        'background': '#ffffff',   # White
        'text': '#333333'          # Dark gray
    }
    
    print(f"Theme Colors: {good_theme_colors}")
    
    # Generate theme CSS
    generated_theme = theme_generator.generate_theme(good_theme_colors)
    
    # Validate the theme
    validation_results = validator.validate_complete_ui_compatibility(
        generated_theme.css_content, good_theme_colors
    )
    
    # Display results
    print(f"\nOverall Compatibility Score: {validation_results['overall_compatibility_score']:.1f}/100")
    
    print(f"\nComponent Validations: {len(validation_results['component_validations'])} components tested")
    for validation in validation_results['component_validations'][:5]:  # Show first 5
        print(f"  - {validation['component']}: {validation['level']}")
    
    print(f"\nInteractive Element Tests: {len(validation_results['interactive_element_tests'])} elements tested")
    for test in validation_results['interactive_element_tests']:
        print(f"  - {test['element']}: {test['accessibility_score']:.1f}/100 (contrast: {test['contrast_ratio']:.2f})")
    
    print(f"\nBrowser Compatibility: {len(validation_results['browser_compatibility'])} browsers tested")
    for browser in validation_results['browser_compatibility']:
        status = "✓ Supported" if not browser['fallback_needed'] else "⚠ Needs fallback"
        print(f"  - {browser['browser']} {browser['version']}: {status}")
    
    error_analysis = validation_results['error_analysis']
    print(f"\nError Analysis:")
    print(f"  - Errors detected: {error_analysis['errors_detected']}")
    print(f"  - Error count: {error_analysis['error_count']}")
    print(f"  - Auto-fixes available: {error_analysis['auto_fixes_available']}")
    
    if validation_results['recommendations']:
        print(f"\nRecommendations:")
        for rec in validation_results['recommendations'][:3]:
            print(f"  • {rec}")
    
    return validation_results


def demo_problematic_theme_validation():
    """Demonstrate validation of a problematic theme with recovery."""
    print("\n" + "=" * 60)
    print("DEMO: Problematic Theme Validation & Recovery")
    print("=" * 60)
    
    validator = UICompatibilityValidator()
    
    # Create a problematic theme with poor contrast and issues
    problematic_colors = {
        'primary': '#cccccc',      # Light gray
        'secondary': '#dddddd',    # Very light gray
        'accent': '#eeeeee',       # Almost white
        'background': '#ffffff',   # White
        'text': '#f0f0f0'          # Very light gray text
    }
    
    print(f"Problematic Theme Colors: {problematic_colors}")
    
    # Create problematic CSS with syntax errors and poor contrast
    problematic_css = """
    .button {
        color: #cccccc;
        background-color: #ffffff;
        /* Very poor contrast */
    }
    .input {
        /* Missing essential properties */
    }
    .broken-element {
        color: invalid-color;
        display: none;
        display: block;  /* Conflicting properties */
    }
    .syntax-error {
        color: #ff0000  /* Missing semicolon */
        background: #ffffff;
    }
    """
    
    print("\nProblematic CSS includes:")
    print("  - Poor color contrast")
    print("  - Missing essential properties")
    print("  - Invalid color values")
    print("  - Conflicting CSS properties")
    print("  - Syntax errors")
    
    # Validate the problematic theme
    validation_results = validator.validate_complete_ui_compatibility(
        problematic_css, problematic_colors
    )
    
    # Display results
    print(f"\nOverall Compatibility Score: {validation_results['overall_compatibility_score']:.1f}/100")
    
    # Show component issues
    print(f"\nComponent Issues:")
    for validation in validation_results['component_validations']:
        if validation['issues']:
            print(f"  - {validation['component']} ({validation['level']}):")
            for issue in validation['issues'][:2]:  # Show first 2 issues
                print(f"    • {issue}")
    
    # Show error analysis
    error_analysis = validation_results['error_analysis']
    print(f"\nError Detection & Recovery:")
    print(f"  - Errors detected: {error_analysis['errors_detected']}")
    print(f"  - Error count: {error_analysis['error_count']}")
    print(f"  - Auto-fixes available: {error_analysis['auto_fixes_available']}")
    
    if error_analysis['recovery_css']:
        print(f"  - Recovery CSS generated: {len(error_analysis['recovery_css'])} characters")
        print("  - Recovery CSS preview:")
        recovery_preview = error_analysis['recovery_css'][:200] + "..." if len(error_analysis['recovery_css']) > 200 else error_analysis['recovery_css']
        print(f"    {recovery_preview}")
    
    if validation_results['recommendations']:
        print(f"\nRecommendations for improvement:")
        for rec in validation_results['recommendations']:
            print(f"  • {rec}")
    
    return validation_results


def demo_compatibility_report():
    """Demonstrate the human-readable compatibility report."""
    print("\n" + "=" * 60)
    print("DEMO: Compatibility Report Generation")
    print("=" * 60)
    
    validator = UICompatibilityValidator()
    theme_generator = ThemeGenerator()
    
    # Create a mixed theme (some good, some issues)
    mixed_colors = {
        'primary': '#007bff',      # Good blue
        'secondary': '#cccccc',    # Light gray (potential contrast issues)
        'accent': '#28a745',       # Good green
        'background': '#ffffff',   # White
        'text': '#666666'          # Medium gray
    }
    
    generated_theme = theme_generator.generate_theme(mixed_colors)
    validation_results = validator.validate_complete_ui_compatibility(
        generated_theme.css_content, mixed_colors
    )
    
    # Generate human-readable report
    report = validator.generate_compatibility_report(validation_results)
    
    print("Generated Compatibility Report:")
    print("-" * 40)
    print(report)
    
    return report


def demo_database_integration():
    """Demonstrate integration with database-stored themes."""
    print("\n" + "=" * 60)
    print("DEMO: Database Integration")
    print("=" * 60)
    
    user, event = create_demo_data()
    validator = UICompatibilityValidator()
    
    try:
        # Create a theme in the database
        theme = EventTheme.objects.create(
            event=event,
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745',
            neutral_light='#ffffff',
            neutral_dark='#333333',
            css_content="""
            .button {
                background-color: #007bff;
                color: #ffffff;
                border: 1px solid #007bff;
                padding: 0.375rem 0.75rem;
                border-radius: 0.25rem;
            }
            .input {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 0.375rem 0.75rem;
            }
            """,
            css_hash='demo-hash-' + str(uuid.uuid4())[:8],
            cache_key='demo-cache-' + str(uuid.uuid4())[:8],
            wcag_compliant=True
        )
        
        print(f"Created theme for event: {event.title}")
        print(f"Theme ID: {theme.id}")
        print(f"WCAG Compliant: {theme.wcag_compliant}")
        
        # Validate the stored theme
        theme_colors = {
            'primary': theme.primary_color,
            'secondary': theme.secondary_color,
            'accent': theme.accent_color,
            'background': theme.neutral_light,
            'text': theme.neutral_dark
        }
        
        validation_results = validator.validate_complete_ui_compatibility(
            theme.css_content, theme_colors
        )
        
        print(f"\nValidation Results:")
        print(f"  - Overall Score: {validation_results['overall_compatibility_score']:.1f}/100")
        print(f"  - Components Tested: {len(validation_results['component_validations'])}")
        print(f"  - Errors Detected: {validation_results['error_analysis']['errors_detected']}")
        
        # Update theme based on validation
        if validation_results['overall_compatibility_score'] >= 80:
            theme.wcag_compliant = True
            theme.save()
            print("  - Theme marked as WCAG compliant")
        
        print(f"\nTheme successfully validated and stored in database")
        
        # Clean up
        theme.delete()
        event.delete()
        user.delete()
        
    except Exception as e:
        print(f"Error in database integration demo: {e}")
        # Clean up on error
        try:
            event.delete()
            user.delete()
        except:
            pass


def main():
    """Run all UI compatibility demos."""
    print("UI Compatibility and Validation System Demo")
    print("Dynamic Event Theming System")
    print("=" * 60)
    
    try:
        # Run demos
        demo_good_theme_validation()
        demo_problematic_theme_validation()
        demo_compatibility_report()
        demo_database_integration()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()