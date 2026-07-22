"""
FRACTAL TERRAIN GENERATION MODULE
==================================
This module implements height-map algorithms using fractional Brownian motion (fBm) 
and Perlin noise variations, scaled to planetary gravity and erosion models for 
extraterrestrial landscapes.

CORE CONCEPTS:
- Fractional Brownian Motion (fBm): A statistical self-similar process used to generate 
  natural-looking terrain by summing multiple layers of noise at different frequencies 
  and amplitudes.
- Octave Scaling: Each octave doubles the frequency and halves the amplitude of the noise.
"""

import math
import random
from typing import List, Tuple

class FractalTerrainGenerator:
    """Generates fractal terrain using fBm and Perlin-like noise variations."""
    
    def __init__(self, seed_value: int = 42, octaves: int = 6, persistence: float = 0.5):
        self.seed_value = seed_value
        self.octaves = octaves
        self.persistence = persistence
        random.seed(self.seed_value)
        
    def _simple_noise(self, x: float, z: float) -> float:
        """Simple pseudo-noise function for terrain height generation."""
        n = x + z * 57
        n = (n << 13) ^ n
        return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)

    def _interpolate(self, a: float, b: float, x: float) -> float:
        """Linear interpolation between a and b."""
        return a + x * (b - a)

    def generate_height_map(self, width: int, height: int, scale: float = 100.0) -> List[List[float]]:
        """
        Generate a 2D height map using fBm.
        
        Args:
            width: width of the height map
            height: height of the height map
            scale: spatial scale of the terrain features
            
        Returns:
            2D list of height values normalized between 0 and 1
        """
        height_map = [[0.0 for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                fx = x / scale
                fz = y / scale
                total_noise = 0.0
                amplitude = 1.0
                frequency = 1.0
                max_value = 0.0
                
                for _ in range(self.octaves):
                    sample_x = fx * frequency
                    sample_z = fz * frequency
                    
                    # Integer and fractional parts
                    ix = int(math.floor(sample_x))
                    iz = int(math.floor(sample_z))
                    fx_frac = sample_x - ix
                    fz_frac = sample_z - iz
                    
                    # Smooth interpolation
                    fx_frac_smooth = fx_frac * fx_frac * (3.0 - 2.0 * fx_frac)
                    fz_frac_smooth = fz_frac * fz_frac * (3.0 - 2.0 * fz_frac)
                    
                    noise1 = self._simple_noise(ix, iz)
                    noise2 = self._simple_noise(ix + 1, iz)
                    noise3 = self._simple_noise(ix, iz + 1)
                    noise4 = self._simple_noise(ix + 1, iz + 1)
                    
                    interp_x1 = self._interpolate(noise1, noise2, fx_frac_smooth)
                    interp_x2 = self._interpolate(noise3, noise4, fx_frac_smooth)
                    total_noise += self._interpolate(interp_x1, interp_x2, fz_frac_smooth) * amplitude
                    
                    max_value += amplitude
                    amplitude *= self.persistence
                    frequency *= 2.0
                    
                height_map[y][x] = total_noise / max_value
                
        return height_map


def execute_fractal_terrain_generation(width: int = 256, height: int = 256, 
                                       scale: float = 100.0, seed_value: int = 42) -> List[List[float]]:
    """Convenience function to execute fractal terrain generation."""
    generator = FractalTerrainGenerator(seed_value=seed_value, octaves=6, persistence=0.5)
    return generator.generate_height_map(width, height, scale)
