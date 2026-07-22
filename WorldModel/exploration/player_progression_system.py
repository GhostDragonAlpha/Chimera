"""
PLAYER PROGRESSION SYSTEM & NATURAL LANGUAGE SEMANTIC PROGRAMMING
==================================================================
This module defines how players unlock new verbs and modules as they learn 
the physics of energy and matter flow in the universal simulation.

The Player Progression System is designed around the **Natural Language Semantic Mapping** 
concept: players progress by learning to use natural language words that are semantically 
mapped to physics modules, membrane patterns, constraints, and emergent behaviors.

PROGRESSION TIERS:
------------------
Tier 1: Basic Verbs & Hierarchy Levels (Foundation)
- Verbs unlocked: GROW, CONNECT
- Concepts learned: Level 1 Energy Source/Sky, Level 2 Matter Source/Ground
- Language mapping: Basic nouns (sun, earth, tree, ground) and basic verbs (grow, connect)

Tier 2: Spectroscopic Exploration & Physical States
- Verbs unlocked: SCAN
- Concepts learned: Spectral signatures (Red Edge, hydration bands, iron oxide), 
  physical states (calm, breezy, windy, gale-force)
- Language mapping: Adjectives and descriptors (green, red, wet, dry, rocky, crystalline)

Tier 3: GROW_ECOSYSTEM & Ecosystem Network Growth
- Verbs unlocked: GROW, CONNECT, GROW_ECOSYSTEM
- Concepts learned: Mycelial network structures, leaf venation networks, environmental data mapping (soil moisture to Hydrodynamic/Hydration Port, light interception/PAR to Spectral/Energy Port with 'Red Edge' signature), growth_timescale for procedural generation to visual emergence
- Language mapping: Prepositions and conjunctions showing relationships (through, with, because-of, to, via)

Tier 4: Orbital Mechanics & Celestial Gravity
- Verbs unlocked: NAVIGATE_ORBIT, SCAN
- Concepts learned: Keplerian mechanics, gravitational anchors, celestial gravity fields, orbital period timescale, thrust adjustment frequency_hz for stable orbit calculations
- Language mapping: Complex natural language sentences describing orbital trajectories and celestial navigation

Tier 5: Natural Language Semantic Programming (DSL)
- Verbs unlocked: All verbs + custom neologisms
- Concepts learned: Full membrane programming via natural language DSL
- Language mapping: Players can "program" the simulation using full natural language 
  sentences that are semantically mapped to physics constraints and emergence patterns.

CONSTRAINT-FIRST PROGRESSION WORKFLOW:
--------------------------------------
1. LEARN BASIC VERBS/NOUNS -> Unlock Tier 1 physics modules (Energy/Matter sources)
2. LEARN ADJECTIVES/SPECTRAL SIGNATURES -> Unlock Tier 2 spectroscopic tools
3. LEARN RELATIONSHIPS/PREPOSITIONS -> Unlock Tier 3 fluid/aerodynamic control
4. LEARN COMPLEX SENTENCES -> Unlock Tier 4 orbital mechanics
5. MASTER NATURAL LANGUAGE SEMANTIC MAPPING -> Unlock Tier 5 natural language programming DSL

VERB UNLOCKING MECHANICS:
-------------------------
Players unlock new verbs by demonstrating understanding of the underlying physics 
constraints and scales of speed. Each verb has a specific scale of speed (temporal 
dynamics or rates at which the verb operates):

- THRUST: acceleration_scale (meters_per_second_squared), thrust_build_up_time_ms
- BALANCE: stabilization_rate (radians_per_second_torque_correction), feedback_loop_frequency_hz
- GROW: growth_timescale (seconds_for_procedural_generation_to_frames_for_visual_emergence)
- CONNECT: connection_establishment_time_ms, interface_handshake_speed
- SCAN: scan_frequency_hz, spectral_analysis_rate
- NAVIGATE_ORBIT: orbital_period_timescale, thrust_adjustment_frequency_hz
- GROW_ECOSYSTEM: ecosystem_evolution_rate, network_growth_speed_per_tick

NATURAL LANGUAGE DSL MAPPING TABLE:
-----------------------------------
Part of Speech | Human Language Example | Mapped Simulation Concept
-------------- | ---------------------- | -------------------------
Verbs          | push, balance, grow    | THRUST, BALANCE, GROW + scales of speed
Nouns          | sun, earth, tree       | Hierarchy Levels (Level 1-4), Matter Sources
Adjectives     | calm, green, rocky     | Physical States, Spectral Signatures
Prepositions   | through, with, under   | LEGO Puzzle Connection Shapes (Aerodynamic Port, Spectral Port, etc.)
"""

from typing import Dict, List, Any

