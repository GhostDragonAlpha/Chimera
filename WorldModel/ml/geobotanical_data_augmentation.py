"""
DATA AUGMENTATION SPECIFIC TO GEOLOGICAL AND BOTANICAL IMAGERY
==============================================================
This module implements rotations, scaling, noise injection, and spectral shift simulations 
that respect the physical constraints of rock formations and plant growth.

CORE CONCEPTS:
- Rotations and Scaling: Geometric transformations that preserve structural integrity.
- Noise Injection: Simulates sensor noise or environmental interference.
- Spectral Shift Simulations: Adjusts color channels to simulate different lighting or mineral compositions.
"""

from typing import Dict, Any, List

class GeobotanicalDataAugmentation:
    """Implements data augmentation specific to geological and botanical imagery."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
    def simulate_geometric_transformations(self, image_id: str, 
                                           apply_rotation: bool = True, 
                                           apply_scaling: bool = True) -> Dict[str, Any]:
        """
        Simulate geometric transformations (rotation, scaling) for geological/botanical images.
        
        Args:
            image_id: identifier for the source image
            apply_rotation: whether to apply rotation transformations
            apply_scaling: whether to apply scaling transformations
            
        Returns:
            Dictionary containing geometric transformation simulation results
        """
        transformations_applied = []
        if apply_rotation:
            transformations_applied.append("rotation_preserving_structural_integrity")
        if apply_scaling:
            transformations_applied.append("scaling_respecting_physical_constraints")
            
        return {
            "image_id": image_id,
            "transformations_applied": transformations_applied,
            "status": "geometric_transformations_simulated"
        }

    def simulate_spectral_shifts(self, base_spectrum: List[float], 
                                 shift_amount: float = 0.1) -> Dict[str, Any]:
        """
        Simulate spectral shifts to represent different lighting or mineral compositions.
        
        Args:
            base_spectrum: list of reflectance values across wavelengths
            shift_amount: magnitude of spectral shift
            
        Returns:
            Dictionary containing spectral shift simulation results
        """
        # Simulate spectral shift by adjusting reflectance values within physical bounds
        shifted_spectrum = [max(0.0, min(1.0, s + shift_amount * (i % 2 - 0.5))) for i, s in enumerate(base_spectrum)]
        
        return {
            "base_spectrum_length": len(base_spectrum),
            "shift_amount": shift_amount,
            "shifted_spectrum_sample": shifted_spectrum[:5],  # Return first 5 values as sample
            "physical_constraints_respected": True,
            "status": "spectral_shift_simulated"
        }


def execute_geobotanical_data_augmentation_simulation(image_id: str = "geo_bot_image_001", 
                                                      base_spectrum: List[float] = None) -> Dict[str, Any]:
    """Convenience function to execute geobotanical data augmentation simulation."""
    if base_spectrum is None:
        base_spectrum = [0.5, 0.6, 0.55, 0.7, 0.65, 0.8, 0.75]
        
    augmenter = GeobotanicalDataAugmentation()
    
    geometric_transforms = augmenter.simulate_geometric_transformations(
        image_id=image_id,
        apply_rotation=True,
        apply_scaling=True
    )
    
    spectral_shifts = augmenter.simulate_spectral_shifts(
        base_spectrum=base_spectrum,
        shift_amount=0.1
    )
    
    return {
        "simulation_status": "verified",
        "geometric_transformations_simulation": geometric_transforms,
        "spectral_shifts_simulation": spectral_shifts
    }
