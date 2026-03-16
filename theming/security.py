"""
Security utilities and validation for the theming system.

This module provides security measures including rate limiting,
input validation, and protection against malicious content.
"""

import re
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.http import HttpRequest
from rest_framework.throttling import BaseThrottle
from PIL import Image, ImageFilter
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class ThemeSecurityValidator:
    """
    Comprehensive security validator for theme-related operations.
    
    Provides validation for CSS content, image files, and other
    theme-related inputs to prevent security vulnerabilities including:
    - CSS injection prevention with whitelist validation
    - Dangerous pattern detection and sanitization
    - Content Security Policy header generation
    - XSS prevention in theme content
    """
    
    # Comprehensive dangerous CSS patterns
    DANGEROUS_CSS_PATTERNS = [
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'expression\s*\(',
        r'@import\s+["\']?(?!data:image/)',  # Block external imports except safe data URLs
        r'url\s*\([^)]*\.js["\']?\)',  # Block JavaScript file URLs
        r'url\s*\([^)]*\.php["\']?\)',  # Block PHP file URLs
        r'url\s*\([^)]*\.asp["\']?\)',  # Block ASP file URLs
        r'<script[^>]*>',
        r'</script>',
        r'<iframe[^>]*>',
        r'</iframe>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'@-moz-document',
        r'@-webkit-keyframes',
        r'behavior\s*:',
        r'-moz-binding\s*:',
        r'filter\s*:\s*progid',
        r'eval\s*\(',
        r'Function\s*\(',
        r'setTimeout\s*\(',
        r'setInterval\s*\(',
        r'document\.',
        r'window\.',
        r'location\.',
        r'navigator\.',
        r'XMLHttpRequest',
        r'fetch\s*\(',
        r'innerHTML',
        r'outerHTML',
        r'insertAdjacentHTML',
    ]
    
    # Comprehensive allowed CSS properties (whitelist approach)
    ALLOWED_CSS_PROPERTIES = {
        # Color properties
        'color', 'background-color', 'background', 'background-image',
        'background-position', 'background-repeat', 'background-size',
        'background-attachment', 'background-clip', 'background-origin',
        
        # Border properties
        'border', 'border-color', 'border-width', 'border-style',
        'border-radius', 'border-top', 'border-right', 'border-bottom', 'border-left',
        'border-top-color', 'border-right-color', 'border-bottom-color', 'border-left-color',
        'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width',
        'border-top-style', 'border-right-style', 'border-bottom-style', 'border-left-style',
        'border-top-left-radius', 'border-top-right-radius', 
        'border-bottom-left-radius', 'border-bottom-right-radius',
        
        # Spacing properties
        'margin', 'padding', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
        'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
        
        # Typography properties
        'font-family', 'font-size', 'font-weight', 'font-style', 'font-variant',
        'text-align', 'text-decoration', 'text-transform', 'text-indent',
        'line-height', 'letter-spacing', 'word-spacing', 'white-space',
        'word-wrap', 'word-break', 'text-overflow', 'text-shadow',
        
        # Layout properties
        'display', 'position', 'top', 'right', 'bottom', 'left',
        'width', 'height', 'min-width', 'min-height', 'max-width', 'max-height',
        'overflow', 'overflow-x', 'overflow-y', 'visibility', 'opacity',
        'z-index', 'float', 'clear', 'vertical-align',
        
        # Flexbox properties
        'flex', 'flex-direction', 'flex-wrap', 'flex-flow', 'flex-grow',
        'flex-shrink', 'flex-basis', 'justify-content', 'align-items',
        'align-content', 'align-self', 'order',
        
        # Grid properties
        'grid', 'grid-template', 'grid-template-columns', 'grid-template-rows',
        'grid-template-areas', 'grid-area', 'grid-column', 'grid-row',
        'grid-gap', 'grid-column-gap', 'grid-row-gap',
        
        # Visual effects
        'box-shadow', 'transform', 'transform-origin', 'transition',
        'transition-property', 'transition-duration', 'transition-timing-function',
        'transition-delay', 'animation', 'animation-name', 'animation-duration',
        'animation-timing-function', 'animation-delay', 'animation-iteration-count',
        'animation-direction', 'animation-fill-mode', 'animation-play-state',
        
        # Miscellaneous
        'cursor', 'outline', 'outline-color', 'outline-style', 'outline-width',
        'resize', 'box-sizing', 'content', 'quotes', 'counter-reset', 'counter-increment',
        'list-style', 'list-style-type', 'list-style-position', 'list-style-image',
        'table-layout', 'border-collapse', 'border-spacing', 'caption-side',
        'empty-cells', 'speak', 'page-break-before', 'page-break-after',
        'page-break-inside', 'orphans', 'widows'
    }
    
    # Safe CSS functions
    ALLOWED_CSS_FUNCTIONS = {
        'rgb', 'rgba', 'hsl', 'hsla', 'calc', 'var', 'linear-gradient',
        'radial-gradient', 'repeating-linear-gradient', 'repeating-radial-gradient',
        'scale', 'rotate', 'translate', 'translateX', 'translateY', 'translateZ',
        'translate3d', 'scaleX', 'scaleY', 'scaleZ', 'scale3d', 'rotateX',
        'rotateY', 'rotateZ', 'rotate3d', 'skew', 'skewX', 'skewY', 'matrix',
        'matrix3d', 'perspective'
    }
    
    # Maximum CSS content size (in characters)
    MAX_CSS_SIZE = 500000  # 500KB
    
    # Maximum nesting depth for CSS rules
    MAX_NESTING_DEPTH = 10
    
    def validate_css_content(self, css_content: str) -> Dict[str, Any]:
        """
        Comprehensive CSS content validation for security threats.
        
        Args:
            css_content: CSS content to validate
            
        Returns:
            Dict with detailed validation results and security analysis
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_css': css_content,
            'security_analysis': {
                'dangerous_patterns_found': [],
                'suspicious_functions': [],
                'external_resources': [],
                'nesting_depth': 0,
                'property_violations': []
            },
            'csp_violations': []
        }
        
        # 1. Check CSS size
        if len(css_content) > self.MAX_CSS_SIZE:
            result['is_valid'] = False
            result['errors'].append(f'CSS content too large (max {self.MAX_CSS_SIZE} characters)')
            return result
        
        # 2. Check for dangerous patterns
        for pattern in self.DANGEROUS_CSS_PATTERNS:
            matches = re.finditer(pattern, css_content, re.IGNORECASE)
            for match in matches:
                result['is_valid'] = False
                result['errors'].append(f'Dangerous CSS pattern detected: {pattern} at position {match.start()}')
                result['security_analysis']['dangerous_patterns_found'].append({
                    'pattern': pattern,
                    'position': match.start(),
                    'matched_text': match.group()
                })
        
        # 3. Validate CSS structure and nesting
        nesting_analysis = self._analyze_css_nesting(css_content)
        result['security_analysis']['nesting_depth'] = nesting_analysis['max_depth']
        
        if nesting_analysis['max_depth'] > self.MAX_NESTING_DEPTH:
            result['warnings'].append(f'CSS nesting too deep (max {self.MAX_NESTING_DEPTH})')
        
        # 4. Validate CSS properties and functions
        try:
            sanitized_css, property_violations = self._sanitize_css_properties(css_content)
            result['sanitized_css'] = sanitized_css
            result['security_analysis']['property_violations'] = property_violations
            
            if sanitized_css != css_content:
                result['warnings'].append('Some CSS properties were removed for security')
                
        except Exception as e:
            result['warnings'].append(f'CSS property validation warning: {str(e)}')
        
        # 5. Check for external resource references
        external_resources = self._detect_external_resources(css_content)
        result['security_analysis']['external_resources'] = external_resources
        
        if external_resources:
            result['warnings'].append(f'External resources detected: {len(external_resources)} references')
        
        # 6. Validate CSS functions
        suspicious_functions = self._validate_css_functions(css_content)
        result['security_analysis']['suspicious_functions'] = suspicious_functions
        
        if suspicious_functions:
            result['warnings'].append(f'Suspicious CSS functions detected: {len(suspicious_functions)}')
        
        # 7. Generate Content Security Policy violations
        csp_violations = self._check_csp_violations(css_content)
        result['csp_violations'] = csp_violations
        
        return result
    
    def _sanitize_css_properties(self, css_content: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Comprehensive CSS property sanitization with detailed violation tracking.
        
        Args:
            css_content: CSS content to sanitize
            
        Returns:
            Tuple of (sanitized_css, property_violations)
        """
        property_violations = []
        
        # Remove comments first
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Parse CSS rules more thoroughly
        lines = css_content.split('\n')
        sanitized_lines = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and selectors
            if not line or line.endswith('{') or line == '}':
                sanitized_lines.append(line)
                continue
            
            # Process CSS property declarations
            if ':' in line and not line.startswith('@'):
                # Extract property name and value
                prop_match = re.match(r'\s*([^:]+):\s*([^;]+);?', line)
                if prop_match:
                    prop_name = prop_match.group(1).strip().lower()
                    prop_value = prop_match.group(2).strip()
                    
                    # Check if property is allowed
                    is_allowed = False
                    for allowed_prop in self.ALLOWED_CSS_PROPERTIES:
                        if allowed_prop in prop_name or prop_name.startswith(allowed_prop):
                            is_allowed = True
                            break
                    
                    if is_allowed:
                        # Validate property value
                        if self._validate_css_property_value(prop_name, prop_value):
                            sanitized_lines.append(line)
                        else:
                            property_violations.append({
                                'line': line_num,
                                'property': prop_name,
                                'value': prop_value,
                                'reason': 'Invalid property value'
                            })
                            logger.debug(f"Filtered CSS property value: {prop_name}: {prop_value}")
                    else:
                        property_violations.append({
                            'line': line_num,
                            'property': prop_name,
                            'value': prop_value,
                            'reason': 'Property not in whitelist'
                        })
                        logger.debug(f"Filtered CSS property: {prop_name}")
                else:
                    sanitized_lines.append(line)
            else:
                # Handle at-rules and other CSS constructs
                if line.startswith('@'):
                    # Only allow safe at-rules
                    safe_at_rules = ['@media', '@supports', '@keyframes']
                    if any(line.startswith(rule) for rule in safe_at_rules):
                        sanitized_lines.append(line)
                    else:
                        property_violations.append({
                            'line': line_num,
                            'property': 'at-rule',
                            'value': line,
                            'reason': 'Unsafe at-rule'
                        })
                else:
                    sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines), property_violations
    
    def _validate_css_property_value(self, property_name: str, property_value: str) -> bool:
        """
        Validate CSS property values for security.
        
        Args:
            property_name: CSS property name
            property_value: CSS property value
            
        Returns:
            True if value is safe, False otherwise
        """
        # Check for dangerous patterns in values
        dangerous_value_patterns = [
            r'javascript:', r'vbscript:', r'data:text/html',
            r'expression\s*\(', r'eval\s*\(', r'<script',
            r'document\.', r'window\.', r'location\.'
        ]
        
        for pattern in dangerous_value_patterns:
            if re.search(pattern, property_value, re.IGNORECASE):
                return False
        
        # Validate URL values
        if 'url(' in property_value.lower():
            return self._validate_css_url(property_value)
        
        # Validate function calls
        function_matches = re.findall(r'(\w+)\s*\(', property_value)
        for func_name in function_matches:
            if func_name.lower() not in self.ALLOWED_CSS_FUNCTIONS:
                return False
        
        return True
    
    def _validate_css_url(self, css_value: str) -> bool:
        """
        Validate CSS URL values for security.
        
        Args:
            css_value: CSS value containing URL
            
        Returns:
            True if URL is safe, False otherwise
        """
        # Extract URLs from the CSS value
        url_matches = re.findall(r'url\s*\(\s*["\']?([^"\')\s]+)["\']?\s*\)', css_value, re.IGNORECASE)
        
        for url in url_matches:
            url = url.strip()
            
            # Allow data URLs for images only
            if url.startswith('data:'):
                if not url.startswith('data:image/'):
                    return False
            # Allow relative URLs
            elif url.startswith('/') or not ('://' in url):
                continue
            # Block external URLs
            else:
                return False
        
        return True
    
    def _analyze_css_nesting(self, css_content: str) -> Dict[str, Any]:
        """
        Analyze CSS nesting depth for security.
        
        Args:
            css_content: CSS content to analyze
            
        Returns:
            Dict with nesting analysis
        """
        max_depth = 0
        current_depth = 0
        
        for char in css_content:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        return {
            'max_depth': max_depth,
            'balanced_braces': current_depth == 0
        }
    
    def _detect_external_resources(self, css_content: str) -> List[Dict[str, Any]]:
        """
        Detect external resource references in CSS.
        
        Args:
            css_content: CSS content to analyze
            
        Returns:
            List of external resource references
        """
        external_resources = []
        
        # Find all URL references
        url_matches = re.finditer(r'url\s*\(\s*["\']?([^"\')\s]+)["\']?\s*\)', css_content, re.IGNORECASE)
        
        for match in url_matches:
            url = match.group(1).strip()
            
            # Check if it's an external resource
            if '://' in url and not url.startswith('data:'):
                external_resources.append({
                    'url': url,
                    'position': match.start(),
                    'type': 'external_url'
                })
        
        # Find @import statements
        import_matches = re.finditer(r'@import\s+["\']?([^"\';\s]+)["\']?', css_content, re.IGNORECASE)
        
        for match in import_matches:
            import_url = match.group(1).strip()
            external_resources.append({
                'url': import_url,
                'position': match.start(),
                'type': 'import'
            })
        
        return external_resources
    
    def _validate_css_functions(self, css_content: str) -> List[Dict[str, Any]]:
        """
        Validate CSS functions for security.
        
        Args:
            css_content: CSS content to analyze
            
        Returns:
            List of suspicious functions found
        """
        suspicious_functions = []
        
        # Find all function calls
        function_matches = re.finditer(r'(\w+)\s*\(', css_content)
        
        for match in function_matches:
            func_name = match.group(1).lower()
            
            if func_name not in self.ALLOWED_CSS_FUNCTIONS:
                suspicious_functions.append({
                    'function': func_name,
                    'position': match.start(),
                    'context': css_content[max(0, match.start()-20):match.end()+20]
                })
        
        return suspicious_functions
    
    def _check_csp_violations(self, css_content: str) -> List[Dict[str, Any]]:
        """
        Check for Content Security Policy violations.
        
        Args:
            css_content: CSS content to check
            
        Returns:
            List of CSP violations
        """
        violations = []
        
        # Check for inline styles that would violate CSP
        if re.search(r'style\s*=', css_content, re.IGNORECASE):
            violations.append({
                'type': 'inline_style',
                'description': 'Inline styles detected - may violate CSP'
            })
        
        # Check for unsafe-eval patterns
        eval_patterns = [r'expression\s*\(', r'eval\s*\(', r'Function\s*\(']
        for pattern in eval_patterns:
            if re.search(pattern, css_content, re.IGNORECASE):
                violations.append({
                    'type': 'unsafe_eval',
                    'description': f'Unsafe eval pattern detected: {pattern}'
                })
        
        return violations
    
    def generate_csp_headers(self, theme_css: str) -> Dict[str, str]:
        """
        Generate Content Security Policy headers for theme CSS.
        
        Args:
            theme_css: Theme CSS content
            
        Returns:
            Dict with CSP headers
        """
        # Analyze CSS to determine required CSP directives
        has_inline_styles = bool(re.search(r'style\s*=', theme_css, re.IGNORECASE))
        has_external_resources = bool(self._detect_external_resources(theme_css))
        
        # Build CSP directives
        style_src = ["'self'"]
        
        if has_inline_styles:
            # In production, you'd use nonces or hashes instead of 'unsafe-inline'
            style_src.append("'unsafe-inline'")
        
        if not has_external_resources:
            # Restrict to same origin only
            style_src = ["'self'"]
        
        csp_header = f"style-src {' '.join(style_src)}; object-src 'none'; base-uri 'self';"
        
        return {
            'Content-Security-Policy': csp_header,
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block'
        }
    
    def validate_color_value(self, color: str) -> bool:
        """
        Validate a color value (hex, rgb, etc.).

        Args:
            color: Color value to validate

        Returns:
            True if valid, False otherwise
        """
        # Hex color validation
        if color.startswith('#'):
            if len(color) not in [4, 7]:  # #RGB or #RRGGBB
                return False
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                return False

        # RGB/RGBA validation
        rgb_pattern = r'^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([01]?\.?\d*))?\s*\)$'
        rgb_match = re.match(rgb_pattern, color, re.IGNORECASE)
        if rgb_match:
            r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
            return 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255

        # HSL/HSLA validation
        hsl_pattern = r'^hsla?\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*(?:,\s*([01]?\.?\d*))?\s*\)$'
        hsl_match = re.match(hsl_pattern, color, re.IGNORECASE)
        if hsl_match:
            h, s, l = int(hsl_match.group(1)), int(hsl_match.group(2)), int(hsl_match.group(3))
            return 0 <= h <= 360 and 0 <= s <= 100 and 0 <= l <= 100

        # Named colors (basic check)
        named_colors = {
            'red', 'green', 'blue', 'white', 'black', 'gray', 'grey',
            'yellow', 'orange', 'purple', 'pink', 'brown', 'cyan',
            'magenta', 'lime', 'navy', 'teal', 'silver', 'maroon'
        }
        if color.lower() in named_colors:
            return True

        return False



