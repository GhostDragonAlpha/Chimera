"""malcolm — THE EDGE REGULATOR: a container for chaos that leaves room for emergence.

"We need a container... the shape of this container will be determined based
on the metric scores of the features and the limitations of Unreal Engine and
modern gaming hardware... I fear that my mechanism will fail and chaos will
reign supreme." — and, the balancing clause — "this concept has to balance
with the concept of emergence from complexity." (human, 2026-07-12)

Complexity science calls the balance point the EDGE OF CHAOS: emergence peaks
at the phase boundary between order and chaos. Too rigid a container: frozen,
sterile. No container: noise, and Malcolm's nightmare. So this organ is not a
wall against chaos — it is a regulator that HOLDS THE SYSTEM IN THE
PRODUCTIVE BAND:

  BANDS, NOT CEILINGS   every axis is {min, max}: a chaos ceiling AND an
                        emergence floor (below min, interaction density is
                        too low for anything to emerge).
  GRAMMAR, NOT SENTENCES caps apply to AUTHORED mechanism (rules, coupling,
                        ms, MB, tasks, atoms) — never to emergent state.
                        Conway's Life: 3 rules, k=8 neighbors, Turing-complete.
  EMERGENCE RESERVE     hardware walls keep a reserve_pct of headroom for the
                        spikes nobody authored. A budget at 100% kills every
                        emergent moment by definition.
  THE BREATH            tune() is a homeostat: the graph's engine-sourced
                        SurpriseMoments are a literal emergence gauge. Rate
                        below band + headroom -> PROPOSE loosening; breaches
                        -> PROPOSE tightening. Gardener-style: the regulator
                        proposes, never self-executes.
  TEETH                 gate_envelope (BLOCKER on measured hard breaches),
                        envelope rep atoms (the fence checked at rep
                        frequency), admission control (growth that would
                        breach a wall is refused with the wall named).

Every wall carries PROVENANCE: researched (with sources), measured (from live
telemetry/state), design (a declared game-design number, e.g. the ~400-rep
dog threshold), existing (already enforced elsewhere), or provisional
(tightest-known-safe default; upgrade me). The shape is fitted from evidence,
never decreed.

CLI
  python -m core.malcolm status            the gauge (all axes, bands, states)
  python -m core.malcolm check             hard breaches only (gate feed)
  python -m core.malcolm admit --axis open_board_tasks --n 4
  python -m core.malcolm tune              the breath (proposals, never applies)
  python -m core.malcolm fit               re-derive measured walls from live state
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENVELOPE_PATH = ROOT / "docs" / "envelope.json"
SOURCE_TREE = ROOT / "Source" / "Chimera" / "ProceduralGenerated"
TELEMETRY_LAST = ROOT / "docs" / "world" / "telemetry_last.json"

# Provenance refs (research pass 2026-07-12):
_REF_FRAME = ("researched: 60fps => 16.67ms shared CPU+GPU; budget in ms, never fps "
              "(Epic 'Guidelines for Optimizing Rendering', dev.epicgames.com; "
              "unrealartoptimization.github.io/book/process/measuring-performance)")
_REF_VRAM = ("researched: 8GB breaks under Nanite+Lumen loads, 12GB entry-usable, "
             "16GB safe dev baseline; mid-range target = fit in 12GB "
             "(medium.com/@mumbamweni3 best-vram-ue5-2026; vagon.io picking-best-gpu; "
             "codeitbro.com ue5 system requirements)")

FOUNDING_ENVELOPE = {
    "doc": "The container. Bands [min,max]; null = unbounded on that side. "
           "reserve_pct = emergence reserve (headroom for unscripted spikes). "
           "GROW/TUNE THIS JSON via `malcolm tune` proposals — never decree.",
    "axes": {
        # --- hardware family: the machine's walls -------------------------
        "frame_time_ms": {"family": "hardware", "min": None, "max": 16.6,
                          "unit": "ms", "reserve_pct": 20,
                          "source": {"kind": "researched", "ref": _REF_FRAME}},
        "vram_gb": {"family": "hardware", "min": None, "max": 12.0,
                    "unit": "GB", "reserve_pct": 15,
                    "source": {"kind": "researched", "ref": _REF_VRAM}},
        "system_memory_gb": {"family": "hardware", "min": None, "max": 12.0,
                             "unit": "GB", "reserve_pct": 15,
                             "source": {"kind": "provisional",
                                        "ref": "tightest-safe default; upgrade with telemetry"}},
        "audio_voices": {"family": "hardware", "min": None, "max": 32,
                         "unit": "concurrent", "reserve_pct": 0,
                         "source": {"kind": "provisional",
                                    "ref": "UE historical default channel count; verify per-platform"}},
        # --- systemic family: walls on the GENERATOR (the chaos-theory part)
        "open_board_tasks": {"family": "systemic", "min": 3, "max": 24,
                             "unit": "tasks",
                             "source": {"kind": "design",
                                        "ref": "floor: below 3 the conveyor starves; "
                                               "ceiling: above 24 nothing converges"}},
        "atoms_per_battery": {"family": "systemic", "min": 1, "max": 400,
                              "unit": "atoms",
                              "source": {"kind": "design",
                                         "ref": "the dog-threshold number as a CEILING: past "
                                                "~400 constraints/feature, reps stop informing"}},
        "decomposition_depth": {"family": "systemic", "min": 1, "max": 3,
                                "unit": "levels",
                                "source": {"kind": "design",
                                           "ref": "parts of parts of parts — recursion is where "
                                                  "generative systems escape their keepers"}},
        "coupling_degree_k": {"family": "systemic", "min": 1, "max": 4,
                              "unit": "systems",
                              "source": {"kind": "design",
                                         "ref": "each system couples to <=k others; bounded degree "
                                                "keeps emergence legible (Life: k=8, Turing-complete)"}},
        "generated_loc": {"family": "systemic", "min": None, "max": 150000,
                          "unit": "lines",
                          "source": {"kind": "measured",
                                     "ref": "fit: ~1.5x current corpus at founding; refit via `fit`"}},
        "generated_files": {"family": "systemic", "min": None, "max": 600,
                            "unit": "files",
                            "source": {"kind": "measured", "ref": "fit at founding; refit via `fit`"}},
        "graph_nodes": {"family": "systemic", "min": None, "max": 5000000,
                        "unit": "nodes",
                        "source": {"kind": "existing",
                                   "ref": "gates.gate_node_count_bounded (runaway backstop)"}},
        "heuristics_per_night": {"family": "systemic", "min": None, "max": 2,
                                 "unit": "candidates",
                                 "source": {"kind": "existing",
                                            "ref": "dream_loop/heuristic_distiller max-candidates"}},
        # --- experience family: the edge-of-chaos band itself --------------
        "interacting_systems_per_slice": {"family": "experience", "min": 3, "max": 7,
                                          "unit": "systems",
                                          "source": {"kind": "design",
                                                     "ref": "emergence floor: <3 systems cannot "
                                                            "interact into anything; >7 untestable"}},
        "active_dots": {"family": "experience", "min": 2, "max": 24,
                        "unit": "NPCs",
                        "source": {"kind": "provisional",
                                   "ref": "PIE-measured wall; floor 2 = a world with others in it"}},
        "engine_surprise_rate_per_week": {"family": "experience", "min": 2, "max": 20,
                                          "unit": "surprises/wk",
                                          "source": {"kind": "design",
                                                     "ref": "THE HOMEOSTAT BAND: engine-sourced "
                                                            "SurpriseMoments are the emergence gauge; "
                                                            "<2 = sterile, >20 = chaos reigning"}},
    },
    "rules": {
        "min_occupant_grade": "C",
        "occupancy": "at a ceiling, admission requires eviction: park the "
                     "lowest-graded occupant first (growth pressure becomes "
                     "curation pressure — the shape follows the metric scores)",
    },
    "pending_adjustments": [],
}


def load_envelope() -> dict:
    if ENVELOPE_PATH.exists():
        try:
            return json.loads(ENVELOPE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    ENVELOPE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENVELOPE_PATH.write_text(json.dumps(FOUNDING_ENVELOPE, indent=1), encoding="utf-8")
    return json.loads(json.dumps(FOUNDING_ENVELOPE))


def save_envelope(env: dict) -> None:
    ENVELOPE_PATH.write_text(json.dumps(env, indent=1), encoding="utf-8")


# ---------------------------------------------------------------------------
# measurement — every axis answers (value|None, evidence). None = honest
# UNMEASURED (PIE-bound or sensor not yet built), never a fabricated zero.
# ---------------------------------------------------------------------------

def _telemetry() -> dict:
    if TELEMETRY_LAST.exists():
        try:
            return json.loads(TELEMETRY_LAST.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _walk_generated() -> tuple:
    files = loc = 0
    if SOURCE_TREE.exists():
        for p in SOURCE_TREE.rglob("*"):
            if p.suffix in (".h", ".cpp"):
                files += 1
                try:
                    loc += sum(1 for _ in p.open(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    return files, loc


def measure_axis(name: str, graph_nodes: list = None, board_state: dict = None) -> tuple:
    """(value|None, evidence). Injectable inputs keep this testable and keep
    tests from touching live stores (surprise_e3944cb57b2994f0's lesson)."""
    tel = _telemetry()
    if name == "frame_time_ms":
        fps = tel.get("fps")
        if not fps:
            return (None, "unmeasured — run telemetry_probe --foreground, writes Chimera/telemetry_last.json")
        if not tel.get("foregrounded"):
            # fps sampled with the editor UNFOCUSED: Windows/GPU throttles background
            # windows to ~3fps, freezing Niagara+anim too. That is a measurement
            # artifact, not a frame time — UNMEASURED, never a breach. (A genuinely
            # foregrounded 3fps WOULD still breach, so a real perf problem is not masked.)
            return (None, f"unmeasured — fps={float(fps):.1f} captured unfocused (background GPU "
                          f"throttle); run telemetry_probe --foreground for an authoritative frame time")
        return (1000.0 / float(fps), f"telemetry fps={float(fps):.1f} (foregrounded)")
    if name in ("vram_gb", "system_memory_gb", "audio_voices", "active_dots",
                "interacting_systems_per_slice", "coupling_degree_k"):
        val = tel.get(name)
        return ((val, "telemetry_last.json") if val is not None
                else (None, "unmeasured (PIE/sensor pending) — wall still gates ADMISSION"))
    if name == "open_board_tasks":
        try:
            if board_state is None:
                from core.task_board import _read_state
                board_state = _read_state()
            n = sum(1 for t in board_state.get("tasks", []) if t.get("status") == "open")
            return (n, f"task board live state ({len(board_state.get('tasks', []))} total)")
        except Exception as e:
            return (None, f"board unreadable ({e})")
    if name == "atoms_per_battery":
        try:
            from core.rep_engine import all_battery_features, load_battery
            sizes = [len(load_battery(f)) for f in all_battery_features()]
            return ((max(sizes), f"largest of {len(sizes)} batteries") if sizes
                    else (None, "no batteries yet"))
        except Exception as e:
            return (None, f"rep engine unreadable ({e})")
    if name == "generated_files":
        files, _loc = _walk_generated()
        return (files, "walk of ProceduralGenerated")
    if name == "generated_loc":
        _files, loc = _walk_generated()
        return (loc, "walk of ProceduralGenerated")
    if name in ("graph_nodes", "heuristics_per_night",
                "engine_surprise_rate_per_week", "decomposition_depth"):
        try:
            if graph_nodes is None:
                from core.graphify_interface import load_dna_graph
                graph_nodes = load_dna_graph().get("nodes", [])
        except Exception as e:
            return (None, f"graph unreadable ({e})")
        now = datetime.now(timezone.utc)
        if name == "graph_nodes":
            return (len(graph_nodes), "live DNA graph")
        if name == "heuristics_per_night":
            # SENSOR FIX (2026-07-14): every Heuristic NODE is a gardener
            # PROMOTION (staged candidates live only in PENDING_HEURISTICS.md);
            # counting nodes measured backlog-draining promotions, not what the
            # wall MEANS (distiller staging <=2/night) — a night that promoted 7
            # old entries read as a 450% false BREACH. Measure the wall's real
            # subject: the staged-candidate count from the latest dream report.
            try:
                _dr = CHIMERA_ROOT / "docs" / "DREAM_REPORT.md" if "CHIMERA_ROOT" in globals() \
                    else Path(__file__).resolve().parents[1] / "docs" / "DREAM_REPORT.md"
                import re as _re_h
                _m = _re_h.search(r"staged\s+(\d+)\s+candidate",
                                  _dr.read_text(encoding="utf-8", errors="replace"),
                                  _re_h.IGNORECASE)
                if _m:
                    return (int(_m.group(1)), "distiller candidates staged (latest Dream Report)")
            except Exception:
                pass
            return (None, "no staged-candidate line in DREAM_REPORT.md; unmeasured (honest skip)")
            day_ago = (now - timedelta(days=1)).isoformat()
            # The wall governs DISTILLER CANDIDATES (<=2/night). Rejection-
            # lineage records (human_rejection:/sim_rejection: signatures) are
            # per-rejection bookkeeping, unbounded by design — counting them
            # was this sensor's day-one census error (Malcolm's own lesson:
            # the count must measure what the wall MEANS, not what it's
            # pointed at).
            n = sum(1 for x in graph_nodes if x.get("type") == "Heuristic"
                    and str(x.get("timestamp", "")) >= day_ago[:19]
                    and not str(x.get("signature", "")).startswith(
                        ("human_rejection:", "sim_rejection:")))
            return (n, "distiller-candidate Heuristic nodes, last 24h "
                       "(rejection-lineage records excluded)")
        if name == "engine_surprise_rate_per_week":
            week_ago = (now - timedelta(days=7)).isoformat()
            n = sum(1 for x in graph_nodes if x.get("type") == "SurpriseMoment"
                    and x.get("source") == "engine"
                    and str(x.get("timestamp", "")) >= week_ago[:19])
            return (n, "engine-sourced SurpriseMoments, last 7d — the emergence gauge")
        if name == "decomposition_depth":
            targets = {x.get("target"): x for x in graph_nodes
                       if x.get("type") == "Decomposition"}
            def depth(t, seen=()):
                if t in seen:
                    return 99  # cycle = escaped containment; will breach
                parent = t.split("/")[0] if "/" in str(t) else None
                return 1 + (depth(parent, seen + (t,)) if parent in targets else 0)
            d = max((depth(t) for t in targets), default=0)
            return (d, f"{len(targets)} Decomposition node(s)")
    return (None, f"no sensor for axis {name!r}")


# ---------------------------------------------------------------------------
# bands, status, teeth
# ---------------------------------------------------------------------------

def axis_state(axis: dict, value) -> str:
    if value is None:
        return "UNMEASURED"
    mx, mn = axis.get("max"), axis.get("min")
    if mx is not None and value > mx:
        return "BREACH"
    if mn is not None and value < mn:
        return "BELOW-FLOOR"
    if mx is not None:
        reserve = axis.get("reserve_pct", 20) or 20
        if value >= mx * (1 - reserve / 100.0):
            return "WARN"
    return "OK"


def status(env: dict = None, graph_nodes: list = None, board_state: dict = None) -> list:
    env = env or load_envelope()
    rows = []
    for name, axis in env["axes"].items():
        value, evidence = measure_axis(name, graph_nodes, board_state)
        state = axis_state(axis, value)
        band = f"[{axis.get('min') if axis.get('min') is not None else '—'}, " \
               f"{axis.get('max') if axis.get('max') is not None else '—'}]"
        pct = ""
        if value is not None and axis.get("max"):
            pct = f"{100.0 * value / axis['max']:5.1f}%"
        rows.append(dict(axis=name, family=axis["family"], value=value,
                         band=band, pct=pct, state=state, evidence=evidence,
                         source=axis["source"]["kind"]))
    return rows


def check_hard(env: dict = None, graph_nodes: list = None, board_state: dict = None) -> list:
    """Measured BREACHes in hardware+systemic families — the gate feed.
    Floors and UNMEASURED never block (emergence health is advised, not
    coerced; absence of a sensor is not evidence of safety OR danger)."""
    return [r for r in status(env, graph_nodes, board_state)
            if r["state"] == "BREACH" and r["family"] in ("hardware", "systemic")]


def admit(axis_name: str, delta: float = 1, env: dict = None,
          graph_nodes: list = None, board_state: dict = None) -> tuple:
    """Admission control: may the system GROW by delta on this axis?
    (allowed, reason). Unmeasured axes admit with a warning — the wall still
    exists; the sensor doesn't. At a ceiling: the occupancy rule applies."""
    env = env or load_envelope()
    axis = env["axes"].get(axis_name)
    if axis is None:
        return (True, f"no wall named {axis_name!r} — unwalled growth (consider adding one)")
    value, _ev = measure_axis(axis_name, graph_nodes, board_state)
    if value is None:
        return (True, f"WALL EXISTS but axis unmeasured — admitted on trust; build the sensor")
    projected = value + delta
    mx = axis.get("max")
    if mx is not None and projected > mx:
        return (False, f"REFUSED by the container: {axis_name} {value}+{delta} > max {mx} "
                       f"({axis['source']['kind']}). Occupancy rule: "
                       f"{env['rules']['occupancy']}")
    if mx is not None and projected >= mx * 0.8:
        return (True, f"admitted at {100.0 * projected / mx:.0f}% of ceiling — headroom thinning")
    return (True, f"admitted ({projected}/{mx if mx is not None else 'unbounded'})")


def tune(env: dict = None, graph_nodes: list = None, board_state: dict = None) -> str:
    """THE BREATH — the edge-of-chaos homeostat. Reads the emergence gauge
    (engine-surprise rate) against its band and the walls' pressure, then
    PROPOSES adjustments into pending_adjustments. Never self-applies:
    the regulator proposes, a capable cycle (or the human) rules."""
    env = env or load_envelope()
    rows = {r["axis"]: r for r in status(env, graph_nodes, board_state)}
    proposals = []
    gauge = rows["engine_surprise_rate_per_week"]
    band = env["axes"]["engine_surprise_rate_per_week"]
    breaches = [r for r in rows.values() if r["state"] == "BREACH"]
    if breaches:
        for b in breaches:
            proposals.append({
                "ts": datetime.now(timezone.utc).isoformat()[:19],
                "direction": "tighten",
                "axis": b["axis"],
                "proposal": f"hold or reduce max on {b['axis']} (currently BREACHED at "
                            f"{b['value']}); investigate before any loosening anywhere",
                "evidence": b["evidence"], "status": "pending"})
    elif (gauge["value"] is not None and band.get("min") is not None
          and gauge["value"] < band["min"]):
        systemic = [r for r in rows.values() if r["family"] == "systemic"
                    and r["value"] is not None and r["pct"]]
        if systemic and all(float(r["pct"].strip("% ")) < 80.0 for r in systemic):
            most = max(systemic, key=lambda r: float(r["pct"].strip("% ")))
            cur_max = env["axes"][most["axis"]]["max"]
            proposals.append({
                "ts": datetime.now(timezone.utc).isoformat()[:19],
                "direction": "loosen",
                "axis": most["axis"],
                "proposal": f"raise max {cur_max} -> {math.ceil(cur_max * 1.2)}: emergence "
                            f"gauge {gauge['value']}/wk is BELOW floor {band['min']} and every "
                            f"systemic wall has headroom — the container is too tight for "
                            f"anything to emerge",
                "evidence": gauge["evidence"], "status": "pending"})
    elif gauge["value"] is not None and band.get("max") is not None \
            and gauge["value"] > band["max"]:
        proposals.append({
            "ts": datetime.now(timezone.utc).isoformat()[:19],
            "direction": "tighten",
            "axis": "engine_surprise_rate_per_week",
            "proposal": f"emergence gauge {gauge['value']}/wk EXCEEDS band max {band['max']} — "
                        f"chaos side rising; tighten the most-pressured systemic wall by 10%",
            "evidence": gauge["evidence"], "status": "pending"})
    if proposals:
        env.setdefault("pending_adjustments", []).extend(proposals)
        save_envelope(env)
    lines = [f"[malcolm] gauge: engine surprises {gauge['value']}/wk "
             f"(band {gauge['band']}) — {gauge['state']}"]
    lines += [f"[malcolm] PROPOSE {p['direction'].upper()} {p['axis']}: {p['proposal'][:110]}"
              for p in proposals]
    if not proposals:
        lines.append("[malcolm] container holding at the edge — no adjustment proposed")
    return "\n".join(lines)


def fit(env: dict = None) -> str:
    """Re-derive 'measured'-kind walls from live state (1.5x headroom rule);
    researched/design/existing walls are never auto-touched."""
    env = env or load_envelope()
    changed = []
    files, loc = _walk_generated()
    for axis_name, current in (("generated_files", files), ("generated_loc", loc)):
        axis = env["axes"][axis_name]
        if axis["source"]["kind"] == "measured":
            new_max = int(math.ceil(current * 1.5 / 10.0) * 10)
            if new_max != axis["max"]:
                changed.append(f"{axis_name}: max {axis['max']} -> {new_max} (1.5x live {current})")
                axis["max"] = new_max
                axis["source"]["ref"] = f"fit {datetime.now(timezone.utc).isoformat()[:10]}: 1.5x live {current}"
    if changed:
        save_envelope(env)
    return "\n".join(changed) or "no measured walls needed refitting"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("check")
    p_admit = sub.add_parser("admit")
    p_admit.add_argument("--axis", required=True)
    p_admit.add_argument("--n", type=float, default=1)
    sub.add_parser("tune")
    sub.add_parser("fit")
    args = parser.parse_args()

    if args.cmd == "status":
        for r in status():
            val = "—" if r["value"] is None else (
                f"{r['value']:.1f}" if isinstance(r["value"], float) else str(r["value"]))
            print(f"{r['state']:>12}  {r['axis']:<34} {val:>10} {r['band']:>16} "
                  f"{r['pct']:>7}  [{r['family']}/{r['source']}]")
        return 0
    if args.cmd == "check":
        breaches = check_hard()
        for b in breaches:
            print(f"BREACH: {b['axis']} = {b['value']} exceeds band {b['band']} ({b['evidence']})")
        print(f"{len(breaches)} hard breach(es)")
        return 1 if breaches else 0
    if args.cmd == "admit":
        ok, reason = admit(args.axis, args.n)
        print(("ADMITTED: " if ok else "") + reason)
        return 0 if ok else 1
    if args.cmd == "tune":
        print(tune())
        return 0
    if args.cmd == "fit":
        print(fit())
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
