"""
Management command to re-extract color palettes from event logos using the new premium algorithm.

This allows updating existing events with the improved navy/gold detection and professional color harmonization.

Usage:
    python manage.py extract_event_colors --event-id 6
    python manage.py extract_event_colors --all
    python manage.py extract_event_colors --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from events.models import Event


class Command(BaseCommand):
    help = 'Extract color palettes from event logos using premium 10/10 algorithm'

    def add_arguments(self, parser):
        parser.add_argument(
            '--event-id',
            type=int,
            help='Extract colors for a specific event ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Extract colors for all events with logos'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force extraction even if colors already exist'
        )

    def handle(self, *args, **options):
        event_id = options.get('event_id')
        all_events = options.get('all')
        dry_run = options.get('dry_run')
        force = options.get('force')

        # Get events to process
        if event_id:
            try:
                events = Event.objects.filter(pk=event_id)
            except Event.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Event {event_id} not found'))
                return
        elif all_events:
            events = Event.objects.filter(logo__isnull=False).exclude(logo='')
        else:
            self.stdout.write(self.style.WARNING('Please specify --event-id or --all'))
            return

        total = events.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No events with logos found'))
            return

        self.stdout.write(f'Processing {total} event(s)...\n')

        processed = 0
        skipped = 0
        errors = 0

        for event in events:
            self.stdout.write(f"\nEvent: {event.title} (ID: {event.pk})")
            
            if not event.logo:
                self.stdout.write(self.style.WARNING('  - No logo, skipping'))
                skipped += 1
                continue

            # Check if already has colors (unless force flag)
            if not force and event.primary_color and event.primary_color != '#007bff':
                self.stdout.write(self.style.WARNING(f'  - Already has colors (use --force to override):'))
                self.stdout.write(f'    Primary: {event.primary_color}')
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(self.style.NOTICE('  - Would extract colors (dry-run)'))
                continue

            # Extract colors
            try:
                with transaction.atomic():
                    old_colors = {
                        'primary': event.primary_color,
                        'secondary': event.secondary_color,
                        'accent': event.accent_color,
                        'background': event.background_color
                    }
                    
                    # Call the new premium extraction
                    event.extract_colors_from_logo()
                    
                    # Save only the color fields to avoid triggering other signals
                    Event.objects.filter(pk=event.pk).update(
                        primary_color=event.primary_color,
                        secondary_color=event.secondary_color,
                        accent_color=event.accent_color,
                        background_color=event.background_color
                    )
                    
                    self.stdout.write(self.style.SUCCESS('  - Colors extracted successfully:'))
                    self.stdout.write(f'    Primary: {old_colors["primary"]} → {event.primary_color}')
                    self.stdout.write(f'    Secondary: {old_colors["secondary"]} → {event.secondary_color}')
                    self.stdout.write(f'    Accent: {old_colors["accent"]} → {event.accent_color}')
                    self.stdout.write(f'    Background: {old_colors["background"]} → {event.background_color}')
                    
                    # Detect if it looks like a navy/gold theme
                    from events.color_utils import hex_to_rgb
                    primary_rgb = hex_to_rgb(event.primary_color)
                    secondary_rgb = hex_to_rgb(event.secondary_color)
                    
                    # Check for gold tones (high red and green, lower blue)
                    is_gold = (primary_rgb[0] > 180 and primary_rgb[1] > 140 and primary_rgb[2] < 100)
                    # Check for navy tones (dark with blue)
                    is_navy = (secondary_rgb[0] < 30 and secondary_rgb[1] < 40 and secondary_rgb[2] > 60)
                    
                    if is_gold:
                        self.stdout.write(self.style.SUCCESS('    ✓ Detected: Gold/Metallic primary color'))
                    if is_navy:
                        self.stdout.write(self.style.SUCCESS('    ✓ Detected: Navy blue secondary color'))
                    
                    processed += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  - Error extracting colors: {e}'))
                errors += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'  Processed: {processed}')
        self.stdout.write(f'  Skipped: {skipped}')
        self.stdout.write(f'  Errors: {errors}')
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('\nDry-run completed. No changes made.'))
        elif errors == 0:
            self.stdout.write(self.style.SUCCESS('\nColor extraction completed successfully!'))
        else:
            self.stdout.write(self.style.WARNING('\nColor extraction completed with some errors.'))
