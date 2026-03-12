#!/usr/bin/env python
"""
Run the Gate Staff Portal on port 8002
"""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_staff')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Run server on port 8002
    sys.argv = ['manage.py', 'runserver', '8002']
    execute_from_command_line(sys.argv)
