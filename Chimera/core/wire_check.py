"""
wire_check — trace the WORKFLOW's dataflow and ask where the wires dangle.

THE HUMAN'S INSIGHT (2026-07-16), after watching a LEAD hand-trace a bug: "That's called
debugging, often done by hand tracing the program line by line. Maybe we need to do that
to the whole project workflow."

WHY THIS EXISTS. A 2026-07-16 audit ran five agents over all 149 modules and found ~40
defects. The DOMINANT class was invisible to every one of them:

    benchmark_titles    accepted, stored ......... NEVER READ   (the AAA grader's lie)
    distance_worst      computed correctly ....... BOUND BY NOTHING
    routes_used         computed correctly ....... BOUND BY NOTHING
    robustness          computed correctly ....... BOUND BY NOTHING
    frame_time_stable   measured honestly ........ NEVER CONSUMED

Five bugs. ZERO broken components. Every producer was correct, every consumer was
correct, and the BUG WAS THE WIRE THAT ISN'T THERE. A component audit cannot see this —
there is nothing wrong with either end. Only a TRACE of the flow can.

The damage is always the same shape and always silent: the honest measurement is
computed, written to the artifact, and discarded, while a weaker proxy beside it carries
the weight. `frame_time_stable` was the only multi-sample measurement in the instrument
layer, and a SINGLE instantaneous fps reading carried the whole stability grade — for as
long as it has existed. Half-doing the honest thing looks exactly like doing it.

THIS TOOL ASKS. IT DOES NOT JUDGE — and that is not modesty, it is correctness. A
dangling wire is a CANDIDATE with three possible readings, and only a reader can tell
them apart:

    MISSING     the wire should exist -> a bug        (the five above)
    QUARANTINED dangling ON PURPOSE   -> correct      telemetry_probe emits
                                                      `fps_nonauthoritative` precisely so
                                                      NOTHING can grade on it (H-13: an
                                                      unfocused editor throttles to ~3fps).
                                                      An earlier cut of this tool reported
                                                      that exemplary code as a defect.
    CONTEXT     reported to be READ   -> correct      attunement's assist_hz/n_osc:
                                                      "reported so a winner can be READ,
                                                      never optimised against."

So it prints candidates and the evidence to triage them, and returns 0 either way. A
tracer that decided would be one more instrument that lies — which is the entire thing
this codebase spent 2026-07-16 removing.

    python -m core.wire_check              # all wires
    python -m core.wire_check --wire objectives|evidence|gates
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _read(rel):
    return io.open(os.path.join(ROOT, rel), encoding="utf-8").read()


def _jread(rel):
    return json.loads(_read(rel))


# ---------------------------------------------------------------------------
# WIRE 1: domain.measure() -> objective.constraints
# ---------------------------------------------------------------------------
def wire_objectives():
    """A measure a domain COMPUTES that no constraint BINDS exerts zero selective
    pressure — it is a fact nobody asked for. Four of today's five dangling wires were
    exactly this, each sitting beside the doctrine that demanded it."""
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "docs", "objectives", "*.json"))):
        name = os.path.basename(path)[:-5]
        if name.endswith(".trained"):
            continue
        trained = os.path.join(ROOT, "docs", "objectives", f"{name}.trained.json")
        if not os.path.exists(trained):
            continue
        produced = set(json.loads(io.open(trained, encoding="utf-8").read())["measures"])
        spec = json.loads(io.open(path, encoding="utf-8").read())
        consumed = {c["measure"] for c in spec["constraints"]}
        climbing = sum(1 for c in spec["constraints"] if c["kind"] in ("maximize", "minimize"))
        rows.append({
            "unit": name,
            "dangling": sorted(produced - consumed),
            "phantom": sorted(consumed - produced),
            "climbing": climbing,
        })
    return rows


# ---------------------------------------------------------------------------
# WIRE 2: telemetry_probe -> evidence dict -> result_grader
# ---------------------------------------------------------------------------
def wire_evidence():
    """The probe writes `telemetry["k"] = v`; the grader reads `.get("k")`. This is where
    frame_time_stable was lost: measured, written, never read, while a one-sample fps
    reading carried the grade."""
    src = _read("core/telemetry_probe.py")
    gsrc = _read("core/result_grader.py")
    produced = set(re.findall(r'telemetry\[\s*"(\w+)"\s*\]\s*=', src))
    consumed = set(re.findall(r'\.get\(\s*"(\w+)"', gsrc))
    return [{"unit": "telemetry -> result_grader",
             "dangling": sorted(produced - consumed),
             "phantom": sorted((consumed & _TELEMETRY_KEYS) - produced),
             "climbing": None}]


# keys the grader plainly treats as telemetry, so "graded but never measured" is real
_TELEMETRY_KEYS = {"crash_free", "fps", "target_fps", "unbounded_growth",
                   "memory_bounded", "frame_time_stable"}


# ---------------------------------------------------------------------------
# WIRE 3: postflight -> gate.check(...)
# ---------------------------------------------------------------------------
def wire_gates():
    """A gate parameter postflight never passes is a fix that does not run.

    PROVEN TWICE TODAY. research_gate.check gained `run_id` and postflight never passed
    it — an unreachable branch shipped by the person who wrote the fix. witness_gate.check
    had NO `feature` parameter at all, so it was structurally incapable of scoping, and a
    feature that never existed drew "17 witness node(s) this session". Both are the same
    defect this wire catches: a signature and a call site that disagree, silently.
    """
    pf = _read("core/postflight.py")
    out = []
    for mod, fn in (("research_gate", "_rg_check"), ("witness_gate", "_wg_check"),
                    ("visual_gate", "_vg_check"), ("training_gate", "_tg_check")):
        try:
            src = _read(f"core/{mod}.py")
        except Exception:
            continue
        m = re.search(r"def check\(([^)]*)\)", src, re.DOTALL)
        if not m:
            continue
        params = {p.split("=")[0].strip() for p in m.group(1).split(",")
                  if p.strip() and p.split("=")[0].strip() not in ("nodes", "self")}
        call = re.search(re.escape(fn) + r"\((.*?)\)\s*\n", pf, re.DOTALL)
        raw = call.group(1) if call else ""
        # KEYWORD **and POSITIONAL**. The first cut counted only `name=`, so it reported
        # training_gate's `feature` as unpassed — while postflight passes it POSITIONALLY
        # on the very next line (`_tg_check(args.feature, status=...)`). The gate was
        # correctly wired and this tool called it a bug: the third time in one day that
        # my instrument lied about a healthy world, which is exactly why this file
        # refuses to render verdicts.
        kw = set(re.findall(r"(\w+)\s*=", raw))
        n_pos = len([a for a in raw.split(",") if a.strip() and "=" not in a.split("(")[0]])
        positional = set(list(params)[:max(0, n_pos)]) if n_pos else set()
        passed = kw | positional
        # `hours` is a tuning default no caller is expected to pass — not a dangling wire.
        out.append({"unit": f"postflight -> {mod}.check",
                    "dangling": sorted(params - passed - {"hours"}),
                    "phantom": [], "climbing": None})
    return out


_WIRES = {"objectives": wire_objectives, "evidence": wire_evidence, "gates": wire_gates}


def run(which=None):
    print("=" * 78)
    print("WIRE CHECK — where does the workflow COMPUTE something nothing CONSUMES?")
    print("  Candidates, not verdicts. Three readings, and only you can tell them apart:")
    print("    MISSING (a bug) · QUARANTINED (correct, e.g. fps_nonauthoritative)")
    print("    · CONTEXT (correct, reported to be READ not bound)")
    print("=" * 78)
    total = 0
    for name, fn in _WIRES.items():
        if which and name != which:
            continue
        print(f"\n--- wire: {name} ---")
        try:
            rows = fn()
        except Exception as e:
            print(f"    trace failed: {type(e).__name__}: {e}")
            continue
        for r in rows:
            bits = []
            if r["dangling"]:
                bits.append(f"DANGLING (computed, nothing consumes): {', '.join(r['dangling'])}")
            if r["phantom"]:
                bits.append(f"PHANTOM (consumed, nothing produces): {', '.join(r['phantom'])}")
            if r.get("climbing") == 0:
                bits.append("NO CLIMBING TERM — a satisficer: it clears every wall and stops")
            total += len(r["dangling"]) + len(r["phantom"])
            print(f"  {r['unit']:32} {'; '.join(bits) if bits else '— every wire connected —'}")
    print("\n" + "=" * 78)
    print(f"{total} candidate(s). Each needs a READER: is this wire missing, or absent on purpose?")
    print("A tracer that decided would be one more instrument that lies.")
    print("=" * 78)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="wire_check", description=__doc__.split("\n")[1])
    p.add_argument("--wire", choices=sorted(_WIRES), default=None)
    a = p.parse_args(argv)
    return run(a.wire)


if __name__ == "__main__":
    sys.exit(main())
