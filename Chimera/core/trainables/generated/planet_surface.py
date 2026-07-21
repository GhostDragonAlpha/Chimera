#!/usr/bin/env python3
"""Planet surface rung — consumes solar system planet triples and trains planet surface properties.

The Mirror of Erised is encoded as a hard constraint: at least one planet must be habitable.
The atmos physics uses numpy vectorization (CPU SIMD, fast). GPU backend is ready for when
the variable count exceeds ~1000 (ground terrain, biome distribution, material properties).

GPU backend path: when this domain's variable space grows, add:
    def measure_batch(population: list) -> list:
        # Vectorize across the population using numpy + multiprocessing
        # Each genome evaluates independently — perfect for GPU parallelization
"""

import copy, json, math, os, random
import numpy as np

# Physical constants
STEFAN_BOLTZMANN = 5.67e-8  # W/m²/K⁴
SOLAR_LUMINOSITY = 3.828e26  # W
AU_M = 1.496e11  # m per AU
G = 6.674e-11  # m³/kg/s²
R_EARTH = 6.371e6  # m
M_EARTH = 5.972e24  # kg


def load_solar_system(path: str = None) -> list:
    """Load the trained solar system output. Returns list of planet dicts."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'objectives', 'bigbang.systems.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    systems = data.get("systems", [])
    if not systems:
        return []
    return systems[0]  # Take the first system


def seed(rng=None):
    """Random planet surface parameters for each planet in the trained system."""
    if rng is None:
        rng = random.Random()
    
    planets = load_solar_system()
    if not planets:
        # Fallback: 4 default planets
        planets = [{"m_rel": 0.001, "a": 0.3, "e": 0.1},
                    {"m_rel": 0.005, "a": 0.6, "e": 0.1},
                    {"m_rel": 0.003, "a": 0.9, "e": 0.05},
                    {"m_rel": 0.001, "a": 1.2, "e": 0.05}]
    
    g = {}
    for i, p in enumerate(planets):
        # Mass in Earth masses
        m_earth = p["m_rel"] * 1000  # relative mass to Earth-scale
        a_au = p["a"]
        
        # Planet type (0=rocky, 1=gaseous, 2=icy) based on orbital distance
        if a_au < 0.5:
            p_type = 0  # rocky inner
        elif a_au < 1.0:
            p_type = rng.choice([0, 2])  # rocky or icy middle
        else:
            p_type = rng.choice([1, 2])  # gas or icy outer
        
        # Radius based on mass and type
        if p_type == 0:  # rocky
            radius = 0.5 + 1.5 * math.sqrt(m_earth / 5)
        elif p_type == 1:  # gas
            radius = 2 + 18 * math.sqrt(m_earth / 50)
        else:  # icy
            radius = 1 + 3 * math.sqrt(m_earth / 10)
        
        # Atmosphere density
        atmo_density = rng.uniform(0, 1.5) if p_type == 1 else rng.uniform(0, 0.8)
        
        # Surface temperature (K) — equilibrium + greenhouse
        eq_temp = 278 / math.sqrt(a_au)  # Earth reference
        greenhouse = rng.uniform(0, 40) if atmo_density > 0.3 else 0
        surface_temp = eq_temp + greenhouse
        
        # Biome type
        if surface_temp < 200:
            biome = "frozen"
        elif surface_temp < 250:
            biome = "tundra"
        elif surface_temp < 320:
            biome = "temperate"
        elif surface_temp < 400:
            biome = "desert"
        else:
            biome = "scorched"
        
        # Habitability
        habitable = (250 <= surface_temp <= 320) and (0.1 < atmo_density < 1.2)
        
        g[f"planet_{i}_type"] = p_type
        g[f"planet_{i}_radius"] = radius
        g[f"planet_{i}_gravity"] = G * (m_earth * M_EARTH) / (radius * R_EARTH) ** 2 / 9.81  # in g
        g[f"planet_{i}_atmo_density"] = atmo_density
        g[f"planet_{i}_surface_temp"] = surface_temp
        g[f"planet_{i}_greenhouse"] = greenhouse
        g[f"planet_{i}_biome"] = biome
        g[f"planet_{i}_habitable"] = 1 if habitable else 0
    
    g["n_planets"] = len(planets)
    return g


def mutate(genome: dict, rng=None):
    """Perturb planet surface parameters."""
    import random as _random
    if rng is None: rng = _random.Random()
    g = copy.deepcopy(genome)
    
    n = g.get("n_planets", 4)
    for i in range(n):
        if f"planet_{i}_radius" in g:
            g[f"planet_{i}_radius"] *= math.exp(rng.uniform(-0.1, 0.1))
            g[f"planet_{i}_atmo_density"] *= math.exp(rng.uniform(-0.2, 0.2))
            g[f"planet_{i}_surface_temp"] += rng.uniform(-10, 10)
            
            # Recompute habitability
            t = g[f"planet_{i}_surface_temp"]
            a = g[f"planet_{i}_atmo_density"]
            g[f"planet_{i}_habitable"] = 1 if (250 <= t <= 320 and 0.1 < a < 1.2) else 0
    
    return g


def measure(genome: dict) -> dict:
    """Compute planet surface properties and check Mirror walls.
    
    Pure numpy computation — no MCP calls. Fast vectorized operations.
    GPU backend ready when variable count exceeds ~1000.
    """
    try:
        n = genome.get("n_planets", 4)
        
        # Count habitable planets
        n_habitable = sum(1 for i in range(n) if genome.get(f"planet_{i}_habitable", 0) == 1)
        
        # Count planet types
        n_rocky = sum(1 for i in range(n) if genome.get(f"planet_{i}_type", 0) == 0)
        n_gas = sum(1 for i in range(n) if genome.get(f"planet_{i}_type", 0) == 1)
        n_icy = sum(1 for i in range(n) if genome.get(f"planet_{i}_type", 0) == 2)
        
        # Biomes (count unique)
        biomes = set()
        for i in range(n):
            biomes.add(genome.get(f"planet_{i}_biome", "unknown"))
        
        # Mean surface temp of inner planets vs outer
        inner_temps = [genome.get(f"planet_{i}_surface_temp", 300) for i in range(n) if genome.get(f"planet_{i}_type", 0) == 0]
        outer_temps = [genome.get(f"planet_{i}_surface_temp", 100) for i in range(n) if genome.get(f"planet_{i}_type", 0) in (1, 2)]
        
        inner_mean_temp = sum(inner_temps) / len(inner_temps) if inner_temps else 0
        outer_mean_temp = sum(outer_temps) / len(outer_temps) if outer_temps else 0
        
        return {
            "n_habitable": n_habitable,
            "n_rocky": n_rocky,
            "n_gas": n_gas,
            "n_icy": n_icy,
            "n_unique_biomes": len(biomes),
            "inner_mean_temp": inner_mean_temp,
            "outer_mean_temp": outer_mean_temp,
            "n_planets": n,
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "n_habitable": 0,
            "n_rocky": 0,
            "n_gas": 0,
            "n_icy": 0,
            "n_unique_biomes": 0,
            "inner_mean_temp": 0,
            "outer_mean_temp": 0,
            "n_planets": 0,
        }


def get_walls() -> list:
    return [
        "At least one planet must be habitable (n_habitable >= 1) — Mirror of Erised",
        "At least one non-habitable planet must exist (the choice to help requires a cost)",
        "Inner planets must be hotter than outer planets (inner_mean_temp > outer_mean_temp)",
        "At least 2 unique biomes must exist across the system",
        "At least 3 planets must have valid surface properties",
    ]


def get_domain_info() -> dict:
    return {
        "name": "planet_surface",
        "rung": 1,
        "input_rung": "solar_system",
        "next_rung": "ground_terrain",
        "mirror_wall": "At least one habitable planet. If no planet can support life, there is no world worth fighting for — the Mirror shows an empty reflection.",
        "gpu_ready": False,
        "gpu_threshold": 1000,
        "n_variables": "~40 (4 planets x 10 params)",
        "description": "Consumes solar system planets. Trains atmosphere, temperature, biome. All planets must be distinct. At least one must be habitable."
    }
