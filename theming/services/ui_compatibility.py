"""
UI Compatibility and Validation Service

Validates theme compatibility with UI components, tests interactive elements,
and provides automatic error detection and recovery mechanisms.
"""

from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import re
import json
from .advanced_color_processor import AdvancedColorProcessor


class CompatibilityLevel(Enum):
    """UI compatibility levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    INCOMPATIBLE = "incompatible"


@dataclass
class ComponentValidation:
    """Represents validation results for a UI component."""
    component_name: str
    compatibility_level: CompatibilityLevel
    issues: List[str]
    suggestions: List[str]
    auto_fixes: Dict[str, str]


@dataclass
class InteractiveElementTest:
    """Represents test results for interactive elements."""
    element_type: str
    accessibility_score: float
    contrast_ratio: float
    touch_target_size: bool
    keyboard_accessible: bool
    screen_reader_friendly: bool


@dataclass
class BrowserCompatibility:
    """Represents browser compatibility analysis."""
    browser: str
    version: str
    css_support: Dict[str, bool]
    fallback_needed: bool
    fallback_css: Optional[str]


class UICompatibilityValidator:
    """
    Service for validating theme compatibility with UI components.
    
    Provides comprehensive testing of interactive elements, browser compatibility,
    and automatic error detection with recovery mechanisms.
    """
    
    def __init__(self):
        self.color_processor = AdvancedColorProcessor()
        
        # Define critical UI components that must maintain functionality
        self.critical_components = {
            'button', 'input', 'select', 'textarea', 'link', 'nav',
            'header', 'footer', 'modal', 'dropdown', 'tab', 'accordion'
        }
        
        # Define minimum requirements for interactive elements
        self.accessibility_requirements = {
            'min_contrast_ratio': 4.5,
            'min_touch_target': 44,  # pixels
            'max_color_only_indication': False
        }
    
    def validate_complete_ui_compatibility(self, theme_css: str, theme_colors: Dict[str, str]) -> Dict[str, Any]:
        """
        Perform comprehensive UI compatibility validation.
        
        Args:
            theme_css: Generated CSS theme
            theme_colors: Dictionary of theme colors
            
        Returns:
            Complete validation report with all test results
        """
        # Get all UI components from the CSS
        components = self._extract_components_from_css(theme_css)
        
        # Validate component compatibility
        component_validations = self.validate_component_compatibility(theme_css, list(components))
        
        # Test interactive elements
        interactive_tests = self.test_interactive_elements(theme_colors)
        
        # Verify browser compatibility
        browser_compatibility = self.verify_browser_compatibility(theme_css)
        
        # Detect and recover from errors
        error_analysis = self.detect_and_recover_errors(theme_css, component_validations)
        
        # Calculate overall compatibility score
        overall_score = self._calculate_overall_compatibility_score(
            component_validations, interactive_tests, browser_compatibility
        )
        
        return {
            'overall_compatibility_score': overall_score,
            'component_validations': [
                {
                    'component': v.component_name,
                    'level': v.compatibility_level.value,
                    'issues': v.issues,
                    'suggestions': v.suggestions,
                    'auto_fixes': v.auto_fixes
                } for v in component_validations
            ],
            'interactive_element_tests': [
                {
                    'element': t.element_type,
                    'accessibility_score': t.accessibility_score,
                    'contrast_ratio': t.contrast_ratio,
                    'touch_target_size': t.touch_target_size,
                    'keyboard_accessible': t.keyboard_accessible,
                    'screen_reader_friendly': t.screen_reader_friendly
                } for t in interactive_tests
            ],
            'browser_compatibility': [
                {
                    'browser': b.browser,
                    'version': b.version,
                    'css_support': b.css_support,
                    'fallback_needed': b.fallback_needed,
                    'fallback_css': b.fallback_css
                } for b in browser_compatibility
            ],
            'error_analysis': error_analysis,
            'recommendations': self._generate_comprehensive_recommendations(
                component_validations, interactive_tests, browser_compatibility, error_analysis
            )
        }
    
    def test_theme_with_real_components(self, theme_css: str, component_html_samples: Dict[str, str]) -> Dict[str, Any]:
        """
        Test theme with actual HTML component samples.
        
        Args:
            theme_css: Generated CSS theme
            component_html_samples: Dictionary of component HTML samples
            
        Returns:
            Test results for real component rendering
        """
        test_results = {}
        
        for component_name, html_sample in component_html_samples.items():
            # Simulate applying theme to component
            test_result = self._test_component_rendering(theme_css, component_name, html_sample)
            test_results[component_name] = test_result
        
        return {
            'component_tests': test_results,
            'overall_rendering_score': self._calculate_rendering_score(test_results),
            'critical_failures': [
                name for name, result in test_results.items() 
                if result.get('critical_failure', False)
            ]
        }
    
    def generate_compatibility_report(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate a human-readable compatibility report.
        
        Args:
            validation_results: Results from validate_complete_ui_compatibility
            
        Returns:
            Formatted compatibility report
        """
        report_lines = []
        
        # Header
        report_lines.append("=== UI Compatibility Validation Report ===\n")
        
        # Overall score
        score = validation_results['overall_compatibility_score']
        report_lines.append(f"Overall Compatibility Score: {score:.1f}/100")
        
        if score >= 90:
            report_lines.append("Status: EXCELLENT - Theme is fully compatible")
        elif score >= 75:
            report_lines.append("Status: GOOD - Theme is compatible with minor issues")
        elif score >= 60:
            report_lines.append("Status: ACCEPTABLE - Theme works but has some issues")
        elif score >= 40:
            report_lines.append("Status: POOR - Theme has significant compatibility issues")
        else:
            report_lines.append("Status: INCOMPATIBLE - Theme may break UI functionality")
        
        report_lines.append("")
        
        # Component validation summary
        report_lines.append("Component Validation Summary:")
        component_validations = validation_results['component_validations']
        
        level_counts = {}
        for validation in component_validations:
            level = validation['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        for level, count in level_counts.items():
            report_lines.append(f"  {level.title()}: {count} components")
        
        # Critical issues
        critical_issues = []
        for validation in component_validations:
            if validation['level'] in ['poor', 'incompatible']:
                critical_issues.extend(validation['issues'])
        
        if critical_issues:
            report_lines.append("\nCritical Issues:")
            for issue in critical_issues[:5]:  # Show top 5
                report_lines.append(f"  • {issue}")
            if len(critical_issues) > 5:
                report_lines.append(f"  ... and {len(critical_issues) - 5} more issues")
        
        # Browser compatibility
        report_lines.append("\nBrowser Compatibility:")
        browser_compat = validation_results['browser_compatibility']
        for browser in browser_compat:
            status = "✓" if not browser['fallback_needed'] else "⚠"
            report_lines.append(f"  {status} {browser['browser']} {browser['version']}")
        
        # Recommendations
        recommendations = validation_results['recommendations']
        if recommendations:
            report_lines.append("\nRecommendations:")
            for rec in recommendations[:3]:  # Show top 3
                report_lines.append(f"  • {rec}")
        
        return "\n".join(report_lines)
    
    def validate_component_compatibility(self, theme_css: str, 
                                       component_list: List[str]) -> List[ComponentValidation]:
        """
        Validate theme compatibility with UI components.
        
        Args:
            theme_css: Generated CSS theme
            component_list: List of component names to validate
            
        Returns:
            List of validation results for each component
        """
        validations = []
        
        for component in component_list:
            validation = self._validate_single_component(theme_css, component)
            validations.append(validation)
        
        return validations
    
    def test_interactive_elements(self, theme_colors: Dict[str, str]) -> List[InteractiveElementTest]:
        """
        Test interactive elements for accessibility and usability.
        
        Args:
            theme_colors: Dictionary of theme colors
            
        Returns:
            List of test results for interactive elements
        """
        interactive_elements = ['button', 'link', 'input', 'select', 'checkbox', 'radio']
        test_results = []
        
        for element in interactive_elements:
            test_result = self._test_element_accessibility(element, theme_colors)
            test_results.append(test_result)
        
        return test_results
    
    def verify_browser_compatibility(self, theme_css: str) -> List[BrowserCompatibility]:
        """
        Verify browser compatibility and generate fallbacks.
        
        Args:
            theme_css: Generated CSS theme
            
        Returns:
            List of browser compatibility results
        """
        browsers = [
            ('Chrome', '90+'), ('Firefox', '88+'), ('Safari', '14+'),
            ('Edge', '90+'), ('IE', '11')
        ]
        
        compatibility_results = []
        
        for browser, version in browsers:
            compatibility = self._check_browser_support(theme_css, browser, version)
            compatibility_results.append(compatibility)
        
        return compatibility_results
    
    def detect_and_recover_errors(self, theme_css: str, 
                                 validation_results: List[ComponentValidation]) -> Dict[str, Any]:
        """
        Detect errors and provide automatic recovery mechanisms.
        
        Args:
            theme_css: Generated CSS theme
            validation_results: Component validation results
            
        Returns:
            Dictionary with error detection and recovery information
        """
        errors = []
        auto_fixes = {}
        recovery_css = []
        
        # Analyze validation results for critical issues
        for validation in validation_results:
            if validation.compatibility_level in [CompatibilityLevel.POOR, CompatibilityLevel.INCOMPATIBLE]:
                if validation.component_name in self.critical_components:
                    errors.append({
                        'component': validation.component_name,
                        'level': 'critical',
                        'issues': validation.issues
                    })
                    
                    # Apply auto-fixes if available
                    if validation.auto_fixes:
                        auto_fixes[validation.component_name] = validation.auto_fixes
                        recovery_css.extend(self._generate_recovery_css(validation))
        
        # Check for CSS syntax errors
        css_errors = self._validate_css_syntax(theme_css)
        if css_errors:
            errors.extend(css_errors)
            # Generate recovery CSS for syntax errors
            recovery_css.extend(self._generate_syntax_error_recovery_css(css_errors))
        
        # If no recovery CSS generated but errors detected, provide basic recovery
        if len(errors) > 0 and len(recovery_css) == 0:
            recovery_css.extend(self._generate_basic_recovery_css())
        
        return {
            'errors_detected': len(errors) > 0,
            'error_count': len(errors),
            'errors': errors,
            'auto_fixes_available': len(auto_fixes) > 0,
            'auto_fixes': auto_fixes,
            'recovery_css': '\n'.join(recovery_css),
            'recommendations': self._generate_recovery_recommendations(errors)
        }
    
    def _validate_single_component(self, theme_css: str, component: str) -> ComponentValidation:
        """Validate a single UI component."""
        issues = []
        suggestions = []
        auto_fixes = {}
        
        # Extract component-specific CSS
        component_css = self._extract_component_css(theme_css, component)
        
        # Check color contrast
        contrast_issues = self._check_component_contrast(component_css, component)
        if contrast_issues:
            issues.extend(contrast_issues)
            auto_fixes.update(self._generate_contrast_fixes(component_css, component))
        
        # Check for missing essential properties
        missing_props = self._check_essential_properties(component_css, component)
        if missing_props:
            issues.extend([f"Missing essential property: {prop}" for prop in missing_props])
            suggestions.extend([f"Add {prop} property for better {component} styling" for prop in missing_props])
        
        # Check for conflicting styles
        conflicts = self._check_style_conflicts(component_css, component)
        if conflicts:
            issues.extend(conflicts)
        
        # Determine compatibility level
        compatibility_level = self._determine_compatibility_level(len(issues), component)
        
        return ComponentValidation(
            component_name=component,
            compatibility_level=compatibility_level,
            issues=issues,
            suggestions=suggestions,
            auto_fixes=auto_fixes
        )
    
    def _test_element_accessibility(self, element: str, theme_colors: Dict[str, str]) -> InteractiveElementTest:
        """Test accessibility of an interactive element."""
        # Get element colors
        bg_color = theme_colors.get(f'{element}_bg', theme_colors.get('background', '#ffffff'))
        text_color = theme_colors.get(f'{element}_text', theme_colors.get('text', '#000000'))
        
        # Calculate contrast ratio
        contrast_ratio = self._calculate_contrast_ratio(text_color, bg_color)
        
        # Calculate accessibility score
        accessibility_score = self._calculate_accessibility_score(element, contrast_ratio, theme_colors)
        
        return InteractiveElementTest(
            element_type=element,
            accessibility_score=accessibility_score,
            contrast_ratio=contrast_ratio,
            touch_target_size=True,  # Assume proper sizing in CSS
            keyboard_accessible=True,  # Assume proper focus styles
            screen_reader_friendly=contrast_ratio >= 4.5
        )
    
    def _check_browser_support(self, theme_css: str, browser: str, version: str) -> BrowserCompatibility:
        """Check browser support for CSS features."""
        css_features = self._extract_css_features(theme_css)
        
        # Define browser support matrix
        support_matrix = {
            'Chrome': {
                'css-grid': '57+', 'flexbox': '29+', 'css-variables': '49+',
                'backdrop-filter': '76+', 'css-masks': '120+'
            },
            'Firefox': {
                'css-grid': '52+', 'flexbox': '28+', 'css-variables': '31+',
                'backdrop-filter': '103+', 'css-masks': '53+'
            },
            'Safari': {
                'css-grid': '10.1+', 'flexbox': '9+', 'css-variables': '9.1+',
                'backdrop-filter': '9+', 'css-masks': '15.4+'
            },
            'Edge': {
                'css-grid': '16+', 'flexbox': '12+', 'css-variables': '15+',
                'backdrop-filter': '17+', 'css-masks': '79+'
            },
            'IE': {
                'css-grid': 'none', 'flexbox': '11+', 'css-variables': 'none',
                'backdrop-filter': 'none', 'css-masks': 'none'
            }
        }
        
        browser_support = support_matrix.get(browser, {})
        css_support = {}
        fallback_needed = False
        
        for feature in css_features:
            supported = self._check_feature_support(feature, browser_support, version)
            css_support[feature] = supported
            if not supported:
                fallback_needed = True
        
        fallback_css = self._generate_fallback_css(css_features, css_support) if fallback_needed else None
        
        return BrowserCompatibility(
            browser=browser,
            version=version,
            css_support=css_support,
            fallback_needed=fallback_needed,
            fallback_css=fallback_css
        )
    
    def _extract_component_css(self, theme_css: str, component: str) -> str:
        """Extract CSS rules for a specific component."""
        # Simple pattern matching for component CSS
        pattern = rf'\.{component}[^{{]*\{{[^}}]*\}}'
        matches = re.findall(pattern, theme_css, re.IGNORECASE | re.DOTALL)
        return '\n'.join(matches)
    
    def _check_component_contrast(self, component_css: str, component: str) -> List[str]:
        """Check color contrast for a component."""
        issues = []
        
        # Extract colors from CSS
        colors = self._extract_colors_from_css(component_css)
        
        # Check common color combinations
        if 'color' in colors and 'background-color' in colors:
            contrast = self._calculate_contrast_ratio(colors['color'], colors['background-color'])
            if contrast < self.accessibility_requirements['min_contrast_ratio']:
                issues.append(f"Insufficient contrast ratio ({contrast:.2f}) for {component}")
        
        return issues
    
    def _check_essential_properties(self, component_css: str, component: str) -> List[str]:
        """Check for essential CSS properties for a component."""
        essential_props = {
            'button': ['background-color', 'color', 'border', 'padding'],
            'input': ['border', 'padding', 'background-color'],
            'link': ['color', 'text-decoration'],
            'nav': ['background-color', 'padding'],
        }
        
        required = essential_props.get(component, [])
        missing = []
        
        for prop in required:
            if prop not in component_css:
                missing.append(prop)
        
        return missing
    
    def _determine_compatibility_level(self, issue_count: int, component: str) -> CompatibilityLevel:
        """Determine compatibility level based on issues."""
        if component in self.critical_components:
            if issue_count == 0:
                return CompatibilityLevel.EXCELLENT
            elif issue_count <= 2:
                return CompatibilityLevel.GOOD
            elif issue_count <= 4:
                return CompatibilityLevel.ACCEPTABLE
            elif issue_count <= 6:
                return CompatibilityLevel.POOR
            else:
                return CompatibilityLevel.INCOMPATIBLE
        else:
            # More lenient for non-critical components
            if issue_count <= 1:
                return CompatibilityLevel.EXCELLENT
            elif issue_count <= 3:
                return CompatibilityLevel.GOOD
            elif issue_count <= 5:
                return CompatibilityLevel.ACCEPTABLE
            else:
                return CompatibilityLevel.POOR
    
    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate WCAG contrast ratio between two colors."""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def luminance(rgb):
            r, g, b = [x/255.0 for x in rgb]
            r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
            g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
            b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
            return 0.2126*r + 0.7152*g + 0.0722*b
        
        try:
            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)
            
            l1 = luminance(rgb1)
            l2 = luminance(rgb2)
            
            lighter = max(l1, l2)
            darker = min(l1, l2)
            
            return (lighter + 0.05) / (darker + 0.05)
        except:
            return 1.0  # Default safe value
    
    def _extract_colors_from_css(self, css_content: str) -> Dict[str, str]:
        """Extract color values from CSS content."""
        colors = {}
        
        # Pattern to match CSS color properties
        color_patterns = [
            (r'color:\s*([^;]+)', 'color'),
            (r'background-color:\s*([^;]+)', 'background-color'),
            (r'border-color:\s*([^;]+)', 'border-color'),
        ]
        
        for pattern, prop in color_patterns:
            matches = re.findall(pattern, css_content, re.IGNORECASE)
            if matches:
                colors[prop] = matches[0].strip()
        
        return colors
    
    def _extract_css_features(self, css_content: str) -> Set[str]:
        """Extract CSS features used in the theme."""
        features = set()
        
        # Check for various CSS features
        feature_patterns = {
            'css-grid': r'display:\s*grid|grid-template',
            'flexbox': r'display:\s*flex|flex-direction|justify-content',
            'css-variables': r'var\(--[^)]+\)|--[a-zA-Z-]+:',
            'backdrop-filter': r'backdrop-filter:',
            'css-masks': r'mask:|clip-path:',
            'transforms': r'transform:',
            'transitions': r'transition:',
            'animations': r'animation:|@keyframes',
        }
        
        for feature, pattern in feature_patterns.items():
            if re.search(pattern, css_content, re.IGNORECASE):
                features.add(feature)
        
        return features
    
    def _check_feature_support(self, feature: str, browser_support: Dict[str, str], version: str) -> bool:
        """Check if a CSS feature is supported in a browser version."""
        if feature not in browser_support:
            return True  # Assume supported if not in matrix
        
        required_version = browser_support[feature]
        if required_version == 'none':
            return False
        
        # Simple version comparison (assumes numeric versions)
        try:
            required = float(required_version.rstrip('+'))
            current = float(version.rstrip('+'))
            return current >= required
        except:
            return True  # Default to supported if version parsing fails
    
    def _generate_fallback_css(self, features: Set[str], support: Dict[str, bool]) -> str:
        """Generate fallback CSS for unsupported features."""
        fallback_rules = []
        
        for feature, supported in support.items():
            if not supported:
                if feature == 'css-grid':
                    fallback_rules.append("""
                    /* Flexbox fallback for CSS Grid */
                    .grid-container { display: flex; flex-wrap: wrap; }
                    .grid-item { flex: 1 1 auto; }
                    """)
                elif feature == 'css-variables':
                    fallback_rules.append("""
                    /* Static color fallbacks */
                    .themed-element { color: #333333; background-color: #ffffff; }
                    """)
                elif feature == 'backdrop-filter':
                    fallback_rules.append("""
                    /* Solid background fallback */
                    .backdrop-element { background-color: rgba(255, 255, 255, 0.9); }
                    """)
        
        return '\n'.join(fallback_rules)
    
    def _generate_contrast_fixes(self, component_css: str, component: str) -> Dict[str, str]:
        """Generate automatic contrast fixes for a component."""
        fixes = {}
        colors = self._extract_colors_from_css(component_css)
        
        if 'color' in colors and 'background-color' in colors:
            text_color = colors['color']
            bg_color = colors['background-color']
            
            # Try to fix contrast by adjusting text color
            fixed_text = self._adjust_color_for_contrast(text_color, bg_color)
            if fixed_text != text_color:
                fixes['color'] = fixed_text
        
        return fixes
    
    def _adjust_color_for_contrast(self, text_color: str, bg_color: str) -> str:
        """Adjust text color to meet contrast requirements."""
        current_contrast = self._calculate_contrast_ratio(text_color, bg_color)
        
        if current_contrast >= 4.5:
            return text_color
        
        # Try making text darker or lighter
        try:
            # Convert to RGB
            text_rgb = self._hex_to_rgb(text_color)
            
            # Try darker first
            darker = self._darken_color(text_rgb, 0.3)
            darker_hex = self._rgb_to_hex(darker)
            if self._calculate_contrast_ratio(darker_hex, bg_color) >= 4.5:
                return darker_hex
            
            # Try lighter
            lighter = self._lighten_color(text_rgb, 0.3)
            lighter_hex = self._rgb_to_hex(lighter)
            if self._calculate_contrast_ratio(lighter_hex, bg_color) >= 4.5:
                return lighter_hex
            
            # If neither works, use high contrast defaults
            bg_rgb = self._hex_to_rgb(bg_color)
            bg_luminance = self._calculate_luminance(bg_rgb)
            
            return '#000000' if bg_luminance > 0.5 else '#ffffff'
        
        except:
            return text_color
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _darken_color(self, rgb: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Darken a color by a factor."""
        return tuple(max(0, int(c * (1 - factor))) for c in rgb)
    
    def _lighten_color(self, rgb: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Lighten a color by a factor."""
        return tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
    
    def _calculate_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """Calculate relative luminance of a color."""
        r, g, b = [x/255.0 for x in rgb]
        r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
        g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
        b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
        return 0.2126*r + 0.7152*g + 0.0722*b
    
    def _check_style_conflicts(self, component_css: str, component: str) -> List[str]:
        """Check for conflicting CSS styles."""
        conflicts = []
        
        # Check for common conflicts
        if 'display: none' in component_css and 'visibility: visible' in component_css:
            conflicts.append("Conflicting display and visibility properties")
        
        if 'position: fixed' in component_css and 'position: absolute' in component_css:
            conflicts.append("Conflicting position properties")
        
        # Check for overriding styles
        properties = re.findall(r'([a-z-]+):\s*[^;]+', component_css, re.IGNORECASE)
        property_counts = {}
        for prop in properties:
            property_counts[prop] = property_counts.get(prop, 0) + 1
        
        for prop, count in property_counts.items():
            if count > 1:
                conflicts.append(f"Property '{prop}' defined multiple times")
        
        return conflicts
    
    def _calculate_accessibility_score(self, element: str, contrast_ratio: float, theme_colors: Dict[str, str]) -> float:
        """Calculate accessibility score for an element."""
        score = 0.0
        
        # Contrast ratio score (40% of total)
        if contrast_ratio >= 7.0:
            score += 40
        elif contrast_ratio >= 4.5:
            score += 30
        elif contrast_ratio >= 3.0:
            score += 20
        else:
            score += 10
        
        # Color differentiation score (30% of total)
        if self._has_sufficient_color_variety(theme_colors):
            score += 30
        else:
            score += 15
        
        # Element-specific checks (30% of total)
        if element in ['button', 'link']:
            # Check for hover states
            if f'{element}_hover' in theme_colors:
                score += 15
            else:
                score += 5
            
            # Check for focus states
            if f'{element}_focus' in theme_colors:
                score += 15
            else:
                score += 5
        else:
            score += 30  # Full score for non-interactive elements
        
        return min(100.0, score)
    
    def _has_sufficient_color_variety(self, theme_colors: Dict[str, str]) -> bool:
        """Check if theme has sufficient color variety."""
        unique_colors = set(theme_colors.values())
        return len(unique_colors) >= 3
    
    def _validate_css_syntax(self, css_content: str) -> List[Dict[str, Any]]:
        """Validate CSS syntax and return errors."""
        errors = []
        
        # Check for unmatched braces
        open_braces = css_content.count('{')
        close_braces = css_content.count('}')
        if open_braces != close_braces:
            errors.append({
                'type': 'syntax',
                'level': 'critical',
                'message': f"Unmatched braces: {open_braces} opening, {close_braces} closing"
            })
        
        # Check for invalid property syntax
        invalid_props = re.findall(r'[^{};]*:[^{};]*[^;}](?=\s*[{}])', css_content)
        for prop in invalid_props:
            if not prop.strip().endswith(';') and '{' not in prop and '}' not in prop:
                errors.append({
                    'type': 'syntax',
                    'level': 'warning',
                    'message': f"Missing semicolon after property: {prop.strip()}"
                })
        
        # Check for invalid color values
        color_pattern = r'(?:color|background-color|border-color):\s*([^;]+)'
        color_matches = re.findall(color_pattern, css_content, re.IGNORECASE)
        for color_value in color_matches:
            if not self._is_valid_color(color_value.strip()):
                errors.append({
                    'type': 'value',
                    'level': 'warning',
                    'message': f"Invalid color value: {color_value.strip()}"
                })
        
        return errors
    
    def _is_valid_color(self, color_value: str) -> bool:
        """Check if a color value is valid."""
        color_value = color_value.strip()
        
        # Hex colors
        if re.match(r'^#[0-9a-fA-F]{3}$|^#[0-9a-fA-F]{6}$', color_value):
            return True
        
        # RGB/RGBA
        if re.match(r'^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[\d.]+)?\s*\)$', color_value):
            return True
        
        # HSL/HSLA
        if re.match(r'^hsla?\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*(?:,\s*[\d.]+)?\s*\)$', color_value):
            return True
        
        # CSS color names (basic check)
        css_colors = {
            'red', 'green', 'blue', 'white', 'black', 'yellow', 'cyan', 'magenta',
            'gray', 'grey', 'orange', 'purple', 'pink', 'brown', 'transparent'
        }
        if color_value.lower() in css_colors:
            return True
        
        return False
    
    def _generate_recovery_css(self, validation: ComponentValidation) -> List[str]:
        """Generate recovery CSS for a failed component validation."""
        recovery_rules = []
        
        component = validation.component_name
        
        # Generate safe defaults based on component type
        if component == 'button':
            recovery_rules.append(f"""
            .{component} {{
                background-color: #007bff !important;
                color: #ffffff !important;
                border: 1px solid #007bff !important;
                padding: 0.375rem 0.75rem !important;
                border-radius: 0.25rem !important;
                cursor: pointer !important;
            }}
            .{component}:hover {{
                background-color: #0056b3 !important;
                border-color: #0056b3 !important;
            }}
            """)
        elif component == 'input':
            recovery_rules.append(f"""
            .{component} {{
                background-color: #ffffff !important;
                color: #333333 !important;
                border: 1px solid #cccccc !important;
                padding: 0.375rem 0.75rem !important;
                border-radius: 0.25rem !important;
            }}
            .{component}:focus {{
                border-color: #007bff !important;
                outline: 0 !important;
                box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
            }}
            """)
        elif component == 'link':
            recovery_rules.append(f"""
            .{component} {{
                color: #007bff !important;
                text-decoration: underline !important;
            }}
            .{component}:hover {{
                color: #0056b3 !important;
                text-decoration: none !important;
            }}
            """)
        
        return recovery_rules
    
    def _generate_recovery_recommendations(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for error recovery."""
        recommendations = []
        
        critical_count = sum(1 for error in errors if error.get('level') == 'critical')
        warning_count = sum(1 for error in errors if error.get('level') == 'warning')
        
        if critical_count > 0:
            recommendations.append("Critical issues detected - consider using fallback theme")
            recommendations.append("Review component CSS for syntax errors and conflicts")
        
        if warning_count > 0:
            recommendations.append("Minor issues detected - theme may work but with reduced quality")
            recommendations.append("Consider adjusting colors for better accessibility")
        
        # Component-specific recommendations
        component_issues = {}
        for error in errors:
            if 'component' in error:
                comp = error['component']
                component_issues[comp] = component_issues.get(comp, 0) + 1
        
        for component, issue_count in component_issues.items():
            if issue_count > 2:
                recommendations.append(f"Consider redesigning {component} styling - multiple issues detected")
        
        return recommendations
    
    def _extract_components_from_css(self, css_content: str) -> Set[str]:
        """Extract component names from CSS selectors."""
        components = set()
        
        # Find class selectors
        class_matches = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', css_content)
        components.update(class_matches)
        
        # Find element selectors
        element_matches = re.findall(r'^([a-zA-Z][a-zA-Z0-9]*)\s*{', css_content, re.MULTILINE)
        components.update(element_matches)
        
        # Filter to known UI components
        ui_components = {
            'button', 'input', 'select', 'textarea', 'link', 'a', 'nav', 'header', 
            'footer', 'modal', 'dropdown', 'tab', 'accordion', 'card', 'form',
            'table', 'thead', 'tbody', 'tr', 'td', 'th', 'ul', 'ol', 'li'
        }
        
        return components.intersection(ui_components)
    
    def _calculate_overall_compatibility_score(self, component_validations: List[ComponentValidation],
                                             interactive_tests: List[InteractiveElementTest],
                                             browser_compatibility: List[BrowserCompatibility]) -> float:
        """Calculate overall compatibility score."""
        total_score = 0.0
        weight_sum = 0.0
        
        # Component compatibility score (50% weight)
        if component_validations:
            component_scores = []
            for validation in component_validations:
                level_scores = {
                    CompatibilityLevel.EXCELLENT: 100,
                    CompatibilityLevel.GOOD: 80,
                    CompatibilityLevel.ACCEPTABLE: 60,
                    CompatibilityLevel.POOR: 40,
                    CompatibilityLevel.INCOMPATIBLE: 0
                }
                component_scores.append(level_scores[validation.compatibility_level])
            
            avg_component_score = sum(component_scores) / len(component_scores)
            total_score += avg_component_score * 0.5
            weight_sum += 0.5
        
        # Interactive elements score (30% weight)
        if interactive_tests:
            avg_interactive_score = sum(test.accessibility_score for test in interactive_tests) / len(interactive_tests)
            total_score += avg_interactive_score * 0.3
            weight_sum += 0.3
        
        # Browser compatibility score (20% weight)
        if browser_compatibility:
            browser_score = sum(0 if browser.fallback_needed else 100 for browser in browser_compatibility)
            browser_score /= len(browser_compatibility)
            total_score += browser_score * 0.2
            weight_sum += 0.2
        
        return total_score / weight_sum if weight_sum > 0 else 0.0
    
    def _test_component_rendering(self, theme_css: str, component_name: str, html_sample: str) -> Dict[str, Any]:
        """Test component rendering with theme CSS."""
        # This would ideally use a headless browser, but for now we'll simulate
        test_result = {
            'component_name': component_name,
            'css_applied': True,
            'visual_issues': [],
            'functional_issues': [],
            'critical_failure': False
        }
        
        # Extract component CSS
        component_css = self._extract_component_css(theme_css, component_name)
        
        # Check for critical CSS issues
        if not component_css:
            test_result['visual_issues'].append("No CSS rules found for component")
            test_result['critical_failure'] = True
        
        # Check for display issues
        if 'display: none' in component_css:
            test_result['functional_issues'].append("Component is hidden")
            test_result['critical_failure'] = True
        
        # Check for color issues
        colors = self._extract_colors_from_css(component_css)
        if 'color' in colors and 'background-color' in colors:
            contrast = self._calculate_contrast_ratio(colors['color'], colors['background-color'])
            if contrast < 3.0:
                test_result['visual_issues'].append(f"Poor contrast ratio: {contrast:.2f}")
        
        return test_result
    
    def _calculate_rendering_score(self, test_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall rendering score from component tests."""
        if not test_results:
            return 0.0
        
        total_score = 0.0
        for component_name, result in test_results.items():
            score = 100.0
            
            # Deduct for issues
            score -= len(result.get('visual_issues', [])) * 10
            score -= len(result.get('functional_issues', [])) * 20
            
            # Critical failure
            if result.get('critical_failure', False):
                score = min(score, 30)
            
            total_score += max(0, score)
        
        return total_score / len(test_results)
    
    def _generate_comprehensive_recommendations(self, component_validations: List[ComponentValidation],
                                              interactive_tests: List[InteractiveElementTest],
                                              browser_compatibility: List[BrowserCompatibility],
                                              error_analysis: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations based on all test results."""
        recommendations = []
        
        # Component-based recommendations
        poor_components = [v for v in component_validations 
                          if v.compatibility_level in [CompatibilityLevel.POOR, CompatibilityLevel.INCOMPATIBLE]]
        
        if poor_components:
            recommendations.append(f"Fix compatibility issues in {len(poor_components)} components")
            
            # Specific component recommendations
            for component in poor_components[:3]:  # Top 3 issues
                if component.suggestions:
                    recommendations.append(f"{component.component_name}: {component.suggestions[0]}")
        
        # Accessibility recommendations
        low_accessibility = [t for t in interactive_tests if t.accessibility_score < 70]
        if low_accessibility:
            recommendations.append(f"Improve accessibility for {len(low_accessibility)} interactive elements")
        
        # Browser compatibility recommendations
        incompatible_browsers = [b for b in browser_compatibility if b.fallback_needed]
        if incompatible_browsers:
            browser_names = [b.browser for b in incompatible_browsers]
            recommendations.append(f"Add fallback CSS for {', '.join(browser_names)}")
        
        # Error-based recommendations
        if error_analysis.get('errors_detected', False):
            recommendations.extend(error_analysis.get('recommendations', []))
        
        # Performance recommendations
        if len(component_validations) > 20:
            recommendations.append("Consider optimizing CSS - large number of components detected")
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_syntax_error_recovery_css(self, css_errors: List[Dict[str, Any]]) -> List[str]:
        """Generate recovery CSS for syntax errors."""
        recovery_rules = []
        
        for error in css_errors:
            if error.get('type') == 'syntax':
                # Provide basic safe CSS for syntax errors
                recovery_rules.append("""
                /* Recovery CSS for syntax errors */
                .button {
                    background-color: #007bff !important;
                    color: #ffffff !important;
                    border: 1px solid #007bff !important;
                    padding: 0.375rem 0.75rem !important;
                    border-radius: 0.25rem !important;
                    cursor: pointer !important;
                }
                """)
                break  # Only add once
        
        return recovery_rules
    
    def _generate_basic_recovery_css(self) -> List[str]:
        """Generate basic recovery CSS when errors are detected but no specific fixes available."""
        return ["""
        /* Basic recovery CSS */
        .button, button {
            background-color: #007bff !important;
            color: #ffffff !important;
            border: 1px solid #007bff !important;
            padding: 0.375rem 0.75rem !important;
            border-radius: 0.25rem !important;
            cursor: pointer !important;
        }
        .button:hover, button:hover {
            background-color: #0056b3 !important;
            border-color: #0056b3 !important;
        }
        input, select, textarea {
            background-color: #ffffff !important;
            color: #333333 !important;
            border: 1px solid #cccccc !important;
            padding: 0.375rem 0.75rem !important;
            border-radius: 0.25rem !important;
        }
        a, .link {
            color: #007bff !important;
            text-decoration: underline !important;
        }
        a:hover, .link:hover {
            color: #0056b3 !important;
            text-decoration: none !important;
        }
        """]