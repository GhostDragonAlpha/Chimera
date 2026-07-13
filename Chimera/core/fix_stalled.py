"""Fix stalled features in the DNA graph so the harness can process them.

LEGACY one-off repair. NOTE: this operates on the JSON snapshot
(docs/chimera_dna_graph.json), which since the 2026-07-12 SQLite migration is a
durability snapshot, not the live working store (docs/world/dna.db). Prefer the
typed `record_*` helpers for live mutations; kept here only for snapshot repair.

Guarded under __main__ so IMPORTING this module has NO side effects. It previously
ran json.load + json.dump at import time on a CWD-relative path — which crashed on
import from Chimera/ and, worse, silently rewrote the snapshot when imported from
the repo root. Both footguns are removed: the path is resolved from this file, and
the work only runs when the module is executed directly.
"""
import json
from pathlib import Path

# DNA snapshot lives at <Chimera>/docs/chimera_dna_graph.json — resolve from this
# file's location (core/ -> Chimera/), never from the current working directory.
DNA_SNAPSHOT = Path(__file__).resolve().parent.parent / "docs" / "chimera_dna_graph.json"
PREFIX_MAP = {'Player_': 0, 'Ground_': 1, 'Verb_': 2, 'Sky_': 3, 'Tool_': 4,
              'NPC_': 5, 'Social_': 5, 'Shelter_': 6, 'Travel_': 7,
              'System_': 8, 'Universe_': 9}


def fix_stalled(path: Path = DNA_SNAPSHOT) -> int:
    """Reset stalled FeatureUpdate nodes to needs_refinement and normalize loop ints."""
    g = json.load(open(path, encoding="utf-8"))
    fixed = 0
    for n in g['nodes']:
        if n.get('type') == 'FeatureUpdate':
            name = n.get('feature_name', '')
            old_status = n.get('status', '')
            raw_loop = n.get('loop')
            if old_status == 'stalled' or (isinstance(raw_loop, str) and raw_loop != '0'):
                n['status'] = 'needs_refinement'
                for prefix, loop in PREFIX_MAP.items():
                    if name.startswith(prefix):
                        n['loop'] = loop
                        break
                fixed += 1
                print(f"  Fixed: {name} ({old_status}, loop={raw_loop!r}) -> needs_refinement, loop={n['loop']}")
    json.dump(g, open(path, 'w', encoding="utf-8"), indent=2)
    print(f"Total fixed: {fixed}")
    return fixed


if __name__ == "__main__":
    fix_stalled()
