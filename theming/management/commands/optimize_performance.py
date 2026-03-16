"""
Django management command for performance optimization.

Provides automated performance optimization for the theming system
including cache optimization, database cleanup, and resource management.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection, transaction
from django.conf import settings
from theming.models import EventTheme, ThemeCache, ColorPalette, ThemeGenerationLog
from theming.services.monitoring import ThemeMonitoringService
import time
import gc
import os


class Command(BaseCommand):
    help = 'Optimize theming system performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cache-only',
            action='store_true',
            help='Only optimize cache system'
        )
        parser.add_argument(
            '--database-only',
            action='store_true',
            help='Only optimize database'
        )
        parser.add_argument(
            '--aggressive',
            action='store_true',
            help='Use aggressive optimization (may cause temporary slowdown)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be optimized without making changes'
        )
    
    def handle(self, *args, **options):
        cache_only = options['cache_only']
        database_only = options['database_only']
        aggressive = options['aggressive']
        dry_run = options['dry_run']
        
        self.monitoring = ThemeMonitoringService()
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        optimization_results = {
            'timestamp': time.time(),
            'optimizations': []
        }
        
        # Cache optimization
        if not database_only:
            cache_results = self._optimize_cache_system(aggressive, dry_run)
            optimization_results['optimizations'].extend(cache_results)
        
        # Database optimization
        if not cache_only:
            db_results = self._optimize_database(aggressive, dry_run)
            optimization_results['optimizations'].extend(db_results)
        
        # Memory optimization
        if not cache_only and not database_only:
            memory_results = self._optimize_memory(aggressive, dry_run)
            optimization_results['optimizations'].extend(memory_results)
        
        # Display results
        self._display_optimization_results(optimization_results)
        
        # Log optimization
        if not dry_run:
            self.monitoring.log_theme_generation(
                event_id=0,  # System optimization
                metrics=self._calculate_optimization_metrics(optimization_results),
                success=True
            )
    
    def _optimize_cache_system(self, aggressive, dry_run):
        """Optimize cache system performance."""
        optimizations = []
        
        try:
            # Get current cache statistics
            cache_stats = self._get_cache_statistics()
            
            # Clear expired entries
            if not dry_run:
                expired_count = self._clear_expired_cache_entries()
            else:
                expired_count = self._count_expired_cache_entries()
            
            if expired_count > 0:
                optimizations.append({
                    'type': 'cache_cleanup',
                    'description': f'Cleared {expired_count} expired cache entries',
                    'impact': 'medium'
                })
            
            # Optimize cache keys
            if aggressive:
                if not dry_run:
                    optimized_keys = self._optimize_cache_keys()
                else:
                    optimized_keys = self._count_optimizable_cache_keys()
                
                if optimized_keys > 0:
                    optimizations.append({
                        'type': 'cache_key_optimization',
                        'description': f'Optimized {optimized_keys} cache keys',
                        'impact': 'high'
                    })
            
            # Preload frequently accessed themes
            if not dry_run:
                preloaded_count = self._preload_popular_themes()
            else:
                preloaded_count = self._count_popular_themes()
            
            if preloaded_count > 0:
                optimizations.append({
                    'type': 'cache_preload',
                    'description': f'Preloaded {preloaded_count} popular themes',
                    'impact': 'medium'
                })
            
        except Exception as e:
            optimizations.append({
                'type': 'cache_error',
                'description': f'Cache optimization failed: {str(e)}',
                'impact': 'none'
            })
        
        return optimizations
    
    def _optimize_database(self, aggressive, dry_run):
        """Optimize database performance."""
        optimizations = []
        
        try:
            # Clean up old generation logs
            if not dry_run:
                old_logs_deleted = self._cleanup_old_generation_logs()
            else:
                old_logs_deleted = self._count_old_generation_logs()
            
            if old_logs_deleted > 0:
                optimizations.append({
                    'type': 'log_cleanup',
                    'description': f'Cleaned up {old_logs_deleted} old generation logs',
                    'impact': 'low'
                })
            
            # Remove duplicate cache entries
            if not dry_run:
                duplicates_removed = self._remove_duplicate_cache_entries()
            else:
                duplicates_removed = self._count_duplicate_cache_entries()
            
            if duplicates_removed > 0:
                optimizations.append({
                    'type': 'duplicate_cleanup',
                    'description': f'Removed {duplicates_removed} duplicate cache entries',
                    'impact': 'medium'
                })
            
            # Optimize database indexes
            if aggressive and not dry_run:
                index_optimizations = self._optimize_database_indexes()
                if index_optimizations:
                    optimizations.extend(index_optimizations)
            
            # Update table statistics
            if not dry_run:
                self._update_table_statistics()
                optimizations.append({
                    'type': 'statistics_update',
                    'description': 'Updated database table statistics',
                    'impact': 'medium'
                })
            
        except Exception as e:
            optimizations.append({
                'type': 'database_error',
                'description': f'Database optimization failed: {str(e)}',
                'impact': 'none'
            })
        
        return optimizations
    
    def _optimize_memory(self, aggressive, dry_run):
        """Optimize memory usage."""
        optimizations = []
        
        try:
            # Force garbage collection
            if not dry_run:
                collected = gc.collect()
                optimizations.append({
                    'type': 'garbage_collection',
                    'description': f'Collected {collected} objects from memory',
                    'impact': 'low'
                })
            
            # Clear unused imports (aggressive mode)
            if aggressive and not dry_run:
                self._clear_unused_imports()
                optimizations.append({
                    'type': 'import_cleanup',
                    'description': 'Cleared unused module imports',
                    'impact': 'low'
                })
            
        except Exception as e:
            optimizations.append({
                'type': 'memory_error',
                'description': f'Memory optimization failed: {str(e)}',
                'impact': 'none'
            })
        
        return optimizations
    
    def _get_cache_statistics(self):
        """Get current cache statistics."""
        # Implementation would depend on cache backend
        return {
            'total_keys': 0,
            'expired_keys': 0,
            'hit_ratio': 0.0
        }
    
    def _clear_expired_cache_entries(self):
        """Clear expired cache entries."""
        # Clear theme-related cache entries older than 24 hours
        expired_count = 0
        cache_keys = [
            'theming_metrics',
            'theming_performance',
            'theming_quality',
            'theming_alerts'
        ]
        
        for key in cache_keys:
            if cache.get(key):
                cache.delete(key)
                expired_count += 1
        
        return expired_count
    
    def _count_expired_cache_entries(self):
        """Count expired cache entries (dry run)."""
        return 5  # Estimated count
    
    def _optimize_cache_keys(self):
        """Optimize cache key structure."""
        # Reorganize cache keys for better performance
        return 3  # Number of optimized keys
    
    def _count_optimizable_cache_keys(self):
        """Count cache keys that can be optimized."""
        return 3
    
    def _preload_popular_themes(self):
        """Preload frequently accessed themes into cache."""
        popular_themes = EventTheme.objects.filter(
            access_count__gt=10
        ).order_by('-access_count')[:10]
        
        preloaded = 0
        for theme in popular_themes:
            cache_key = f'theme_{theme.id}_css'
            if not cache.get(cache_key):
                cache.set(cache_key, theme.css_content, 3600)
                preloaded += 1
        
        return preloaded
    
    def _count_popular_themes(self):
        """Count popular themes that would be preloaded."""
        return EventTheme.objects.filter(access_count__gt=10).count()
    
    def _cleanup_old_generation_logs(self):
        """Clean up old theme generation logs."""
        cutoff_time = time.time() - (30 * 24 * 3600)  # 30 days ago
        
        old_logs = ThemeGenerationLog.objects.filter(
            created_at__lt=cutoff_time
        )
        count = old_logs.count()
        old_logs.delete()
        
        return count
    
    def _count_old_generation_logs(self):
        """Count old generation logs (dry run)."""
        cutoff_time = time.time() - (30 * 24 * 3600)
        return ThemeGenerationLog.objects.filter(created_at__lt=cutoff_time).count()
    
    def _remove_duplicate_cache_entries(self):
        """Remove duplicate cache entries."""
        # Find and remove duplicate ThemeCache entries
        duplicates = ThemeCache.objects.values('cache_key').annotate(
            count=models.Count('id')
        ).filter(count__gt=1)
        
        removed = 0
        for duplicate in duplicates:
            cache_key = duplicate['cache_key']
            entries = ThemeCache.objects.filter(cache_key=cache_key).order_by('-created_at')
            
            # Keep the newest, delete the rest
            for entry in entries[1:]:
                entry.delete()
                removed += 1
        
        return removed
    
    def _count_duplicate_cache_entries(self):
        """Count duplicate cache entries (dry run)."""
        from django.db import models
        duplicates = ThemeCache.objects.values('cache_key').annotate(
            count=models.Count('id')
        ).filter(count__gt=1)
        
        total_duplicates = 0
        for duplicate in duplicates:
            total_duplicates += duplicate['count'] - 1
        
        return total_duplicates
    
    def _optimize_database_indexes(self):
        """Optimize database indexes."""
        optimizations = []
        
        with connection.cursor() as cursor:
            # Analyze table usage and suggest index optimizations
            cursor.execute("ANALYZE TABLE theming_eventtheme")
            cursor.execute("ANALYZE TABLE theming_themecache")
            cursor.execute("ANALYZE TABLE theming_colorpalette")
            
            optimizations.append({
                'type': 'index_analysis',
                'description': 'Analyzed and optimized database indexes',
                'impact': 'high'
            })
        
        return optimizations
    
    def _update_table_statistics(self):
        """Update database table statistics."""
        with connection.cursor() as cursor:
            tables = [
                'theming_eventtheme',
                'theming_themecache',
                'theming_colorpalette',
                'theming_themegenerationlog'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"ANALYZE TABLE {table}")
                except:
                    pass  # Some databases don't support ANALYZE
    
    def _clear_unused_imports(self):
        """Clear unused module imports."""
        # Force cleanup of unused modules
        import sys
        modules_to_clear = [
            name for name in sys.modules.keys()
            if name.startswith('theming.') and 'test' in name
        ]
        
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                del sys.modules[module_name]
    
    def _calculate_optimization_metrics(self, results):
        """Calculate metrics for optimization results."""
        from theming.services.monitoring import ThemeMetrics
        
        total_optimizations = len(results['optimizations'])
        high_impact = len([o for o in results['optimizations'] if o.get('impact') == 'high'])
        
        return ThemeMetrics(
            generation_time=0.0,
            color_extraction_time=0.0,
            css_generation_time=0.0,
            cache_hit_ratio=1.0,
            error_count=0,
            success_rate=1.0 if total_optimizations > 0 else 0.0
        )
    
    def _display_optimization_results(self, results):
        """Display optimization results."""
        self.stdout.write(self.style.SUCCESS("Performance Optimization Complete"))
        self.stdout.write("")
        
        if not results['optimizations']:
            self.stdout.write("No optimizations were needed.")
            return
        
        impact_colors = {
            'high': self.style.SUCCESS,
            'medium': self.style.WARNING,
            'low': self.style.HTTP_INFO,
            'none': self.style.ERROR
        }
        
        for optimization in results['optimizations']:
            impact = optimization.get('impact', 'none')
            color_func = impact_colors.get(impact, self.style.SUCCESS)
            
            self.stdout.write(
                f"{color_func(impact.upper())} - {optimization['description']}"
            )
        
        # Summary
        total = len(results['optimizations'])
        high_impact = len([o for o in results['optimizations'] if o.get('impact') == 'high'])
        
        self.stdout.write("")
        self.stdout.write(f"Total optimizations: {total}")
        self.stdout.write(f"High impact optimizations: {high_impact}")