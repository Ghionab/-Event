"""
Django management command for regenerating event themes.

Provides bulk theme regeneration with progress tracking and error handling.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from theming.models import EventTheme
from theming.services.color_extractor import ColorExtractor
from theming.services.theme_generator import ThemeGenerator
from theming.services.monitoring import ThemeMonitoringService
import logging
from tqdm import tqdm


class Command(BaseCommand):
    help = 'Regenerate themes for events'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--event-id',
            type=int,
            help='Regenerate theme for specific event ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate all active themes'
        )
        parser.add_argument(
            '--failed-only',
            action='store_true',
            help='Regenerate only failed themes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even for successful themes'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of themes to process in each batch (default: 10)'
        )
    
    def handle(self, *args, **options):
        event_id = options.get('event_id')
        regenerate_all = options['all']
        failed_only = options['failed_only']
        force = options['force']
        batch_size = options['batch_size']
        
        # Initialize services
        self.color_extractor = ColorExtractor()
        self.theme_generator = ThemeGenerator()
        self.monitoring = ThemeMonitoringService()
        
        # Determine which themes to regenerate
        if event_id:
            themes = EventTheme.objects.filter(id=event_id)
            if not themes.exists():
                raise CommandError(f"Event theme with ID {event_id} not found")
        elif regenerate_all:
            themes = EventTheme.objects.filter(is_active=True)
        elif failed_only:
            themes = EventTheme.objects.filter(
                is_active=True,
                generation_status='failed'
            )
        else:
            raise CommandError("Must specify --event-id, --all, or --failed-only")
        
        total_themes = themes.count()
        
        if total_themes == 0:
            self.stdout.write("No themes to regenerate")
            return
        
        self.stdout.write(f"Regenerating {total_themes} themes...")
        
        # Process themes in batches
        success_count = 0
        error_count = 0
        
        with tqdm(total=total_themes, desc="Regenerating themes") as pbar:
            for i in range(0, total_themes, batch_size):
                batch = themes[i:i + batch_size]
                
                for theme in batch:
                    try:
                        success = self._regenerate_theme(theme, force)
                        if success:
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Failed to regenerate theme {theme.id}: {e}")
                        )
                        error_count += 1
                    
                    pbar.update(1)
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"Regeneration complete: {success_count} successful, {error_count} failed"
            )
        )
    
    def _regenerate_theme(self, theme, force=False):
        """Regenerate a single theme."""
        if not force and theme.generation_status == 'completed':
            self.stdout.write(f"Skipping theme {theme.id} (already completed)")
            return True
        
        try:
            with transaction.atomic():
                # Update status
                theme.generation_status = 'processing'
                theme.save()
                
                # Extract colors from event assets
                if theme.event.logo:
                    colors = self.color_extractor.extract_colors(theme.event.logo.path)
                else:
                    # Use fallback colors
                    colors = ['#2563eb', '#1e40af', '#3b82f6']
                
                # Generate theme CSS
                css_content = self.theme_generator.generate_complete_theme(
                    colors=colors,
                    theme_name=f"event_{theme.event.id}",
                    portal_type='all'
                )
                
                # Update theme
                theme.primary_color = colors[0] if colors else '#2563eb'
                theme.css_content = css_content
                theme.generation_status = 'completed'
                theme.save()
                
                self.stdout.write(f"Successfully regenerated theme {theme.id}")
                return True
                
        except Exception as e:
            # Update status to failed
            theme.generation_status = 'failed'
            theme.error_message = str(e)
            theme.save()
            
            self.stdout.write(
                self.style.ERROR(f"Failed to regenerate theme {theme.id}: {e}")
            )
            return False