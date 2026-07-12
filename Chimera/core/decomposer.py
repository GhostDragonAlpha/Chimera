"""decomposer — THE BREAKDOWN PROCESS: compound targets become processed parts.

"Everything needs to go through the process. If a feature needs to be broken
down, there should be a process for THAT, so the parts get processed — not a
system." (human directive, 2026-07-12)

The gap this closes: rehearsal PICKS work, the board CLAIMS it, atoms VERIFY
it — but when evidence indicts something compound ("the sprint input rig"),
no organ mechanically broke it into parts. Agents did that step in their
heads, out-of-band, and the monolith got worked as a blob. Now decomposition
is itself a processed, recorded step:

  evidence (simtest/elimination ids)
      │
      ▼
  decompose(target, kind)          <- kind selects a PART TEMPLATE from
      │                               docs/decomposition_templates.json
      │                               (the studio's scars codified; GROW THE
      │                               JSON, never this engine)
      ├── records a Decomposition node in the DNA graph (auditable)
      ├── seeds ONE BOARD TASK PER PART (footprint, deps, not_scope naming
      │       sibling parts — hard negatives with provenance)
      ├── mints REP ATOMS per part (each part measurable from birth)
      └── MONOLITH GUARD: any open bare-parent task is blocked
              ("claim the parts, not the system")

Each part then rides the EXISTING conveyor: claim -> tunnel -> work -> reps
-> beats -> collapse. The decomposer decides nothing about priority order
beyond declared dependencies — rehearsal and the board keep that authority.

CLI
  python -m core.decomposer run --target Sprint_Input --kind input_rig \
      --evidence simtest_...,elim_... [--dry-run]
  python -m core.decomposer list-templates
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_PATH = ROOT / "docs" / "decomposition_templates.json"

# Founding templates — each part is the smallest independently-verifiable
# unit: its own footprint, its own probe, its own dependency edge. These are
# codified scars (H-31/H-34 lineage for component/telemetry kinds; the sprint
# saga for input_rig). Stored to JSON on first run; edits belong in the JSON.
FOUNDING_TEMPLATES = {
    "input_rig": {
        "doc": "An input-driven verb that evidence shows never reaches the "
               "movement/world state (the sprint case: key pressed, nothing "
               "changes). Parts run source-of-truth -> binding -> harness "
               "parity -> live read-back.",
        "parts": [
            {"slug": "state", "title": "movement state: verb flag changes the simulation",
             "recipe": "Add the verb's state to the movement component (e.g. bSprinting + "
                       "SprintMultiplier consumed in the tick's speed calculation) with a "
                       "BlueprintCallable setter. The flag must CHANGE simulated numbers (H-21).",
             "files": ["Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.*"],
             "editor": "none",
             "verify": {"type": "tree_contains",
                        "root": "Source/Chimera/ProceduralGenerated", "glob": "*.cpp",
                        "regex": r"SprintMultiplier|bSprinting"},
             "tier": 1, "after": []},
            {"slug": "binding", "title": "input binding: the physical key drives the state",
             "recipe": "Bind the key (LeftShift) press/release to the state setter so the "
                       "input path — not a test injection — flips the flag (H-14).",
             "files": ["Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.*",
                       "Source/Chimera/ProceduralGenerated/GameMode/**"],
             "editor": "none",
             "verify": {"type": "tree_contains",
                        "root": "Source/Chimera/ProceduralGenerated", "glob": "*.*",
                        "regex": r"LeftShift[\s\S]{0,160}Sprint|Sprint[\s\S]{0,160}LeftShift"},
             "tier": 1, "after": ["state"]},
            {"slug": "harness_parity", "title": "harness parity: sleepwalker and bridge agree on the key token",
             "recipe": "The sleepwalker sends a modifier token; the McpAutomationBridge must "
                       "accept the SAME token (historic failure: harness said LeftShift, "
                       "bridge expected LShift/RShift). Align one side to the other.",
             "files": ["core/sleepwalker.py",
                       "Plugins/McpAutomationBridge/Source/**"],
             "editor": "none",
             "verify": {"type": "tree_contains", "root": "Plugins", "glob": "*.cpp",
                        "regex": r"LeftShift"},
             "tier": 0, "after": []},
            {"slug": "readback", "title": "live read-back: a beat proves the verb changed the world",
             "recipe": "Beat asserts pawn speed >= threshold while the key is held "
                       "(timed read-back per H-28, reset_position first per H-25), THEN "
                       "the downstream expects (volume_scales_with_speed) may run.",
             "files": ["docs/beats/audio_visual_sync.beats.json"],
             "editor": "open",
             "verify": {"type": "pie",
                        "note": "beat: key_down LeftShift -> pawn speed read-back >= 300cm/s"},
             "tier": 2, "after": ["binding", "harness_parity"]},
        ],
    },
    "component_attachment": {
        "doc": "A component evidence shows is queried but never constructed "
               "(the SandSound/H-34 case). Parts: attach site -> population -> "
               "accessor surface -> live read-back.",
        "parts": [
            {"slug": "attach", "title": "attach site: something constructs the component",
             "recipe": "CreateDefaultSubobject in a constructor, or runtime NewObject+"
                       "RegisterComponent in BeginPlay of a component that always exists.",
             "files": ["Source/Chimera/ProceduralGenerated/**"], "editor": "none",
             "verify": {"type": "tree_contains",
                        "root": "Source/Chimera/ProceduralGenerated", "glob": "*.*",
                        "regex": r"(CreateDefaultSubobject|NewObject)\s*<"},
             "tier": 0, "after": []},
            {"slug": "population", "title": "population: runtime events write real data into it",
             "recipe": "The producing system calls the component's record/update API on "
                       "real events — no hardcoded fallback sentinels (H-31).",
             "files": ["Source/Chimera/ProceduralGenerated/**"], "editor": "none",
             "verify": {"type": "tree_lacks",
                        "root": "Source/Chimera/ProceduralGenerated", "glob": "*.cpp",
                        "regex": r"=\s*999(\.0f?)?\b"},
             "tier": 1, "after": ["attach"]},
            {"slug": "accessors", "title": "accessor surface: the exact names the caller queries",
             "recipe": "Expose the getters under the EXACT names the MCP bridge/beat "
                       "vocabulary uses (the Avg-vs-Average lesson).",
             "files": ["Source/Chimera/ProceduralGenerated/**"], "editor": "none",
             "verify": {"type": "tree_contains",
                        "root": "Source/Chimera/ProceduralGenerated", "glob": "*.h",
                        "regex": r"UFUNCTION"},
             "tier": 1, "after": ["attach"]},
            {"slug": "readback", "title": "live read-back: a beat consumes the accessors in PIE",
             "recipe": "Beat exercises the producer then asserts accessor values are live "
                       "(counts > 0, latencies < sentinel).",
             "files": ["docs/beats/**"], "editor": "open",
             "verify": {"type": "pie", "note": "beat asserts live accessor values"},
             "tier": 2, "after": ["population", "accessors"]},
        ],
    },
}


def load_templates() -> dict:
    if TEMPLATES_PATH.exists():
        try:
            return json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    TEMPLATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES_PATH.write_text(json.dumps(FOUNDING_TEMPLATES, indent=1),
                              encoding="utf-8")
    return dict(FOUNDING_TEMPLATES)


def _dc_id(target: str, kind: str) -> str:
    stamp = datetime.now(timezone.utc).isoformat()
    return "dc_" + hashlib.sha256(f"{target}|{kind}|{stamp}".encode()).hexdigest()[:12]


def decompose(target: str, kind: str, evidence: list, dry_run: bool = False,
              base_priority: float = 1.2) -> dict:
    """THE PROCESS. Returns the manifest {dc_id, parts:[{slug, task_id,
    feature, atom_id}], blocked_monoliths:[...]}. Priority ordering beyond
    dependency edges stays with rehearsal/the board."""
    templates = load_templates()
    if kind not in templates:
        raise KeyError(f"unknown decomposition kind {kind!r}; "
                       f"available: {sorted(templates)} "
                       f"(grow docs/decomposition_templates.json, never this engine)")
    tmpl = templates[kind]
    dc_id = _dc_id(target, kind)
    parts_manifest = []
    slug_to_task: dict = {}

    # sibling footprints for each part's not_scope (hard negatives w/ provenance)
    all_files = {p["slug"]: p["files"] for p in tmpl["parts"]}

    for i, part in enumerate(tmpl["parts"]):
        feature = f"{target}/{part['slug']}"
        sibling_files = sorted({f for s, fl in all_files.items()
                                if s != part["slug"] for f in fl
                                if f not in part["files"]})
        not_scope = {
            "subsystems": [f"{target}/{s}" for s in all_files if s != part["slug"]],
            "files": sibling_files,
            "rationale": {f"{target}/{s}": f"sibling part of {dc_id} — its own task"
                          for s in all_files if s != part["slug"]},
        }
        task_id = f"(dry-run tb-?{i})"
        if not dry_run:
            from core.task_board import add_task
            depends = [slug_to_task[a] for a in part.get("after", [])
                       if a in slug_to_task]
            t = add_task(
                f"{target}: {part['title']}",
                part["recipe"] + f"  [decomposition {dc_id}; evidence: "
                + ", ".join(evidence) + "]",
                files=part["files"], editor=part.get("editor", "none"),
                feature=feature, priority=round(base_priority - i * 0.02, 3),
                depends_on=depends, created_by=f"decomposer:{dc_id}",
                not_scope=not_scope)
            task_id = t["id"]
        slug_to_task[part["slug"]] = task_id

        atom_id = None
        verify = part.get("verify") or {}
        if not dry_run and verify:
            from core.rep_engine import make_atom, merge_battery
            kind_probe = verify.get("type", "pie")
            spec = {k: v for k, v in verify.items() if k != "type"}
            atom = make_atom(feature, int(part.get("tier", 1)), kind_probe, spec,
                             f"part '{part['slug']}' of {target}: {part['title']}",
                             f"decomposition:{dc_id}",
                             kind=("pie" if kind_probe == "pie" else "headless"))
            merge_battery(feature, [atom])
            atom_id = atom["id"]
        parts_manifest.append({"slug": part["slug"], "feature": feature,
                               "task_id": task_id, "atom_id": atom_id})

    blocked = []
    if not dry_run:
        from core.task_board import mark_superseded_by_decomposition
        blocked = mark_superseded_by_decomposition(target, dc_id)
        try:
            from core.graphify_interface import record_decomposition
            record_decomposition(target, kind, evidence,
                                 [{"slug": p["slug"], "task_id": p["task_id"],
                                   "feature": p["feature"]} for p in parts_manifest],
                                 dc_id=dc_id)
        except Exception as e:                     # noqa: BLE001 — record, never wedge
            print(f"!! decomposition graph record failed: {e}")

    return {"dc_id": dc_id, "target": target, "kind": kind,
            "evidence": evidence, "parts": parts_manifest,
            "blocked_monoliths": blocked}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--target", required=True,
                       help="the compound thing the evidence indicts")
    p_run.add_argument("--kind", required=True,
                       help="template key (list-templates shows them)")
    p_run.add_argument("--evidence", required=True,
                       help="comma-separated simtest/elimination ids (H-19: fresh only)")
    p_run.add_argument("--dry-run", action="store_true")
    sub.add_parser("list-templates")
    args = parser.parse_args()

    if args.cmd == "list-templates":
        for name, t in load_templates().items():
            print(f"{name}: {t['doc'][:90]}")
            for p in t["parts"]:
                after = f"  (after {', '.join(p['after'])})" if p.get("after") else ""
                print(f"   - {p['slug']}: {p['title']}{after}")
        return 0

    manifest = decompose(args.target, args.kind,
                         [e.strip() for e in args.evidence.split(",") if e.strip()],
                         dry_run=args.dry_run)
    mode = "DRY-RUN " if args.dry_run else ""
    print(f"[decomposer] {mode}{manifest['dc_id']}: {manifest['target']} "
          f"({manifest['kind']}) -> {len(manifest['parts'])} parts")
    for p in manifest["parts"]:
        print(f"   {p['task_id']}  {p['feature']}"
              + (f"  atom {p['atom_id']}" if p["atom_id"] else ""))
    for b in manifest["blocked_monoliths"]:
        print(f"   monolith guard: {b} blocked — claim the parts, not the system")
    if not args.dry_run:
        print("Parts now ride the standard conveyor: "
              "python -m core.task_board claim --agent <id>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
