"""rep_engine — resolution through repetition (the dog-sit threshold, mechanized).

THE IDEA (human vision, 2026-07-12): a behavior emerges at a repetition
threshold (~400 labeled trials trains a dog to sit), not from a handful of
perfect heuristics. Chimera's loop currently produces ~1 elimination per
feature per DAY (H-31..H-34 took four nights to binary-search one bug).
This engine raises constraint-rep throughput by ~2 orders of magnitude by
shrinking the rep unit from "beat script in PIE" (minutes, editor-bound) to
the CONSTRAINT ATOM (one machine-checkable predicate, milliseconds,
editor-free by default). AAA fidelity = the conjunction of hundreds of small
constraints held simultaneously; you choose resolution by choosing battery
size, and the engine fills the container by repetition.

MECHANICS
  atom      one typed predicate {id, feature, tier, kind, probe, provenance}.
            kind=headless runs here in milliseconds; kind=pie is exported for
            the sleepwalker batch (never silently counted as pass).
  battery   a feature's atom set, persisted in docs/rep_batteries/<feature>.json
            (committed; additive/idempotent by atom id — archive-never-delete).
  ledger    docs/world/reps.db (SQLite, machine-local, gitignored with the
            rest of docs/world/). One row per verdict. 8k rows/day is a
            rounding error post-world_store migration.
  shaping   successive approximation, the dog-trainer rule: criteria rise only
            on a passing streak. Tiers: 0 exists -> 1 behaves -> 2 measures ->
            3 perceptual -> 4 comparative. Promotion = streak on current tier.
  rep gate  collapse eligibility: >= REP_GATE reps AND a recent >=95% streak.
            Advisory by default; CHIMERA_ENFORCE_REP_GATE=1 makes it hard.

ATOM SOURCES (generated, never hand-written)
  A assets     Content/** standard battery (pairing, presence, known traps)
  B reflection UPROPERTY/UCLASS scan of ProceduralGenerated (declared => used;
               every component => spawned/registered somewhere: H-34 generalized)
  C h-rules    encodable promoted heuristics from CLAUDE.md become probes
               (H-17 beat actions registered; H-21 verbs have bodies; H-31
               no fallback sentinels; H-2 no desktop captures)
  D eliminations  Elimination nodes in the DNA graph -> permanent regression
               atoms (a rejection is a chisel that strikes every night forever)
  E dsl        declared spec tokens must exist in generated code

CLI
  python -m core.rep_engine build [--feature X]     compose/refresh batteries
  python -m core.rep_engine run   [--feature X] [--runs N]
  python -m core.rep_engine status [--feature X]
  python -m core.rep_engine gate --feature X
  python -m core.rep_engine tend                    build + run + summary (dream_loop hook)
  python -m core.rep_engine export-pie              manifest of PIE-bound atoms
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # E:/PythonChimera/Chimera
SOURCE_TREE = "Source/Chimera/ProceduralGenerated"
BATTERY_DIR = ROOT / "docs" / "rep_batteries"
PIE_MANIFEST = ROOT / "docs" / "rep_batteries" / "pie_manifest.json"
DB_PATH = ROOT / "docs" / "world" / "reps.db"
CLAUDE_MD = ROOT.parent / "CLAUDE.md"

# shaping / gate tuning (the dog numbers). per_atom scales the rep threshold
# to the battery: a 1-atom feature needs 25 trials of its one constraint, not
# 200 nightly runs (~7 months) — the threshold measures TRIALS PER CONSTRAINT,
# capped at min_reps for big batteries (tuning pass 2026-07-12).
REP_GATE = dict(min_reps=200, per_atom=25, streak_runs=8, streak_rate=0.95)
PROMOTE = dict(streak_runs=8, streak_rate=0.95, min_reps_per_tier=100)
TIER_NAMES = {0: "exists", 1: "behaves", 2: "measures", 3: "perceptual", 4: "comparative"}

# manual-lane directory -> owning feature (loop-built files under ProceduralGenerated)
DIR_FEATURE = {
    "Sound": "Ground_Sand_Sound",
    "Tools": "Verb_Shovel",
    "Interactions": "Verb_PickUp",
    "UI": "UI_Suit_HUD",
    "NPC": "NPC_Basic_AI",
    "Save": "System_SaveGame",
}

# tb-0001 accessor contract — the PhD student's telemetry surface
TELEMETRY_ACCESSORS = [
    "GetFootstepSyncEventCount", "GetFootstepSyncAvgLatencyMs",
    "GetFootstepSyncMaxLatencyMs", "GetVolumeScalesWithSpeed",
    "ClearFootstepSyncTelemetry",
]

# the documented template-stamp trap (CLAUDE.md troubleshooting §demo level)
TEMPLATE_STAMP_MD5 = "b734cff5"   # prefix match on the known-bad md5


# ---------------------------------------------------------------------------
# file cache — hundreds of atoms grep the same tree; read each file once/run
# ---------------------------------------------------------------------------

class _FileCache:
    def __init__(self, root: Path):
        self.root = root
        self._text: dict = {}

    def paths(self, rel_root: str, pattern: str) -> list:
        base = self.root / rel_root
        if not base.exists():
            return []
        return sorted(p for p in base.rglob(pattern) if p.is_file())

    def text(self, path: Path) -> str:
        key = str(path)
        if key not in self._text:
            try:
                self._text[key] = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                self._text[key] = ""
        return self._text[key]


# ---------------------------------------------------------------------------
# probes — each returns (passed: bool|None, evidence: str). None = skip (PIE).
# ---------------------------------------------------------------------------

def _probe_glob_nonempty(spec: dict, cache: _FileCache):
    hits = [p for p in (cache.root.glob(spec["pattern"]))]
    return (len(hits) > 0, f"{len(hits)} match(es) for {spec['pattern']}")


def _probe_file_contains(spec: dict, cache: _FileCache):
    p = cache.root / spec["path"]
    if not p.exists():
        return (False, f"missing file {spec['path']}")
    ok = re.search(spec["regex"], cache.text(p)) is not None
    return (ok, f"{'found' if ok else 'ABSENT'}: /{spec['regex']}/ in {spec['path']}")


def _probe_tree_contains(spec: dict, cache: _FileCache):
    rx = re.compile(spec["regex"])
    for p in cache.paths(spec.get("root", SOURCE_TREE), spec.get("glob", "*.*")):
        if rx.search(cache.text(p)):
            return (True, f"found in {p.relative_to(cache.root)}")
    return (False, f"ABSENT in tree {spec.get('root', SOURCE_TREE)}: /{spec['regex']}/")


def _probe_tree_lacks(spec: dict, cache: _FileCache):
    """The inversion probe: PASSES on absence. A negative constraint made
    executable — 'this tree must NOT contain X' (fallback sentinels, desktop
    captures, junk writes)."""
    rx = re.compile(spec["regex"])
    for p in cache.paths(spec.get("root", SOURCE_TREE), spec.get("glob", "*.*")):
        m = rx.search(cache.text(p))
        if m:
            return (False, f"FORBIDDEN /{spec['regex']}/ present in "
                           f"{p.relative_to(cache.root)}: '{m.group(0)[:60]}'")
    return (True, f"clean: /{spec['regex']}/ absent from {spec.get('root', SOURCE_TREE)}")


def _probe_json_valid(spec: dict, cache: _FileCache):
    bad = []
    for p in cache.root.glob(spec["pattern"]):
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:                      # noqa: BLE001 — verdict, not crash
            bad.append(f"{p.name}: {e}")
    return (not bad, "; ".join(bad) or f"all json under {spec['pattern']} parse")


def _probe_file_md5_not(spec: dict, cache: _FileCache):
    p = cache.root / spec["path"]
    if not p.exists():
        return (False, f"missing file {spec['path']}")
    digest = hashlib.md5(p.read_bytes()).hexdigest()
    ok = not digest.startswith(spec["md5_prefix"].lower())
    return (ok, f"md5={digest[:8]} ({'OK' if ok else 'TEMPLATE-STAMPED — known trap'})")


def parse_sleepwalker_actions(source_text: str) -> set:
    """The registered-action vocabulary, parsed from sleepwalker._do_action's
    own dispatch (`"key" in a` / `a.get("key")` patterns) — self-maintaining:
    when the sleepwalker grows a verb, the registry grows with it (H-17)."""
    keys = set(re.findall(r'"([a-z_]+)"\s+in\s+a', source_text))
    keys |= set(re.findall(r'a\.get\(\s*"([a-z_]+)"', source_text))
    keys |= {"hold_s", "shift"}                    # modifiers, not actions
    return keys


def _probe_beats_registered(spec: dict, cache: _FileCache):
    sw = cache.root / "core" / "sleepwalker.py"
    if not sw.exists():
        return (None, "sleepwalker.py not found; skip")
    registry = parse_sleepwalker_actions(cache.text(sw))
    unknown = []
    for p in cache.root.glob("docs/beats/*.beats.json"):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            unknown.append(f"{p.name}: unparseable")
            continue
        beats = doc.get("beats", doc if isinstance(doc, list) else [])
        for beat in beats:
            for action in beat.get("actions", []) if isinstance(beat, dict) else []:
                if isinstance(action, dict) and not (set(action) & registry):
                    unknown.append(f"{p.name}:{beat.get('name', '?')}:{sorted(action)[:2]}")
    return (not unknown,
            "; ".join(unknown[:6]) or f"all beat actions in registry ({len(registry)} verbs)")


def _probe_graph_status(spec: dict, cache: _FileCache):
    try:
        from core.graphify_interface import graphify_query
        nodes = graphify_query("feature", spec["feature"]) or []
        if not nodes:
            return (False, f"no feature node for {spec['feature']}")
        status = (nodes[-1].get("parameters") or {}).get("status") or nodes[-1].get("status", "")
        forbidden = spec.get("forbidden", ["unknown"])
        ok = all(f not in str(status) for f in forbidden)
        return (ok, f"status={status}")
    except Exception as e:                          # noqa: BLE001
        return (None, f"graph unavailable; skip ({e})")


def _probe_envelope_axis(spec: dict, cache: _FileCache):
    """The container's fence line, checked at rep frequency (core.malcolm).
    Skips honestly when the axis has no sensor yet; fails on BREACH or
    BELOW-FLOOR (a floor failure is a sterility warning, and it counts)."""
    try:
        from core.malcolm import load_envelope, measure_axis, axis_state
        env = load_envelope()
        axis = env["axes"].get(spec["axis"])
        if axis is None:
            return (None, f"no wall named {spec['axis']}; skip")
        value, evidence = measure_axis(spec["axis"])
        state = axis_state(axis, value)
        if state == "UNMEASURED":
            return (None, f"{spec['axis']} unmeasured; skip ({evidence})")
        ok = state in ("OK", "WARN")
        return (ok, f"{spec['axis']}={value} {state} "
                    f"[{axis.get('min')},{axis.get('max')}] ({evidence[:80]})")
    except Exception as e:                          # noqa: BLE001
        return (None, f"malcolm unavailable; skip ({e})")


def _probe_feel_metric(spec: dict, cache: _FileCache):
    """Tier-3 feel wall (core.metronome): reads docs/world/feel_last.json —
    refreshed by every sleepwalk. Skips honestly when no walk has run."""
    try:
        from core.metronome import FEEL_LAST
        if not FEEL_LAST.exists():
            return (None, "no feel snapshot yet (run a sleepwalk); skip")
        data = json.loads(FEEL_LAST.read_text(encoding="utf-8"))
        val = data.get(spec["metric"])
        if val is None:
            return (None, f"{spec['metric']} unmeasured in last walk; skip")
        mx, mn = spec.get("max"), spec.get("min")
        ok = (mx is None or val <= mx) and (mn is None or val >= mn)
        return (ok, f"{spec['metric']}={val} band[min={mn},max={mx}] "
                    f"(session {data.get('session', '?')})")
    except Exception as e:                          # noqa: BLE001
        return (None, f"metronome unavailable; skip ({e})")


PROBES = {
    "glob_nonempty": _probe_glob_nonempty,
    "file_contains": _probe_file_contains,
    "tree_contains": _probe_tree_contains,
    "tree_lacks": _probe_tree_lacks,
    "json_valid": _probe_json_valid,
    "file_md5_not": _probe_file_md5_not,
    "beats_registered": _probe_beats_registered,
    "graph_status": _probe_graph_status,
    "envelope_axis": _probe_envelope_axis,
    "feel_metric": _probe_feel_metric,
}


# ---------------------------------------------------------------------------
# atoms & batteries
# ---------------------------------------------------------------------------

def _atom_id(feature: str, probe_type: str, payload: str) -> str:
    h = hashlib.sha1(f"{feature}|{probe_type}|{payload}".encode()).hexdigest()[:12]
    return f"atom_{h}"


def make_atom(feature: str, tier: int, probe_type: str, spec: dict,
              desc: str, provenance: str, kind: str = "headless") -> dict:
    return {
        "id": _atom_id(feature, probe_type, json.dumps(spec, sort_keys=True)),
        "feature": feature, "tier": tier, "kind": kind,
        "probe": {"type": probe_type, **spec},
        "desc": desc, "provenance": provenance,
    }


def _safe_name(feature: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", feature)


def load_battery(feature: str) -> list:
    p = BATTERY_DIR / f"{_safe_name(feature)}.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []   # non-battery json (drift ledger etc.)
    except Exception:
        return []


def save_battery(feature: str, atoms: list) -> None:
    BATTERY_DIR.mkdir(parents=True, exist_ok=True)
    p = BATTERY_DIR / f"{_safe_name(feature)}.json"
    p.write_text(json.dumps(atoms, indent=1), encoding="utf-8")


def merge_battery(feature: str, new_atoms: list) -> list:
    """Additive & idempotent by atom id — the container only grows (raising
    criteria = adding atoms); pruning is a deliberate manual act."""
    existing = {a["id"]: a for a in load_battery(feature)}
    for a in new_atoms:
        existing.setdefault(a["id"], a)
    merged = sorted(existing.values(), key=lambda a: (a["tier"], a["id"]))
    save_battery(feature, merged)
    return merged


def all_battery_features() -> list:
    """Battery files only — a battery is a json LIST of atoms; sibling json
    (pie manifest, drift ledger) is data the Book reads, not a battery."""
    if not BATTERY_DIR.exists():
        return []
    out = []
    for p in sorted(BATTERY_DIR.glob("*.json")):
        if p.name == PIE_MANIFEST.name:
            continue
        try:
            if isinstance(json.loads(p.read_text(encoding="utf-8")), list):
                out.append(p.stem)
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# generators — where hundreds of atoms come from, no hand-writing
# ---------------------------------------------------------------------------

def gen_assets(cache: _FileCache) -> list:
    atoms = []
    # every audio source has an imported engine asset (pairing)
    for wav in cache.paths("Content/Audio", "*.wav"):
        rel = wav.relative_to(cache.root).as_posix()
        pair = rel[:-4] + ".uasset"
        atoms.append(make_atom(
            "Ground_Sand_Sound", 0, "glob_nonempty", {"pattern": pair},
            f"{wav.name} imported as uasset", "asset-standards:pairing"))
    atoms.append(make_atom("Ground_Sand_Sound", 0, "glob_nonempty",
                           {"pattern": "Content/Audio/Footsteps/SOURCES.md"},
                           "audio license ledger present", "asset-standards:license"))
    atoms.append(make_atom("Ground_Sand_Surface", 0, "glob_nonempty",
                           {"pattern": "Content/Levels/L_RegolithYard.umap"},
                           "demo level exists", "asset-standards:level"))
    atoms.append(make_atom("Demo_Level", 0, "file_md5_not",
                           {"path": "Content/Levels/chimeradefaultlevel.umap",
                            "md5_prefix": TEMPLATE_STAMP_MD5},
                           "default level is NOT template-stamped",
                           "CLAUDE.md troubleshooting: template-stamp trap"))
    atoms.append(make_atom("Sleepwalker_Beats", 0, "json_valid",
                           {"pattern": "docs/beats/*.beats.json"},
                           "all beat scripts parse", "asset-standards:beats"))
    return atoms


_UPROP_RE = re.compile(
    r"UPROPERTY\s*\([^)]*\)\s*\n\s*(?:[\w:<>*&\s]+?)\b(\w+)\s*(?:=[^;]*)?;",
    re.MULTILINE)
_UCLASS_COMPONENT_RE = re.compile(r"class\s+CHIMERA_API\s+(U\w+Component)\b")


def _dir_feature(path: Path, cache: _FileCache) -> str:
    try:
        rel = path.relative_to(cache.root / SOURCE_TREE)
        top = rel.parts[0] if len(rel.parts) > 1 else ""
    except ValueError:
        top = ""
    return DIR_FEATURE.get(top, f"subsystem/{top or 'root'}")


def gen_code_reflection(cache: _FileCache) -> list:
    """B: every declared UPROPERTY must be USED beyond its declaration (the
    H-21 inversion — metadata is not behavior); every UCLASS component must
    be SPAWNED/REGISTERED somewhere (H-34, generalized to all components)."""
    atoms = []
    headers = cache.paths(SOURCE_TREE, "*.h")
    cpp_blob = "\n".join(cache.text(p) for p in cache.paths(SOURCE_TREE, "*.cpp"))
    for h in headers:
        feature = _dir_feature(h, cache)
        text = cache.text(h)
        for prop in sorted(set(_UPROP_RE.findall(text))):
            if len(prop) < 4:
                continue
            atoms.append(make_atom(
                feature, 1, "tree_contains",
                {"root": SOURCE_TREE, "glob": "*.cpp", "regex": rf"\b{re.escape(prop)}\b"},
                f"UPROPERTY {prop} ({h.name}) is used in a .cpp, not dead metadata",
                f"reflection:UPROPERTY:{h.name}"))
        for comp in sorted(set(_UCLASS_COMPONENT_RE.findall(text))):
            atoms.append(make_atom(
                feature, 0, "tree_contains",
                {"root": SOURCE_TREE, "glob": "*.cpp",
                 "regex": rf"(CreateDefaultSubobject|NewObject)\s*<\s*{re.escape(comp)}\b"
                          rf"|{re.escape(comp)}[^;\n]*RegisterComponent"},
                f"component {comp} is spawned/registered somewhere (H-34)",
                f"reflection:UCLASS:{h.name}"))
        _ = cpp_blob  # cached for the probes above via tree_contains
    return atoms


def parse_h_rules(md_text: str) -> list:
    """[H-n] lines from CLAUDE.md — the promoted constitution."""
    return re.findall(r"\*\*\[(H-\d+)[^\]]*\]\*\*\s*(.+)", md_text)


def gen_h_rules(cache: _FileCache) -> list:
    """C: the encodable constitution. Each promoted heuristic that CAN be a
    machine probe becomes one; the rest become PIE/provenance atoms so the
    battery is honest about what only the editor can verify."""
    atoms = [
        make_atom("Sleepwalker_Beats", 0, "beats_registered", {},
                  "beat scripts declare only registered sleepwalker actions",
                  "H-17"),
        make_atom("Verb_Shovel", 1, "tree_contains",
                  {"root": SOURCE_TREE, "glob": "*.cpp", "regex": r"::Dig\s*\("},
                  "shovel verb has a body, not just metadata", "H-21"),
        make_atom("audio_visual_sync/report_telemetry", 2, "tree_lacks",
                  {"root": f"{SOURCE_TREE}/Sound", "glob": "*.cpp",
                   "regex": r"=\s*999(\.0f?)?\b"},
                  "no hardcoded 999 fallback sentinel in Sound (defaults mean "
                  "the backend isn't populating — H-31/H-32 smell)", "H-31"),
        make_atom("MCP_Pathways", 0, "tree_lacks",
                  {"root": "core", "glob": "*.py",
                   "regex": r"mode\s*=\s*[\"']desktop[\"']"},
                  "no desktop screenshot captures anywhere in core", "H-2"),
        make_atom("audio_visual_sync/telemetry_accessors", 0, "tree_contains",
                  {"root": SOURCE_TREE, "glob": "*.*",
                   "regex": r"(CreateDefaultSubobject|NewObject)\s*<\s*USandSoundComponent"
                            r"|SandSoundComponent[^;\n]*RegisterComponent"},
                  "SandSoundComponent attached at construction/BeginPlay (H-34 root case)",
                  "H-34"),
    ]
    for accessor in TELEMETRY_ACCESSORS:
        atoms.append(make_atom(
            "audio_visual_sync/telemetry_accessors", 1, "tree_contains",
            {"root": SOURCE_TREE, "glob": "*.*", "regex": rf"\b{accessor}\b"},
            f"telemetry accessor {accessor} exists (tb-0001 MCP contract)",
            "tb-0001"))
    # rules only PIE can judge stay in the battery as exported atoms
    for h_id, rule in parse_h_rules(cache.text(CLAUDE_MD) if CLAUDE_MD.exists() else ""):
        if h_id in ("H-14", "H-19", "H-22", "H-24", "H-25", "H-28", "H-29"):
            atoms.append(make_atom("Sleepwalker_Beats", 2, "pie",
                                   {"rule": h_id, "note": rule[:140]},
                                   f"{h_id} (PIE-judged): {rule[:80]}",
                                   h_id, kind="pie"))
    return atoms


def gen_eliminations(cache: _FileCache) -> list:
    """D: every Elimination node in the DNA graph becomes a permanent
    regression atom. A rejection is a chisel that strikes every night."""
    atoms = []
    try:
        from core.graphify_interface import load_dna_graph
        nodes = load_dna_graph().get("nodes", [])
    except Exception:
        return atoms
    for n in nodes:
        if n.get("type") != "Elimination":
            continue
        feature = n.get("feature", "unattributed")
        probe = n.get("probe") or {}
        if probe.get("type") in PROBES:
            spec = {k: v for k, v in probe.items() if k != "type"}
            atoms.append(make_atom(feature, int(n.get("tier", 1)), probe["type"], spec,
                                   f"regression: {n.get('boundary', '')[:100]}",
                                   f"elimination:{n.get('id', '?')}"))
        else:
            atoms.append(make_atom(feature, int(n.get("tier", 2)), "pie",
                                   {"boundary": n.get("boundary", "")[:140]},
                                   f"regression (PIE): {n.get('boundary', '')[:100]}",
                                   f"elimination:{n.get('id', '?')}", kind="pie"))
    return atoms


_DSL_KEY_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]{7,})\s*[:=]", re.MULTILINE)

# Tokens the PIPELINE consumes (uproject/Build.cs/config), never expected to
# surface as C++ identifiers — probing generated code for them is a category
# error (triage 2026-07-12: the config class).
DSL_CONFIG_TOKENS = {"engine_version", "target_platforms", "network_model",
                     "module_dependencies"}


def _camel(token: str) -> str:
    return "".join(w.capitalize() for w in token.split("_"))


def gen_dsl_fidelity(cache: _FileCache, cap: int = 160) -> list:
    """E: declared spec tokens must surface in generated code — the DSL is
    the top of the top-down flow; silence in the C++ is drift.
    Probe v2 (triage 2026-07-12): match snake OR CamelCase (the generator
    emits identifiers in CamelCase — 13 false reds came from probing the
    literal snake token), scan all of Source/ (Build.cs included), and skip
    the config-token class entirely."""
    atoms = []
    for spec_file in cache.paths("tests/dsl_grammar", "*.chimera"):
        keys = sorted(set(_DSL_KEY_RE.findall(cache.text(spec_file))))[:cap]
        for key in keys:
            if key in DSL_CONFIG_TOKENS:
                continue
            atoms.append(make_atom(
                "System_DSL_Fidelity", 0, "tree_contains",
                {"root": "Source", "glob": "*.*",
                 "regex": rf"({re.escape(key)}|{re.escape(_camel(key))})"},
                f"DSL token '{key}' ({spec_file.name}) surfaces in Source "
                f"(snake or CamelCase)",
                f"dsl2:{spec_file.name}"))
    return atoms


def gen_envelope(cache: _FileCache) -> list:
    """F: the container's walls as atoms (core.malcolm) — every envelope axis
    with a headless sensor becomes a fence-line check run at rep frequency;
    PIE-only axes are exported honestly as pie atoms."""
    atoms = []
    try:
        from core.malcolm import load_envelope
        env = load_envelope()
    except Exception:
        return atoms
    headless_axes = {"open_board_tasks", "atoms_per_battery", "decomposition_depth",
                     "generated_loc", "generated_files", "graph_nodes",
                     "heuristics_per_night", "engine_surprise_rate_per_week",
                     # sensor-fed since the sleepwalk wire (tuning pass):
                     # every walk refreshes telemetry_last.json; the probe
                     # skips honestly when the snapshot is absent.
                     "frame_time_ms", "system_memory_gb"}
    for name, axis in env.get("axes", {}).items():
        kind = "headless" if name in headless_axes else "pie"
        probe = ({"type": "envelope_axis", "axis": name} if kind == "headless"
                 else {"type": "pie", "axis": name,
                       "note": "telemetry/PIE-measured wall (frame/vram/dots/voices)"})
        atoms.append(make_atom(
            "Malcolm_Envelope", 2, probe["type"],
            {k: v for k, v in probe.items() if k != "type"},
            f"container wall {name} holds: band [{axis.get('min')},{axis.get('max')}] "
            f"{axis.get('unit', '')} ({axis['source']['kind']})",
            "malcolm:envelope", kind=kind))
    return atoms


def gen_feel(cache: _FileCache) -> list:
    """G: the Metronome's tier-3 feel walls — the first perceptual atoms.
    Bands from game-feel canon (~100ms response rule)."""
    try:
        from core.metronome import FEEL_BANDS
    except Exception:
        return []
    return [make_atom("Game_Feel", 3, "feel_metric", {"metric": name, **band},
                      f"feel wall {name} holds band {band} (metronome, "
                      f"mined from chronicle x UE log)",
                      "metronome:feel-canon")
            for name, band in FEEL_BANDS.items()]


GENERATORS = [gen_assets, gen_code_reflection, gen_h_rules, gen_eliminations,
              gen_dsl_fidelity, gen_envelope, gen_feel]


def build(feature: str = None, cache: _FileCache = None) -> dict:
    """Compose/refresh batteries from all generators. Returns {feature: n_atoms}."""
    cache = cache or _FileCache(ROOT)
    by_feature: dict = {}
    for gen in GENERATORS:
        for atom in gen(cache):
            by_feature.setdefault(atom["feature"], []).append(atom)
    out = {}
    for feat, atoms in sorted(by_feature.items()):
        if feature and _safe_name(feat) != _safe_name(feature):
            continue
        out[feat] = len(merge_battery(feat, atoms))
    return out


# ---------------------------------------------------------------------------
# ledger — the rep counter (docs/world/reps.db)
# ---------------------------------------------------------------------------

def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS reps(
        id INTEGER PRIMARY KEY, ts REAL, run_id TEXT, feature TEXT,
        atom_id TEXT, passed INTEGER, evidence TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_reps_feat ON reps(feature, ts)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_reps_run ON reps(feature, run_id)")
    con.execute("""CREATE TABLE IF NOT EXISTS promotions(
        feature TEXT PRIMARY KEY, tier INTEGER, ts REAL, note TEXT)""")
    return con


def run(feature: str = None, runs: int = 1, cache: _FileCache = None) -> dict:
    """Execute batteries; record every verdict. Skips (PIE atoms, unavailable
    probes) are recorded as neither pass nor fail — never silently counted."""
    features = ([_f for _f in all_battery_features()
                 if not feature or _f == _safe_name(feature)])
    con = _db()
    summary: dict = {}
    for _ in range(max(1, runs)):
        cache_run = cache or _FileCache(ROOT)
        run_id = f"run_{time.time_ns()}"
        for feat_file in features:
            atoms = load_battery(feat_file)
            passed = failed = skipped = 0
            rows = []
            for atom in atoms:
                probe = atom["probe"]
                fn = PROBES.get(probe["type"])
                if atom["kind"] != "headless" or fn is None:
                    skipped += 1
                    continue
                ok, evidence = fn({k: v for k, v in probe.items() if k != "type"},
                                  cache_run)
                if ok is None:
                    skipped += 1
                    continue
                rows.append((time.time(), run_id, atom["feature"], atom["id"],
                             1 if ok else 0, evidence[:300]))
                passed += 1 if ok else 0
                failed += 0 if ok else 1
            if rows:
                con.executemany(
                    "INSERT INTO reps(ts, run_id, feature, atom_id, passed, evidence)"
                    " VALUES(?,?,?,?,?,?)", rows)
            s = summary.setdefault(feat_file, dict(passed=0, failed=0, skipped=0, runs=0))
            s["passed"] += passed
            s["failed"] += failed
            s["skipped"] += skipped
            s["runs"] += 1
        con.commit()
    con.close()
    return summary


def _run_rates(con: sqlite3.Connection, feature: str, last_n: int) -> list:
    """Per-run pass rates, newest first, for the feature's last N runs."""
    rows = con.execute(
        "SELECT run_id, SUM(passed), COUNT(*) FROM reps WHERE feature=? "
        "GROUP BY run_id ORDER BY MAX(ts) DESC LIMIT ?",
        (feature, last_n)).fetchall()
    return [(r[1] or 0) / r[2] for r in rows if r[2]]


