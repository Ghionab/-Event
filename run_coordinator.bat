@echo off
cd /d "%~dp0"
echo Starting Coordinator Portal Setup...
set DJANGO_SETTINGS_MODULE=event_project.settings
python setup_test_coordinator.py
echo.
echo Starting Coordinator Portal on port 8003...
set DJANGO_SETTINGS_MODULE=event_project.settings_coordinator
python manage.py runserver 8003
pause
