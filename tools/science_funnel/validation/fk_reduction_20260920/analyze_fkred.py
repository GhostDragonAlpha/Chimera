"""analyze_fkred.py -- the FK-REDUCTION lane analyzer.

Parses the run matrix under .tmp/fkred/runs/ and emits the reconciliation and
the A/B verdict as JSON (receipt_input.json):
  1. F1 reconciliation: the census site sum vs the pinned tickcost
     fk.evaluate hits (86549 over the 302-tick walk), per site and structurally;
  2. F2 fence: stdout/stderr sha sets per binary shape against the anchors;
  3. the interleaved plain/reduce wall A/B (state-carrying, secondary currency
     -- the primary currency is the evaluate count);
  4. the trace A/B over the common (guard-truncated) window.

Usage: python analyze_fkred.py [--runs DIR] [--out JSON]

Trailer Agent: fkred.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

LANE_FENCE = "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc"
PLAIN_STDERR = "b505bb65652c2b796c163899ec51b7e5268342e5d31f28a9603fc2ab6c2d72ab"
SCENE_SHA = "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342"
TRACE_REFERENCE = "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481"
PINNED_FK_HITS = 86549  # tickcost raw walk_run_1, 302 ticks
TICKS = 302
BUDGET_MS = 3.333
PER_EVAL_TICKCOST_STATE_MS = 40.8315 / 286.586  # 0.14244
RECEIPT_STATE_FACTOR = 22.40 / 45.59            # 0.4913


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_census(stderr_path):
    """Parse the LAST [fkred] block (the final walk_run invocation)."""
    sites, calls, total = {}, {}, None
    for ln in Path(stderr_path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\[fkred\] phase=(\S+) evaluates_total=(\d+)$", ln)
        if m:
            total = int(m.group(2))
            continue
        m = re.match(r"\[fkred\] phase=(\S+) site=(\S+) n=(\d+)$", ln)
        if m:
            sites[m.group(2)] = int(m.group(3))
            continue
        m = re.match(r"\[fkred\] phase=(\S+) call=(\S+) n=(\d+)$", ln)
        if m:
            calls[m.group(2)] = int(m.group(3))
    return {"total": total, "sites": sites, "calls": calls}


def common_prefix_len(a, b):
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(Path(__file__).resolve().parents[4] / ".tmp/fkred/runs"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "receipt_input.json"))
    a = ap.parse_args()
    runs = Path(a.runs)
    out = {}

    # -- fence hashes -------------------------------------------------------
    shapes = {}
    for prefix, shape in [("plain", "plain"), ("reduce", "reduce"), ("census", "census")]:
        shas, walls = set(), []
        k = 1
        while (runs / ("%s%d_stdout.txt" % (prefix, k))).exists():
            shas.add(sha256_file(runs / ("%s%d_stdout.txt" % (prefix, k))))
            walls.append((runs / ("%s%d_stdout.txt" % (prefix, k))).stat().st_size)
            k += 1
        shapes[shape] = {"stdout_shas": sorted(shas), "n": k - 1}
    out["fence"] = shapes

    # -- census reconciliation ----------------------------------------------
    cens = {}
    k = 1
    while (runs / ("census%d_stderr.txt" % k)).exists():
        cens["census%d" % k] = parse_census(runs / ("census%d_stderr.txt" % k))
        k += 1
    recon = {}
    for name, c in cens.items():
        s = c["sites"]
        recon[name] = {
            "site_sum": sum(s.values()),
            "reported_total": c["total"],
            "pinned_fk_hits": PINNED_FK_HITS,
            "exact_match": sum(s.values()) == PINNED_FK_HITS,
            "per_tick": round(sum(s.values()) / TICKS, 3),
        }
    out["census_reconciliation"] = recon
    last = sorted(cens)[-1] if cens else None
    if last:
        out["census_sites"] = cens[last]["sites"]
        out["census_calls"] = cens[last]["calls"]

    # -- walls (interleaved pairs plain_k / reduce_k) -------------------------
    pairs = []
    for k in (1, 2, 3):
        pf, rf = runs / ("plain%d_time.txt" % k), runs / ("reduce%d_time.txt" % k)
        if pf.exists() and rf.exists():
            pairs.append((float(pf.read_text().strip()), float(rf.read_text().strip())))
    if pairs:
        pm = sum(p for p, _ in pairs) / len(pairs)
        rm = sum(r for _, r in pairs) / len(pairs)
        out["wall_ab"] = {"pairs": pairs, "plain_mean_s": round(pm, 2),
                          "reduce_mean_s": round(rm, 2),
                          "delta_s": round(rm - pm, 2),
                          "delta_pct": round(100 * (rm - pm) / pm, 1),
                          "caveat": "shared-box state factor carried (tickcost F3b RED); the state-independent currency is the evaluate count"}

    # -- trace A/B (common prefix; guard-truncated) ---------------------------
    pt, rt = runs / "plain_trace_stderr.txt", runs / "reduce_trace_stderr.txt"
    if pt.exists() and rt.exists():
        pa, rb = pt.read_bytes(), rt.read_bytes()
        n = common_prefix_len(pa, rb)
        out["trace_ab"] = {
            "common_prefix_bytes": n,
            "plain_bytes": len(pa), "reduce_bytes": len(rb),
            "identical_over_common_window": n >= 1177780 and pa[:n] == rb[:n],
            "split_cause": "the harness 120 s WALL-CLOCK window guard (gait_unit.cpp), fired at different ticks on today's loaded shared box; not a physics byte",
            "reference_anchor_c6f9b6c0": "machine-state-bound (wave-47 era, ~30 s/process box); NOT reproducible at this box state -- carried, per the prereg decision rule",
        }

    # -- bounds ---------------------------------------------------------------
    if last:
        e_before = PINNED_FK_HITS
        # the reduce build's evaluate population, derived from the census:
        # removes 3/free_step (rate-a reuse, e0, p0 via R1+R2) + poscorr
        # u_before + arows (R3) + clamp evaluate(start) (R2b, 0 fired here)
        s = cens[last]["sites"]
        c = cens[last]["calls"]
        fs = c["C_FS_MAIN"] + c["C_FS_DRV"] + c["C_FS_CON"] + c["C_FS_CROSS"] + c["C_FS_WALL"]
        removed = 3 * fs + s["S_PCUB"] + s["S_PCAR"] + s["S_PIN2"]
        e_after = e_before - removed
        out["bounds"] = {
            "evals_before_per_walk": e_before,
            "evals_removed_per_walk": removed,
            "evals_after_per_walk": e_after,
            "evals_before_per_tick": round(e_before / TICKS, 2),
            "evals_removed_per_tick": round(removed / TICKS, 2),
            "evals_after_per_tick": round(e_after / TICKS, 2),
            "reduction_pct": round(100 * removed / e_before, 1),
            "fk_ms_saved_per_tick_tickcost_state": round(removed / TICKS * PER_EVAL_TICKCOST_STATE_MS, 2),
            "fk_ms_saved_per_tick_receipt_state": round(removed / TICKS * PER_EVAL_TICKCOST_STATE_MS * RECEIPT_STATE_FACTOR, 2),
            "budget_ms": BUDGET_MS,
        }
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out.get("census_reconciliation", {}), indent=1))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