class PlayerProgressionSystem:
    """Manages player progression through tiers of physics understanding and verb unlocking."""
    
    def __init__(self):
        self.current_tier = 1
        self.unlocked_verbs = ["GROW", "CONNECT"]
        self.unlocked_modules = [
            "Level_1_Energy_Source_Physics",
            "Level_2_Matter_Source_Physics"
        ]
        
    def unlock_tier(self, tier_number: int) -> Dict[str, Any]:
        """Unlock a specific progression tier and its associated verbs/modules."""
        if tier_number > self.current_tier + 1:
            raise ValueError("Cannot skip tiers. Must progress sequentially.")
            
        tier_data = {
            1: {
                "verbs": ["GROW", "CONNECT"],
                "modules": ["Level_1_Energy_Source_Physics", "Level_2_Matter_Source_Physics"],
                "language_mapping": "Basic nouns and verbs",
                "physics_constraints": "Energy/Matter sources, hierarchical membrane system Level 1-2"
            },
            2: {
                "verbs": ["SCAN"],
                "modules": ["Spectroscopic_Exploration_Tools"],
                "language_mapping": "Adjectives and spectral descriptors",
                "physics_constraints": "Spectral signatures (Red Edge, hydration bands, iron oxide), physical states"
            },
            3: {
                "verbs": ["GROW", "CONNECT", "GROW_ECOSYSTEM"],
                "modules": ["Grow_Ecosystem_Simulation", "Fluid_Dynamics_Buoyancy", "Aerodynamics_Flight_Dynamics"],
                "language_mapping": "Prepositions and relationship words",
                "physics_constraints": "Soil moisture to Hydrodynamic/Hydration Port, PAR to Spectral/Energy Port, growth_timescale for procedural generation to visual emergence"
            },
            4: {
                "verbs": ["NAVIGATE_ORBIT", "SCAN"],
                "modules": ["Orbital_Mechanics_Celestial_Gravity"],
                "language_mapping": "Complex sentences describing trajectories",
                "physics_constraints": "Keplerian mechanics, gravitational anchors, celestial gravity fields, orbital period timescale, thrust adjustment frequency_hz"
            },
            5: {
                "verbs": ["ALL_VERBS", "CUSTOM NEOLOGISMS"],
                "modules": ["Natural_Language_Semantic_Programming_DSL"],
                "language_mapping": "Full natural language semantic programming"
            }
        }
        
        if tier_number in tier_data:
            self.current_tier = tier_number
            self.unlocked_verbs.extend(tier_data[tier_number]["verbs"])
            self.unlocked_modules.extend(tier_data[tier_number]["modules"])
            
            return {
                "tier_unlocked": tier_number,
                "new_verbs": tier_data[tier_number]["verbs"],
                "new_modules": tier_data[tier_number]["modules"],
                "language_mapping_focus": tier_data[tier_number]["language_mapping"]
            }
        else:
            raise ValueError(f"Invalid tier number: {tier_number}")

    def get_progression_status(self) -> Dict[str, Any]:
        """Return the current progression status of the player."""
        return {
            "current_tier": self.current_tier,
            "unlocked_verbs": self.unlocked_verbs,
            "unlocked_modules": self.unlocked_modules
        }


class NaturalLanguageDSLMapper:
    """Maps human language parts of speech to simulation concepts for natural language programming."""
    
    @staticmethod
    def map_verb_to_simulation_concept(verb: str) -> Dict[str, Any]:
        """Map a human language verb to its corresponding simulation concept and scale of speed."""
        verb_mappings = {
            "push": {"concept": "THRUST", "scale_of_speed": "acceleration_scale (m/s²)"},
            "balance": {"concept": "BALANCE", "scale_of_speed": "stabilization_rate (rad/s)"},
            "grow": {"concept": "GROW", "scale_of_speed": "growth_timescale (seconds to frames)"},
            "connect": {"concept": "CONNECT", "scale_of_speed": "connection_establishment_time_ms"},
            "scan": {"concept": "SCAN", "scale_of_speed": "scan_frequency_hz"},
            "navigate": {"concept": "NAVIGATE_ORBIT", "scale_of_speed": "orbital_period_timescale"},
            "plant_nurture": {"concept": "GROW_ECOSYSTEM", "scale_of_speed": "ecosystem_evolution_rate"}
        }
        
        return verb_mappings.get(verb.lower(), {"concept": "UNKNOWN_VERB", "scale_of_speed": "undefined"})

    @staticmethod
    def map_noun_to_hierarchy_level(noun: str) -> Dict[str, Any]:
        """Map a human language noun to its corresponding hierarchy level or matter source."""
        noun_mappings = {
            "sun": {"level": "Level_1_Energy_Source", "concept": "Solar granulation + Night sky stellar distribution"},
            "sky": {"level": "Level_1_Energy_Source", "concept": "Radiative Transfer / Spectral Environment"},
            "earth": {"level": "Level_2_Matter_Source", "concept": "Geological patterns + Physical dynamics"},
            "ground": {"level": "Level_2_Matter_Source", "concept": "Substrate/Geological Port"},
            "tree": {"level": "Level_3_Transformation_Engine", "concept": "Phyllotaxis + Fractal_Branching + Canopy_PAR"},
            "river": {"level": "Level_3_Atmosphere_Fluid", "concept": "Fluid Dynamics & Buoyancy"},
            "wind": {"level": "Level_3_Atmosphere_Fluid", "concept": "Aerodynamic/Atmospheric Port"},
            "orbit": {"level": "Level_4_Orbit_Deep_Space", "concept": "Orbital Mechanics & Celestial Gravity"},
            "space": {"level": "Level_4_Orbit_Deep_Space", "concept": "Deep space vacuum environment"}
        }
        
        return noun_mappings.get(noun.lower(), {"level": "UNKNOWN_NOUN", "concept": "undefined"})

    @staticmethod
    def map_preposition_to_connection_shape(preposition: str) -> Dict[str, Any]:
        """Map a human language preposition to its corresponding LEGO puzzle connection shape."""
        preposition_mappings = {
            "under_gravity": {"shape": "Gravitational Anchor", "physics": "Newtonian gravity, mass attraction"},
            "with_light": {"shape": "Spectral/Energy Port", "physics": "Light interception, Red Edge signature, PAR distribution"},
            "in_water": {"shape": "Hydrodynamic/Hydration Port", "physics": "Buoyancy, fluid drag, water hydration bands"},
            "through_air": {"shape": "Aerodynamic/Atmospheric Port", "physics": "Lift, drag, thrust, airflow patterns"},
            "on_ground": {"shape": "Substrate/Geological Port", "physics": "Mineral absorption, soil topography, friction"}
        }
        
        return preposition_mappings.get(preposition.lower(), {"shape": "UNKNOWN_CONNECTION", "physics": "undefined"})
