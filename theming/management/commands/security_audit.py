"""
Management command to perform security audit of the theming system.

This command validates all existing themes for security compliance,
checks for potential vulnerabilities, and generates security reports.
"""

import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from theming.models import EventTheme, ThemeGenerationLog
from theming.security import (
    security_validator,
    image_processor,
    audit_logger
)


class Command(BaseCommand):
    help = 'Perform security audit of the theming system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--theme-id',
            type=int,
            help='Audit specific theme by ID'
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Automatically fix security issues where possible'
        )
        parser.add_argument(
            '--output-format',
            choices=['json', 'text'],
            default='text',
            help='Output format for the audit report'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Save audit report to file'
        )
    
    def handle(self, *args, **options):
        """Execute the security audit."""
        self.stdout.write(
            self.style.SUCCESS('Starting theming system security audit...')
        )
        
        audit_results = {
            'timestamp': timezone.now().isoformat(),
            'themes_audited': 0,
            'security_issues': [],
            'recommendations': [],
            'summary': {}
        }
        
        try:
            # Get themes to audit
            if options['theme_id']:
                themes = EventTheme.objects.filter(id=options['theme_id'])
                if not themes.exists():
                    raise CommandError(f'Theme with ID {options["theme_id"]} not found')
            else:
                themes = EventTheme.objects.all()
            
            self.stdout.write(f'Auditing {themes.count()} themes...')
            
            # Audit each theme
            for theme in themes:
                theme_audit = self.audit_theme(theme, options['fix_issues'])
                audit_results['themes_audited'] += 1
                
                if theme_audit['issues']:
                    audit_results['security_issues'].extend(theme_audit['issues'])
                
                if theme_audit['recommendations']:
                    audit_results['recommendations'].extend(theme_audit['recommendations'])
            
            # Generate summary
            audit_results['summary'] = self.generate_summary(audit_results)
            
            # Output results
            self.output_results(audit_results, options)
            
            # Log audit completion
            audit_logger.log_security_event(
                'security_audit_completed',
                None,  # System operation
                None,
                themes_audited=audit_results['themes_audited'],
                issues_found=len(audit_results['security_issues']),
                recommendations=len(audit_results['recommendations'])
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Security audit completed. '
                    f'Audited {audit_results["themes_audited"]} themes, '
                    f'found {len(audit_results["security_issues"])} issues.'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Security audit failed: {str(e)}')
            )
            raise CommandError(f'Audit failed: {str(e)}')
    
    def audit_theme(self, theme, fix_issues=False):
        """Audit a single theme for security issues."""
        self.stdout.write(f'Auditing theme {theme.id} for event "{theme.event.title}"...')
        
        audit_result = {
            'theme_id': theme.id,
            'event_title': theme.event.title,
            'issues': [],
            'recommendations': [],
            'fixed_issues': []
        }
        
        # 1. Validate CSS content
        if theme.css_content:
            css_validation = security_validator.validate_css_content(theme.css_content)
            
            if not css_validation['is_valid']:
                for error in css_validation['errors']:
                    audit_result['issues'].append({
                        'type': 'css_security',
                        'severity': 'high',
                        'description': error,
                        'theme_id': theme.id
                    })
                
                if fix_issues and css_validation['sanitized_css']:
                    # Apply sanitized CSS
                    theme.css_content = css_validation['sanitized_css']
                    theme.save()
                    audit_result['fixed_issues'].append('Applied CSS sanitization')
                    
                    # Log the fix
                    ThemeGenerationLog.log_operation(
                        event=theme.event,
                        operation_type='security_fix',
                        status='success',
                        metadata={'action': 'css_sanitized', 'theme_id': theme.id}
                    )
            
            # Check for security warnings
            if css_validation['warnings']:
                for warning in css_validation['warnings']:
                    audit_result['recommendations'].append({
                        'type': 'css_warning',
                        'description': warning,
                        'theme_id': theme.id
                    })
        
        # 2. Validate color values
        colors = {
            'primary_color': theme.primary_color,
            'secondary_color': theme.secondary_color,
            'accent_color': theme.accent_color,
            'neutral_light': theme.neutral_light,
            'neutral_dark': theme.neutral_dark
        }
        
        for color_name, color_value in colors.items():
            if not security_validator.validate_color_value(color_value):
                audit_result['issues'].append({
                    'type': 'invalid_color',
                    'severity': 'medium',
                    'description': f'Invalid color value for {color_name}: {color_value}',
                    'theme_id': theme.id
                })
        
        # 3. Check accessibility compliance
        if not theme.wcag_compliant:
            audit_result['recommendations'].append({
                'type': 'accessibility',
                'description': 'Theme is not WCAG compliant - consider regenerating with accessibility fixes',
                'theme_id': theme.id
            })
        
        # 4. Check generation method
        if theme.generation_method not in ['auto', 'manual', 'secure_api', 'fallback']:
            audit_result['issues'].append({
                'type': 'unknown_generation_method',
                'severity': 'low',
                'description': f'Unknown generation method: {theme.generation_method}',
                'theme_id': theme.id
            })
        
        return audit_result
    
    def generate_summary(self, audit_results):
        """Generate audit summary statistics."""
        issues_by_type = {}
        issues_by_severity = {'high': 0, 'medium': 0, 'low': 0}
        
        for issue in audit_results['security_issues']:
            issue_type = issue['type']
            severity = issue['severity']
            
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
            issues_by_severity[severity] += 1
        
        return {
            'total_issues': len(audit_results['security_issues']),
            'total_recommendations': len(audit_results['recommendations']),
            'issues_by_type': issues_by_type,
            'issues_by_severity': issues_by_severity,
            'themes_with_issues': len(set(issue['theme_id'] for issue in audit_results['security_issues'])),
            'security_score': self.calculate_security_score(audit_results)
        }
    
    def calculate_security_score(self, audit_results):
        """Calculate overall security score (0-100)."""
        if audit_results['themes_audited'] == 0:
            return 100
        
        total_themes = audit_results['themes_audited']
        high_severity_issues = sum(1 for issue in audit_results['security_issues'] if issue['severity'] == 'high')
        medium_severity_issues = sum(1 for issue in audit_results['security_issues'] if issue['severity'] == 'medium')
        low_severity_issues = sum(1 for issue in audit_results['security_issues'] if issue['severity'] == 'low')
        
        # Calculate deductions
        high_deduction = (high_severity_issues / total_themes) * 30
        medium_deduction = (medium_severity_issues / total_themes) * 15
        low_deduction = (low_severity_issues / total_themes) * 5
        
        score = max(0, 100 - high_deduction - medium_deduction - low_deduction)
        return round(score, 2)
    
    def output_results(self, audit_results, options):
        """Output audit results in the specified format."""
        if options['output_format'] == 'json':
            output = json.dumps(audit_results, indent=2, default=str)
        else:
            output = self.format_text_output(audit_results)
        
        if options['output_file']:
            with open(options['output_file'], 'w') as f:
                f.write(output)
            self.stdout.write(f'Audit report saved to {options["output_file"]}')
        else:
            self.stdout.write(output)
    
    def format_text_output(self, audit_results):
        """Format audit results as human-readable text."""
        output = []
        output.append('=' * 60)
        output.append('THEMING SYSTEM SECURITY AUDIT REPORT')
        output.append('=' * 60)
        output.append(f'Audit Date: {audit_results["timestamp"]}')
        output.append(f'Themes Audited: {audit_results["themes_audited"]}')
        output.append('')
        
        # Summary
        summary = audit_results['summary']
        output.append('SUMMARY')
        output.append('-' * 20)
        output.append(f'Security Score: {summary["security_score"]}/100')
        output.append(f'Total Issues: {summary["total_issues"]}')
        output.append(f'Total Recommendations: {summary["total_recommendations"]}')
        output.append(f'Themes with Issues: {summary["themes_with_issues"]}')
        output.append('')
        
        # Issues by severity
        if summary['issues_by_severity']:
            output.append('ISSUES BY SEVERITY')
            output.append('-' * 20)
            for severity, count in summary['issues_by_severity'].items():
                if count > 0:
                    output.append(f'{severity.upper()}: {count}')
            output.append('')
        
        # Issues by type
        if summary['issues_by_type']:
            output.append('ISSUES BY TYPE')
            output.append('-' * 20)
            for issue_type, count in summary['issues_by_type'].items():
                output.append(f'{issue_type}: {count}')
            output.append('')
        
        # Detailed issues
        if audit_results['security_issues']:
            output.append('DETAILED ISSUES')
            output.append('-' * 20)
            for issue in audit_results['security_issues']:
                output.append(f'[{issue["severity"].upper()}] Theme {issue["theme_id"]}: {issue["description"]}')
            output.append('')
        
        # Recommendations
        if audit_results['recommendations']:
            output.append('RECOMMENDATIONS')
            output.append('-' * 20)
            for rec in audit_results['recommendations']:
                output.append(f'Theme {rec["theme_id"]}: {rec["description"]}')
            output.append('')
        
        output.append('=' * 60)
        return '\n'.join(output)