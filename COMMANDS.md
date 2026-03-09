# Quick Command Reference

## 🚀 Start Servers

```bash
# Participant Portal (Port 8001)
python manage.py runserver 8001

# Organizer Portal (Port 8000)
python manage.py runserver 8000
```

## 🧪 Run Tests

```bash
# Test QR code feature
python test_qr_registration.py

# Check registrations
python check_tickets.py
```

## 🔍 View Logs

```bash
# View last 20 lines of registration log
Get-Content registration_log.txt -Tail 20

# Watch log in real-time
Get-Content registration_log.txt -Wait -Tail 10
```

## 🌐 Quick URLs

### Participant Portal (8001):
```
Events List:        http://127.0.0.1:8001/events/
Success Page:       http://127.0.0.1:8001/registration/success/25/
Register API:       http://127.0.0.1:8001/api/v1/register/
Email API:          http://127.0.0.1:8001/api/v1/send-qr-email/
```

### Organizer Portal (8000):
```
Admin:              http://127.0.0.1:8000/admin/
Events:             http://127.0.0.1:8000/events/
Registrations:      http://127.0.0.1:8000/registration/
```

## 📧 Test Email API

```bash
# Send QR code email
curl -X POST http://127.0.0.1:8001/api/v1/send-qr-email/ \
  -H "Content-Type: application/json" \
  -d '{"registration_id": 25}'
```

## 🔧 Database Queries

```bash
# Get latest registration
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings'); django.setup(); from registration.models import Registration; reg = Registration.objects.order_by('-id').first(); print(f'ID: {reg.id}, Number: {reg.registration_number}')"

# Count registrations
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings'); django.setup(); from registration.models import Registration; print(f'Total: {Registration.objects.count()}')"
```

## 📦 Install Dependencies

```bash
# Install QR code library
pip install qrcode[pil]

# Install all requirements
pip install -r requirements.txt
```

## 🗄️ Database

```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## 🧹 Cleanup

```bash
# Clear registration log
Clear-Content registration_log.txt

# Remove test files
Remove-Item test_success_page.html
```

## 📊 Check Status

```bash
# Check if servers are running
Get-Process python

# Check port usage
netstat -ano | findstr :8001
netstat -ano | findstr :8000
```

## 🎯 Quick Test Sequence

```bash
# 1. Start server
python manage.py runserver 8001

# 2. In another terminal, run tests
python test_qr_registration.py

# 3. Open browser to test
start http://127.0.0.1:8001/registration/success/25/
```

## 📝 View Files

```bash
# View success page template
code templates/participant/registration_success.html

# View email logic
code registration/views_success.py

# View registration API
code events_api/views/simple_registration.py
```

## 🔄 Restart Server

```bash
# Stop server: Ctrl+C in terminal

# Start again
python manage.py runserver 8001
```

## 📚 Documentation

```bash
# Open documentation
start FINAL_SUMMARY.md
start TEST_NOW.md
start QUICK_START.md
```