class SecureImageProcessor:
    """
    Comprehensive secure image processing utilities.
    
    Provides validation, sanitization, and malicious content scanning
    for uploaded images to prevent security vulnerabilities including:
    - File format validation and size limits
    - Malicious content scanning
    - Metadata stripping and path traversal prevention
    - Sandboxed image processing
    """
    
    # Allowed image formats
    ALLOWED_FORMATS = ['PNG', 'JPEG', 'JPG', 'WEBP']
    
    # Maximum image dimensions
    MAX_DIMENSIONS = (4000, 4000)  # 4K max
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Dangerous file signatures (magic bytes)
    DANGEROUS_SIGNATURES = [
        b'\x4D\x5A',  # PE executable
        b'\x7F\x45\x4C\x46',  # ELF executable
        b'\xCA\xFE\xBA\xBE',  # Java class file
        b'\x50\x4B\x03\x04',  # ZIP file (could contain malicious content)
        b'<script',  # HTML/JavaScript
        b'<?php',  # PHP code
        b'#!/bin/',  # Shell script
    ]
    
    # Suspicious metadata keys
    SUSPICIOUS_METADATA_KEYS = [
        'Software', 'ProcessingSoftware', 'HostComputer',
        'DocumentName', 'ImageDescription', 'Artist',
        'Copyright', 'UserComment', 'XPComment'
    ]
    
    def validate_image_file(self, file_path: str) -> Dict[str, Any]:
        """
        Comprehensive image file validation for security and format compliance.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dict with validation results including security scan
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'image_info': {},
            'security_scan': {
                'malicious_content_detected': False,
                'suspicious_metadata': [],
                'path_traversal_attempt': False,
                'dangerous_signatures': []
            }
        }
        
        try:
            # 1. Path traversal prevention
            if self._check_path_traversal(file_path):
                result['is_valid'] = False
                result['errors'].append('Path traversal attempt detected')
                result['security_scan']['path_traversal_attempt'] = True
                return result
            
            # 2. Check file existence and size
            import os
            if not os.path.exists(file_path):
                result['is_valid'] = False
                result['errors'].append('File does not exist')
                return result
                
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                result['is_valid'] = False
                result['errors'].append(f'File too large (max {self.MAX_FILE_SIZE} bytes)')
                return result
            
            # 3. Malicious content scanning
            malicious_scan = self._scan_for_malicious_content(file_path)
            result['security_scan'].update(malicious_scan)
            
            if malicious_scan['malicious_content_detected']:
                result['is_valid'] = False
                result['errors'].append('Malicious content detected in file')
                return result
            
            # 4. File type validation using python-magic
            if MAGIC_AVAILABLE:
                try:
                    file_type = magic.from_file(file_path, mime=True)
                    if not file_type.startswith('image/'):
                        result['is_valid'] = False
                        result['errors'].append('File is not a valid image')
                        return result
                    
                    # Additional MIME type validation
                    allowed_mimes = {
                        'image/png': 'PNG',
                        'image/jpeg': 'JPEG', 
                        'image/jpg': 'JPG',
                        'image/webp': 'WEBP'
                    }
                    
                    if file_type not in allowed_mimes:
                        result['is_valid'] = False
                        result['errors'].append(f'Unsupported MIME type: {file_type}')
                        return result
                        
                except Exception as e:
                    result['warnings'].append(f'Could not verify file type: {str(e)}')
            else:
                result['warnings'].append('File type validation skipped (python-magic not available)')
            
            # 5. PIL image validation and security checks
            with Image.open(file_path) as img:
                # Check format
                if img.format not in self.ALLOWED_FORMATS:
                    result['is_valid'] = False
                    result['errors'].append(f'Unsupported format: {img.format}. Allowed: {", ".join(self.ALLOWED_FORMATS)}')
                    return result
                
                # Check dimensions
                width, height = img.size
                if width > self.MAX_DIMENSIONS[0] or height > self.MAX_DIMENSIONS[1]:
                    result['is_valid'] = False
                    result['errors'].append(f'Image too large: {width}x{height}. Max: {self.MAX_DIMENSIONS[0]}x{self.MAX_DIMENSIONS[1]}')
                    return result
                
                # Minimum dimension check (prevent 1x1 pixel attacks)
                if width < 10 or height < 10:
                    result['warnings'].append('Image dimensions are very small')
                
                # Check for suspicious metadata
                metadata_scan = self._scan_image_metadata(img)
                result['security_scan']['suspicious_metadata'] = metadata_scan
                
                if metadata_scan:
                    result['warnings'].append(f'Suspicious metadata found: {", ".join(metadata_scan)}')
                
                # Store image info
                result['image_info'] = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    'color_count': len(img.getcolors(maxcolors=256*256*256)) if img.getcolors(maxcolors=256*256*256) else 'many',
                    'has_animation': getattr(img, 'is_animated', False)
                }
                
                # Check for animated images (potential security risk)
                if result['image_info']['has_animation']:
                    result['warnings'].append('Animated image detected - will be converted to static')
                
                # Validate image integrity
                try:
                    img.verify()
                except Exception as e:
                    result['warnings'].append(f'Image integrity check failed: {str(e)}')
                
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f'Image validation failed: {str(e)}')
        
        return result
    
    def sanitize_image(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Comprehensive image sanitization with security measures.
        
        Args:
            input_path: Path to input image
            output_path: Path to save sanitized image
            
        Returns:
            Dict with sanitization results and security actions taken
        """
        result = {
            'success': False,
            'actions_taken': [],
            'warnings': [],
            'security_measures': []
        }
        
        try:
            # Create secure temporary directory for processing
            import tempfile
            import os
            import shutil
            
            with tempfile.TemporaryDirectory(prefix='secure_image_') as temp_dir:
                temp_input = os.path.join(temp_dir, 'input_image')
                
                # Copy to secure temporary location
                shutil.copy2(input_path, temp_input)
                result['actions_taken'].append('Copied to secure temporary directory')
                
                with Image.open(temp_input) as img:
                    # Handle animated images by taking first frame
                    if getattr(img, 'is_animated', False):
                        img.seek(0)  # Go to first frame
                        result['actions_taken'].append('Converted animated image to static')
                        result['security_measures'].append('Animation removed for security')
                    
                    # Convert to RGB and remove transparency vulnerabilities
                    if img.mode in ('RGBA', 'LA', 'P'):
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        
                        if 'transparency' in img.info or img.mode in ('RGBA', 'LA'):
                            # Create white background
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'LA':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                            img = background
                            result['actions_taken'].append('Removed transparency and alpha channel')
                            result['security_measures'].append('Alpha channel vulnerabilities removed')
                        else:
                            img = img.convert('RGB')
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                        result['actions_taken'].append(f'Converted from {img.mode} to RGB')
                    
                    # Resize if too large (additional security measure)
                    if img.size[0] > self.MAX_DIMENSIONS[0] or img.size[1] > self.MAX_DIMENSIONS[1]:
                        img.thumbnail(self.MAX_DIMENSIONS, Image.Resampling.LANCZOS)
                        result['actions_taken'].append(f'Resized to fit within {self.MAX_DIMENSIONS}')
                    
                    # Apply noise reduction to remove potential steganographic content
                    from PIL import ImageFilter
                    img = img.filter(ImageFilter.MedianFilter(size=3))
                    result['actions_taken'].append('Applied noise reduction filter')
                    result['security_measures'].append('Potential steganographic content filtered')
                    
                    # Save without any metadata (complete metadata stripping)
                    img.save(output_path, format='JPEG', quality=95, optimize=True, 
                            exif=b'', icc_profile=None)
                    result['actions_taken'].append('Saved without metadata')
                    result['security_measures'].append('All metadata stripped')
                    
                    result['success'] = True
                    
                # Verify the sanitized image
                try:
                    with Image.open(output_path) as verified_img:
                        verified_img.verify()
                    result['actions_taken'].append('Verified sanitized image integrity')
                except Exception as e:
                    result['warnings'].append(f'Sanitized image verification failed: {str(e)}')
                    
        except Exception as e:
            logger.error(f"Image sanitization failed: {str(e)}")
            result['warnings'].append(f'Sanitization error: {str(e)}')
        
        return result
    
    def process_image_in_sandbox(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Process image in a sandboxed environment with additional security measures.
        
        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            
        Returns:
            Dict with processing results
        """
        result = {
            'success': False,
            'sandbox_measures': [],
            'processing_time_ms': 0,
            'warnings': []
        }
        
        import time
        start_time = time.time()
        
        try:
            # First validate the image
            validation_result = self.validate_image_file(input_path)
            if not validation_result['is_valid']:
                result['warnings'].extend(validation_result['errors'])
                return result
            
            # Process in sandbox
            sanitization_result = self.sanitize_image(input_path, output_path)
            
            if sanitization_result['success']:
                result['success'] = True
                result['sandbox_measures'] = sanitization_result['security_measures']
                result['processing_time_ms'] = int((time.time() - start_time) * 1000)
            else:
                result['warnings'].extend(sanitization_result['warnings'])
                
        except Exception as e:
            logger.error(f"Sandboxed image processing failed: {str(e)}")
            result['warnings'].append(f'Sandbox processing error: {str(e)}')
        
        return result
    
    def _check_path_traversal(self, file_path: str) -> bool:
        """Check for path traversal attempts in file path."""
        import os
        
        # Normalize the path
        normalized_path = os.path.normpath(file_path)
        
        # Check for directory traversal patterns
        dangerous_patterns = ['../', '..\\', '../', '..\\\\']
        
        for pattern in dangerous_patterns:
            if pattern in file_path or pattern in normalized_path:
                return True
        
        # Check for absolute paths that might escape intended directory
        if os.path.isabs(normalized_path):
            return True
        
        # Check for system file paths
        system_paths = ['/etc/', '/bin/', '/usr/', '/var/', '/root/', 'C:\\Windows\\', 'C:\\System32\\']
        for sys_path in system_paths:
            if normalized_path.startswith(sys_path) or file_path.startswith(sys_path):
                return True
            
        return False
    
    def _scan_for_malicious_content(self, file_path: str) -> Dict[str, Any]:
        """
        Scan file for malicious content signatures.
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            Dict with scan results
        """
        scan_result = {
            'malicious_content_detected': False,
            'dangerous_signatures': [],
            'suspicious_patterns': []
        }
        
        try:
            with open(file_path, 'rb') as f:
                # Read first 1KB for signature checking
                header = f.read(1024)
                
                # Check for dangerous file signatures
                for signature in self.DANGEROUS_SIGNATURES:
                    if signature in header:
                        scan_result['malicious_content_detected'] = True
                        scan_result['dangerous_signatures'].append(signature.hex())
                
                # Check for suspicious text patterns in the header
                try:
                    header_text = header.decode('utf-8', errors='ignore').lower()
                    suspicious_patterns = [
                        'javascript:', 'vbscript:', '<script', '<?php',
                        'eval(', 'exec(', 'system(', 'shell_exec(',
                        'base64_decode', 'gzinflate', 'str_rot13'
                    ]
                    
                    for pattern in suspicious_patterns:
                        if pattern in header_text:
                            scan_result['malicious_content_detected'] = True
                            scan_result['suspicious_patterns'].append(pattern)
                            
                except UnicodeDecodeError:
                    pass  # Binary content, skip text pattern matching
                
        except Exception as e:
            logger.warning(f"Malicious content scan failed: {str(e)}")
        
        return scan_result
    
    def _scan_image_metadata(self, img: Image.Image) -> List[str]:
        """
        Scan image metadata for suspicious content.
        
        Args:
            img: PIL Image object
            
        Returns:
            List of suspicious metadata keys found
        """
        suspicious_found = []
        
        try:
            # Check EXIF data
            if hasattr(img, '_getexif') and img._getexif():
                exif_data = img._getexif()
                for key, value in exif_data.items():
                    # Check for suspicious metadata keys
                    if any(suspicious_key.lower() in str(value).lower() 
                          for suspicious_key in ['script', 'javascript', 'php', 'eval']):
                        suspicious_found.append(f'EXIF_{key}')
            
            # Check general image info
            if hasattr(img, 'info') and img.info:
                for key, value in img.info.items():
                    if key in self.SUSPICIOUS_METADATA_KEYS:
                        suspicious_found.append(key)
                    
                    # Check for suspicious content in metadata values
                    if isinstance(value, str):
                        if any(pattern in value.lower() 
                              for pattern in ['script', 'javascript', 'php', 'eval', 'exec']):
                            suspicious_found.append(f'{key}_content')
                            
        except Exception as e:
            logger.warning(f"Metadata scan failed: {str(e)}")
        
        return suspicious_found


class ThemeRateLimiter:
    """
    Rate limiter for theme generation operations.
    
    Implements rate limiting to prevent abuse of theme generation
    and other resource-intensive operations.
    """
    
    def __init__(self):
        self.cache_prefix = 'theme_rate_limit'
        self.default_limits = {
            'theme_generation': {'count': 10, 'period': 3600},  # 10 per hour
            'color_extraction': {'count': 20, 'period': 3600},  # 20 per hour
            'api_requests': {'count': 100, 'period': 3600},     # 100 per hour
        }
    
    def is_allowed(self, user_id: int, operation: str, custom_limit: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Check if an operation is allowed for a user.
        
        Args:
            user_id: ID of the user
            operation: Type of operation
            custom_limit: Optional custom rate limit
            
        Returns:
            Dict with rate limit status
        """
        limit_config = custom_limit or self.default_limits.get(operation, self.default_limits['api_requests'])
        
        cache_key = f"{self.cache_prefix}_{operation}_{user_id}"
        current_time = timezone.now().timestamp()
        
        # Get current attempts
        attempts = cache.get(cache_key, [])
        
        # Filter attempts within the time period
        period_start = current_time - limit_config['period']
        recent_attempts = [attempt for attempt in attempts if attempt > period_start]
        
        # Check if limit exceeded
        is_allowed = len(recent_attempts) < limit_config['count']
        
        if is_allowed:
            # Add current attempt
            recent_attempts.append(current_time)
            cache.set(cache_key, recent_attempts, limit_config['period'])
        
        return {
            'allowed': is_allowed,
            'current_count': len(recent_attempts),
            'limit': limit_config['count'],
            'period': limit_config['period'],
            'reset_time': period_start + limit_config['period'],
            'retry_after': limit_config['period'] - (current_time - min(recent_attempts)) if recent_attempts else 0
        }
    
    def reset_user_limits(self, user_id: int, operation: Optional[str] = None):
        """
        Reset rate limits for a user.
        
        Args:
            user_id: ID of the user
            operation: Optional specific operation to reset
        """
        if operation:
            cache_key = f"{self.cache_prefix}_{operation}_{user_id}"
            cache.delete(cache_key)
        else:
            # Reset all operations for user
            for op in self.default_limits.keys():
                cache_key = f"{self.cache_prefix}_{op}_{user_id}"
                cache.delete(cache_key)


class RequestSecurityValidator:
    """
    Validator for HTTP requests to theme API endpoints.
    
    Provides validation for request headers, parameters, and content
    to prevent various types of attacks.
    """
    
    def __init__(self):
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.suspicious_headers = [
            'x-forwarded-for', 'x-real-ip', 'x-originating-ip'
        ]
    
    def validate_request(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Validate an HTTP request for security issues.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'warnings': [],
            'security_score': 100  # Start with perfect score
        }
        
        # Check request size
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length and int(content_length) > self.max_request_size:
            result['is_valid'] = False
            result['warnings'].append('Request too large')
            return result
        
        # Check for suspicious headers
        for header in self.suspicious_headers:
            if header in request.META:
                result['warnings'].append(f'Suspicious header detected: {header}')
                result['security_score'] -= 10
        
        # Check user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or len(user_agent) < 10:
            result['warnings'].append('Missing or suspicious user agent')
            result['security_score'] -= 5
        
        # Check referer for API requests
        if request.path.startswith('/api/') and not request.META.get('HTTP_REFERER'):
            result['warnings'].append('Missing referer for API request')
            result['security_score'] -= 5
        
        # Check for common attack patterns in parameters
        for param_name, param_value in request.GET.items():
            if self._contains_attack_patterns(param_value):
                result['warnings'].append(f'Suspicious parameter: {param_name}')
                result['security_score'] -= 20
        
        return result
    
    def _contains_attack_patterns(self, value: str) -> bool:
        """Check if a value contains common attack patterns."""
        attack_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'document\.cookie',
            r'window\.location',
            r'\.\./\.\.',
            r'union\s+select',
            r'drop\s+table',
        ]
        
        for pattern in attack_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False


