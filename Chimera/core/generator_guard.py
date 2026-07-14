"""
Generator Guard — enforce the constitution's most-repeated rule: never hand-edit
generator-owned C++.

Why (2026-07-13, the human): "never hand-edit generator-owned files" appears in
SIX docs, yet nothing PREVENTS it — the only "enforcement" is that the next
pipeline run silently CLOBBERS the hand-edit (it already cost the Haiku fleet and
a wave-1 mistake this session). Enforced-by-destruction is the worst kind: you
learn you broke the rule only after losing the work. This guard makes the
violation VISIBLE before the clobber.

Detection is LM-driven (the human's steer, 2026-07-13): the hard question isn't
"is this filename in a list?" but "is this DIFF a hand-edit to generator-owned
C++ (doomed) or a legit change — and where should it have gone?" That's a
semantic judgment a regex can't make. LM Studio reads the path + diff, grounded
in the ownership map below, and returns a schema-validated verdict (H-3: a
reasoning dump is a retry, never an answer). Two guardrails keep it a reliable
GATE, not a flaky one:
  1. Deterministic PRE-FILTER — only spend an LM call when a file under
     ProceduralGenerated/ is dirty AND core/game_code_generator.py (and the DSL)
     was NOT changed too (a generator/DSL change means the generated diff is
     plausibly regeneration — the legit case — so skip it).
  2. Deterministic FALLBACK — if LM Studio is down, fall back to stem matching
     over the ownership map so the guard still signals (marked heuristic).

Toggle: CHIMERA_GENERATOR_GUARD=warn (or off) softens block -> warn.
"""
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("CHIMERA_ROOT", Path(__file__).resolve().parents[2]))
GENERATED_REL = "Chimera/Source/Chimera/ProceduralGenerated/"
GENERATOR_REL = "Chimera/core/game_code_generator.py"
DSL_REL_PREFIX = "Chimera/tests/dsl_grammar/"

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
try:
    from core.lm_gateway import LM_MODEL as LM_STUDIO_MODEL   # single source of truth
except Exception:
    LM_STUDIO_MODEL = ""   # blank ON PURPOSE — see lm_gateway.LM_MODEL. Naming a
                           # model here would pin one the operator never chose.

ENFORCE_DEFAULT = True

# The ownership map (CLAUDE.md). Fed to the LM as grounding context AND used by
# the deterministic fallback — one source of truth for both.
OWNERSHIP_RULE = """\
Generator-owned files under Source/Chimera/ProceduralGenerated/ are REGENERATED
every pipeline run from core/game_code_generator.py; hand-edits to them are
silently CLOBBERED. The rule: fix the generator template, never the generated C++.

GENERATOR-OWNED (clobbered if hand-edited): Flight, Ship, DeepSpaceTraderGameMode,
PCGVolumeManager, MissionData/MissionComponent, Docking, QuantumTravel,
FactionComponent, Economy (CommodityData/EconomyManager/StationTradingData),
DeepSpaceTraderSaveGame/SaveGameComponent, the Combat suite (Weapon, Projectile,
Shield, Damage, SystemDamage, CombatTarget), PirateAIController + behaviour tree,
and the module files (DeepSpaceTrader.h/.cpp).

LOOP-BUILT / MANUAL (no template, SAFE to hand-edit): Tools, Interactions, Sound,
UI, NPC AI, ChimeraMovementComponent, StationActor, Demo, Inventory, VFX, Suit,
Tests, Shelter, Wind, Weather, Footprint.
"""

# Fallback-only stem lists (LM offline). LOOP checked first so a test/demo file
# that merely references an owned system is treated as safe.
LOOP_STEMS = ("Tool", "Interaction", "Sound", "WID_", "StationActor",
              "ChimeraMovementComponent", "Demo", "Inventory", "Suit", "Test",
              "Shelter", "Wind", "Weather", "Footprint", "LifeSupport", "Pickup")
