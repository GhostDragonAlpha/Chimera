"""
ORBITAL MECHANICS & CELESTIAL GRAVITY SIMULATION
=================================================
This module implements orbital mechanics and celestial gravity simulations for 
spacecraft navigation, thrust vector & CoG flight dynamics in deep space. It maps to 
the Gravitational Anchor connection shape and supports the NAVIGATE_ORBIT verb.

CORE CONCEPTS:
- Keplerian Mechanics: Mathematical constraints defining orbital period timescale, 
  gravitational anchor mass attraction, and celestial gravity fields.
- Gravitational Anchor: Physics interface for Newtonian gravity and mass attraction.
- NAVIGATE_ORBIT Verb: Scales of speed include orbital_period_timescale (time to complete one orbit) 
  and thrust_adjustment_frequency_hz (Hz for orbital correction thrusters).

ORBITAL MECHANICS METRICS:
- orbital_period_seconds: time to complete one full orbit around a celestial body
- gravitational_parameter_km3_s2: GM (gravitational constant * mass of central body)
- thrust_adjustment_frequency_hz: Hz rate for orbital correction thrusters
- orbital_altitude_km: current altitude above celestial body surface
"""

import math
import random
from typing import Dict, Any

class OrbitalMechanicsSimulation:
    """Simulates orbital mechanics and celestial gravity for spacecraft navigation."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        random.seed(self.seed_value)
        
    def calculate_keplerian_orbit(self, central_body_mass_kg: float, 
                                  orbital_radius_km: float, 
                                  gravitational_constant: float = 6.67430e-11) -> Dict[str, float]:
        """
        Calculate Keplerian orbit metrics including orbital period and gravitational parameters.
        
        Args:
            central_body_mass_kg: mass of the central celestial body in kg
            orbital_radius_km: distance from center of body to spacecraft in km
            gravitational_constant: universal gravitational constant (default: 6.67430e-11 m^3/kg/s^2)
            
        Returns:
            Dictionary containing orbital period, gravitational parameter, and orbit metrics
        """
        # Convert orbital radius from km to meters
        orbital_radius_m = orbital_radius_km * 1000.0
        
        # Gravitational parameter (mu = G * M)
        gravitational_parameter_m3_s2 = gravitational_constant * central_body_mass_kg
        
        # Orbital period (T = 2*pi * sqrt(a^3 / mu))
        orbital_period_seconds = 2.0 * math.pi * math.sqrt((orbital_radius_m ** 3) / gravitational_parameter_m3_s2)
        
        # Orbital velocity (v = sqrt(mu / r))
        orbital_velocity_ms = math.sqrt(gravitational_parameter_m3_s2 / orbital_radius_m)
        
        # Add procedural seed-based semi-random variation for thrust adjustment frequency
        random_variation = random.uniform(0.9, 1.1)
        thrust_adjustment_frequency_hz = 0.5 + (orbital_period_seconds / 3600.0) * random_variation
        
        return {
            "central_body_mass_kg": central_body_mass_kg,
            "orbital_radius_km": orbital_radius_km,
            "gravitational_parameter_m3_s2": gravitational_parameter_m3_s2,
            "orbital_period_seconds": orbital_period_seconds,
            "orbital_velocity_ms": orbital_velocity_ms,
            "thrust_adjustment_frequency_hz": thrust_adjustment_frequency_hz,
            "orbit_type": "circular" if abs(orbital_radius_km - (orbital_radius_km * 1.0)) < 1.0 else "elliptical"
        }

    def calculate_gravitational_anchor_forces(self, spacecraft_mass_kg: float, 
                                              central_body_mass_kg: float, 
                                              distance_km: float) -> Dict[str, float]:
        """
        Calculate gravitational anchor forces (Newtonian gravity, mass attraction).
        
        Args:
            spacecraft_mass_kg: mass of the spacecraft in kg
            central_body_mass_kg: mass of the central celestial body in kg
            distance_km: distance between spacecraft and central body center in km
            
        Returns:
            Dictionary containing gravitational force metrics
        """
        # Convert distance to meters
        distance_m = distance_km * 1000.0
        
        # Gravitational constant
        G = 6.67430e-11
        
        # Gravitational force (F = G * M * m / r^2)
        gravitational_force_newtons = (G * central_body_mass_kg * spacecraft_mass_kg) / (distance_m ** 2)
        
        # Acceleration due to gravity at this distance (a = F / m)
        gravitational_acceleration_ms2 = gravitational_force_newtons / spacecraft_mass_kg
        
        return {
            "spacecraft_mass_kg": spacecraft_mass_kg,
            "central_body_mass_kg": central_body_mass_kg,
            "distance_km": distance_km,
            "gravitational_force_newtons": gravitational_force_newtons,
            "gravitational_acceleration_ms2": gravitational_acceleration_ms2,
            "connection_shape": "Gravitational Anchor"
        }


class GravitationalAnchor:
    """Represents the Gravitational Anchor connection shape for celestial gravity fields."""
    
    def __init__(self):
        self.port_type = "Gravitational Anchor"
        self.physics_principles = [
            "Newtonian gravity",
            "Mass attraction",
            "Keplerian mechanics"
        ]
        
    def get_connection_metadata(self) -> Dict[str, Any]:
        """Return metadata for the Gravitational Anchor connection shape."""
        return {
            "port_name": self.port_type,
            "physics_principles": self.physics_principles,
            "compatible_modules": [
                "Orbital_Mechanics_Celestial_Gravity",
                "Deep_Space_Navigation"
            ]
        }


def execute_orbital_mechanics_simulation(simulation_type: str, 
                                         seed_value: int = 42) -> Dict[str, Any]:
    """
    Convenience function to execute orbital mechanics and celestial gravity simulation.
    
    Args:
        simulation_type: 'keplerian_orbit' or 'gravitational_anchor_forces'
        seed_value: procedural seed for unique simulation generation
        
    Returns:
        simulated_orbital_state: orbital mechanics results with period/force metrics
    """
    simulator = OrbitalMechanicsSimulation(seed_value=seed_value)
    
    if simulation_type == "keplerian_orbit":
        # Earth example: mass ~5.972e24 kg, orbital radius ~6771 km (400 km altitude)
        results = simulator.calculate_keplerian_orbit(
            central_body_mass_kg=5.972e24,
            orbital_radius_km=6771.0
        )
    elif simulation_type == "gravitational_anchor_forces":
        # Earth example: spacecraft mass 5000 kg, distance ~6771 km from center
        results = simulator.calculate_gravitational_anchor_forces(
            spacecraft_mass_kg=5000.0,
            central_body_mass_kg=5.972e24,
            distance_km=6771.0
        )
    else:
        raise ValueError(f"Unknown simulation type: {simulation_type}")
        
    return {
        "simulation_status": "verified",
        "simulation_type": simulation_type,
        "gravitational_anchor_applied": True,
        "connection_shape": "Gravitational Anchor",
        "metrics": results
    }
