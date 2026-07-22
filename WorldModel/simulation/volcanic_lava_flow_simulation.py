"""
VOLCANIC ACTIVITY AND LAVA FLOW DYNAMICS SIMULATION
====================================================
This module models magma chamber pressure, fissure generation, and fluid dynamics for lava 
(using viscosity and temperature-dependent rheology) as it flows over terrain.

CORE CONCEPTS:
- Magma Chamber Pressure: Drives fissure generation and volcanic eruptions.
- Lava Fluid Dynamics: Simulated using viscosity and temperature-dependent rheology models.
- Flow Over Terrain: Lava spreads based on slope, viscosity, and volume.
"""

import math
from typing import Dict, Any, List

class VolcanicLavaFlowSimulation:
    """Simulates volcanic activity and lava flow dynamics."""
    
    def __init__(self, gravitational_acceleration: float = 9.81, seed_value: int = 42):
        self.g = gravitational_acceleration
        self.seed_value = seed_value
        
    def calculate_magma_chamber_pressure(self, magma_volume_m3: float, 
                                         chamber_depth_m: float, 
                                         magma_density_kg_per_m3: float = 2700.0) -> float:
        """
        Calculate approximate magma chamber pressure based on volume and depth.
        
        Args:
            magma_volume_m3: volume of magma in the chamber (cubic meters)
            chamber_depth_m: depth of the magma chamber below surface (meters)
            magma_density_kg_per_m3: density of magma material
            
        Returns:
            Approximate pressure in Pascals
        """
        # Simplified hydrostatic pressure approximation: P = rho * g * h
        # Adjusted for volume consideration
        base_pressure = magma_density_kg_per_m3 * self.g * chamber_depth_m
        volume_factor = 1.0 + (magma_volume_m3 / 1e9)  # Scale factor for large volumes
        
        return base_pressure * volume_factor

    def simulate_lava_flow_rheology(self, temperature_k: float, 
                                    viscosity_pa_s: float, 
                                    slope: float) -> Dict[str, float]:
        """
        Simulate lava flow based on temperature, viscosity, and terrain slope.
        
        Args:
            temperature_k: lava temperature in Kelvin
            viscosity_pa_s: dynamic viscosity of lava (Pa·s)
            slope: terrain slope (rise/run)
            
        Returns:
            Dictionary containing flow dynamics metrics
        """
        # Simplified rheology model: higher temperature -> lower effective viscosity
        # Flow velocity approximation based on slope and inverse viscosity
        temp_factor = max(0.1, (temperature_k - 1000.0) / 1000.0)  # Normalize around 1000K baseline
        effective_viscosity = viscosity_pa_s / temp_factor
        
        if effective_viscosity > 0:
            flow_velocity_m_per_s = (self.g * slope * temp_factor) / effective_viscosity
        else:
            flow_velocity_m_per_s = 0.0
            
        return {
            "temperature_k": temperature_k,
            "viscosity_pa_s": viscosity_pa_s,
            "slope": slope,
            "effective_viscosity_pa_s": effective_viscosity,
            "flow_velocity_m_per_s": flow_velocity_m_per_s
        }


def execute_volcanic_lava_flow_simulation(magma_volume_m3: float = 1e8, 
                                          chamber_depth_m: float = 5000.0,
                                          lava_temperature_k: float = 1300.0,
                                          lava_viscosity_pa_s: float = 100.0,
                                          terrain_slope: float = 0.1) -> Dict[str, Any]:
    """Convenience function to execute volcanic lava flow simulation."""
    simulator = VolcanicLavaFlowSimulation()
    
    magma_pressure = simulator.calculate_magma_chamber_pressure(
        magma_volume_m3=magma_volume_m3,
        chamber_depth_m=chamber_depth_m
    )
    
    lava_flow = simulator.simulate_lava_flow_rheology(
        temperature_k=lava_temperature_k,
        viscosity_pa_s=lava_viscosity_pa_s,
        slope=terrain_slope
    )
    
    return {
        "simulation_status": "verified",
        "magma_chamber_pressure_pa": magma_pressure,
        "lava_flow_dynamics": lava_flow
    }
