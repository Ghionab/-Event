"""
Advanced Color Processing Service

Implements sophisticated color analysis algorithms including color harmony calculation,
visual prominence ranking, color diversity scoring, and brand color hierarchy generation.
"""

import colorsys
import math
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from PIL import Image, ImageStat
import numpy as np
from sklearn.cluster import KMeans
from .color_extractor import ColorExtractor


@dataclass
class ColorHarmony:
    """Represents color harmony analysis results."""
    harmony_type: str
    harmony_score: float
    complementary_colors: List[str]
    analogous_colors: List[str]
    triadic_colors: List[str]
    split_complementary: List[str]


@dataclass
class ColorProminence:
    """Represents visual prominence analysis of a color."""
    color: str
    prominence_score: float
    visual_weight: float
    contrast_ratio: float
    saturation_impact: float
    brightness_impact: float


@dataclass
class ColorDiversity:
    """Represents color diversity analysis results."""
    diversity_score: float
    hue_distribution: Dict[str, float]
    saturation_range: Tuple[float, float]
    brightness_range: Tuple[float, float]
    color_temperature: str  # 'warm', 'cool', 'neutral'


@dataclass
class BrandColorHierarchy:
    """Represents brand color hierarchy analysis."""
    primary_color: str
    secondary_colors: List[str]
    accent_colors: List[str]
    neutral_colors: List[str]
    hierarchy_confidence: float


