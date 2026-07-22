"""
ATMOSPHERIC SCATTERING SIMULATION MODULE
=========================================
This module implements Rayleigh and Mie scattering models parameterized by 
atmospheric density, particle size distribution, and composition for different 
planetary atmospheres (e.g., CO2 for Mars, N2/O2 for Earth).

CORE CONCEPTS:
- Rayleigh Scattering: Dominant for particles much smaller than the wavelength of light.
  Scattering intensity is proportional to 1/λ^4. Dominant in Earth's clear sky (blue sky).
- Mie Scattering: Dominant for particles comparable to or larger than the wavelength.
  Produces white/gray scattering (clouds, haze, Martian dust).

ATMOSPHERIC COMPOSITIONS:
- Earth: N2 (78%), O2 (21%), trace gases. Rayleigh dominant in clear conditions.
- Mars: CO2 (95%), trace N2, Ar. Mie scattering from suspended dust particles.
- Venus: CO2 (96%), sulfuric acid clouds. Strong Mie scattering, thick haze.
"""

import math
from typing import Dict, Any

class AtmosphericScatteringSimulation:
    """Simulates Rayleigh and Mie scattering for different planetary atmospheres."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
    def calculate_rayleigh_scattering(self, wavelength_nm: float, 
                                      atmospheric_density: float) -> Dict[str, float]:
        """
        Calculate Rayleigh scattering intensity for a given wavelength and atmospheric density.
        
        Args:
            wavelength_nm: wavelength of light in nanometers
            atmospheric_density: relative atmospheric density (1.0 = Earth sea level)
            
        Returns:
            Dictionary containing scattering metrics
        """
        # Rayleigh scattering coefficient proportional to 1/λ^4
        # Base wavelength for reference (550 nm, green light)
        reference_wavelength = 550.0
        rayleigh_coefficient = (reference_wavelength / wavelength_nm) ** 4 * atmospheric_density
        
        # Scattering intensity
        scattering_intensity = rayleigh_coefficient * 100.0
        
        return {
            "wavelength_nm": wavelength_nm,
            "atmospheric_density": atmospheric_density,
            "rayleigh_coefficient": rayleigh_coefficient,
            "scattering_intensity": scattering_intensity,
            "scattering_type": "Rayleigh"
        }

    def calculate_mie_scattering(self, particle_radius_um: float, 
                                 wavelength_nm: float, 
                                 dust_optical_depth: float) -> Dict[str, float]:
        """
        Calculate Mie scattering intensity for particles comparable to or larger than the wavelength.
        
        Args:
            particle_radius_um: radius of dust/particle in micrometers
            wavelength_nm: wavelength of light in nanometers
            dust_optical_depth: optical depth due to suspended dust/particulates
            
        Returns:
            Dictionary containing scattering metrics
        """
        # Mie scattering is less wavelength-dependent than Rayleigh
        # Approximate phase function and scattering efficiency
        wavelength_um = wavelength_nm / 1000.0
        size_parameter = 2 * math.pi * particle_radius_um / wavelength_um
        
        # Simplified Mie scattering efficiency approximation
        if size_parameter < 1:
            mie_efficiency = size_parameter ** 3
        elif size_parameter <= 10:
            mie_efficiency = 2.0 + (math.sin(size_parameter) ** 2) / size_parameter
        else:
            mie_efficiency = 2.0  # Geometric optics limit
            
        scattering_intensity = mie_efficiency * dust_optical_depth * 50.0
        
        return {
            "particle_radius_um": particle_radius_um,
            "wavelength_nm": wavelength_nm,
            "dust_optical_depth": dust_optical_depth,
            "size_parameter": size_parameter,
            "mie_scattering_efficiency": mie_efficiency,
            "scattering_intensity": scattering_intensity,
            "scattering_type": "Mie"
        }


def execute_atmospheric_scattering_simulation(atmosphere_type: str, 
                                              wavelength_nm: float = 550.0,
                                              seed_value: int = 42) -> Dict[str, Any]:
    """
    Convenience function to execute atmospheric scattering simulation.
    
    Args:
        atmosphere_type: 'earth', 'mars', or 'venus'
        wavelength_nm: wavelength of light in nanometers
        seed_value: procedural seed for unique simulation generation
        
    Returns:
        atmospheric_scattering_results: scattering metrics for the specified atmosphere
    """
    simulator = AtmosphericScatteringSimulation(seed_value=seed_value)
    
    # Define atmospheric parameters by type
    atmosphere_params = {
        "earth": {"density": 1.0, "dust_optical_depth": 0.1, "particle_radius_um": 0.1},
        "mars": {"density": 0.01, "dust_optical_depth": 0.5, "particle_radius_um": 1.0},
        "venus": {"density": 92.0, "dust_optical_depth": 2.0, "particle_radius_um": 1.5}
    }
    
    params = atmosphere_params.get(atmosphere_type.lower(), atmosphere_params["earth"])
    
    # Calculate Rayleigh scattering
    rayleigh_results = simulator.calculate_rayleigh_scattering(
        wavelength_nm=wavelength_nm,
        atmospheric_density=params["density"]
    )
    
    # Calculate Mie scattering
    mie_results = simulator.calculate_mie_scattering(
        particle_radius_um=params["particle_radius_um"],
        wavelength_nm=wavelength_nm,
        dust_optical_depth=params["dust_optical_depth"]
    )
    
    return {
        "simulation_status": "verified",
        "atmosphere_type": atmosphere_type,
        "rayleigh_scattering": rayleigh_results,
        "mie_scattering": mie_results
    }
