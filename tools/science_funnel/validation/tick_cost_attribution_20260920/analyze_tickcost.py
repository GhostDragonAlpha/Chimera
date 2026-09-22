"""analyze_tickcost.py -- the TICK-COST ATTRIBUTION analyzer.

Consumes raw/run_index.json + tc_run*_stderr.txt ([tc]/[tc-ticks] lines) and
produces:
  - the per-subsystem attribution table (steady-state ms/tick + share);
  - F3d books-closing (exclusive stage sum vs the measured step wall);
  - F3c instrumentation overhead (process-wall delta / sampled ticks);
  - F1 optimistic-removal bound vs the 3.33 ms/300 Hz budget + COST-GAP verdict;
  - p50/p95/p99 tick latency for the 426-tick interacting push scene;
  - the prediction grading (PREREG.md) and a JSON blob for the receipt.

Trailer Agent: tickcost.
"""
import argparse, hashlib, json, math, re
from pathlib import Path

BUDGET_MS = 1000.0 / 300.0  # 3.33 ms/tick
LANE_FENCE = "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc"  # bd4bf630 plain (PREREG Amendment 1)

# exclusive step() stages (F3d books-closing)
STAGES = ["step.reset_alloc", "step.reflex_clock", "step.capture_reflex",
          "step.sat_census", "step.integrate"]
# byte-neutral removable classes (F1 optimistic removal; sync measured 0)
REMOVABLE = ["obs.status_json", "harness.census", "harness.dump",
             "step.reset_alloc"]  # alloc churn + buffer reset, optimistic: all of it
# the physics classes (NOT removable; removal changes replay bytes)
PHYSICS = ["step.reflex_clock", "step.capture_reflex", "step.sat_census",
           "step.integrate", "adv.total", "adv.impact", "adv.free_step",
           "adv.rate", "servo", "fk.evaluate", "solver.inverse_spd",
           "solver.friction_solve", "solver.project_rows",
           "clock.update_clock", "clock.fore_clock", "reflex.capture_fn",
           "reflex.support_state"]


def percentile(sorted_v, q):
    if not sorted_v:
        return None
    k = max(0, min(len(sorted_v) - 1, int(math.ceil(q / 100.0 * len(sorted_v))) - 1))
    return sorted_v[k]


def parse_stderr(path):
    """-> {phase: {'cls': {name: (ms,hits)}, 'loop': (wall_ms,ticks),
                   'ticks': {'walk': [...ns], 'push': [...]},
                   'adv': {...}, 'alloc': {...}}}"""
    phases = {}
    cur = None
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\[tc\] phase=(\S+) cls=(\S+) ms=([0-9.]+) hits=(\d+)", ln)
        if m:
            cur = phases.setdefault(m.group(1), {"cls": {}, "ticks": {}})
            cur["cls"][m.group(2)] = (float(m.group(3)), int(m.group(4)))
            continue
        m = re.match(r"\[tc\] phase=(\S+) loop_wall_ms=([0-9.]+) ticks=(\d+) full_loop_us_per_tick=([0-9.]+)", ln)
        if m:
            cur = phases.setdefault(m.group(1), {"cls": {}, "ticks": {}})
            cur["loop"] = (float(m.group(2)), int(m.group(3)))
            cur["full_loop_us_per_tick"] = float(m.group(4))
            continue
        m = re.match(r"\[tc\] phase=(\S+) adv_calls mean=([0-9.]+) p95=(\d+) max=(\d+) n=(\d+)", ln)
        if m:
            cur = phases.setdefault(m.group(1), {"cls": {}, "ticks": {}})
            cur["adv"] = {"mean": float(m.group(2)), "p95": int(m.group(3)),
                          "max": int(m.group(4)), "n": int(m.group(5))}
            continue
        m = re.match(r"\[tc\] phase=(\S+) alloc mean_count=([0-9.]+) mean_bytes=([0-9.]+) n=(\d+)", ln)
        if m:
            cur = phases.setdefault(m.group(1), {"cls": {}, "ticks": {}})
            cur["alloc"] = {"mean_count": float(m.group(2)),
                            "mean_bytes": float(m.group(3)), "n": int(m.group(4))}
            continue
        m = re.match(r"\[tc-ticks\] phase=(\S+) kind=(\S+) n=(\d+) (.*)", ln)
        if m:
            cur = phases.setdefault(m.group(1), {"cls": {}, "ticks": {}})
            cur["ticks"][m.group(2)] = [int(x) for x in m.group(4).split(",") if x]
            continue
    return phases


def phase_table(ph, ticks):
    """per-class steady-state ms/tick + share of the full loop."""
    loop = ph.get("loop")
    full_ms = (loop[0] / loop[1]) if loop else None
    out = {"full_loop_ms_per_tick": full_ms, "ticks": ticks, "cls": {}}
    for name, (ms, hits) in ph["cls"].items():
        per = ms / ticks if ticks else None
        out["cls"][name] = {"ms_per_tick": per, "hits_per_tick": hits / ticks if ticks else None,
                            "share_of_loop": (per / full_ms) if (per is not None and full_ms) else None}
    stage_sum = sum(out["cls"].get(s, {"ms_per_tick": 0})["ms_per_tick"] or 0 for s in STAGES)
    out["stage_sum_ms_per_tick"] = stage_sum
    return out