def status(feature_file: str) -> dict:
    atoms = load_battery(feature_file)
    features_in_battery = sorted({a["feature"] for a in atoms}) or [feature_file]
    feat = features_in_battery[0]
    con = _db()
    total = con.execute("SELECT COUNT(*) FROM reps WHERE feature=?", (feat,)).fetchone()[0]
    rates = _run_rates(con, feat, PROMOTE["streak_runs"])
    streak = 0
    for r in rates:
        if r >= PROMOTE["streak_rate"]:
            streak += 1
        else:
            break
    row = con.execute("SELECT tier FROM promotions WHERE feature=?", (feat,)).fetchone()
    tier = row[0] if row else 0
    recent = (sum(rates) / len(rates)) if rates else 0.0
    con.close()
    max_tier = max((a["tier"] for a in atoms), default=0)
    return dict(feature=feat, battery=len(atoms),
                pie=sum(1 for a in atoms if a["kind"] == "pie"),
                reps=total, recent_rate=recent, streak=streak,
                tier=tier, max_tier=max_tier,
                gate=rep_gate(feat)[0])


def rep_gate(feature: str) -> tuple:
    """Collapse eligibility by repetition: the dog-sit threshold as a gate.
    (eligible, reason). Threshold scales to the battery — trials PER
    CONSTRAINT, capped at min_reps. Advisory unless CHIMERA_ENFORCE_REP_GATE=1."""
    con = _db()
    total = con.execute("SELECT COUNT(*) FROM reps WHERE feature=?", (feature,)).fetchone()[0]
    rates = _run_rates(con, feature, REP_GATE["streak_runs"])
    con.close()
    battery_size = len(load_battery(feature)) or 1
    required = min(REP_GATE["min_reps"], battery_size * REP_GATE["per_atom"])
    if total == 0:
        return (False, f"no reps recorded for '{feature}' "
                       f"(need >={required}) — build+run a battery")
    if total < required:
        return (False, f"{total}/{required} reps — below threshold "
                       f"({battery_size} atoms x {REP_GATE['per_atom']}/atom, "
                       f"cap {REP_GATE['min_reps']})")
    if len(rates) < REP_GATE["streak_runs"]:
        return (False, f"only {len(rates)}/{REP_GATE['streak_runs']} runs on record")
    weak = [f"{r:.0%}" for r in rates if r < REP_GATE["streak_rate"]]
    if weak:
        return (False, f"streak broken: recent runs at {', '.join(weak[:3])} "
                       f"(need >={REP_GATE['streak_rate']:.0%} x{REP_GATE['streak_runs']})")
    return (True, f"{total} reps (>= {required} for {battery_size} atoms), "
                  f"{REP_GATE['streak_runs']}-run streak >={REP_GATE['streak_rate']:.0%}")


