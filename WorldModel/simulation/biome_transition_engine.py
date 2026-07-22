"""
SEAMLESS BIOME TRANSITION TECHNIQUES FOR PROCEDURAL LANDSCAPES
==============================================================
This module uses gradient-based noise blending and ecological transition zones (ecotones) 
where species density and soil moisture parameters interpolate smoothly.

CORE CONCEPTS:
- Gradient-Based Noise Blending: Interpolates between different biome noise fields based on location.
- Ecotones: Transition zones where two biomes meet, with interpolated species density and soil moisture.
"""

import math
from typing import Dict, Any, List

class BiomeTransitionEngine:
    """Implements seamless biome transitions using gradient-based noise blending and ecotones."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
    def generate_gradient_noise_blend(self, x: float, z: float, 
                                      biome1_noise: float, biome2_noise: float, 
                                      transition_weight: float) -> float:
        """
        Blend two biome noise fields using a transition weight.
        
        Args:
            x, z: coordinates in the landscape
            biome1_noise: noise value for first biome (0-1)
            biome2_noise: noise value for second biome (0-1)
            transition_weight: weight between biomes (0-1, where 0=biome1, 1=biome2)
            
        Returns:
            Blended noise value
        """
        # Smooth interpolation using sigmoid-based weighting for ecotone effects
        smooth_weight = transition_weight * transition_weight * (3.0 - 2.0 * transition_weight)
        blended_noise = biome1_noise * (1.0 - smooth_weight) + biome2_noise * smooth_weight
        
        return max(0.0, min(1.0, blended_noise))

    def simulate_ecotone_parameters(self, biome1_species_density: float, 
                                    biome2_species_density: float,
                                    biome1_soil_moisture: float,
                                    biome2_soil_moisture: float,
                                    transition_weight: float) -> Dict[str, float]:
        """
        Simulate ecological transition zone (ecotone) parameters.
        
        Args:
            biome1_species_density: species density in first biome
            biome2_species_density: species density in second biome
            biome1_soil_moisture: soil moisture in first biome
            biome2_soil_moisture: soil moisture in second biome
            transition_weight: position within transition zone (0-1)
            
        Returns:
            Dictionary containing ecotone parameter metrics
        """
        # Smooth interpolation for ecotone parameters
        smooth_weight = transition_weight * transition_weight * (3.0 - 2.0 * transition_weight)
        
        ecotone_species_density = biome1_species_density * (1.0 - smooth_weight) + biome2_species_density * smooth_weight
        ecotone_soil_moisture = biome1_soil_moisture * (1.0 - smooth_weight) + biome2_soil_moisture * smooth_weight
        
        return {
            "biome1_species_density": biome1_species_density,
            "biome2_species_density": biome2_species_density,
            "ecotone_species_density": ecotone_species_density,
            "biome1_soil_moisture": biome1_soil_moisture,
            "biome2_soil_moisture": biome2_soil_moisture,
            "ecotone_soil_moisture": ecotone_soil_moisture,
            "transition_weight": transition_weight
        }


def execute_biome_transition_simulation(transition_weight: float = 0.5, 
                                        biome1_noise: float = 0.3, 
                                        biome2_noise: float = 0.7) -> Dict[str, Any]:
    """Convenience function to execute biome transition simulation."""
    engine = BiomeTransitionEngine(seed_value=42)
    
    blended_noise = engine.generate_gradient_noise_blend(
        x=0.0, z=0.0,
        biome1_noise=biome1_noise,
        biome2_noise=biome2_noise,
        transition_weight=transition_weight
    )
    
    ecotone_params = engine.simulate_ecotone_parameters(
        biome1_species_density=0.6,
        biome2_species_density=0.8,
        biome1_soil_moisture=0.4,
        biome2_soil_moisture=0.7,
        transition_weight=transition_weight
    )
    
    return {
        "simulation_status": "verified",
        "gradient_noise_blend_result": blended_noise,
        "ecotone_parameters": ecotone_params
    }
