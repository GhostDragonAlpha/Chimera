"""
UNIVERSAL SCALE HIERARCHY
=========================
This module maps out the specific celestial environments (Earth surface, atmosphere, 
orbit, deep space) and their corresponding physics modules for the exploration product/
universal simulation architecture.

HIERARCHY LEVELS:
Level 1: Energy Source / Sky -> Solar granulation + Night sky stellar distribution
         Physics Module: Radiative Transfer / Spectral Environment
         
Level 2: Matter Source / Ground -> Geological patterns + Physical dynamics
         Physics Module: Substrate/Geological Port, Rigid Body Dynamics
         
Level 3: Atmosphere / Fluid Dynamics -> River meanders, sand dunes, cloud formations
         Physics Module: Aerodynamic/Atmospheric Port, Fluid Dynamics & Buoyancy
         
Level 4: Orbit / Deep Space -> Orbital mechanics, celestial gravity, space environments
         Physics Module: Gravitational Anchor, Orbital Mechanics & Celestial Gravity

CONNECTION SHAPES (LEGO PUZZLE PHYSICS INTERFACES):
- Gravitational Anchor: Newtonian gravity, mass attraction — All modules snap to the planet's gravity field.
- Spectral/Energy Port: Light interception, "Red Edge" spectral signature, PAR distribution — Biological modules connect to Sky/Sun energy source.
- Hydrodynamic/Hydration Port: Buoyancy, fluid drag, water hydration absorption bands (1.4µm, 1.9µm) — Watercraft modules connect to River/Ocean surfaces; Root systems connect to soil moisture.
- Aerodynamic/Atmospheric Port: Lift, drag, thrust, airflow patterns (Bernoulli's principle) — Aircraft modules connect to the atmosphere/sky layer.
- Substrate/Geological Port: Mineral absorption, soil topography, friction coefficients — Building foundations, Tree roots, Character controllers connect to the Ground/Surface layer.

VERBS ASSOCIATED WITH EACH LEVEL:
Level 1 (Energy): SCAN (spectral analysis of sky/sun), GROW_ECOSYSTEM (energy-driven growth)
Level 2 (Matter): CONNECT (substrate connection shapes), GROW (root system anchoring)
Level 3 (Atmosphere/Fluid): BALANCE (aerodynamic stability), THRUST (fluid dynamics propulsion)
Level 4 (Orbit/Space): NAVIGATE_ORBIT (orbital mechanics, Keplerian calculations)
"""

from typing import Dict, List, Any