def maybe_promote(feature_file: str) -> str:
    """Shaping: raise criteria only on a streak (the 8-of-10 trainer rule).
    Promotion is the ONLY rep event recorded to the DNA graph — summaries,
    never the 8k/day firehose."""
    st = status(feature_file)
    feat = st["feature"]
    if st["tier"] >= st["max_tier"]:
        return ""
    if (st["reps"] >= PROMOTE["min_reps_per_tier"] * (st["tier"] + 1)
            and st["streak"] >= PROMOTE["streak_runs"]):
        new_tier = st["tier"] + 1
        con = _db()
        con.execute("INSERT OR REPLACE INTO promotions(feature, tier, ts, note) "
                    "VALUES(?,?,?,?)",
                    (feat, new_tier, time.time(),
                     f"streak {st['streak']} @ {st['recent_rate']:.0%}"))
        con.commit()
        con.close()
        try:
            from core.graphify_interface import record_phase
            record_phase(f"rep_promotion:{feat}",
                         f"tier {st['tier']} -> {new_tier} "
                         f"({TIER_NAMES.get(new_tier, '?')}) after {st['reps']} reps")
        except Exception:
            pass
        return f"{feat}: tier {st['tier']} -> {new_tier} ({TIER_NAMES.get(new_tier)})"
    return ""