class AdvancedColorProcessor:
    """
    Advanced color processing service for sophisticated color analysis.
    
    Provides color harmony calculation, visual prominence ranking,
    color diversity scoring, and brand color hierarchy generation.
    """
    
    def __init__(self):
        self.color_extractor = ColorExtractor()
        
        # Color harmony ratios (based on color wheel degrees)
        self.harmony_ratios = {
            'complementary': [180],
            'analogous': [30, 60],
            'triadic': [120, 240],
            'split_complementary': [150, 210],
            'tetradic': [90, 180, 270],
            'square': [90, 180, 270],
            'monochromatic': [0]
        }
        
        # Visual prominence weights for color psychology
        self.prominence_weights = {
            'contrast': 0.4,
            'saturation': 0.3,
            'brightness': 0.2,
            'visual_weight': 0.1
        }
        
        # Color temperature ranges (hue values 0-1)
        self.color_temperatures = {
            'warm': [(0.0, 0.17), (0.83, 1.0)],  # Red-orange range
            'cool': [(0.33, 0.67)],  # Green-blue range
            'neutral': [(0.17, 0.33), (0.67, 0.83)]  # Yellow-green and purple ranges
        }
    
    def analyze_color_harmony(self, colors: List[str]) -> ColorHarmony:
        """
        Calculate color harmony for a set of colors.
        
        Args:
            colors: List of hex color codes
            
        Returns:
            ColorHarmony object with analysis results
        """
        if not colors:
            return ColorHarmony(
                harmony_type='none',
                harmony_score=0.0,
                complementary_colors=[],
                analogous_colors=[],
                triadic_colors=[],
                split_complementary=[]
            )
        
        # Convert colors to HSV for analysis
        hsv_colors = [self._hex_to_hsv(color) for color in colors]
        
        # Determine dominant harmony type
        harmony_type, harmony_score = self._calculate_harmony_score(hsv_colors)
        
        # Generate harmony variations based on primary color
        primary_hsv = hsv_colors[0] if hsv_colors else (0, 0, 0)
        
        return ColorHarmony(
            harmony_type=harmony_type,
            harmony_score=harmony_score,
            complementary_colors=self._generate_complementary(primary_hsv),
            analogous_colors=self._generate_analogous(primary_hsv),
            triadic_colors=self._generate_triadic(primary_hsv),
            split_complementary=self._generate_split_complementary(primary_hsv)
        )
    
    def calculate_visual_prominence(self, colors: List[str], 
                                  background_color: str = '#ffffff') -> List[ColorProminence]:
        """
        Calculate visual prominence ranking for colors.
        
        Args:
            colors: List of hex color codes to analyze
            background_color: Background color for contrast calculation
            
        Returns:
            List of ColorProminence objects sorted by prominence score
        """
        prominences = []
        bg_rgb = self._hex_to_rgb(background_color)
        
        for color in colors:
            rgb = self._hex_to_rgb(color)
            hsv = self._hex_to_hsv(color)
            
            # Calculate various prominence factors
            contrast_ratio = self._calculate_contrast_ratio(rgb, bg_rgb)
            saturation_impact = hsv[1]  # Higher saturation = more prominent
            brightness_impact = abs(hsv[2] - 0.5) * 2  # Distance from middle gray
            
            # Calculate visual weight based on color psychology
            visual_weight = self._calculate_visual_weight(rgb, hsv)
            
            # Combine factors for overall prominence score using configured weights
            prominence_score = (
                contrast_ratio * self.prominence_weights['contrast'] +
                saturation_impact * self.prominence_weights['saturation'] +
                brightness_impact * self.prominence_weights['brightness'] +
                visual_weight * self.prominence_weights['visual_weight']
            )
            
            prominences.append(ColorProminence(
                color=color,
                prominence_score=prominence_score,
                visual_weight=visual_weight,
                contrast_ratio=contrast_ratio,
                saturation_impact=saturation_impact,
                brightness_impact=brightness_impact
            ))
        
        # Sort by prominence score (highest first)
        return sorted(prominences, key=lambda x: x.prominence_score, reverse=True)
    
    def calculate_color_diversity(self, colors: List[str]) -> ColorDiversity:
        """
        Calculate color diversity score and distribution analysis.
        
        Args:
            colors: List of hex color codes
            
        Returns:
            ColorDiversity object with analysis results
        """
        if not colors:
            return ColorDiversity(
                diversity_score=0.0,
                hue_distribution={},
                saturation_range=(0.0, 0.0),
                brightness_range=(0.0, 0.0),
                color_temperature='neutral'
            )
        
        hsv_colors = [self._hex_to_hsv(color) for color in colors]
        
        # Calculate hue distribution
        hue_distribution = self._calculate_hue_distribution(hsv_colors)
        
        # Calculate saturation and brightness ranges
        saturations = [hsv[1] for hsv in hsv_colors]
        brightnesses = [hsv[2] for hsv in hsv_colors]
        
        saturation_range = (min(saturations), max(saturations))
        brightness_range = (min(brightnesses), max(brightnesses))
        
        # Calculate advanced diversity score
        diversity_score = self._calculate_advanced_diversity_score(hsv_colors)
        
        # Determine color temperature
        color_temperature = self._determine_color_temperature(hsv_colors)
        
        return ColorDiversity(
            diversity_score=diversity_score,
            hue_distribution=hue_distribution,
            saturation_range=saturation_range,
            brightness_range=brightness_range,
            color_temperature=color_temperature
        )
    
    def _calculate_advanced_diversity_score(self, hsv_colors: List[Tuple[float, float, float]]) -> float:
        """Calculate advanced color diversity score using multiple metrics."""
        if len(hsv_colors) < 2:
            return 0.0
        
        # 1. Hue diversity (most important)
        hues = [hsv[0] for hsv in hsv_colors]
        hue_diversity = self._calculate_hue_diversity(hues)
        
        # 2. Saturation diversity
        saturations = [hsv[1] for hsv in hsv_colors]
        saturation_diversity = max(saturations) - min(saturations)
        
        # 3. Brightness diversity
        brightnesses = [hsv[2] for hsv in hsv_colors]
        brightness_diversity = max(brightnesses) - min(brightnesses)
        
        # 4. Color space coverage (how well colors are distributed)
        space_coverage = self._calculate_color_space_coverage(hsv_colors)
        
        # 5. Perceptual distance diversity
        perceptual_diversity = self._calculate_perceptual_diversity(hsv_colors)
        
        # Combine factors with weights
        diversity_score = (
            hue_diversity * 0.35 +
            saturation_diversity * 0.2 +
            brightness_diversity * 0.15 +
            space_coverage * 0.15 +
            perceptual_diversity * 0.15
        )
        
        return min(diversity_score, 1.0)
    
    def _calculate_hue_diversity(self, hues: List[float]) -> float:
        """Calculate hue diversity using circular statistics."""
        if len(hues) < 2:
            return 0.0
        
        # Convert to angles and calculate circular variance
        angles = [h * 2 * math.pi for h in hues]
        
        # Calculate mean direction
        sum_sin = sum(math.sin(angle) for angle in angles)
        sum_cos = sum(math.cos(angle) for angle in angles)
        
        # Calculate circular variance (0 = all same direction, 1 = maximum spread)
        n = len(angles)
        r = math.sqrt(sum_sin**2 + sum_cos**2) / n
        circular_variance = 1 - r
        
        return min(circular_variance, 1.0)
    
    def _calculate_color_space_coverage(self, hsv_colors: List[Tuple[float, float, float]]) -> float:
        """Calculate how well colors cover the available color space."""
        if len(hsv_colors) < 2:
            return 0.0
        
        # Divide HSV space into regions and check coverage
        hue_regions = 8  # 8 regions of 45 degrees each
        saturation_regions = 3  # Low, medium, high saturation
        brightness_regions = 3  # Dark, medium, bright
        
        covered_regions = set()
        
        for h, s, v in hsv_colors:
            hue_region = int(h * hue_regions) % hue_regions
            sat_region = min(int(s * saturation_regions), saturation_regions - 1)
            bright_region = min(int(v * brightness_regions), brightness_regions - 1)
            
            covered_regions.add((hue_region, sat_region, bright_region))
        
        total_regions = hue_regions * saturation_regions * brightness_regions
        coverage = len(covered_regions) / min(len(hsv_colors) * 2, total_regions)
        
        return min(coverage, 1.0)
    
    def _calculate_perceptual_diversity(self, hsv_colors: List[Tuple[float, float, float]]) -> float:
        """Calculate perceptual diversity using Delta E color differences."""
        if len(hsv_colors) < 2:
            return 0.0
        
        # Convert HSV to LAB for perceptual distance calculation
        lab_colors = []
        for h, s, v in hsv_colors:
            # Convert HSV -> RGB -> LAB (simplified)
            rgb = colorsys.hsv_to_rgb(h, s, v)
            # Simplified LAB conversion (for demonstration)
            lab_colors.append(rgb)  # Using RGB as approximation
        
        # Calculate average pairwise distance
        total_distance = 0
        pairs = 0
        
        for i in range(len(lab_colors)):
            for j in range(i + 1, len(lab_colors)):
                # Euclidean distance in RGB space (simplified)
                distance = sum((a - b) ** 2 for a, b in zip(lab_colors[i], lab_colors[j])) ** 0.5
                total_distance += distance
                pairs += 1
        
        if pairs == 0:
            return 0.0
        
        avg_distance = total_distance / pairs
        # Normalize to 0-1 scale
        return min(avg_distance / 1.0, 1.0)  # Assuming max distance of 1.0 in RGB
    
    def generate_brand_hierarchy(self, colors: List[str], 
                               image_path: Optional[str] = None) -> BrandColorHierarchy:
        """
        Generate brand color hierarchy from extracted colors.
        
        Args:
            colors: List of hex color codes
            image_path: Optional path to source image for additional analysis
            
        Returns:
            BrandColorHierarchy object with categorized colors
        """
        if not colors:
            return BrandColorHierarchy(
                primary_color='#000000',
                secondary_colors=[],
                accent_colors=[],
                neutral_colors=[],
                hierarchy_confidence=0.0
            )
        
        # Calculate prominence for hierarchy determination
        prominences = self.calculate_visual_prominence(colors)
        
        # Analyze color properties with advanced metrics
        color_analysis = {}
        for color in colors:
            hsv = self._hex_to_hsv(color)
            rgb = self._hex_to_rgb(color)
            
            color_analysis[color] = {
                'hsv': hsv,
                'rgb': rgb,
                'is_neutral': self._is_neutral_color(hsv),
                'is_vibrant': self._is_vibrant_color(hsv),
                'is_dark': hsv[2] < 0.3,
                'is_light': hsv[2] > 0.8,
                'warmth': self._calculate_color_warmth(hsv),
                'brand_suitability': self._calculate_brand_suitability(hsv, rgb),
                'accessibility_score': self._calculate_accessibility_score(rgb)
            }
        
        # Advanced primary color selection
        primary_color = self._select_optimal_primary_color(colors, color_analysis, prominences)
        
        # Categorize remaining colors with advanced logic
        secondary_colors, accent_colors, neutral_colors = self._categorize_brand_colors(
            colors, primary_color, color_analysis, prominences
        )
        
        # Calculate enhanced confidence score
        hierarchy_confidence = self._calculate_enhanced_hierarchy_confidence(
            color_analysis, prominences, primary_color
        )
        
        return BrandColorHierarchy(
            primary_color=primary_color,
            secondary_colors=secondary_colors,
            accent_colors=accent_colors,
            neutral_colors=neutral_colors,
            hierarchy_confidence=hierarchy_confidence
        )
    
    def _is_vibrant_color(self, hsv: Tuple[float, float, float]) -> bool:
        """Enhanced vibrant color detection."""
        h, s, v = hsv
        # More sophisticated vibrant detection
        return s > 0.6 and v > 0.4 and v < 0.95  # Avoid pure white
    
    def _calculate_color_warmth(self, hsv: Tuple[float, float, float]) -> float:
        """Calculate color warmth score (0 = cool, 1 = warm)."""
        h, s, v = hsv
        
        # Warm colors: red, orange, yellow
        if 0 <= h <= 0.17 or 0.83 <= h <= 1.0:  # Red-orange range
            warmth = 1.0
        elif 0.17 < h <= 0.25:  # Yellow range
            warmth = 0.8
        elif 0.25 < h <= 0.33:  # Yellow-green range
            warmth = 0.3
        elif 0.33 < h <= 0.67:  # Green-blue range (cool)
            warmth = 0.0
        elif 0.67 < h <= 0.83:  # Purple range
            warmth = 0.2
        else:
            warmth = 0.5
        
        # Adjust based on saturation (more saturated = more pronounced temperature)
        return warmth * s + 0.5 * (1 - s)
    
    def _calculate_brand_suitability(self, hsv: Tuple[float, float, float], 
                                   rgb: Tuple[int, int, int]) -> float:
        """Calculate how suitable a color is for branding."""
        h, s, v = hsv
        
        # Factors that make a color good for branding
        suitability = 0.0
        
        # 1. Moderate to high saturation (not too dull, not too intense)
        if 0.4 <= s <= 0.8:
            suitability += 0.3
        elif 0.2 <= s < 0.4:
            suitability += 0.15
        
        # 2. Good brightness range (not too dark or too light)
        if 0.3 <= v <= 0.8:
            suitability += 0.3
        elif 0.2 <= v < 0.3 or 0.8 < v <= 0.9:
            suitability += 0.15
        
        # 3. Professional color ranges (blues, greens, some reds)
        if 0.5 <= h <= 0.67:  # Blue range - very professional
            suitability += 0.2
        elif 0.33 <= h < 0.5:  # Green range - trustworthy
            suitability += 0.15
        elif 0 <= h <= 0.08 or 0.92 <= h <= 1.0:  # Red range - attention-grabbing
            suitability += 0.1
        
        # 4. Avoid problematic colors
        if self._is_neutral_color(hsv):
            suitability += 0.1  # Neutrals are safe but not exciting
        
        return min(suitability, 1.0)
    
    def _calculate_accessibility_score(self, rgb: Tuple[int, int, int]) -> float:
        """Calculate accessibility score based on contrast potential."""
        # Calculate contrast with both white and black
        white_contrast = self._calculate_contrast_ratio(rgb, (255, 255, 255))
        black_contrast = self._calculate_contrast_ratio(rgb, (0, 0, 0))
        
        # Best contrast ratio determines accessibility score
        best_contrast = max(white_contrast, black_contrast)
        
        # WCAG AA requires 4.5:1, AAA requires 7:1
        if best_contrast >= 7.0:
            return 1.0
        elif best_contrast >= 4.5:
            return 0.8
        elif best_contrast >= 3.0:
            return 0.6
        else:
            return 0.3
    
    def _select_optimal_primary_color(self, colors: List[str], 
                                    color_analysis: Dict[str, Any],
                                    prominences: List[ColorProminence]) -> str:
        """Select the optimal primary color using advanced criteria."""
        if not colors:
            return '#000000'
        
        # Score each color for primary suitability
        primary_scores = {}
        
        for color in colors:
            analysis = color_analysis[color]
            prominence = next((p for p in prominences if p.color == color), None)
            
            score = 0.0
            
            # Visual prominence (30%)
            if prominence:
                score += prominence.prominence_score * 0.3
            
            # Brand suitability (25%)
            score += analysis['brand_suitability'] * 0.25
            
            # Accessibility (20%)
            score += analysis['accessibility_score'] * 0.2
            
            # Not neutral (15%) - primary should be distinctive
            if not analysis['is_neutral']:
                score += 0.15
            
            # Vibrant but not overwhelming (10%)
            if analysis['is_vibrant'] and not (analysis['hsv'][1] > 0.9):
                score += 0.1
            
            primary_scores[color] = score
        
        # Return color with highest primary score
        return max(primary_scores.items(), key=lambda x: x[1])[0]
    
    def _categorize_brand_colors(self, colors: List[str], primary_color: str,
                               color_analysis: Dict[str, Any],
                               prominences: List[ColorProminence]) -> Tuple[List[str], List[str], List[str]]:
        """Categorize colors into secondary, accent, and neutral with advanced logic."""
        secondary_colors = []
        accent_colors = []
        neutral_colors = []
        
        remaining_colors = [c for c in colors if c != primary_color]
        
        for color in remaining_colors:
            analysis = color_analysis[color]
            prominence = next((p for p in prominences if p.color == color), None)
            
            if analysis['is_neutral']:
                neutral_colors.append(color)
            elif analysis['is_vibrant'] and analysis['brand_suitability'] > 0.6:
                # High-quality vibrant colors become accents
                accent_colors.append(color)
            elif prominence and prominence.prominence_score > 0.5:
                # Prominent non-neutral colors become secondary
                secondary_colors.append(color)
            elif analysis['accessibility_score'] > 0.7:
                # High accessibility colors are good for secondary use
                secondary_colors.append(color)
            else:
                # Everything else goes to neutral
                neutral_colors.append(color)
        
        # Sort by suitability and limit quantities
        secondary_colors.sort(key=lambda c: color_analysis[c]['brand_suitability'], reverse=True)
        accent_colors.sort(key=lambda c: color_analysis[c]['brand_suitability'], reverse=True)
        neutral_colors.sort(key=lambda c: color_analysis[c]['accessibility_score'], reverse=True)
        
        return secondary_colors[:3], accent_colors[:2], neutral_colors[:3]
    
    def _calculate_enhanced_hierarchy_confidence(self, color_analysis: Dict[str, Any],
                                               prominences: List[ColorProminence],
                                               primary_color: str) -> float:
        """Calculate enhanced confidence score for the hierarchy."""
        if not prominences:
            return 0.0
        
        confidence_factors = []
        
        # 1. Primary color quality
        primary_analysis = color_analysis.get(primary_color, {})
        primary_suitability = primary_analysis.get('brand_suitability', 0.0)
        confidence_factors.append(primary_suitability)
        
        # 2. Prominence spread (clear hierarchy)
        prominence_scores = [p.prominence_score for p in prominences]
        if len(prominence_scores) > 1:
            prominence_spread = max(prominence_scores) - min(prominence_scores)
            confidence_factors.append(prominence_spread)
        
        # 3. Color diversity
        color_types = {
            'neutral': sum(1 for analysis in color_analysis.values() if analysis.get('is_neutral', False)),
            'vibrant': sum(1 for analysis in color_analysis.values() if analysis.get('is_vibrant', False)),
            'accessible': sum(1 for analysis in color_analysis.values() if analysis.get('accessibility_score', 0) > 0.7)
        }
        
        # Good balance of color types increases confidence
        balance_score = min(1.0, (color_types['neutral'] + color_types['vibrant'] + color_types['accessible']) / 6)
        confidence_factors.append(balance_score)
        
        # 4. Overall accessibility
        avg_accessibility = sum(analysis.get('accessibility_score', 0) for analysis in color_analysis.values()) / len(color_analysis)
        confidence_factors.append(avg_accessibility)
        
        # Calculate weighted average
        return min(sum(confidence_factors) / len(confidence_factors), 1.0)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _hex_to_hsv(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to HSV tuple."""
        rgb = self._hex_to_rgb(hex_color)
        return colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    
    def _hsv_to_hex(self, hsv: Tuple[float, float, float]) -> str:
        """Convert HSV tuple to hex color."""
        rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
    
    def _calculate_harmony_score(self, hsv_colors: List[Tuple[float, float, float]]) -> Tuple[str, float]:
        """Calculate harmony score and determine harmony type."""
        if len(hsv_colors) < 2:
            return 'monochromatic', 1.0
        
        # Calculate hue differences
        hues = [hsv[0] * 360 for hsv in hsv_colors]
        
        best_harmony = 'none'
        best_score = 0.0
        
        for harmony_type, target_angles in self.harmony_ratios.items():
            score = self._calculate_harmony_match(hues, target_angles)
            if score > best_score:
                best_score = score
                best_harmony = harmony_type
        
        return best_harmony, best_score
    
    def _calculate_harmony_match(self, hues: List[float], target_angles: List[float]) -> float:
        """Calculate how well hues match a harmony pattern."""
        if not hues or not target_angles:
            return 0.0
        
        base_hue = hues[0]
        total_score = 0.0
        matches = 0
        
        for hue in hues[1:]:
            hue_diff = abs(hue - base_hue)
            hue_diff = min(hue_diff, 360 - hue_diff)  # Handle wrap-around
            
            # Find closest target angle
            closest_match = min(target_angles, key=lambda x: abs(x - hue_diff))
            error = abs(closest_match - hue_diff)
            
            # Score based on how close to target (max error tolerance: 30 degrees)
            score = max(0, 1 - (error / 30))
            total_score += score
            matches += 1
        
        return total_score / max(matches, 1)
    
    def _generate_complementary(self, hsv: Tuple[float, float, float]) -> List[str]:
        """Generate complementary colors."""
        comp_hue = (hsv[0] + 0.5) % 1.0
        return [self._hsv_to_hex((comp_hue, hsv[1], hsv[2]))]
    
    def _generate_analogous(self, hsv: Tuple[float, float, float]) -> List[str]:
        """Generate analogous colors."""
        colors = []
        for offset in [-1/12, 1/12]:  # ±30 degrees
            new_hue = (hsv[0] + offset) % 1.0
            colors.append(self._hsv_to_hex((new_hue, hsv[1], hsv[2])))
        return colors
    
    def _generate_triadic(self, hsv: Tuple[float, float, float]) -> List[str]:
        """Generate triadic colors."""
        colors = []
        for offset in [1/3, 2/3]:  # 120, 240 degrees
            new_hue = (hsv[0] + offset) % 1.0
            colors.append(self._hsv_to_hex((new_hue, hsv[1], hsv[2])))
        return colors
    
    def _generate_split_complementary(self, hsv: Tuple[float, float, float]) -> List[str]:
        """Generate split complementary colors."""
        colors = []
        for offset in [5/12, 7/12]:  # 150, 210 degrees
            new_hue = (hsv[0] + offset) % 1.0
            colors.append(self._hsv_to_hex((new_hue, hsv[1], hsv[2])))
        return colors
    
    def _generate_square_harmony(self, hsv: Tuple[float, float, float]) -> List[str]:
        """Generate square harmony colors (90 degrees apart)."""
        colors = []
        for offset in [0.25, 0.5, 0.75]:  # 90, 180, 270 degrees
            new_hue = (hsv[0] + offset) % 1.0
            colors.append(self._hsv_to_hex((new_hue, hsv[1], hsv[2])))
        return colors
    
    def _generate_tetradic_harmony(self, hsv: Tuple[float, float, float]) -> List[str]:
        """Generate tetradic (rectangle) harmony colors."""
        colors = []
        # Tetradic uses two complementary pairs
        for offset in [1/6, 0.5, 2/3]:  # 60, 180, 240 degrees
            new_hue = (hsv[0] + offset) % 1.0
            colors.append(self._hsv_to_hex((new_hue, hsv[1], hsv[2])))
        return colors
    
    def calculate_advanced_harmony_score(self, colors: List[str]) -> Dict[str, float]:
        """
        Calculate advanced harmony scores for multiple harmony types.
        
        Args:
            colors: List of hex color codes
            
        Returns:
            Dictionary with harmony type scores
        """
        if not colors:
            return {}
        
        hsv_colors = [self._hex_to_hsv(color) for color in colors]
        harmony_scores = {}
        
        for harmony_type, target_angles in self.harmony_ratios.items():
            score = self._calculate_harmony_match(
                [hsv[0] * 360 for hsv in hsv_colors], 
                target_angles
            )
            harmony_scores[harmony_type] = score
        
        return harmony_scores
    
    def generate_harmony_palette(self, base_color: str, harmony_type: str) -> List[str]:
        """
        Generate a complete harmony palette based on a base color and harmony type.
        
        Args:
            base_color: Base hex color
            harmony_type: Type of harmony ('complementary', 'triadic', etc.)
            
        Returns:
            List of hex colors forming the harmony palette
        """
        hsv = self._hex_to_hsv(base_color)
        palette = [base_color]  # Include base color
        
        if harmony_type == 'complementary':
            palette.extend(self._generate_complementary(hsv))
        elif harmony_type == 'analogous':
            palette.extend(self._generate_analogous(hsv))
        elif harmony_type == 'triadic':
            palette.extend(self._generate_triadic(hsv))
        elif harmony_type == 'split_complementary':
            palette.extend(self._generate_split_complementary(hsv))
        elif harmony_type == 'square':
            palette.extend(self._generate_square_harmony(hsv))
        elif harmony_type == 'tetradic':
            palette.extend(self._generate_tetradic_harmony(hsv))
        elif harmony_type == 'monochromatic':
            # Generate monochromatic variations
            for lightness_offset in [-0.3, -0.15, 0.15, 0.3]:
                new_lightness = max(0.0, min(1.0, hsv[2] + lightness_offset))
                palette.append(self._hsv_to_hex((hsv[0], hsv[1], new_lightness)))
        
        return palette
    
    def _calculate_contrast_ratio(self, rgb1: Tuple[int, int, int], 
                                rgb2: Tuple[int, int, int]) -> float:
        """Calculate WCAG contrast ratio between two colors."""
        def luminance(rgb):
            r, g, b = [x/255.0 for x in rgb]
            r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
            g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
            b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
            return 0.2126*r + 0.7152*g + 0.0722*b
        
        l1 = luminance(rgb1)
        l2 = luminance(rgb2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def _calculate_visual_weight(self, rgb: Tuple[int, int, int], 
                               hsv: Tuple[float, float, float]) -> float:
        """Calculate visual weight based on color psychology."""
        # Warm colors appear heavier
        hue_weight = 1.0
        if 0 <= hsv[0] <= 0.17 or 0.83 <= hsv[0] <= 1.0:  # Red-orange range
            hue_weight = 1.2
        elif 0.17 < hsv[0] <= 0.33:  # Yellow-green range
            hue_weight = 1.1
        elif 0.5 < hsv[0] <= 0.67:  # Blue range
            hue_weight = 0.8
        
        # Higher saturation increases weight
        saturation_weight = 0.5 + (hsv[1] * 0.5)
        
        # Darker colors appear heavier
        brightness_weight = 1.0 - (hsv[2] * 0.3)
        
        return hue_weight * saturation_weight * brightness_weight
    
    def _calculate_hue_distribution(self, hsv_colors: List[Tuple[float, float, float]]) -> Dict[str, float]:
        """Calculate distribution of hues across color wheel segments."""
        segments = {
            'red': 0, 'orange': 0, 'yellow': 0, 'green': 0,
            'cyan': 0, 'blue': 0, 'purple': 0, 'magenta': 0
        }
        
        segment_ranges = [
            ('red', 0, 0.083), ('orange', 0.083, 0.167),
            ('yellow', 0.167, 0.25), ('green', 0.25, 0.417),
            ('cyan', 0.417, 0.5), ('blue', 0.5, 0.667),
            ('purple', 0.667, 0.833), ('magenta', 0.833, 1.0)
        ]
        
        for hsv in hsv_colors:
            hue = hsv[0]
            for segment, start, end in segment_ranges:
                if start <= hue < end:
                    segments[segment] += 1
                    break
        
        # Convert to percentages
        total = len(hsv_colors)
        return {k: v/total for k, v in segments.items()} if total > 0 else segments
    
    def _calculate_diversity_score(self, hsv_colors: List[Tuple[float, float, float]]) -> float:
        """Calculate overall color diversity score."""
        if len(hsv_colors) < 2:
            return 0.0
        
        # Calculate hue spread
        hues = [hsv[0] for hsv in hsv_colors]
        hue_range = max(hues) - min(hues)
        
        # Calculate saturation spread
        saturations = [hsv[1] for hsv in hsv_colors]
        saturation_range = max(saturations) - min(saturations)
        
        # Calculate brightness spread
        brightnesses = [hsv[2] for hsv in hsv_colors]
        brightness_range = max(brightnesses) - min(brightnesses)
        
        # Combine factors (hue diversity is most important)
        diversity_score = (
            hue_range * 0.5 +
            saturation_range * 0.3 +
            brightness_range * 0.2
        )
        
        return min(diversity_score, 1.0)
    
    def _determine_color_temperature(self, hsv_colors: List[Tuple[float, float, float]]) -> str:
        """Determine overall color temperature (warm/cool/neutral)."""
        if not hsv_colors:
            return 'neutral'
        
        warm_score = 0
        cool_score = 0
        
        for hsv in hsv_colors:
            hue = hsv[0]
            saturation = hsv[1]
            
            # Weight by saturation (more saturated colors have more influence)
            weight = saturation
            
            # Warm hues: red, orange, yellow (0-0.25 and 0.83-1.0)
            if (0 <= hue <= 0.25) or (0.83 <= hue <= 1.0):
                warm_score += weight
            # Cool hues: green, cyan, blue, purple (0.25-0.83)
            elif 0.25 < hue < 0.83:
                cool_score += weight
        
        if warm_score > cool_score * 1.2:
            return 'warm'
        elif cool_score > warm_score * 1.2:
            return 'cool'
        else:
            return 'neutral'
    
    def _is_neutral_color(self, hsv: Tuple[float, float, float]) -> bool:
        """Determine if a color is neutral (low saturation)."""
        return hsv[1] < 0.15  # Saturation threshold for neutral colors
    
    def _calculate_hierarchy_confidence(self, color_analysis: Dict[str, Any], 
                                      prominences: List[ColorProminence]) -> float:
        """Calculate confidence in the generated hierarchy."""
        if not prominences:
            return 0.0
        
        # Factors that increase confidence:
        # 1. Clear prominence differences
        # 2. Good mix of neutral and vibrant colors
        # 3. Reasonable color distribution
        
        prominence_scores = [p.prominence_score for p in prominences]
        
        # Calculate prominence spread
        if len(prominence_scores) > 1:
            prominence_spread = max(prominence_scores) - min(prominence_scores)
        else:
            prominence_spread = 0
        
        # Count color types
        neutral_count = sum(1 for analysis in color_analysis.values() 
                          if analysis['is_neutral'])
        vibrant_count = sum(1 for analysis in color_analysis.values() 
                          if analysis['is_vibrant'])
        
        # Calculate confidence factors
        spread_factor = min(prominence_spread, 1.0)  # Max 1.0
        balance_factor = min(neutral_count + vibrant_count, 3) / 3  # Prefer some variety
        
        confidence = (spread_factor * 0.6 + balance_factor * 0.4)
        return min(confidence, 1.0)