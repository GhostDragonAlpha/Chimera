#!/usr/bin/env python3
"""
Domain Generator — the meta-pipeline.

Takes a constraint set JSON + element catalog query and generates a trainable
domain file (seed/mutate/measure). The measure function uses MCP to test
the constraint against the live game. The trainer optimizes within walls.

Usage:
    python -m core.domain_generator docs/constraints/resource_pickup.json

This generates: core/trainables/generated/resource_pickup.py
"""

import json, os, sys, importlib, inspect
from pathlib import Path

TEMPLATE = '''#!/usr/bin/env python3
"""Auto-generated domain: {name}"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {{
{seed_fields}
    }}

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
{mutate_fields}
    return g

def measure(genome: dict) -> dict:
    """
    Apply genome to game state, test constraint, report facts.
    Uses MCPStdioClient to interact with the running editor.
    """
    try:
        from core.telemetry_probe import MCPStdioClient
        c = MCPStdioClient()
    except Exception as e:
        return {{"error": str(e)}}
    
{measure_body}

def get_walls() -> list:
    return {walls}
'''

FIELD_TEMPLATES = {
    "float": '    "{name}": rng.uniform({min_val}, {max_val}),',
    "int": '    "{name}": rng.randint({min_val}, {max_val}),',
    "choice": '    "{name}": rng.choice({options}),',
    "bool": '    "{name}": rng.choice([True, False]),',
}

MUTATE_TEMPLATES = {
    "float": '    g["{name}"] *= math.exp(rng.uniform(-0.2, 0.2))\n    g["{name}"] = max({min_val}, min({max_val}, g["{name}"]))',
    "int": '    g["{name}"] += rng.randint(-1, 1)\n    g["{name}"] = max({min_val}, min({max_val}, g["{name}"]))',
    "choice": '    g["{name}"] = rng.choice({options})',
    "bool": '    g["{name}"] = not g["{name}"]',
}


def load_constraint(path: str) -> dict:
    """Load a constraint set JSON."""
    with open(path) as f:
        return json.load(f)


def query_catalog(elements_file: str, query: dict) -> list:
    """Query the element catalog for relevant variables."""
    with open(elements_file) as f:
        catalog = json.load(f)
    
    categories = query.get("categories", [])
    classes = query.get("classes", [])
    relevant = []
    
    for e in catalog["elements"]:
        cat = e.get("category", "")
        cls = e.get("class", "")
        prop = e.get("property", "")
        match = any(c.lower() in (cat + cls + prop).lower() for c in categories)
        match = match or any(c.lower() in cls.lower() for c in classes)
        if match:
            relevant.append(e)
    
    return relevant


def infer_field_type(element: dict) -> dict:
    """Infer a field type from an element catalog entry."""
    prop = element.get("property", "")
    # Try to infer type from element flags
    flags = element.get("flags", "")
    if "bool" in flags.lower() or "bitmask" in flags.lower():
        return {"type": "bool"}
    if "int" in flags.lower():
        return {"type": "int", "min": 0, "max": 100}
    if "float" in flags.lower():
        return {"type": "float", "min": 0.0, "max": 1.0}
    if "enum" in flags.lower():
        return {"type": "choice", "options": ["Value1", "Value2"]}
    # Default to float
    return {"type": "float", "min": 0.0, "max": 1000.0}


def generate_domain(constraint: dict, elements: list) -> str:
    """Generate a domain file from constraint + elements."""
    name = constraint.get("name", "unnamed")
    walls = constraint.get("walls", [])
    
    # Build seed fields
    seed_lines = []
    mutate_lines = []
    measure_lines = []
    
    # Add MCP-based state variables for each wall
    for i, wall in enumerate(walls):
        field_name = f"wall_{i}_{wall[:20].lower().replace(' ', '_')}"
        field_type = infer_field_type({"property": field_name, "flags": "bool"})
        
        seed_lines.append(f'    "{field_name}": True,')
        mutate_lines.append(f'    g["{field_name}"] = rng.choice([True, False])')
    
    # Build measure body
    measure_lines.append('    results = {}')
    for i, wall in enumerate(walls):
        field_name = f"wall_{i}_{wall[:20].lower().replace(' ', '_')}"
        measure_lines.append(f'    # Test: {wall}')
        measure_lines.append(f'    results["{field_name}"] = True  # replace with actual MCP test')
    
    measure_lines.append('    return results')
    
    # Format the template
    seed_fields = "\n".join(seed_lines)
    mutate_fields = "\n".join(mutate_lines)
    measure_body = "\n".join(measure_lines)
    walls_json = json.dumps(walls, indent=4)
    
    domain_code = TEMPLATE.format(
        name=name,
        seed_fields=seed_fields,
        mutate_fields=mutate_fields,
        measure_body=measure_body,
        walls=walls_json
    )
    
    return domain_code


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m core.domain_generator <constraint_file.json>")
        sys.exit(1)
    
    constraint_path = sys.argv[1]
    constraint = load_constraint(constraint_path)
    
    elements_file = os.path.join(os.path.dirname(__file__), "..", "docs", "element_catalog.json")
    elements = query_catalog(elements_file, constraint.get("element_query", {}))
    
    print(f"Loaded constraint: {constraint['name']}")
    print(f"Found {len(elements)} relevant elements in catalog")
    
    domain_code = generate_domain(constraint, elements)
    
    # Write domain file
    output_dir = Path(__file__).parent / "trainables" / "generated"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{constraint['name']}.py"
    output_path.write_text(domain_code)
    
    print(f"Generated domain: {output_path}")
    print(f"Train with: python -m core.trainer --domain core.trainables.generated.{constraint['name']} --objective {constraint_path}")


if __name__ == "__main__":
    main()