OWNED_STEMS = ("Flight", "Ship", "DeepSpaceTraderGameMode", "PCGVolumeManager",
               "MissionData", "MissionComponent", "Docking", "QuantumTravel",
               "Faction", "CommodityData", "EconomyManager", "StationTradingData",
               "SaveGame", "Weapon", "Projectile", "Shield", "SystemDamage",
               "DamageComponent", "CombatTarget", "PirateAI", "DeepSpaceTrader")


def enforced():
    if os.environ.get("CHIMERA_GENERATOR_GUARD", "").strip().lower() in ("warn", "off", "0", "false"):
        return False
    return ENFORCE_DEFAULT


# --------------------------------------------------------------------------
# deterministic pre-filter + helpers
# --------------------------------------------------------------------------
def _git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True, timeout=20)


def dirty_generated():
    """(generated_files, generator_or_dsl_also_changed). A generator/DSL change
    means dirty generated files are plausibly regeneration output — the legit
    case — so the caller skips the check."""
    out = _git("status", "--porcelain").stdout
    generated, gen_changed = [], False
    for line in out.splitlines():
        path = line[3:].strip().strip('"')
        if not path:
            continue
        if path.startswith(GENERATED_REL):
            generated.append(path)
        if path == GENERATOR_REL or path.startswith(DSL_REL_PREFIX):
            gen_changed = True
    return generated, gen_changed


def _diff(path):
    d = _git("diff", "--", path).stdout
    if not d.strip():
        d = _git("diff", "--cached", "--", path).stdout
    if not d.strip():                      # untracked new file — show its head
        try:
            d = (ROOT / path).read_text(encoding="utf-8", errors="replace")[:4000]
        except Exception:
            d = ""
    return d[:6000]


def _classify_stem(path):
    name = Path(path).name
    if any(s in name for s in LOOP_STEMS):
        return "loop"
    if any(s in name for s in OWNED_STEMS):
        return "owned"
    return "unknown"


def deterministic_flags():
    """Fast, LM-FREE: dirty generated files that LOOK generator-owned by stem.
    For preflight's heads-up (preflight must stay quick); postflight runs the
    authoritative LM judgment. Empty if the generator/DSL was also changed."""
    generated, gen_changed = dirty_generated()
    if not generated or gen_changed:
        return []
    return [p for p in generated if _classify_stem(p) == "owned"]


# --------------------------------------------------------------------------
# LM-driven detection (H-3: schema-validate; a reasoning dump is a retry)
# --------------------------------------------------------------------------
# The local model is a ~20 tok/s reasoning model (long thinking trace before it
# answers), so we judge ALL dirty files in ONE call — one trace, not N. Files
# beyond this cap fall back to the deterministic classifier (logged, never
# silently dropped).
MAX_LM_FILES = 12


def _heuristic_violation(path, extra=""):
    return {"path": path, "is_hand_edit": True,
            "belongs_in": "core/game_code_generator.py (heuristic — no LM verdict)",
            "reason": ("filename matches a generator-owned class; no LM verdict" + extra),
            "confidence": 0.5, "source": "heuristic"}


def _match_verdict(verdicts, path):
    if path in verdicts:
        return verdicts[path]
    base = Path(path).name
    for k, v in verdicts.items():
        if Path(k).name == base:
            return v
    return None