class UniversalScaleHierarchy:
    """Maps celestial environments to their corresponding physics modules and connection shapes."""
    
    def __init__(self):
        self.hierarchy_levels = {
            "level_1_energy_source": {
                "environment": "Sky/Sun",
                "assets": ["astro_sun_solar_surface_granulation_convection_cells", 
                           "astro_night_sky_stellar_distribution_constellation_star_field_patterns"],
                "physics_module": "Radiative Transfer / Spectral Environment",
                "connection_shape": "Spectral/Energy Port",
                "associated_verbs": ["SCAN", "GROW_ECOSYSTEM"]
            },
            "level_2_matter_source": {
                "environment": "Ground/Surface",
                "assets": ["rock_basalt_hexagonal_columnar_jointing_tessellation",
                           "mineral_quartz_hexagonal_prismatic_with_rhombohedral_termination",
                           "sediment_dune_ripple_wavelength_transverse_formations",
                           "sediment_mudcrack_desiccation_polygonal_fractures"],
                "physics_module": "Substrate/Geological Port, Rigid Body Dynamics",
                "connection_shape": "Substrate/Geological Port",
                "associated_verbs": ["CONNECT", "GROW"]
            },
            "level_3_atmosphere_fluid": {
                "environment": "Atmosphere/Fluid Dynamics",
                "assets": ["river_meander_loops_sinuous_curvature",
                           "sand_dune_ripples_transverse_formations",
                           "ice_crack_networks_frazil_crystals",
                           "mud_crack_desiccation_polygons"],
                "physics_module": "Aerodynamic/Atmospheric Port, Fluid Dynamics & Buoyancy",
                "connection_shape": "Aerodynamic/Atmospheric Port / Hydrodynamic/Hydration Port",
                "associated_verbs": ["BALANCE", "THRUST"]
            },
            "level_4_orbit_deep_space": {
                "environment": "Orbit/Deep Space",
                "assets": ["orbital_mechanics_celestial_gravity_fields",
                           "deep_space_vacuum_environment",
                           "solar_system_planetary_orbits"],
                "physics_module": "Gravitational Anchor, Orbital Mechanics & Celestial Gravity",
                "connection_shape": "Gravitational Anchor",
                "associated_verbs": ["NAVIGATE_ORBIT"]
            }
        }
        
    def get_environment_physics_mapping(self, environment_level: str) -> Dict[str, Any]:
        """
        Get the physics module and connection shape for a specific environment level.
        
        Args:
            environment_level: string identifier for the hierarchy level
            
        Returns:
            Dictionary containing physics module, connection shape, and associated verbs
        """
        return self.hierarchy_levels.get(environment_level, {})
    
    def get_all_connection_shapes(self) -> List[str]:
        """Return all available LEGO puzzle connection shapes."""
        return [
            "Gravitational Anchor",
            "Spectral/Energy Port",
            "Hydrodynamic/Hydration Port",
            "Aerodynamic/Atmospheric Port",
            "Substrate/Geological Port"
        ]
    
    def get_all_verbs_by_level(self) -> Dict[str, List[str]]:
        """Return all verbs associated with each hierarchy level."""
        verb_mapping = {}
        for level, data in self.hierarchy_levels.items():
            verb_mapping[level] = data.get("associated_verbs", [])
        return verb_mapping


class PhysicsControlModules:
    """Defines the modular physics control systems that govern how entities interact with their environment."""
    
    @staticmethod
    def get_rigid_body_dynamics_module() -> Dict[str, Any]:
        """Rigid Body Dynamics module for character walking and physical interactions."""
        return {
            "module_name": "Rigid Body Dynamics",
            "connection_shape": "Gravitational Anchor + Substrate/Geological Port",
            "associated_verbs": ["THRUST", "BALANCE"],
            "physical_laws": ["Newtonian gravity", "mass attraction", "friction coefficients"]
        }
    
    @staticmethod
    def get_fluid_dynamics_buoyancy_module() -> Dict[str, Any]:
        """Fluid Dynamics & Buoyancy module for watercraft and fluid interactions."""
        return {
            "module_name": "Fluid Dynamics & Buoyancy",
            "connection_shape": "Hydrodynamic/Hydration Port",
            "associated_verbs": ["THRUST", "BALANCE"],
            "physical_laws": ["fluid drag", "buoyancy forces", "water hydration absorption bands"]
        }
    
    @staticmethod
    def get_aerodynamics_flight_dynamics_module() -> Dict[str, Any]:
        """Aerodynamics & Flight Dynamics module for aircraft and atmospheric interactions."""
        return {
            "module_name": "Aerodynamics & Flight Dynamics",
            "connection_shape": "Aerodynamic/Atmospheric Port",
            "associated_verbs": ["THRUST", "BALANCE"],
            "physical_laws": ["lift", "drag", "thrust", "airflow patterns (Bernoulli's principle)"]
        }
    
    @staticmethod
    def get_orbital_mechanics_module() -> Dict[str, Any]:
        """Orbital Mechanics & Celestial Gravity module for spacecraft and orbital interactions."""
        return {
            "module_name": "Orbital Mechanics & Celestial Gravity",
            "connection_shape": "Gravitational Anchor",
            "associated_verbs": ["NAVIGATE_ORBIT"],
            "physical_laws": ["Keplerian mechanics", "Newtonian gravity", "mass attraction"]
        }