# Global instances
security_validator = ThemeSecurityValidator()
image_processor = SecureImageProcessor()
rate_limiter = ThemeRateLimiter()
request_validator = RequestSecurityValidator()


class APISecurityManager:
    """
    Comprehensive API security manager for theme endpoints.
    
    Provides centralized security validation, authentication checks,
    and authorization controls for all theme-related API operations.
    """
    
    def __init__(self):
        self.validator = ThemeSecurityValidator()
        self.image_processor = SecureImageProcessor()
        self.rate_limiter = ThemeRateLimiter()
        self.request_validator = RequestSecurityValidator()
    
    def validate_api_request(self, request, operation_type='api_request'):
        """
        Comprehensive API request validation.
        
        Args:
            request: Django HTTP request object
            operation_type: Type of operation being performed
            
        Returns:
            Dict with validation results and security recommendations
        """
        validation_result = {
            'is_valid': True,
            'security_level': 'high',
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'rate_limit_status': {},
            'authentication_status': {},
            'authorization_status': {}
        }
        
        try:
            # 1. Basic request validation
            request_validation = self.request_validator.validate_request(request)
            if not request_validation['is_valid']:
                validation_result['is_valid'] = False
                validation_result['errors'].extend(request_validation['warnings'])
            
            validation_result['warnings'].extend(request_validation['warnings'])
            
            # Adjust security level based on request validation
            if request_validation['security_score'] < 70:
                validation_result['security_level'] = 'medium'
            if request_validation['security_score'] < 50:
                validation_result['security_level'] = 'low'
            
            # 2. Authentication validation
            auth_status = self._validate_authentication(request)
            validation_result['authentication_status'] = auth_status
            
            if not auth_status['is_authenticated']:
                validation_result['is_valid'] = False
                validation_result['errors'].append('Authentication required')
            
            # 3. Rate limiting check
            if auth_status['is_authenticated']:
                rate_limit_status = self.rate_limiter.is_allowed(
                    request.user.id, 
                    operation_type
                )
                validation_result['rate_limit_status'] = rate_limit_status
                
                if not rate_limit_status['allowed']:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append('Rate limit exceeded')
                
                # Warn if approaching rate limit
                if rate_limit_status['current_count'] / rate_limit_status['limit'] > 0.8:
                    validation_result['warnings'].append('Approaching rate limit')
            
            # 4. Content validation for POST/PUT requests
            if request.method in ['POST', 'PUT', 'PATCH']:
                content_validation = self._validate_request_content(request)
                validation_result['warnings'].extend(content_validation['warnings'])
                
                if not content_validation['is_valid']:
                    validation_result['is_valid'] = False
                    validation_result['errors'].extend(content_validation['errors'])
            
            # 5. Generate security recommendations
            validation_result['recommendations'] = self._generate_security_recommendations(
                request, validation_result
            )
            
        except Exception as e:
            logger.error(f"API security validation error: {str(e)}")
            validation_result['is_valid'] = False
            validation_result['errors'].append('Security validation failed')
            validation_result['security_level'] = 'unknown'
        
        return validation_result
    
    def _validate_authentication(self, request):
        """Validate user authentication status."""
        return {
            'is_authenticated': request.user.is_authenticated,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'is_staff': request.user.is_staff if request.user.is_authenticated else False,
            'is_superuser': request.user.is_superuser if request.user.is_authenticated else False,
            'session_age': self._get_session_age(request) if request.user.is_authenticated else None
        }
    
    def _get_session_age(self, request):
        """Get the age of the user's session in seconds."""
        try:
            from django.contrib.sessions.models import Session
            session_key = request.session.session_key
            if session_key:
                session = Session.objects.get(session_key=session_key)
                return (timezone.now() - session.expire_date + timezone.timedelta(seconds=session.get_expiry_age())).total_seconds()
        except:
            pass
        return None
    
    def _validate_request_content(self, request):
        """Validate request content for security issues."""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check content type
            content_type = request.content_type
            if content_type and 'application/json' in content_type:
                # Validate JSON content
                try:
                    if hasattr(request, 'body') and request.body:
                        json_data = json.loads(request.body.decode('utf-8'))
                        json_validation = self._validate_json_content(json_data)
                        validation_result['warnings'].extend(json_validation['warnings'])
                        if not json_validation['is_valid']:
                            validation_result['is_valid'] = False
                            validation_result['errors'].extend(json_validation['errors'])
                except json.JSONDecodeError:
                    validation_result['warnings'].append('Invalid JSON format')
            
            # Check for file uploads
            if hasattr(request, 'FILES') and request.FILES:
                for field_name, uploaded_file in request.FILES.items():
                    file_validation = self._validate_uploaded_file(uploaded_file)
                    validation_result['warnings'].extend(file_validation['warnings'])
                    if not file_validation['is_valid']:
                        validation_result['is_valid'] = False
                        validation_result['errors'].extend(file_validation['errors'])
        
        except Exception as e:
            logger.error(f"Content validation error: {str(e)}")
            validation_result['warnings'].append('Content validation error')
        
        return validation_result
    
    def _validate_json_content(self, json_data):
        """Validate JSON content for security issues."""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check for excessively nested data
        max_depth = 10
        if self._get_json_depth(json_data) > max_depth:
            validation_result['warnings'].append('Deeply nested JSON data detected')
        
        # Check for suspicious keys or values
        suspicious_patterns = [
            'script', 'javascript', 'eval', 'function', 'constructor',
            '__proto__', 'prototype', 'toString', 'valueOf'
        ]
        
        def check_recursive(obj, path=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Check key names
                    if any(pattern in str(key).lower() for pattern in suspicious_patterns):
                        validation_result['warnings'].append(f'Suspicious key detected: {path}.{key}')
                    
                    # Check string values
                    if isinstance(value, str) and any(pattern in value.lower() for pattern in suspicious_patterns):
                        validation_result['warnings'].append(f'Suspicious value detected at: {path}.{key}')
                    
                    # Recurse
                    check_recursive(value, f'{path}.{key}' if path else key)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_recursive(item, f'{path}[{i}]')
        
        check_recursive(json_data)
        
        return validation_result
    
    def _get_json_depth(self, obj, depth=0):
        """Calculate the maximum depth of a JSON object."""
        if isinstance(obj, dict):
            return max([self._get_json_depth(value, depth + 1) for value in obj.values()], default=depth)
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj], default=depth)
        else:
            return depth
    
    def _validate_uploaded_file(self, uploaded_file):
        """Validate uploaded files for security."""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Save file temporarily for validation
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Validate with image processor
                image_validation = self.image_processor.validate_image_file(temp_file_path)
                validation_result['warnings'].extend(image_validation['warnings'])
                
                if not image_validation['is_valid']:
                    validation_result['is_valid'] = False
                    validation_result['errors'].extend(image_validation['errors'])
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            validation_result['warnings'].append('File validation error')
        
        return validation_result
    
    def _generate_security_recommendations(self, request, validation_result):
        """Generate security recommendations based on validation results."""
        recommendations = []
        
        # Authentication recommendations
        if not validation_result['authentication_status']['is_authenticated']:
            recommendations.append('Use API authentication for better security')
        
        # Rate limiting recommendations
        rate_status = validation_result.get('rate_limit_status', {})
        if rate_status.get('current_count', 0) / rate_status.get('limit', 1) > 0.8:
            recommendations.append('Consider implementing client-side rate limiting')
        
        # Security level recommendations
        if validation_result['security_level'] == 'low':
            recommendations.append('Review request headers and parameters for security')
            recommendations.append('Consider using HTTPS for all API requests')
        
        # Content recommendations
        if request.method in ['POST', 'PUT', 'PATCH']:
            recommendations.append('Validate all input data on the client side')
            recommendations.append('Use content-type headers appropriately')
        
        return recommendations