def status_lines(limit: int = 8) -> list:
    lines = []
    for feat_file in all_battery_features()[:limit]:
        s = status(feat_file)
        gate_mark = "READY" if s["gate"] else f"tier {s['tier']}/{s['max_tier']}"
        lines.append(
            f"{s['feature'][:34]:34s} {s['reps']:>6} reps  "
            f"{s['recent_rate']:>4.0%}  streak {s['streak']:>2}  "
            f"battery {s['battery']:>3} ({s['pie']} pie)  {gate_mark}")
    return lines


def prune_to_current(feature: str, cache: _FileCache = None) -> tuple:
    """Deliberate battery surgery: drop atoms whose ids no longer appear in
    the CURRENT generator output for this feature (stale probe specs after a
    fidelity upgrade). Prints what it removes — pruning is loud by design;
    the ledger keeps the old atoms' rep history untouched (archive-never-
    delete applies to evidence, not to obsolete probes)."""
    cache = cache or _FileCache(ROOT)
    current_ids = set()
    for gen in GENERATORS:
        for atom in gen(cache):
            if _safe_name(atom["feature"]) == _safe_name(feature):
                current_ids.add(atom["id"])
    existing = load_battery(feature)
    keep = [a for a in existing if a["id"] in current_ids]
    dropped = [a for a in existing if a["id"] not in current_ids]
    save_battery(feature, keep)
    return keep, dropped


