@echo off
cd /d "%~dp0"
set DJANGO_SETTINGS_MODULE=event_project.settings
python manage.py runserver 8000