def _lm_judge_batch(items, max_retries=1):
    """items: [{path, diff}] -> {path: verdict} in ONE LM call, or None if LM is
    unavailable. One reasoning trace judges every file (the model is ~20 tok/s, so
    N sequential calls would be untenable at postflight)."""
    listing = "\n\n".join(f"### FILE {i + 1}: {it['path']}\nDIFF:\n{it['diff'][:2500]}"
                          for i, it in enumerate(items))
    system = (
        "You enforce Chimera's generator-ownership rule.\n" + OWNERSHIP_RULE +
        "\nFor EACH file below, decide whether its diff is a hand-edit to a "
        "GENERATOR-OWNED file (which the next pipeline run will clobber). A pure "
        "regeneration, or any change to a loop-built/manual file, is NOT a "
        "violation. Return ONLY a JSON array, one object per file, echoing its "
        'path:\n[{"path": "<path>", "is_generator_owned": true|false, '
        '"is_hand_edit": true|false, "belongs_in": "<generator method / DSL / fine>", '
        '"confidence": 0.0-1.0, "reason": "<one sentence>"}]')
    user = f"{len(items)} changed file(s) under ProceduralGenerated/:\n\n{listing}"
    token_budget = 2000 + 700 * len(items)
    for _ in range(max_retries + 1):
        payload = {"model": LM_STUDIO_MODEL,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                   "max_tokens": token_budget, "temperature": 0.2}
        req = urllib.request.Request(LM_STUDIO_URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            from core.lm_gateway import lm_urlopen, LM_TIMEOUT
            with lm_urlopen(req, timeout=LM_TIMEOUT, agent="generator-guard") as r:
                msg = json.load(r)["choices"][0]["message"]
        except Exception:
            return None                    # LM unavailable -> caller falls back
        for text in (msg.get("content") or "", msg.get("reasoning_content") or ""):
            m = re.search(r"\[.*\]", text, re.DOTALL)   # a JSON array
            if not m:
                continue
            try:
                arr = json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
            if isinstance(arr, list) and arr:
                out = {}
                for v in arr:
                    if isinstance(v, dict) and isinstance(v.get("is_generator_owned"), bool):
                        out[v.get("path", "")] = v
                if out:
                    return out
        token_budget += 2500               # H-3: retry with a larger budget
    return None


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------
def check():
    """Return a list of violations (generator-owned files with a hand-edit).
    Empty when clean, when the generator/DSL was also changed (regeneration), or
    when no generated files are dirty."""
    generated, gen_changed = dirty_generated()
    if not generated or gen_changed:
        return []
    judged, overflow = generated[:MAX_LM_FILES], generated[MAX_LM_FILES:]
    verdicts = _lm_judge_batch([{"path": p, "diff": _diff(p)} for p in judged])
    violations = []
    if verdicts is None:                   # LM unavailable -> deterministic for all
        for p in generated:
            if _classify_stem(p) == "owned":
                violations.append(_heuristic_violation(p, " (LM Studio offline)"))
        return violations
    for p in judged:
        v = _match_verdict(verdicts, p)
        if v is None:                      # LM returned no verdict for this file
            if _classify_stem(p) == "owned":
                violations.append(_heuristic_violation(p, " (no LM verdict returned)"))
        elif v.get("is_generator_owned") and v.get("is_hand_edit"):
            v["path"] = p
            v.setdefault("source", "lm")
            violations.append(v)
    for p in overflow:                     # beyond the batch cap -> deterministic
        if _classify_stem(p) == "owned":
            violations.append(_heuristic_violation(p, " (beyond LM batch cap)"))
    if overflow:
        print(f"[generator-guard] note: {len(overflow)} file(s) beyond the LM batch "
              f"cap judged heuristically (not silently dropped)")
    return violations


def format_violations(violations):
    lines = []
    for v in violations:
        src = v.get("source", "?")
        lines.append(f"  x {v['path']}  [{src}]")
        if v.get("belongs_in"):
            lines.append(f"      -> belongs in: {v['belongs_in']}")
        if v.get("reason"):
            lines.append(f"      {v['reason']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    viols = check()
    if not viols:
        print("[generator-guard] clean — no hand-edits to generator-owned files.")
        sys.exit(0)
    print(f"[generator-guard] {len(viols)} hand-edit(s) to GENERATOR-OWNED files "
          f"(they will be clobbered on the next pipeline run):")
    print(format_violations(viols))
    print("Fix the generator template in core/game_code_generator.py, not the C++.")
    sys.exit(1 if enforced() else 0)
