"""Farm launcher — dispatch sub-agents with the right model for each season.

Reads docs/season_models.json to determine which model to use for each season.
Dispatches background sub-agents that any model can execute.

Usage:
  python core/farm_launcher.py SPRING "Design the shelter system"
  python core/farm_launcher.py SUMMER
  python core/farm_launcher.py FALL
  python core/farm_launcher.py WINTER
"""

import json, sys
from pathlib import Path

SEASON_CONFIG = Path(__file__).parent.parent.parent / "docs/season_models.json"
CHIMERA_DIR = Path("E:/PythonChimera/Chimera")


def load_config():
    return json.loads(SEASON_CONFIG.read_text())


def get_model(season: str) -> str:
    config = load_config()
    entry = config.get(season.upper(), {})
    provider = entry.get("provider", "deepseek")
    model_id = entry.get("modelId", "deepseek-v4-pro")
    return f"{provider}/{model_id}"


def spring_batches(topic: str) -> list[dict]:
    """SPRING: Design. Council debate + catalog elements."""
    model = get_model("SPRING")
    return [
        {
            "description": f"Council: {topic}",
            "prompt": f"""Run the council to design this feature. Work in E:\\PythonChimera\\Chimera.

1. Run: python -m core.council "{topic}" --rounds 2 --record
2. Catalog relevant elements from CHIMERA_VISION.py
3. Write a feature spec to docs/features/<feature>.json

Report the council synthesis and spec location.""",
        },
        {
            "description": "Catalog elements for feature",
            "prompt": f"""Catalog trainable elements relevant to: {topic}. Work in E:\\PythonChimera\\Chimera.

1. Read CHIMERA_VISION.py — find relevant classes and systems
2. Query the DNA graph: python -m core.graphify_record feature --name <X> --loop <N> --status researching
3. List UPROPERTY, CVars, and config entries that would be affected

Report the element list.""",
        },
    ]


def summer_batches() -> list[dict]:
    """SUMMER: Build. Train domains, decode genomes, spawn assets."""
    return [
        {
            "description": "Train all domains",
            "prompt": """Train all domains and report stuck rates. Work in E:\\PythonChimera\\Chimera.

Run for each domain in [erisaid_mirror, npc_behavior, economy_engine, beat_generator]:
  python -m core.train_loop <domain>
  
Report stuck rates and any model bugs found.""",
        },
        {
            "description": "Decode and apply genomes",
            "prompt": """Decode trained genomes to config files. Work in E:\\PythonChimera\\Chimera.

For each domain:
  python -c "from core.decoder import apply_genome; from core.train_loop import train_and_audit; r=train_and_audit('<domain>',pop=30,gens=15); apply_genome(r['best_genome'], '<domain>', dry_run=True)"

Report config files written.""",
        },
    ]


def fall_batches() -> list[dict]:
    """FALL: Verify. Run sleepwalker, record evidence, postflight."""
    return [
        {
            "description": "Run comprehensive verification",
            "prompt": """Run the complete game verification. Work in E:\\PythonChimera\\Chimera.

1. Foreground editor (powershell command)
2. Run: python -m core.sleepwalker --beats docs/beats/chimera_complete.beats.json --session fall_verify
3. Record observations for all exercised features
4. Run: python -m core.collapse_proxy --from-simtest <simtest_id> --valence accepted
5. Run: python -m core.why --backfill --apply

Report beats reached and features observed.""",
        },
    ]


def winter_batches() -> list[dict]:
    """WINTER: Reflect. Audit, dream, garden, compact."""
    return [
        {
            "description": "Run all winter batches",
            "prompt": """Run WINTER season batches. Work in E:\\PythonChimera\\Chimera.

1. Run: python -m core.dream_loop
2. Run: python -m core.gardener --tend
3. Run: python -m core.graph_compactor --dry-run
4. Run: python -m core.why --backfill --apply
5. Run: python -m core.history_book search --query "lesson"
6. For each domain: python -c "from core.train_loop import train_and_audit; r=train_and_audit('<domain>',pop=20,gens=10); print(f'{r[\"domain\"]}: {r[\"audit\"][\"stuck_rate\"]:.0%} stuck')"

Report what each produced.""",
        },
    ]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable seasons: SPRING SUMMER FALL WINTER")
        sys.exit(1)

    season = sys.argv[1].upper()
    model = get_model(season)
    topic = sys.argv[2] if len(sys.argv) > 2 else "Next feature"

    batches = {
        "SPRING": spring_batches(topic),
        "SUMMER": summer_batches(),
        "FALL": fall_batches(),
        "WINTER": winter_batches(),
    }

    if season not in batches:
        print(f"Unknown season: {season}")
        sys.exit(1)

    print(f"Season: {season}")
    print(f"Model:  {model}")
    print(f"Batches: {len(batches[season])}")
    print()
    print("To dispatch, paste these into your Pi session:")
    print()

    for i, batch in enumerate(batches[season]):
        print(f"# Batch {i+1}: {batch['description']}")
        print(f'Agent(subagent_type="general-purpose", model="{model}",')
        print(f'      description="{batch["description"]}",')
        print(f'      prompt="""{batch["prompt"]}""",')
        print(f'      run_in_background=True)')
        print()


if __name__ == "__main__":
    main()
