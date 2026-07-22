"""
GROW_ECOSYSTEM SIMULATION MODULE
=================================
This module implements the GROW_ECOSYSTEM verb to simulate mycelial network structures 
and leaf venation networks driven by environmental data (soil moisture, light interception/PAR).

CORE CONCEPTS:
- GROW_ECOSYSTEM Verb: Drives biological network growth patterns including mycelial networks 
  and reticulate/campylodromous leaf venation.
- Environmental Data Drivers: 
  - Soil moisture maps to the Hydrodynamic/Hydration Port connection shape.
  - Light interception/PAR maps to the Spectral/Energy Port connection shape with "Red Edge" spectral signature integration.
- CONNECT Verb Parameters: connection_establishment_time_ms and interface_handshake_speed map to 
  the LEGO puzzle connection shapes (Spectral/Energy Port, Hydrodynamic/Hydration Port).
- GROW Verb Growth Timescale: seconds for procedural generation to frames for visual emergence.

GROW_ECOSYSTEM METRICS:
- growth_timescale_seconds: time for procedural generation to frames for visual emergence
- soil_moisture_level: 0.0 to 1.0 mapping to Hydrodynamic/Hydration Port
- light_interception_PAR: photosynthetically active radiation mapping to Spectral/Energy Port
- connection_establishment_time_ms: ms for network node connection establishment
- interface_handshake_speed: speed of spectral/hydration port handshake
"""

import math
import random
from typing import Dict, Any

class GrowEcosystemSimulation:
    """Simulates GROW_ECOSYSTEM verb for mycelial networks and leaf venation driven by environmental data."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        random.seed(self.seed_value)
        
    def simulate_mycelial_network_growth(self, soil_moisture_level: float, 
                                         growth_timescale_seconds: float) -> Dict[str, Any]:
        """
        Simulate mycelial network structure growth driven by soil moisture.
        
        Args:
            soil_moisture_level: 0.0 to 1.0 mapping to Hydrodynamic/Hydration Port
            growth_timescale_seconds: time for procedural generation to frames for visual emergence
            
        Returns:
            Dictionary containing mycelial network growth metrics
        """
        # Mycelial network expansion rate based on soil moisture
        expansion_rate = 0.5 + (soil_moisture_level * 0.5)
        
        # Network node connection establishment time
        connection_establishment_time_ms = int(100 - (soil_moisture_level * 50))
        
        # Interface handshake speed for Hydrodynamic/Hydration Port
        interface_handshake_speed = 0.8 + (soil_moisture_level * 0.2)
        
        return {
            "network_type": "mycelial",
            "soil_moisture_level": soil_moisture_level,
            "growth_timescale_seconds": growth_timescale_seconds,
            "expansion_rate": expansion_rate,
            "connection_establishment_time_ms": connection_establishment_time_ms,
            "interface_handshake_speed": interface_handshake_speed,
            "connection_shape": "Hydrodynamic/Hydration Port"
        }

    def simulate_leaf_venation_growth(self, light_interception_PAR: float, 
                                      growth_timescale_seconds: float) -> Dict[str, Any]:
        """
        Simulate reticulate/campylodromous leaf venation network growth driven by light interception/PAR.
        
        Args:
            light_interception_PAR: photosynthetically active radiation mapping to Spectral/Energy Port
            growth_timescale_seconds: time for procedural generation to frames for visual emergence
            
        Returns:
            Dictionary containing leaf venation growth metrics
        """
        # Leaf venation density based on PAR
        venation_density = 0.6 + (light_interception_PAR * 0.4)
        
        # Network node connection establishment time
        connection_establishment_time_ms = int(150 - (light_interception_PAR * 75))
        
        # Interface handshake speed for Spectral/Energy Port with "Red Edge" signature
        interface_handshake_speed = 0.7 + (light_interception_PAR * 0.3)
        
        return {
            "network_type": "leaf_venation_reticulate_campylodromous",
            "light_interception_PAR": light_interception_PAR,
            "growth_timescale_seconds": growth_timescale_seconds,
            "venation_density": venation_density,
            "connection_establishment_time_ms": connection_establishment_time_ms,
            "interface_handshake_speed": interface_handshake_speed,
            "connection_shape": "Spectral/Energy Port",
            "spectral_signature": "Red Edge"
        }


def execute_grow_ecosystem_simulation(simulation_type: str, 
                                      soil_moisture_level: float = 0.75,
                                      light_interception_PAR: float = 0.85,
                                      growth_timescale_seconds: float = 5.0,
                                      seed_value: int = 42) -> Dict[str, Any]:
    """
    Convenience function to execute GROW_ECOSYSTEM simulation.
    
    Args:
        simulation_type: 'mycelial_network' or 'leaf_venation'
        soil_moisture_level: 0.0 to 1.0 for mycelial networks
        light_interception_PAR: 0.0 to 1.0 for leaf venation
        growth_timescale_seconds: time for procedural generation to frames for visual emergence
        seed_value: procedural seed for unique simulation generation
        
    Returns:
        grow_ecosystem_results: GROW_ECOSYSTEM simulation results with network metrics
    """
    simulator = GrowEcosystemSimulation(seed_value=seed_value)
    
    if simulation_type == "mycelial_network":
        results = simulator.simulate_mycelial_network_growth(
            soil_moisture_level=soil_moisture_level,
            growth_timescale_seconds=growth_timescale_seconds
        )
    elif simulation_type == "leaf_venation":
        results = simulator.simulate_leaf_venation_growth(
            light_interception_PAR=light_interception_PAR,
            growth_timescale_seconds=growth_timescale_seconds
        )
    else:
        raise ValueError(f"Unknown simulation type: {simulation_type}")
        
    return {
        "simulation_status": "verified",
        "verb_applied": "GROW_ECOSYSTEM",
        "simulation_type": simulation_type,
        "growth_timescale_seconds": growth_timescale_seconds,
        "metrics": results
    }
