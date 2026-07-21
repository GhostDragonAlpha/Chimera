# The Emergent Workflow

> Everything is trained. Nothing is authored.
> The element catalog has 69,749 variables. The trainer does 30,000 evals/sec.
> Every game artifact starts as a constraint set and emerges from the trainer.

## The Pipeline

```
CONSTRAINT SET  →  CATALOG QUERY  →  DOMAIN  →  TRAIN  →  DECODE  →  VERIFY
(walls only)      (find elements)    (seed/     (walls     (apply     (sleepwalker
                                     mutate/    only,      winner)    beat tests
                                     measure)   no max/                constraint)
                                                 min)
```

Every step is data. Nothing is hand-authored.

## Step 1: Constraint Set

Written as a JSON file at `docs/constraints/<name>.json`. No maximize/minimize. Walls only.

```json
{
  "name": "resource_pickup",
  "walls": [
    "Player must be able to collect a resource by pressing E while near it",
    "Resource must have a visible mesh",
    "Collected resource must be tracked in inventory",
    "Resource must persist in the world until collected"
  ],
  "element_query": {
    "categories": ["Pickup", "Interaction", "Collision", "Inventory"],
    "classes": ["APickupActor", "PickupInteractionComponent"]
  }
}
```

## Step 2: Catalog Query

Query `docs/element_catalog.json` for elements matching the categories and classes.
Returns a reduced set of trainable variables.

```python
import json
catalog = json.load(open('docs/element_catalog.json'))
elements = [e for e in catalog['elements'] 
            if any(cat in e.get('category','') for cat in constraint['element_query']['categories'])]
```

## Step 3: Domain

A `core/trainables/<name>.py` file with three functions:

```python
def seed(rng=None) -> dict:
    """Random genome. Each key maps to an element catalog variable."""
    return {
        "pickup_radius": rng.uniform(50, 500),
        "collision_channel": rng.choice(["Pawn", "WorldDynamic", "WorldStatic"]),
        "overlap_enabled": rng.choice([True, False]),
        "auto_collect": rng.choice([True, False])
    }

def mutate(genome: dict, rng=None) -> dict:
    """Perturb the genome. Small changes to continuous, occasional to discrete."""
    g = copy.deepcopy(genome)
    g["pickup_radius"] *= math.exp(rng.uniform(-0.2, 0.2))
    return g

def measure(genome: dict) -> dict:
    """Simulate and report FACTS. Does the player's E key work? Report the numbers."""
    # Apply genome to game state (via MCP or direct C++ property set)
    # Run a beat: walk near resource → press E → check inventory
    # Return facts about what happened
    return {
        "pickup_distance": 0.0,
        "item_in_inventory": False,
        "time_to_pickup_ms": 0.0
    }
```

## Step 4: Train

```powershell
python -m core.trainer --domain core.trainables.<name> --objective docs/constraints/<name>.json
```

No maximize/minimize. Only walls. The trainer reports which genomes satisfy all walls.
The human judges the survivors.

## Step 5: Decode

Convert the winning genome to game artifacts:
- C++ config values → written to the appropriate files
- Blueprint properties → set via MCP `set_component_property`
- Spawn commands → generated as a sleepwalker beat

```python
from core.decoder import apply_genome
apply_genome(winning_genome, '<name>')  # writes config, spawns actors, creates beat
```

## Step 6: Verify

```powershell
python -m core.beat_lint --beats docs/beats/<name>.beats.json
python -m core.sleepwalker --beats docs/beats/<name>.beats.json --session verify_<name>
```

If the beat passes, the constraint is satisfied. No human judgment needed for the
mechanical part. The human judges the pattern (e.g., "does this pickup feel right?").

---

## The Commitments

From this point forward:

1. **No hand-written C++ for gameplay systems.** If a system needs behavior, write a domain and train it. The element catalog provides the variables.
2. **No MCP-spawned actors for content.** If content needs to be in the level, train its placement or write a decoder that the trainer's output drives.
3. **No Blueprint authoring via MCP.** If a Blueprint needs to exist, its parameters are a genome and the trainer discovers them.
4. **No placed objects.** If an object needs to be in the world, the decoder places it based on trained output.
5. **The only authored code is the domain scaffold** (seed/mutate/measure) and the decoder. Everything else emerges.

## The Exception

The shelter proximity trigger (ShelterHabitatComponent Tick modification) is the LAST hand-authored C++ change. It was necessary because the shelter constraint was already compiled and only needed a small bridge. Every future system starts as a constraint set and goes through the pipeline.

## The Transition

Existing content (player character, NPCs, educational pickups, cosmic rung objects, shelter) stays as-is. New content follows the emergent workflow. When existing content fails a human judgment, it goes through the audit backlog — retrained through the emergent workflow, not patched.