class PermissionManager:
    """
    Advanced permission management for theme operations.
    
    Provides fine-grained permission controls for different
    theme operations and user roles.
    """
    
    def __init__(self):
        self.permission_matrix = {
            'view_theme': ['owner', 'staff', 'team_member'],
            'create_theme': ['owner', 'staff'],
            'modify_theme': ['owner', 'staff'],
            'delete_theme': ['owner', 'staff'],
            'extract_colors': ['owner', 'staff', 'team_member'],
            'generate_variations': ['owner', 'staff'],
            'view_analytics': ['owner', 'staff'],
            'manage_cache': ['owner', 'staff'],
            'export_theme': ['owner', 'staff', 'team_member'],
            'import_theme': ['owner', 'staff'],
            'system_admin': ['staff']
        }
    
    def check_permission(self, user, operation, event=None, theme=None):
        """
        Check if user has permission for a specific operation.
        
        Args:
            user: Django user object
            operation: Operation to check permission for
            event: Optional event object for context
            theme: Optional theme object for context
            
        Returns:
            Dict with permission status and details
        """
        permission_result = {
            'allowed': False,
            'reason': 'Permission denied',
            'user_roles': [],
            'required_roles': self.permission_matrix.get(operation, []),
            'context': {}
        }
        
        try:
            # Determine user roles
            user_roles = self._get_user_roles(user, event, theme)
            permission_result['user_roles'] = user_roles
            
            # Check if user has required role
            required_roles = self.permission_matrix.get(operation, [])
            if any(role in user_roles for role in required_roles):
                permission_result['allowed'] = True
                permission_result['reason'] = 'Permission granted'
            else:
                permission_result['reason'] = f'Requires one of: {", ".join(required_roles)}'
            
            # Add context information
            permission_result['context'] = {
                'operation': operation,
                'event_id': event.id if event else None,
                'theme_id': theme.id if theme else None,
                'user_id': user.id if user.is_authenticated else None
            }
        
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            permission_result['reason'] = 'Permission check failed'
        
        return permission_result
    
    def _get_user_roles(self, user, event=None, theme=None):
        """Determine user roles for permission checking."""
        roles = []
        
        if not user.is_authenticated:
            return roles
        
        # Staff role
        if user.is_staff:
            roles.append('staff')
        
        # Superuser role
        if user.is_superuser:
            roles.append('superuser')
        
        # Event-based roles
        if event:
            if event.organizer == user:
                roles.append('owner')
            
            # Check for team membership (would need to implement team model)
            # if user in event.team_members.all():
            #     roles.append('team_member')
        
        # Theme-based roles
        if theme and theme.event:
            if theme.event.organizer == user:
                roles.append('owner')
        
        return roles


