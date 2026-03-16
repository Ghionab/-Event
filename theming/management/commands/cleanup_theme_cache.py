"""
Django management command for cleaning up theme cache.

Provides cache cleanup functionality with configurable retention periods
and automatic optimization of cache performance.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from theming.models import ThemeCache, EventTheme
import logging


class Command(BaseCommand):
    help = 'Clean up theme cache and optimize performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to retain cache entries (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='Optimize cache performance after cleanup'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        optimize = options['optimize']
        force = options['force']
        
        self.stdout.write(f"Theme cache cleanup - retaining {days} days")
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find expired cache entries
        expired_entries = ThemeCache.objects.filter(
            created_at__lt=cutoff_date
        )
        
        expired_count = expired_entries.count()
        
        if expired_count == 0:
            self.stdout.write(
                self.style.SUCCESS("No expired cache entries found")
            )
            return
        
        self.stdout.write(f"Found {expired_count} expired cache entries")
        
        if dry_run:
            self.stdout.write("DRY RUN - Would delete:")
            for entry in expired_entries[:10]:  # Show first 10
                self.stdout.write(f"  - {entry.cache_key} (created: {entry.created_at})")
            if expired_count > 10:
                self.stdout.write(f"  ... and {expired_count - 10} more")
            return
        
        # Confirm deletion
        if not force:
            confirm = input(f"Delete {expired_count} cache entries? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write("Cleanup cancelled")
                return
        
        # Perform cleanup
        try:
            deleted_count, _ = expired_entries.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {deleted_count} expired cache entries")
            )
            
            # Clear Redis cache for deleted entries
            self._clear_redis_cache(expired_entries)
            
            if optimize:
                self._optimize_cache()
                
        except Exception as e:
            raise CommandError(f"Cache cleanup failed: {str(e)}")
    
    def _clear_redis_cache(self, entries):
        """Clear corresponding Redis cache entries."""
        cleared_count = 0
        for entry in entries:
            if cache.delete(entry.cache_key):
                cleared_count += 1
        
        self.stdout.write(f"Cleared {cleared_count} Redis cache entries")
    
    def _optimize_cache(self):
        """Optimize cache performance."""
        self.stdout.write("Optimizing cache performance...")
        
        # Rebuild frequently accessed themes
        popular_themes = EventTheme.objects.filter(
            is_active=True
        ).order_by('-updated_at')[:10]
        
        rebuilt_count = 0
        for theme in popular_themes:
            try:
                # Trigger cache rebuild
                theme.get_cached_css()
                rebuilt_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Failed to rebuild cache for theme {theme.id}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Rebuilt cache for {rebuilt_count} popular themes")
        )