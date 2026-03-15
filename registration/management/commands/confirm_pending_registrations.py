"""
Management command to confirm all pending registrations.
Useful when no payment system is in place and all purchases should be confirmed.
"""
from django.core.management.base import BaseCommand
from registration.models import Registration, RegistrationStatus


class Command(BaseCommand):
    help = 'Confirm all pending registrations by setting their status to confirmed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Get all pending registrations
        pending_registrations = Registration.objects.filter(status=RegistrationStatus.PENDING)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Dry run: Would confirm {pending_registrations.count()} pending registrations')
            )
            for reg in pending_registrations[:10]:  # Show first 10
                self.stdout.write(f'  - {reg.registration_number}: {reg.attendee_name} ({reg.event.title})')
            if pending_registrations.count() > 10:
                self.stdout.write(f'  ... and {pending_registrations.count() - 10} more')
        else:
            count = 0
            for reg in pending_registrations:
                reg.confirm()  # This will set to confirmed and update ticket counts
                count += 1
                if count % 100 == 0:
                    self.stdout.write(f'Processed {count} registrations...')

            self.stdout.write(
                self.style.SUCCESS(f'Successfully confirmed {count} pending registrations')
            )
