"""
ColorExtractor service for extracting dominant colors from brand assets.

This module implements advanced color extraction using K-means clustering,
image preprocessing, and confidence scoring for the Dynamic Event Theming System.
"""

import os
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from io import BytesIO
import tempfile

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from colorthief import ColorThief
import colorsys

logger = logging.getLogger(__name__)


@dataclass
class ExtractedColor:
    """Represents an extracted color with metadata."""
    color: str  # Hex color code
    rgb: Tuple[int, int, int]  # RGB values
    confidence: float  # Confidence score 0-1
    frequency: float  # Frequency in image 0-1
    name: Optional[str] = None  # Human-readable color name


@dataclass
class ImageProperties:
    """Properties of the analyzed image."""
    width: int
    height: int
    format: str
    mode: str
    has_transparency: bool
    dominant_colors_count: int
    noise_level: float
    contrast_level: float


@dataclass
class ColorExtractionResult:
    """Result of color extraction process."""
    colors: List[ExtractedColor]
    image_properties: ImageProperties
    processing_time_ms: int
    algorithm_used: str
    confidence_score: float
    diversity_score: float
    metadata: Dict[str, Any]


class ColorExtractor:
    """
    Advanced color extraction engine using K-means clustering and image processing.
    
    Features:
    - K-means clustering for dominant color extraction
    - Support for PNG, JPG, JPEG, SVG, and WebP formats
    - Confidence scoring system for extracted colors
    - Image preprocessing (resize, noise reduction, transparent pixel handling)
    - Multiple extraction algorithms with fallback
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {'PNG', 'JPEG', 'JPG', 'WEBP', 'SVG'}
    
    # Default parameters
    DEFAULT_NUM_COLORS = 5
    MAX_IMAGE_SIZE = (800, 800)  # Resize large images for performance
    MIN_CONFIDENCE_THRESHOLD = 0.1
    
    # Color filtering thresholds
    WHITE_THRESHOLD = 240  # RGB values above this are considered white/near-white
    BLACK_THRESHOLD = 15   # RGB values below this are considered black/near-black
    MIN_COLOR_DISTANCE = 30  # Minimum distance between colors to avoid duplicates
    
    def __init__(self, num_colors: int = DEFAULT_NUM_COLORS):
        """
        Initialize ColorExtractor.
        
        Args:
            num_colors: Number of dominant colors to extract
        """
        self.num_colors = num_colors
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def extract_colors(self, image_path: str, algorithm: str = 'kmeans') -> ColorExtractionResult:
        """
        Extract dominant colors from brand asset.
        
        Args:
            image_path: Path to the image file
            algorithm: Extraction algorithm ('kmeans', 'colorthief', 'hybrid')
            
        Returns:
            ColorExtractionResult with extracted colors and metadata
            
        Raises:
            ValueError: If image format is not supported
            FileNotFoundError: If image file doesn't exist
            Exception: For other processing errors
        """
        import time
        start_time = time.time()
        
        try:
            # Validate and load image
            image = self._load_and_validate_image(image_path)
            image_properties = self._analyze_image_properties(image)
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract colors using specified algorithm
            if algorithm == 'kmeans':
                colors = self._extract_colors_kmeans(processed_image)
            elif algorithm == 'colorthief':
                colors = self._extract_colors_colorthief(image_path)
            elif algorithm == 'hybrid':
                colors = self._extract_colors_hybrid(processed_image, image_path)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            # Calculate confidence and diversity scores
            confidence_score = self._calculate_overall_confidence(colors)
            diversity_score = self._calculate_color_diversity(colors)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return ColorExtractionResult(
                colors=colors,
                image_properties=image_properties,
                processing_time_ms=processing_time,
                algorithm_used=algorithm,
                confidence_score=confidence_score,
                diversity_score=diversity_score,
                metadata={
                    'num_colors_requested': self.num_colors,
                    'num_colors_extracted': len(colors),
                    'preprocessing_applied': True,
                    'image_resized': image.size != processed_image.size
                }
            )
            
        except Exception as e:
            self.logger.error(f"Color extraction failed for {image_path}: {str(e)}")
            raise
    
    def _load_and_validate_image(self, image_path: str) -> Image.Image:
        """Load and validate image file."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            image = Image.open(image_path)
            
            # Check format support
            if image.format not in self.SUPPORTED_FORMATS:
                supported = ', '.join(self.SUPPORTED_FORMATS)
                raise ValueError(
                    f"Unsupported image format: {image.format}. "
                    f"Supported formats: {supported}"
                )
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                # Handle transparency by creating white background
                if image.mode == 'P':
                    image = image.convert('RGBA')
                
                if 'transparency' in image.info or image.mode in ('RGBA', 'LA'):
                    # Create white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'LA':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                    image = background
                else:
                    image = image.convert('RGB')
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            raise Exception(f"Failed to load image {image_path}: {str(e)}")
    
    def _analyze_image_properties(self, image: Image.Image) -> ImageProperties:
        """Analyze image properties for better extraction."""
        # Check for transparency
        has_transparency = (
            image.mode in ('RGBA', 'LA') or 
            'transparency' in image.info
        )
        
        # Convert to numpy array for analysis
        img_array = np.array(image)
        
        # Calculate contrast level
        gray = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
        contrast_level = float(np.std(gray) / 255.0)
        
        # Estimate noise level (simplified)
        noise_level = float(np.std(np.diff(gray.flatten())) / 255.0)
        
        # Count unique colors (approximation)
        unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0))
        
        return ImageProperties(
            width=image.width,
            height=image.height,
            format=image.format or 'Unknown',
            mode=image.mode,
            has_transparency=has_transparency,
            dominant_colors_count=min(unique_colors, 50),  # Cap for performance
            noise_level=noise_level,
            contrast_level=contrast_level
        )
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better color extraction."""
        processed = image.copy()
        
        # Resize if too large
        if processed.size[0] > self.MAX_IMAGE_SIZE[0] or processed.size[1] > self.MAX_IMAGE_SIZE[1]:
            processed.thumbnail(self.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            self.logger.debug(f"Resized image from {image.size} to {processed.size}")
        
        # Apply noise reduction
        processed = processed.filter(ImageFilter.MedianFilter(size=3))
        
        # Enhance contrast slightly
        enhancer = ImageEnhance.Contrast(processed)
        processed = enhancer.enhance(1.1)
        
        return processed
    
    def _extract_colors_kmeans(self, image: Image.Image) -> List[ExtractedColor]:
        """Extract colors using K-means clustering."""
        # Convert image to numpy array
        img_array = np.array(image)
        pixels = img_array.reshape(-1, 3)
        
        # Remove white and near-white pixels
        non_white_mask = np.any(pixels < self.WHITE_THRESHOLD, axis=1)
        non_black_mask = np.any(pixels > self.BLACK_THRESHOLD, axis=1)
        valid_mask = non_white_mask & non_black_mask
        
        if np.sum(valid_mask) < 100:  # Not enough valid pixels
            self.logger.warning("Not enough non-white/non-black pixels, using all pixels")
            valid_pixels = pixels
        else:
            valid_pixels = pixels[valid_mask]
        
        # Determine optimal number of clusters
        n_clusters = min(self.num_colors, len(np.unique(valid_pixels, axis=0)))
        if n_clusters < 2:
            n_clusters = 2
        
        # Apply K-means clustering
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
            max_iter=300
        )
        
        try:
            kmeans.fit(valid_pixels)
            cluster_centers = kmeans.cluster_centers_
            labels = kmeans.labels_
            
            # Calculate color frequencies and confidence scores
            colors = []
            unique_labels, counts = np.unique(labels, return_counts=True)
            total_pixels = len(labels)
            
            for i, (label, count) in enumerate(zip(unique_labels, counts)):
                rgb = tuple(map(int, cluster_centers[label]))
                frequency = count / total_pixels
                
                # Calculate confidence based on cluster quality
                cluster_pixels = valid_pixels[labels == label]
                if len(cluster_pixels) > 1:
                    # Intra-cluster distance (lower is better)
                    center = cluster_centers[label]
                    distances = np.linalg.norm(cluster_pixels - center, axis=1)
                    avg_distance = np.mean(distances)
                    confidence = max(0.1, 1.0 - (avg_distance / 255.0))
                else:
                    confidence = 0.5
                
                # Boost confidence for more frequent colors
                confidence = min(1.0, confidence + (frequency * 0.3))
                
                if confidence >= self.MIN_CONFIDENCE_THRESHOLD:
                    colors.append(ExtractedColor(
                        color=self._rgb_to_hex(rgb),
                        rgb=rgb,
                        confidence=confidence,
                        frequency=frequency,
                        name=self._get_color_name(rgb)
                    ))
            
            # Sort by confidence and frequency
            colors.sort(key=lambda c: (c.confidence * 0.7 + c.frequency * 0.3), reverse=True)
            
            # Remove similar colors
            colors = self._remove_similar_colors(colors)
            
            return colors[:self.num_colors]
            
        except Exception as e:
            self.logger.error(f"K-means clustering failed: {str(e)}")
            # Fallback to simple color extraction
            return self._extract_colors_simple(image)
    
    def _extract_colors_colorthief(self, image_path: str) -> List[ExtractedColor]:
        """Extract colors using ColorThief library."""
        try:
            color_thief = ColorThief(image_path)
            
            # Get dominant color
            dominant_color = color_thief.get_color(quality=1)
            
            # Get color palette
            palette = color_thief.get_palette(color_count=self.num_colors, quality=1)
            
            colors = []
            for i, rgb in enumerate(palette):
                # Higher confidence for earlier colors (more dominant)
                confidence = max(0.3, 1.0 - (i * 0.15))
                frequency = max(0.1, 1.0 - (i * 0.1))  # Approximate frequency
                
                colors.append(ExtractedColor(
                    color=self._rgb_to_hex(rgb),
                    rgb=rgb,
                    confidence=confidence,
                    frequency=frequency,
                    name=self._get_color_name(rgb)
                ))
            
            return colors
            
        except Exception as e:
            self.logger.error(f"ColorThief extraction failed: {str(e)}")
            # Fallback to K-means
            image = self._load_and_validate_image(image_path)
            return self._extract_colors_kmeans(image)
    
    def _extract_colors_hybrid(self, image: Image.Image, image_path: str) -> List[ExtractedColor]:
        """Extract colors using hybrid approach (K-means + ColorThief)."""
        try:
            # Get results from both methods
            kmeans_colors = self._extract_colors_kmeans(image)
            colorthief_colors = self._extract_colors_colorthief(image_path)
            
            # Combine and deduplicate
            all_colors = kmeans_colors + colorthief_colors
            unique_colors = self._remove_similar_colors(all_colors)
            
            # Re-score based on consensus
            for color in unique_colors:
                # Boost confidence if color appears in both methods
                similar_count = sum(1 for c in all_colors if self._color_distance(color.rgb, c.rgb) < 30)
                if similar_count > 1:
                    color.confidence = min(1.0, color.confidence * 1.2)
            
            # Sort and return top colors
            unique_colors.sort(key=lambda c: c.confidence, reverse=True)
            return unique_colors[:self.num_colors]
            
        except Exception as e:
            self.logger.error(f"Hybrid extraction failed: {str(e)}")
            return self._extract_colors_kmeans(image)
    
    def _extract_colors_simple(self, image: Image.Image) -> List[ExtractedColor]:
        """Simple fallback color extraction."""
        # Get most common colors
        colors = image.getcolors(maxcolors=256*256*256)
        if not colors:
            return []
        
        # Sort by frequency
        colors.sort(key=lambda x: x[0], reverse=True)
        
        extracted = []
        total_pixels = sum(count for count, _ in colors)
        
        for count, rgb in colors[:self.num_colors]:
            if isinstance(rgb, int):  # Grayscale
                rgb = (rgb, rgb, rgb)
            
            frequency = count / total_pixels
            confidence = min(1.0, frequency * 2)  # Simple confidence based on frequency
            
            extracted.append(ExtractedColor(
                color=self._rgb_to_hex(rgb),
                rgb=rgb,
                confidence=confidence,
                frequency=frequency,
                name=self._get_color_name(rgb)
            ))
        
        return extracted
    
    def _remove_similar_colors(self, colors: List[ExtractedColor]) -> List[ExtractedColor]:
        """Remove colors that are too similar to each other."""
        if not colors:
            return colors
        
        unique_colors = [colors[0]]  # Keep the first color
        
        for color in colors[1:]:
            is_unique = True
            for existing in unique_colors:
                if self._color_distance(color.rgb, existing.rgb) < self.MIN_COLOR_DISTANCE:
                    is_unique = False
                    # Keep the one with higher confidence
                    if color.confidence > existing.confidence:
                        unique_colors.remove(existing)
                        unique_colors.append(color)
                    break
            
            if is_unique:
                unique_colors.append(color)
        
        return unique_colors
    
    def _color_distance(self, rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two RGB colors."""
        return np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))
    
    def _calculate_overall_confidence(self, colors: List[ExtractedColor]) -> float:
        """Calculate overall confidence score for the extraction."""
        if not colors:
            return 0.0
        
        # Weighted average of individual confidences
        weights = [c.frequency for c in colors]
        if sum(weights) == 0:
            return np.mean([c.confidence for c in colors])
        
        weighted_confidence = sum(c.confidence * w for c, w in zip(colors, weights)) / sum(weights)
        return min(1.0, weighted_confidence)
    
    def _calculate_color_diversity(self, colors: List[ExtractedColor]) -> float:
        """Calculate color diversity score (0-1, higher is more diverse)."""
        if len(colors) < 2:
            return 0.0
        
        # Calculate average distance between all color pairs
        distances = []
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                distance = self._color_distance(colors[i].rgb, colors[j].rgb)
                distances.append(distance)
        
        if not distances:
            return 0.0
        
        # Normalize to 0-1 scale (max possible distance is ~441 for RGB)
        avg_distance = np.mean(distances)
        diversity_score = min(1.0, avg_distance / 200.0)  # Normalize to reasonable range
        
        return diversity_score
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color code."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _get_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Get human-readable color name (simplified)."""
        r, g, b = rgb
        
        # Convert to HSV for better color classification
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        h = h * 360  # Convert to degrees
        
        # Simple color naming based on HSV
        if s < 0.1:  # Low saturation - grayscale
            if v < 0.2:
                return "Black"
            elif v < 0.4:
                return "Dark Gray"
            elif v < 0.6:
                return "Gray"
            elif v < 0.8:
                return "Light Gray"
            else:
                return "White"
        
        # Color names based on hue
        if h < 15 or h >= 345:
            return "Red"
        elif h < 45:
            return "Orange"
        elif h < 75:
            return "Yellow"
        elif h < 105:
            return "Yellow Green"
        elif h < 135:
            return "Green"
        elif h < 165:
            return "Blue Green"
        elif h < 195:
            return "Cyan"
        elif h < 225:
            return "Blue"
        elif h < 255:
            return "Blue Violet"
        elif h < 285:
            return "Violet"
        elif h < 315:
            return "Magenta"
        else:
            return "Pink"
    
    def analyze_image_properties(self, image_path: str) -> ImageProperties:
        """
        Analyze image characteristics for better extraction.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            ImageProperties with detailed image analysis
        """
        image = self._load_and_validate_image(image_path)
        return self._analyze_image_properties(image)
    
    def calculate_confidence_scores(self, colors: List[ExtractedColor]) -> List[float]:
        """
        Score extracted colors based on suitability for theming.
        
        Args:
            colors: List of extracted colors
            
        Returns:
            List of confidence scores (0-1)
        """
        return [color.confidence for color in colors]


# Utility functions for external use
def extract_colors_from_file(
    image_path: str, 
    num_colors: int = 5, 
    algorithm: str = 'kmeans'
) -> ColorExtractionResult:
    """
    Convenience function to extract colors from an image file.
    
    Args:
        image_path: Path to the image file
        num_colors: Number of colors to extract
        algorithm: Extraction algorithm to use
        
    Returns:
        ColorExtractionResult with extracted colors and metadata
    """
    extractor = ColorExtractor(num_colors=num_colors)
    return extractor.extract_colors(image_path, algorithm=algorithm)


def is_supported_format(image_path: str) -> bool:
    """
    Check if image format is supported.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if format is supported, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            return img.format in ColorExtractor.SUPPORTED_FORMATS
    except Exception:
        return False


def get_supported_formats() -> List[str]:
    """Get list of supported image formats."""
    return list(ColorExtractor.SUPPORTED_FORMATS)