def export_pie() -> int:
    """Manifest of PIE-bound atoms for the sleepwalker's nightly batch."""
    atoms = []
    for feat_file in all_battery_features():
        atoms += [a for a in load_battery(feat_file) if a["kind"] == "pie"]
    PIE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    PIE_MANIFEST.write_text(json.dumps(atoms, indent=1), encoding="utf-8")
    return len(atoms)


def tend() -> str:
    """The dream_loop hook: refresh batteries, run everything once, promote
    on streaks, report one summary block."""
    built = build()
    summary = run()
    promotions = [p for p in (maybe_promote(f) for f in all_battery_features()) if p]
    n_pie = export_pie()
    total_reps = sum(s["passed"] + s["failed"] for s in summary.values())
    total_fail = sum(s["failed"] for s in summary.values())
    lines = [f"[rep] {len(built)} batteries, {sum(built.values())} atoms, "
             f"{total_reps} reps this pass ({total_fail} failing), "
             f"{n_pie} PIE atoms exported"]
    lines += [f"[rep] PROMOTED: {p}" for p in promotions]
    worst = sorted(summary.items(), key=lambda kv: -kv[1]["failed"])[:3]
    for feat, s in worst:
        if s["failed"]:
            lines.append(f"[rep] failing: {feat} ({s['failed']} atoms red)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_build = sub.add_parser("build")
    p_build.add_argument("--feature")
    p_run = sub.add_parser("run")
    p_run.add_argument("--feature")
    p_run.add_argument("--runs", type=int, default=1)
    p_status = sub.add_parser("status")
    p_status.add_argument("--feature")
    p_gate = sub.add_parser("gate")
    p_gate.add_argument("--feature", required=True)
    p_prune = sub.add_parser("prune", help="drop atoms not in the current generator "
                                           "output for a feature (loud, deliberate)")
    p_prune.add_argument("--feature", required=True)
    sub.add_parser("tend")
    sub.add_parser("export-pie")
    args = parser.parse_args()

    if args.cmd == "build":
        for feat, n in build(args.feature).items():
            print(f"battery {feat}: {n} atoms")
    elif args.cmd == "run":
        for feat, s in run(args.feature, args.runs).items():
            print(f"{feat}: +{s['passed']} pass, {s['failed']} fail, "
                  f"{s['skipped']} skipped (x{s['runs']} runs)")
    elif args.cmd == "status":
        targets = ([_safe_name(args.feature)] if args.feature
                   else all_battery_features())
        for f in targets:
            s = status(f)
            print(f"{s['feature']}: {s['reps']} reps, {s['recent_rate']:.0%} recent, "
                  f"streak {s['streak']}, tier {s['tier']}/{s['max_tier']}, "
                  f"battery {s['battery']} ({s['pie']} pie), "
                  f"gate={'READY' if s['gate'] else 'not yet'}")
    elif args.cmd == "gate":
        ok, reason = rep_gate(args.feature)
        print(f"{'ELIGIBLE' if ok else 'NOT ELIGIBLE'}: {reason}")
        return 0 if ok else 1
    elif args.cmd == "prune":
        keep, dropped = prune_to_current(args.feature)
        print(f"battery {args.feature}: kept {len(keep)}, pruned {len(dropped)}")
        for a in dropped[:20]:
            print(f"  pruned {a['id']}  {a['desc'][:70]}")
        if len(dropped) > 20:
            print(f"  ... and {len(dropped) - 20} more")
    elif args.cmd == "tend":
        print(tend())
    elif args.cmd == "export-pie":
        print(f"{export_pie()} PIE atoms -> {PIE_MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
