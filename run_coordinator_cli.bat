@echo off
cd /d "%~dp0"
echo Starting Coordinator Portal CLI...
set DJANGO_SETTINGS_MODULE=event_project.settings_coordinator
python run_coordinator_cli.py
pause
