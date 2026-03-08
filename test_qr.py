#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_project.settings_participant')
django.setup()

from registration.models import Registration

reg = Registration.objects.first()
print('Registration exists:', reg is not None)
if reg:
    print('QR method exists:', hasattr(reg, 'generate_qr_code_image'))
    print('QR code:', reg.qr_code)
    try:
        qr_image = reg.generate_qr_code_image()
        print('QR image generated successfully, length:', len(qr_image) if qr_image else 'None')
    except Exception as e:
        print('Error generating QR image:', e)