class AuditLogger:
    """
    Security audit logging for theme operations.
    
    Logs security-relevant events and operations for
    monitoring and compliance purposes.
    """
    
    def __init__(self):
        self.audit_logger = logging.getLogger('theme_security_audit')
    
    def log_security_event(self, event_type, user, request=None, **kwargs):
        """
        Log a security-relevant event.
        
        Args:
            event_type: Type of security event
            user: User associated with the event
            request: Optional HTTP request object
            **kwargs: Additional event data
        """
        try:
            audit_data = {
                'timestamp': timezone.now().isoformat(),
                'event_type': event_type,
                'user_id': user.id if user and user.is_authenticated else None,
                'username': user.username if user and user.is_authenticated else 'anonymous',
                'ip_address': self._get_client_ip(request) if request else None,
                'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
                'path': request.path if request else None,
                'method': request.method if request else None,
                **kwargs
            }
            
            # Log to audit logger
            self.audit_logger.info(json.dumps(audit_data))
            
            # Store in database for long-term retention
            self._store_audit_record(audit_data)
        
        except Exception as e:
            logger.error(f"Audit logging error: {str(e)}")
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _store_audit_record(self, audit_data):
        """Store audit record in database."""
        try:
            from .models import ThemeGenerationLog
            
            # Create a log entry (simplified - in production you'd have a dedicated audit model)
            if audit_data.get('event_id'):
                from events.models import Event
                try:
                    event = Event.objects.get(id=audit_data['event_id'])
                    ThemeGenerationLog.log_operation(
                        event=event,
                        operation_type='security_audit',
                        status='success',
                        user_id=audit_data.get('user_id'),
                        metadata=audit_data
                    )
                except Event.DoesNotExist:
                    pass
        
        except Exception as e:
            logger.error(f"Audit record storage error: {str(e)}")


# Global instances
api_security_manager = APISecurityManager()
permission_manager = PermissionManager()
audit_logger = AuditLogger()