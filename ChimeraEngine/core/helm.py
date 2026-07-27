"""helm — the agent's hand on the wheel: steer toward the seed, close the gap.

The control loop the human named: the SEED (CHIMERA_VISION.py) is true north —
the finished game, written down. The STATE is what actually exists and is
verified (rep gauges, source, graduations). The helm reads target - state each
cycle and points the agent's effort at the largest, highest-value shortfall.
It edits nothing; it reads and points.

  seed - state = the gap ;  the helm turns the gap into the next heading.

TRUE NORTH is wired in literally: parse_vision() ast-parses CHIMERA_VISION.py
(valid Python, so no guessing) into its named systems; realization() scores how
far each is realized in the live project (absent -> declared -> built ->
verified/graduated). The unrealized-but-high-value systems ARE the Build gap.

The helm scores a handful of focus categories by current pressure (how far
below target), highest wins:
  Contain  — a container wall is breached (malcolm)            [overrides all]
  Fix      — red rep atoms pile up
  Graduate — a feature is 1-2 clean nights from earning trust
  Build    — vision systems still unrealized (the seed gap)
  Verify   — worry has outrun evidence (stale pains, obs queue)
  Polish   — it works but doesn't FEEL AAA (metronome reds)
  Consolidate — the clock calls it night (circadian)

  python -m core.helm            # the heading right now
  python -m core.helm targets    # the vision gap, ranked (true north)
  python -m core.helm gauges     # every pressure reading
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # Chimera/
VISION = ROOT.parent / "CHIMERA_VISION.py"           # the seed lives at repo root
SOURCE_TREE = ROOT / "Source" / "Chimera" / "ProceduralGenerated"

# Section line markers are read from the file; these label the domains by weight.
# Game-content domains matter more for STEERING than engine plumbing — you sail
# toward the world, not toward the renderer's math.
DOMAIN_WEIGHT = {
    "§1": 0.2,   # core math — infrastructure
    "§2": 0.4,   # engine/loop
    "§3": 0.6,   # ECS / crowd
    "§4": 0.7,   # rendering
    "§5": 0.9,   # audio (the game's wordless voice)
    "§6": 0.9,   # AI / the dots (other people)
    "§7": 0.8,   # movement / input (the body)
    "§8": 0.9,   # gameplay / GAS / save (the verbs + meaning)
    "§9": 0.5,   # networking
    "§10": 1.0,  # WORLD SYSTEMS — Erisaid, sacrifice, sky, memorial: the soul
    "§11": 0.5,  # boot/assembly
}

# Project-distinctive tokens: a vision class carrying one of these is OUR game
# content (steer toward it), not an engine builtin re-declared as pseudocode.
PROJECT_TOKENS = {
    "chimera", "erisaid", "sacrifice", "dot", "habitat", "sand", "regolith",
    "titan", "sky", "weather", "star", "memorial", "attunement", "sprint",
    "ground", "dust", "footstep", "suit", "gesture", "will", "costless",
    "sleepwalk", "yard", "stranger", "trade", "economy", "faction", "mission",
    "quantum", "ship", "station", "scanner", "shovel", "tool", "verb",
}
_ENGINE_BUILTIN = re.compile(
    r"^(FVector|FRotator|FQuat|FMatrix|FTransform|UStaticMesh|USkeletal|"
    r"UNiagara|UBehaviorTree|UBlackboard|UAudioComponent|UCapsule|UPointLight|"
    r"UDirectionalLight|APlayerC|UWorld|UGameInstance|AGameMode|AGameState|"
    r"UActorComponent|USceneComponent|AActor|UObject|FMass|UMass|UPCG|"
    r"UInput|UEnhanced|UControlRig|UCharacterMovement)")


class VisionSystem:
    __slots__ = ("name", "section", "doc", "tokens", "weight", "is_project")

    def __init__(self, name, section, doc):
        self.name = name
        self.section = section
        self.doc = doc
        self.tokens = _camel_tokens(name)
        self.weight = DOMAIN_WEIGHT.get(section, 0.5)
        self.is_project = bool(self.tokens & PROJECT_TOKENS) and \
            not _ENGINE_BUILTIN.match(name)


def _camel_tokens(name: str) -> set:
    """CamelCase/underscore -> lowercase tokens, dropping UE affixes so
    UChimeraSandSoundComponent and SandSoundComponent share a stem. The
    leading UE type-prefix (UClass/AActor/FStruct/EEnum) is a DOUBLE capital
    glued to the stem (AErisaid), which no camel-boundary split catches —
    strip it first or 'erisaid' hides inside 'aerisaid'."""
    stem = re.sub(r"^[UAFE](?=[A-Z])", "", name)     # AErisaidActor -> ErisaidActor
    raw = re.sub(r"([a-z])([A-Z])", r"\1 \2", stem).replace("_", " ").lower().split()
    drop = {"u", "a", "f", "e", "component", "actor", "system", "subsystem",
            "manager", "chimera", "spec", "data", "ref", "the", "mass", "fragment"}
    return {t for t in raw if t not in drop and len(t) > 2}


def parse_vision() -> list:
    """The seed, machine-read: every top-level class in CHIMERA_VISION.py, with
    its § domain and one-line docstring. Deterministic (ast), no LM."""
    if not VISION.exists():
        return []
    src = VISION.read_text(encoding="utf-8", errors="replace")
    # map line number -> current section marker
    section_at = {}
    cur = "§0"
    for i, line in enumerate(src.splitlines(), start=1):
        m = re.match(r"#\s*(§\d+)\.", line)
        if m:
            cur = m.group(1)
        section_at[i] = cur
    systems = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            doc = (ast.get_docstring(node) or "").strip().split("\n")[0][:100]
            systems.append(VisionSystem(node.name, section_at.get(node.lineno, "§0"), doc))
    return systems


def _source_index() -> dict:
    """Everything the live project has to offer as realization evidence:
    declared C++ class names + all rep-battery feature stems + graduated set."""
    idx = {"classes": set(), "features": set(), "graduated": set()}
    if SOURCE_TREE.exists():
        for p in SOURCE_TREE.rglob("*.h"):
            for m in re.finditer(r"class\s+CHIMERA_API\s+(\w+)", p.read_text(
                    encoding="utf-8", errors="replace")):
                idx["classes"] |= _camel_tokens(m.group(1))
    try:
        from core.rep_engine import all_battery_features, status
        for f in all_battery_features():
            idx["features"] |= _camel_tokens(f.replace("/", "_"))
            if status(f).get("gate"):
                idx["graduated"] |= _camel_tokens(f.replace("/", "_"))
    except Exception:
        pass
    return idx


def realization(system: VisionSystem, idx: dict) -> float:
    """0..1: absent -> declared/built (0.5) -> feature-tracked (0.75) ->
    graduated (1.0). Token overlap is a HEURISTIC — the helm steers by it,
    it does not certify."""
    if not system.tokens:
        return 1.0                                   # unnameable stem: don't chase
    if system.tokens & idx["graduated"]:
        return 1.0
    hit_feature = bool(system.tokens & idx["features"])
    hit_class = bool(system.tokens & idx["classes"])
    if hit_feature and hit_class:
        return 0.8
    if hit_class:
        return 0.5
    if hit_feature:
        return 0.4
    return 0.0


def vision_gap() -> dict:
    """The seed-vs-state distance, focused on PROJECT systems (the game's
    content, not engine plumbing). Returns overall realized fraction + the
    ranked unrealized targets (biggest value-weighted gap first)."""
    systems = parse_vision()
    idx = _source_index()
    project = [s for s in systems if s.is_project]
    scored = []
    for s in project:
        r = realization(s, idx)
        gap_value = (1.0 - r) * s.weight             # unrealized x domain importance
        scored.append((gap_value, r, s))
    scored.sort(key=lambda t: -t[0])
    realized_frac = (sum(r for _g, r, _s in scored) / len(scored)) if scored else 1.0
    return {
        "total_project_systems": len(project),
        "realized_fraction": round(realized_frac, 3),
        "targets": [
            {"name": s.name, "section": s.section, "realization": round(r, 2),
             "gap_value": round(g, 2), "doc": s.doc}
            for g, r, s in scored if r < 0.75
        ],
    }


# --- the pressure gauges (all read from existing organs) --------------------

def gauges() -> dict:
    g = {}
    try:
        from core.rep_engine import all_battery_features, status
        stats = [status(f) for f in all_battery_features()]
        g["red_features"] = sum(1 for s in stats if s.get("reps") and s.get("recent_rate", 1) < 0.9)
        g["near_graduation"] = sum(1 for s in stats
                                   if not s.get("gate") and s.get("streak", 0) >= 5)
        g["graduated"] = sum(1 for s in stats if s.get("gate"))
        g["total_features"] = len(stats)
    except Exception:
        g["red_features"] = g["near_graduation"] = 0
    try:
        from core.malcolm import status as mstatus
        rows = mstatus()
        g["breaches"] = sum(1 for r in rows if r["state"] == "BREACH"
                            and r["family"] in ("hardware", "systemic"))
        gauge = next((r for r in rows if r["axis"] == "engine_surprise_rate_per_week"), None)
        g["emergence"] = gauge["value"] if gauge else None
    except Exception:
        g["breaches"] = 0
    try:
        from core.graphify_interface import load_dna_graph, collect_inheritance
        nodes = load_dna_graph().get("nodes", [])
        inh = collect_inheritance(nodes)
        g["stale_pains"] = sum(1 for p in inh.get("open_pains", []) if (p.get("age_days") or 0) >= 5)
    except Exception:
        g["stale_pains"] = 0
    try:
        from core.metronome import FEEL_LAST, FEEL_BANDS
        if FEEL_LAST.exists():
            d = json.loads(FEEL_LAST.read_text(encoding="utf-8"))
            g["feel_reds"] = sum(1 for m, b in FEEL_BANDS.items()
                                 if d.get(m) is not None and
                                 ((b.get("max") is not None and d[m] > b["max"]) or
                                  (b.get("min") is not None and d[m] < b["min"])))
        else:
            g["feel_reds"] = None
    except Exception:
        g["feel_reds"] = None
    try:
        from core.circadian import status as cstatus
        cs = cstatus()
        g["night_due"] = cs["night_due"]
        g["phase"] = cs["phase"]
    except Exception:
        g["night_due"] = False
        g["phase"] = "day"
    g["vision"] = vision_gap()
    return g


def steer() -> dict:
    """Score focus categories by pressure; highest is the heading. Contain and
    Consolidate can override (a breach or the night's call trump routine work)."""
    g = gauges()
    total = max(g.get("total_features", 1), 1)
    v = g["vision"]
    # each pressure in 0..1
    cats = {
        "Contain":   1.0 if g.get("breaches", 0) else 0.0,
        "Fix":       min(1.0, g.get("red_features", 0) / max(total * 0.25, 1)),
        "Graduate":  min(1.0, g.get("near_graduation", 0) / max(total * 0.15, 1)),
        "Build":     1.0 - v["realized_fraction"],   # rounded once, below, with the rest
        "Verify":    min(1.0, g.get("stale_pains", 0) / 8.0),
        "Polish":    (min(1.0, (g.get("feel_reds") or 0) / 3.0)
                      if g.get("feel_reds") is not None else 0.0),
        "Consolidate": 1.0 if g.get("night_due") else 0.0,
    }
    # overrides: a breach is an emergency; the night is a scheduled duty
    if cats["Contain"] >= 1.0:
        heading = "Contain"
    elif cats["Consolidate"] >= 1.0 and g.get("phase") == "night":
        heading = "Consolidate"
    else:
        heading = max(cats, key=cats.get)
    target = None
    if heading == "Build" and v["targets"]:
        t = v["targets"][0]
        target = f"{t['name']} ({t['section']}, realized {t['realization']:.0%}) — {t['doc']}"
    elif heading == "Consolidate":
        target = "python -m core.circadian tick --run"
    return {"heading": heading, "scores": {k: round(x, 2) for k, x in cats.items()},
            "target": target, "realized_fraction": v["realized_fraction"]}


def preflight_line() -> str:
    s = steer()
    lines = [f"[0.7] Helm: steer -> {s['heading'].upper()}  "
             f"(vision realized {s['realized_fraction']:.0%}; "
             + ", ".join(f"{k} {v:.1f}" for k, v in sorted(
                 s["scores"].items(), key=lambda kv: -kv[1])[:3]) + ")"]
    if s["target"]:
        lines.append(f"    -> {s['target'][:110]}")
    lines.append("    heading: python -m core.helm   |   vision gap: python -m core.helm targets")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("targets")
    sub.add_parser("gauges")
    args = parser.parse_args(argv)
    if args.cmd == "targets":
        v = vision_gap()
        print(f"Vision (true north): {v['total_project_systems']} project systems, "
              f"{v['realized_fraction']:.0%} realized. Biggest gaps:")
        for t in v["targets"][:15]:
            print(f"  [{t['section']}] {t['name']:32s} realized {t['realization']:.0%}  "
                  f"gap {t['gap_value']:.2f}  {t['doc'][:50]}")
    elif args.cmd == "gauges":
        print(json.dumps({k: v for k, v in gauges().items() if k != "vision"}, indent=1))
    else:
        s = steer()
        print(f"HELM -> steer toward {s['heading'].upper()}")
        print(f"  vision realized: {s['realized_fraction']:.0%}")
        print("  focus pressures: " + ", ".join(
            f"{k}={v}" for k, v in sorted(s["scores"].items(), key=lambda kv: -kv[1])))
        if s["target"]:
            print(f"  target: {s['target']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
