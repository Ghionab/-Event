"""
Django management command for system health checks.

Provides comprehensive health monitoring for the theming system
including performance, accessibility, and functionality validation.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from theming.models import EventTheme, ThemeCache
from theming.services.monitoring import ThemeMonitoringService
from theming.services.ui_compatibility import UICompatibilityValidator
import time
import json


class Command(BaseCommand):
    help = 'Perform comprehensive health check of theming system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed health information'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results in JSON format'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix detected issues'
        )
    
    def handle(self, *args, **options):
        detailed = options['detailed']
        json_output = options['json']
        auto_fix = options['fix']
        
        # Initialize services
        self.monitoring = ThemeMonitoringService()
        self.validator = UICompatibilityValidator()
        
        # Perform health checks
        health_results = {
            'timestamp': time.time(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Database connectivity check
        health_results['checks']['database'] = self._check_database()
        
        # Cache system check
        health_results['checks']['cache'] = self._check_cache_system()
        
        # Theme generation check
        health_results['checks']['theme_generation'] = self._check_theme_generation()
        
        # Performance check
        health_results['checks']['performance'] = self._check_performance()
        
        # Accessibility check
        health_results['checks']['accessibility'] = self._check_accessibility()
        
        # System resources check
        health_results['checks']['resources'] = self._check_system_resources()
        
        # Determine overall status
        failed_checks = [
            name for name, result in health_results['checks'].items()
            if result['status'] != 'healthy'
        ]
        
        if failed_checks:
            if any(health_results['checks'][name]['status'] == 'critical' for name in failed_checks):
                health_results['overall_status'] = 'critical'
            else:
                health_results['overall_status'] = 'warning'
        
        # Auto-fix if requested
        if auto_fix and failed_checks:
            health_results['fixes_applied'] = self._apply_fixes(health_results['checks'])
        
        # Output results
        if json_output:
            self.stdout.write(json.dumps(health_results, indent=2))
        else:
            self._display_health_results(health_results, detailed)
    
    def _check_database(self):
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Check theme table
            theme_count = EventTheme.objects.count()
            cache_count = ThemeCache.objects.count()
            
            response_time = time.time() - start_time
            
            status = 'healthy'
            if response_time > 1.0:
                status = 'warning'
            elif response_time > 5.0:
                status = 'critical'
            
            return {
                'status': status,
                'response_time': response_time,
                'theme_count': theme_count,
                'cache_count': cache_count,
                'message': f"Database responsive in {response_time:.3f}s"
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'Database connection failed'
            }
    
    def _check_cache_system(self):
        """Check cache system functionality."""
        try:
            start_time = time.time()
            
            # Test cache operations
            test_key = 'health_check_test'
            test_value = {'timestamp': time.time()}
            
            # Set and get test
            cache.set(test_key, test_value, 60)
            retrieved = cache.get(test_key)
            cache.delete(test_key)
            
            response_time = time.time() - start_time
            
            if retrieved != test_value:
                return {
                    'status': 'critical',
                    'message': 'Cache set/get operation failed'
                }
            
            status = 'healthy' if response_time < 0.1 else 'warning'
            
            return {
                'status': status,
                'response_time': response_time,
                'message': f"Cache system responsive in {response_time:.3f}s"
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'Cache system failed'
            }
    
    def _check_theme_generation(self):
        """Check theme generation functionality."""
        try:
            # Check recent theme generation success rate
            recent_themes = EventTheme.objects.filter(
                updated_at__gte=time.time() - 86400  # Last 24 hours
            )
            
            total_recent = recent_themes.count()
            successful_recent = recent_themes.filter(generation_status='completed').count()
            
            if total_recent == 0:
                success_rate = 1.0  # No recent activity
            else:
                success_rate = successful_recent / total_recent
            
            status = 'healthy'
            if success_rate < 0.9:
                status = 'warning'
            elif success_rate < 0.7:
                status = 'critical'
            
            return {
                'status': status,
                'success_rate': success_rate,
                'recent_themes': total_recent,
                'successful_themes': successful_recent,
                'message': f"Theme generation success rate: {success_rate:.1%}"
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'Theme generation check failed'
            }
    
    def _display_health_results(self, results, detailed):
        """Display health check results in human-readable format."""
        status_colors = {
            'healthy': self.style.SUCCESS,
            'warning': self.style.WARNING,
            'critical': self.style.ERROR
        }
        
        # Overall status
        color_func = status_colors.get(results['overall_status'], self.style.SUCCESS)
        self.stdout.write(
            color_func(f"Overall System Status: {results['overall_status'].upper()}")
        )
        self.stdout.write("")
        
        # Individual checks
        for check_name, check_result in results['checks'].items():
            status = check_result['status']
            message = check_result.get('message', 'No message')
            
            color_func = status_colors.get(status, self.style.SUCCESS)
            self.stdout.write(f"{check_name.title()}: {color_func(status.upper())} - {message}")
            
            if detailed and 'error' in check_result:
                self.stdout.write(f"  Error: {check_result['error']}")
        
        # Fixes applied
        if 'fixes_applied' in results:
            self.stdout.write("")
            self.stdout.write("Fixes Applied:")
            for fix in results['fixes_applied']:
                self.stdout.write(f"  - {fix}")
    
    def _check_performance(self):
        """Check system performance metrics."""
        try:
            # Get dashboard metrics
            dashboard_metrics = self.monitoring.get_dashboard_metrics()
            overview = dashboard_metrics['overview']
            
            # Check response time
            avg_response = overview['avg_response_time']
            error_rate = overview['error_rate']
            
            status = 'healthy'
            issues = []
            
            if avg_response > 2.0:
                status = 'warning'
                issues.append(f"High response time: {avg_response:.2f}s")
            
            if avg_response > 5.0:
                status = 'critical'
            
            if error_rate > 5.0:
                status = 'warning' if status == 'healthy' else 'critical'
                issues.append(f"High error rate: {error_rate:.1f}%")
            
            return {
                'status': status,
                'avg_response_time': avg_response,
                'error_rate': error_rate,
                'uptime': overview['uptime'],
                'issues': issues,
                'message': f"Performance: {avg_response:.2f}s avg, {error_rate:.1f}% errors"
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'Performance check failed'
            }
    
    def _check_accessibility(self):
        """Check accessibility compliance of recent themes."""
        try:
            # Check recent themes for accessibility compliance
            recent_themes = EventTheme.objects.filter(
                updated_at__gte=time.time() - 86400  # Last 24 hours
            )[:10]  # Check last 10 themes
            
            if not recent_themes:
                return {
                    'status': 'healthy',
                    'message': 'No recent themes to check'
                }
            
            compliant_count = 0
            total_count = len(recent_themes)
            
            for theme in recent_themes:
                if theme.wcag_compliant:
                    compliant_count += 1
            
            compliance_rate = compliant_count / total_count
            
            status = 'healthy'
            if compliance_rate < 0.9:
                status = 'warning'
            elif compliance_rate < 0.7:
                status = 'critical'
            
            return {
                'status': status,
                'compliance_rate': compliance_rate,
                'compliant_themes': compliant_count,
                'total_themes': total_count,
                'message': f"Accessibility compliance: {compliance_rate:.1%}"
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'Accessibility check failed'
            }
    
    def _check_system_resources(self):
        """Check system resource usage."""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = 'healthy'
            issues = []
            
            if cpu_percent > 80:
                status = 'warning'
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if cpu_percent > 95:
                status = 'critical'
            
            if memory.percent > 85:
                status = 'warning' if status == 'healthy' else 'critical'
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 90:
                status = 'warning' if status == 'healthy' else 'critical'
                issues.append(f"High disk usage: {disk.percent:.1f}%")
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'issues': issues,
                'message': f"Resources: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"
            }
            
        except ImportError:
            return {
                'status': 'warning',
                'message': 'psutil not available - cannot check system resources'
            }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'System resource check failed'
            }
    
    def _apply_fixes(self, checks):
        """Apply automatic fixes for detected issues."""
        fixes_applied = []
        
        # Cache system fixes
        if checks.get('cache', {}).get('status') != 'healthy':
            try:
                cache.clear()
                fixes_applied.append("Cleared cache system")
            except Exception as e:
                fixes_applied.append(f"Failed to clear cache: {str(e)}")
        
        # Database fixes
        if checks.get('database', {}).get('status') != 'healthy':
            try:
                # Clean up old cache entries
                old_cache_entries = ThemeCache.objects.filter(
                    created_at__lt=time.time() - 86400 * 7  # Older than 7 days
                )
                deleted_count = old_cache_entries.count()
                old_cache_entries.delete()
                fixes_applied.append(f"Cleaned up {deleted_count} old cache entries")
            except Exception as e:
                fixes_applied.append(f"Failed to clean database: {str(e)}")
        
        # Performance fixes
        if checks.get('performance', {}).get('status') != 'healthy':
            try:
                # Clear performance cache to reset metrics
                cache.delete('theming_metrics')
                cache.delete('theming_performance')
                fixes_applied.append("Reset performance metrics")
            except Exception as e:
                fixes_applied.append(f"Failed to reset performance metrics: {str(e)}")
        
        # Theme generation fixes
        if checks.get('theme_generation', {}).get('status') != 'healthy':
            try:
                # Reset failed theme generations
                failed_themes = EventTheme.objects.filter(
                    generation_status='failed',
                    updated_at__gte=time.time() - 3600  # Last hour
                )
                reset_count = failed_themes.count()
                failed_themes.update(generation_status='pending')
                fixes_applied.append(f"Reset {reset_count} failed theme generations")
            except Exception as e:
                fixes_applied.append(f"Failed to reset theme generations: {str(e)}")
        
        return fixes_applied