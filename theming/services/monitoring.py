"""
Monitoring and Logging Service

Provides comprehensive logging, performance monitoring, error tracking,
and quality monitoring dashboards for the theming system.
"""

import time
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
import threading


@dataclass
class ThemeMetrics:
    """Theme generation metrics."""
    generation_time: float
    color_extraction_time: float
    css_generation_time: float
    cache_hit_ratio: float
    error_count: int
    success_rate: float


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics."""
    avg_response_time: float
    peak_response_time: float
    throughput: float  # requests per second
    memory_usage: float
    cpu_usage: float


@dataclass
class QualityMetrics:
    """Theme quality metrics."""
    accessibility_score: float
    color_harmony_score: float
    contrast_compliance: float
    browser_compatibility: float
    user_satisfaction: float


class ThemeMonitoringService:
    """
    Comprehensive monitoring service for the theming system.
    
    Tracks performance, quality, errors, and provides analytics
    for system optimization and quality assurance.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('theming.monitoring')
        self.metrics_cache_key = 'theming_metrics'
        self.performance_cache_key = 'theming_performance'
        self.quality_cache_key = 'theming_quality'
        
        # Thread-safe counters
        self._lock = threading.Lock()
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0
    
    def log_theme_generation(self, event_id: int, metrics: ThemeMetrics, 
                           success: bool, error_message: Optional[str] = None):
        """Log theme generation event with detailed metrics."""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_id': event_id,
            'success': success,
            'metrics': asdict(metrics),
            'error_message': error_message
        }
        
        if success:
            self.logger.info(f"Theme generated successfully for event {event_id}", extra=log_data)
        else:
            self.logger.error(f"Theme generation failed for event {event_id}: {error_message}", extra=log_data)
        
        # Update cached metrics
        self._update_cached_metrics(metrics, success)
    
    def track_performance(self, operation: str, duration: float, 
                         memory_usage: Optional[float] = None):
        """Track performance metrics for operations."""
        with self._lock:
            self._request_count += 1
            self._total_response_time += duration
        
        performance_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration': duration,
            'memory_usage': memory_usage
        }
        
        self.logger.debug(f"Performance: {operation} took {duration:.3f}s", extra=performance_data)
        
        # Update performance cache
        self._update_performance_cache(operation, duration, memory_usage)
    
    def track_quality_metrics(self, event_id: int, quality: QualityMetrics):
        """Track theme quality metrics."""
        quality_data = {
            'timestamp': datetime.now().isoformat(),
            'event_id': event_id,
            'quality_metrics': asdict(quality)
        }
        
        self.logger.info(f"Quality metrics for event {event_id}", extra=quality_data)
        
        # Update quality cache
        self._update_quality_cache(quality)
    
    def log_error(self, error_type: str, error_message: str, 
                 context: Optional[Dict[str, Any]] = None):
        """Log system errors with context."""
        with self._lock:
            self._error_count += 1
        
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {}
        }
        
        self.logger.error(f"System error: {error_type} - {error_message}", extra=error_data)
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics for monitoring dashboard."""
        # Get cached metrics
        theme_metrics = cache.get(self.metrics_cache_key, {})
        performance_metrics = cache.get(self.performance_cache_key, {})
        quality_metrics = cache.get(self.quality_cache_key, {})
        
        # Calculate current rates
        with self._lock:
            current_error_rate = (self._error_count / max(self._request_count, 1)) * 100
            avg_response_time = self._total_response_time / max(self._request_count, 1)
        
        return {
            'overview': {
                'total_requests': self._request_count,
                'total_errors': self._error_count,
                'error_rate': current_error_rate,
                'avg_response_time': avg_response_time,
                'uptime': self._calculate_uptime()
            },
            'theme_metrics': theme_metrics,
            'performance_metrics': performance_metrics,
            'quality_metrics': quality_metrics,
            'alerts': self._check_alerts()
        }
    
    def _update_cached_metrics(self, metrics: ThemeMetrics, success: bool):
        """Update cached theme metrics."""
        cached_metrics = cache.get(self.metrics_cache_key, {
            'total_generations': 0,
            'successful_generations': 0,
            'avg_generation_time': 0.0,
            'avg_extraction_time': 0.0,
            'avg_css_time': 0.0,
            'cache_hit_ratio': 0.0
        })
        
        # Update counters
        cached_metrics['total_generations'] += 1
        if success:
            cached_metrics['successful_generations'] += 1
        
        # Update averages
        total = cached_metrics['total_generations']
        cached_metrics['avg_generation_time'] = (
            (cached_metrics['avg_generation_time'] * (total - 1) + metrics.generation_time) / total
        )
        cached_metrics['avg_extraction_time'] = (
            (cached_metrics['avg_extraction_time'] * (total - 1) + metrics.color_extraction_time) / total
        )
        cached_metrics['avg_css_time'] = (
            (cached_metrics['avg_css_time'] * (total - 1) + metrics.css_generation_time) / total
        )
        cached_metrics['cache_hit_ratio'] = (
            (cached_metrics['cache_hit_ratio'] * (total - 1) + metrics.cache_hit_ratio) / total
        )
        
        cache.set(self.metrics_cache_key, cached_metrics, 3600)  # 1 hour
    
    def _update_performance_cache(self, operation: str, duration: float, memory_usage: Optional[float]):
        """Update cached performance metrics."""
        perf_key = f"{self.performance_cache_key}_{operation}"
        cached_perf = cache.get(perf_key, {
            'count': 0,
            'total_duration': 0.0,
            'max_duration': 0.0,
            'avg_memory': 0.0
        })
        
        cached_perf['count'] += 1
        cached_perf['total_duration'] += duration
        cached_perf['max_duration'] = max(cached_perf['max_duration'], duration)
        
        if memory_usage:
            cached_perf['avg_memory'] = (
                (cached_perf['avg_memory'] * (cached_perf['count'] - 1) + memory_usage) / cached_perf['count']
            )
        
        cache.set(perf_key, cached_perf, 3600)
    
    def _check_alerts(self) -> List[Dict[str, Any]]:
        """Check for system alerts based on thresholds."""
        alerts = []
        
        # Check error rate
        with self._lock:
            error_rate = (self._error_count / max(self._request_count, 1)) * 100
            avg_response = self._total_response_time / max(self._request_count, 1)
        
        if error_rate > 5.0:  # 5% error rate threshold
            alerts.append({
                'type': 'error_rate',
                'severity': 'high' if error_rate > 10 else 'medium',
                'message': f"High error rate: {error_rate:.1f}%",
                'value': error_rate
            })
        
        if avg_response > 2.0:  # 2 second response time threshold
            alerts.append({
                'type': 'response_time',
                'severity': 'high' if avg_response > 5 else 'medium',
                'message': f"Slow response time: {avg_response:.2f}s",
                'value': avg_response
            })
        
    def _update_quality_cache(self, quality: QualityMetrics):
        """Update cached quality metrics."""
        cached_quality = cache.get(self.quality_cache_key, {
            'count': 0,
            'avg_accessibility': 0.0,
            'avg_harmony': 0.0,
            'avg_contrast': 0.0,
            'avg_compatibility': 0.0,
            'avg_satisfaction': 0.0
        })
        
        cached_quality['count'] += 1
        count = cached_quality['count']
        
        cached_quality['avg_accessibility'] = (
            (cached_quality['avg_accessibility'] * (count - 1) + quality.accessibility_score) / count
        )
        cached_quality['avg_harmony'] = (
            (cached_quality['avg_harmony'] * (count - 1) + quality.color_harmony_score) / count
        )
        cached_quality['avg_contrast'] = (
            (cached_quality['avg_contrast'] * (count - 1) + quality.contrast_compliance) / count
        )
        cached_quality['avg_compatibility'] = (
            (cached_quality['avg_compatibility'] * (count - 1) + quality.browser_compatibility) / count
        )
        cached_quality['avg_satisfaction'] = (
            (cached_quality['avg_satisfaction'] * (count - 1) + quality.user_satisfaction) / count
        )
        
        cache.set(self.quality_cache_key, cached_quality, 3600)
    
    def _calculate_uptime(self) -> float:
        """Calculate system uptime percentage."""
        # Simple uptime calculation based on error rate
        with self._lock:
            if self._request_count == 0:
                return 100.0
            return max(0.0, 100.0 - (self._error_count / self._request_count * 100))
    
    def create_performance_alert(self, threshold_type: str, current_value: float, threshold: float):
        """Create performance threshold alert."""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'performance_threshold',
            'threshold_type': threshold_type,
            'current_value': current_value,
            'threshold': threshold,
            'severity': 'high' if current_value > threshold * 2 else 'medium'
        }
        
        self.logger.warning(
            f"Performance threshold exceeded: {threshold_type} = {current_value} (threshold: {threshold})",
            extra=alert_data
        )
        
        # Store alert in cache for dashboard
        alerts_key = 'theming_alerts'
        alerts = cache.get(alerts_key, [])
        alerts.append(alert_data)
        
        # Keep only last 100 alerts
        if len(alerts) > 100:
            alerts = alerts[-100:]
        
        cache.set(alerts_key, alerts, 86400)  # 24 hours
    
    def monitor_cache_hit_ratio(self, cache_hits: int, total_requests: int):
        """Monitor cache performance and alert on low hit ratios."""
        if total_requests > 0:
            hit_ratio = cache_hits / total_requests
            if hit_ratio < 0.7:  # 70% threshold
                self.create_performance_alert('cache_hit_ratio', hit_ratio, 0.7)
    
    def monitor_user_experience(self, response_times: List[float]):
        """Monitor user experience metrics."""
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            p95_response = sorted(response_times)[int(len(response_times) * 0.95)]
            
            if avg_response > 2.0:  # 2 second threshold
                self.create_performance_alert('avg_response_time', avg_response, 2.0)
            
            if p95_response > 5.0:  # 5 second threshold for 95th percentile
                self.create_performance_alert('p95_response_time', p95_response, 5.0)
    
    def get_system_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score."""
        dashboard_metrics = self.get_dashboard_metrics()
        
        # Calculate health score based on various factors
        health_factors = {
            'error_rate': min(100, max(0, 100 - dashboard_metrics['overview']['error_rate'] * 10)),
            'response_time': min(100, max(0, 100 - dashboard_metrics['overview']['avg_response_time'] * 20)),
            'uptime': dashboard_metrics['overview']['uptime'],
            'cache_performance': 100  # Default if no cache metrics
        }
        
        # Add cache performance if available
        theme_metrics = dashboard_metrics.get('theme_metrics', {})
        if 'cache_hit_ratio' in theme_metrics:
            health_factors['cache_performance'] = theme_metrics['cache_hit_ratio'] * 100
        
        # Calculate weighted average
        weights = {'error_rate': 0.3, 'response_time': 0.3, 'uptime': 0.25, 'cache_performance': 0.15}
        overall_score = sum(health_factors[factor] * weights[factor] for factor in health_factors)
        
        return {
            'overall_score': overall_score,
            'factors': health_factors,
            'status': 'healthy' if overall_score >= 80 else 'warning' if overall_score >= 60 else 'critical'
        }