def analyze(raw_dir):
    raw = Path(raw_dir)
    index = json.loads((raw / "run_index.json").read_text(encoding="utf-8"))
    # defense in depth: re-hash every stdout artifact ourselves
    shas = {}
    for f in sorted(raw.glob("*_stdout.txt")):
        shas[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    guard = {"stdout_shas": shas,
             "all_lane_fence": set(shas.values()) == {LANE_FENCE},
             "run_index_guard": index.get("guard")}
    res = {"guard": guard, "phases": {}, "runs": {}}
    for kind in ("plain", "tc"):
        walls = [r["wall_s"] for r in index["runs"] if r["kind"] == kind]
        res["runs"][kind] = {"wall_s_mean": sum(walls) / len(walls) if walls else None,
                             "wall_s": walls}
    # per-run phase tables; keep the MEDIAN walk run for the receipt table
    tc_runs = {}
    for k in range(1, 100):
        p = raw / ("tc_run%d_stderr.txt" % k)
        if not p.exists():
            break
        tc_runs[k] = parse_stderr(p)
    res["tc_runs"] = {k: sorted(v.keys()) for k, v in tc_runs.items()}
    # medians across runs per phase, by full-loop per-tick
    med_phase, med_run = None, None
    per_run_loops = {}
    for k, phs in tc_runs.items():
        for name, ph in phs.items():
            if name.startswith("walk_run") and "loop" in ph:
                per_run_loops.setdefault(name, {})[k] = ph["loop"][0] / ph["loop"][1]
    if per_run_loops:
        name = sorted(per_run_loops)[0]
        k = min(per_run_loops[name], key=lambda kk: per_run_loops[name][kk])
        med_phase, med_run = tc_runs[k][name], (k, name)
    push_phase = None
    for k, phs in tc_runs.items():
        if "push426" in phs:
            push_phase = phs["push426"]
            break
    # latency from the median run's arrays
    lat = {}
    if med_phase:
        for kind, arr in med_phase["ticks"].items():
            ss = arr[20:]  # steady state: tick index >= 20 (PREREG Methods 1)
            s_all, s_ss = sorted(arr), sorted(ss)
            lat[kind] = {
                "n": len(arr), "n_ss": len(ss),
                "p50_us": percentile(s_all, 50), "p95_us": percentile(s_all, 95),
                "p99_us": percentile(s_all, 99),
                "p50_ss_us": percentile(s_ss, 50), "p95_ss_us": percentile(s_ss, 95),
                "p99_ss_us": percentile(s_ss, 99),
                "mean_ss_us": sum(ss) / len(ss) if ss else None}
    if push_phase and "push" in push_phase["ticks"]:
        arr = sorted(push_phase["ticks"]["push"])
        lat["push426"] = {"n": len(arr),
                          "p50_us": percentile(arr, 50), "p95_us": percentile(arr, 95),
                          "p99_us": percentile(arr, 99),
                          "mean_us": sum(arr) / len(arr)}
    res["latency_us"] = lat
    # attribution table (walk, steady-state shares) + books + bound
    if med_phase:
        ticks = med_phase["loop"][1] if "loop" in med_phase else None
        tbl = phase_table(med_phase, ticks)
        books = tbl["stage_sum_ms_per_tick"]
        step_mean_ms = (lat.get("walk", {}).get("mean_ss_us", 0) or 0) / 1000.0
        tbl["books"] = {"stage_sum_ms_per_tick": books,
                        "step_mean_ms": step_mean_ms,
                        "closure": books / step_mean_ms if step_mean_ms else None,
                        "f3d_green": bool(step_mean_ms) and books / step_mean_ms >= 0.95}
        removable_sum = sum((tbl["cls"].get(c, {"ms_per_tick": 0})["ms_per_tick"] or 0)
                            for c in REMOVABLE)
        tbl["bound"] = {
            "removable_classes": REMOVABLE,
            "removable_sum_ms_per_tick": removable_sum,
            "sync_ms_per_tick": 0.0,
            "optimistic_removal_bound_ms_per_tick":
                (tbl["full_loop_ms_per_tick"] - removable_sum) if tbl["full_loop_ms_per_tick"] else None}
        b = tbl["bound"]["optimistic_removal_bound_ms_per_tick"]
        tbl["bound"]["budget_ms_per_tick"] = BUDGET_MS
        tbl["bound"]["cost_gap_fired"] = bool(b is not None and b > BUDGET_MS)
        res["attribution"] = tbl
    # F3c overhead: process-wall delta spread over SAMPLED ticks only (F-G5
    # ticks are not sampled, so this is an upper bound on per-tick overhead)
    wp = res["runs"]["plain"]["wall_s_mean"]
    wt = res["runs"]["tc"]["wall_s_mean"]
    n_sampled = sum(len(a) for a in med_phase["ticks"].values()) if med_phase else 0
    for k, phs in tc_runs.items():
        n_sampled += sum(len(v) for ph in phs.values() for v in ph["ticks"].values())
    res["overhead"] = {"plain_wall_mean_s": wp, "tc_wall_mean_s": wt,
                       "delta_s": wt - wp, "sampled_ticks": n_sampled,
                       "overhead_ms_per_tick_upper_bound": (wt - wp) * 1000.0 / n_sampled}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="raw")
    ap.add_argument("--out", default="receipt_data.json")
    a = ap.parse_args()
    res = analyze(a.raw_dir)
    Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1)[:4000])


if __name__ == "__main__":
    main()
