from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from events.models import Event
from theming.models import EventTheme, ThemeGenerationLog
from django.db import transaction


class Command(BaseCommand):
    help = 'Generate themes for events that don\'t have them'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--event-id',
            type=int,
            help='Generate theme for specific event ID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate themes even if they already exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
    
    def handle(self, *args, **options):
        if options['event_id']:
            # Generate theme for specific event
            try:
                event = Event.objects.get(id=options['event_id'])
                self.generate_theme_for_event(event, options['force'], options['dry_run'])
            except Event.DoesNotExist:
                raise CommandError(f'Event with ID {options["event_id"]} does not exist')
        else:
            # Generate themes for all events without themes
            events_without_themes = Event.objects.filter(theme__isnull=True)
            
            if options['force']:
                # Include all events if force is specified
                events_without_themes = Event.objects.all()
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING(
                        f'DRY RUN: Would generate themes for {events_without_themes.count()} events'
                    )
                )
                for event in events_without_themes:
                    self.stdout.write(f'  - {event.title} (ID: {event.id})')
                return
            
            self.stdout.write(f'Generating themes for {events_without_themes.count()} events...')
            
            success_count = 0
            error_count = 0
            
            for event in events_without_themes:
                try:
                    self.generate_theme_for_event(event, options['force'], options['dry_run'])
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Generated theme for "{event.title}"')
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to generate theme for "{event.title}": {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCompleted: {success_count} successful, {error_count} errors'
                )
            )
    
    def generate_theme_for_event(self, event, force=False, dry_run=False):
        """Generate theme for a single event"""
        if dry_run:
            self.stdout.write(f'DRY RUN: Would generate theme for "{event.title}"')
            return
        
        # Check if theme already exists
        existing_theme = None
        try:
            existing_theme = EventTheme.objects.get(event=event)
            if not force:
                self.stdout.write(
                    self.style.WARNING(f'Theme already exists for "{event.title}". Use --force to regenerate.')
                )
                return
        except EventTheme.DoesNotExist:
            pass
        
        # Generate basic theme (this would be replaced with actual color extraction logic)
        theme_data = {
            'primary_color': '#007bff',
            'secondary_color': '#6c757d',
            'accent_color': '#28a745',
            'neutral_light': '#f8f9fa',
            'neutral_dark': '#343a40',
            'css_content': self.generate_basic_css(),
            'generation_method': 'auto',
            'extraction_confidence': 0.8,
            'wcag_compliant': True,
            'is_fallback': True,  # Mark as fallback since we're not doing real extraction
        }
        
        with transaction.atomic():
            if existing_theme and force:
                # Update existing theme
                for key, value in theme_data.items():
                    setattr(existing_theme, key, value)
                existing_theme.save()
                theme = existing_theme
                operation_type = 'generation'
            else:
                # Create new theme
                theme = EventTheme.objects.create(event=event, **theme_data)
                operation_type = 'generation'
            
            # Log the operation
            ThemeGenerationLog.log_operation(
                event=event,
                operation_type=operation_type,
                status='success',
                processing_time_ms=100,  # Placeholder
                extraction_confidence=0.8,
            )
        
        return theme
    
    def generate_basic_css(self):
        """Generate basic CSS theme (placeholder implementation)"""
        return """
        :root {
            --theme-primary: #007bff;
            --theme-secondary: #6c757d;
            --theme-accent: #28a745;
            --theme-neutral-light: #f8f9fa;
            --theme-neutral-dark: #343a40;
            
            /* Interactive states */
            --theme-hover: #0056b3;
            --theme-active: #004085;
            --theme-focus: rgba(0, 123, 255, 0.25);
        }
        
        /* Apply theme colors to common elements */
        .btn-primary {
            background-color: var(--theme-primary);
            border-color: var(--theme-primary);
        }
        
        .btn-primary:hover {
            background-color: var(--theme-hover);
            border-color: var(--theme-hover);
        }
        
        .navbar-brand {
            color: var(--theme-primary) !important;
        }
        
        .card-header {
            background-color: var(--theme-neutral-light);
            border-bottom: 1px solid var(--theme-primary);
        }
        
        /* Navigation theming */
        .nav-pills .nav-link.active {
            background-color: var(--theme-primary);
        }
        
        /* Form theming */
        .form-control:focus {
            border-color: var(--theme-primary);
            box-shadow: 0 0 0 0.2rem var(--theme-focus);
        }
        
        /* Alert theming */
        .alert-primary {
            color: var(--theme-primary);
            background-color: rgba(0, 123, 255, 0.1);
            border-color: var(--theme-primary);
        }
        """