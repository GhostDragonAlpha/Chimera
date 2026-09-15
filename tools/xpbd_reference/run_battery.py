"""Battery runner — PARALLEL (the operator's standing rule: independent
work overlaps; no serial single-threaded battery).

    python -m tools.xpbd_reference.run_battery [--json OUT.json] [--workers N]

Structure:
  * battery.parallel_task_list() emits the battery as 36 INDEPENDENT atomic
    probes (each builds fresh systems inside; determinism does not depend on
    scheduling or on process count).
  * The probes map over a multiprocessing POOL (spawn; Windows-safe via the
    __main__ guard below). The four cells' frequency probes, the six P2
    boundary cells, the ring modes and every bar run concurrently — the
    critical path is the slowest single probe, not the sum.
  * I/O is OVERLAPPED with compute: as each result lands, the runner prints
    one progress line and rewrites the partial JSON, so a killed run still
    leaves every completed probe on disk.

What stays serial (and why): the final assembly + bar-table formatting
(microseconds), and probe-internal numpy calls (small dense solves, 3x3 to
12x12 — BLAS overhead would exceed the arithmetic; parallelism here is at
the PROBE level, which is where the minutes are).
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import get_context

from . import battery


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", help="write raw results JSON here "
                                   "(incrementally, as probes finish)")
    ap.add_argument("--workers", type=int, default=0,
                    help="pool size (0 = min(cpu_count, n_probes))")
    args = ap.parse_args(argv)

    tasks = battery.parallel_task_list()
    nproc = args.workers or min(len(tasks), os.cpu_count() or 2)

    t0 = time.perf_counter()
    print("A1_XPBD B1x — the coupled XPBD reference model, falsifier battery")
    print("(world: live 4-cell table, DIAGNOSTIC.md; contract: PREREG.md)")
    print("%d independent probes on a %d-worker process pool "
          "(multiprocessing, spawn)." % (len(tasks), nproc), flush=True)

    results = {}
    ctx = get_context("spawn")
    with ctx.Pool(nproc) as pool:
        done = 0
        for name, val in pool.imap_unordered(battery.run_probe, tasks):
            results[name] = val
            done += 1
            print("  [%2d/%d] %-24s done  (%.1fs elapsed)"
                  % (done, len(tasks), name, time.perf_counter() - t0),
                  flush=True)
            if args.json:                       # OVERLAPPED I/O: the partial
                with open(args.json, "w") as f:  # JSON is rewritten between
                    json.dump(results, f, indent=1, default=float)  # probes
    elapsed = time.perf_counter() - t0

    r = battery.assemble(results)
    print("\n" + "=" * 92)
    print("ALL %d PROBES DONE in %.1fs wall (probes ran concurrently on %d "
          "workers)." % (len(tasks), elapsed, nproc))
    print("=" * 92 + "\n")
    print(battery.format_bar_table(r))
    print()
    print("  divergence demo (torso-weight press at the hip ring, 3 ticks,")
    print("  release; amplitude = worst |dV|/V0; DIVERGED = >1e3 x press-on):")
    demo = {"explicit n=1": r["P2_demo"]["explicit"],
            "xpbd n=4": r["P2_demo"]["xpbd"]}
    print("  tick   explicit n=1            xpbd n=4")
    for t in range(max(len(demo[k]["trace"]) for k in demo)):
        e = demo["explicit n=1"]["trace"]
        x = demo["xpbd n=4"]["trace"]
        print("  %4d   %-20s %s" % (
            t,
            "%.3e%s" % (e[t], "  DIVERGED"
                        if demo["explicit n=1"]["diverged_at"] == t + 1 else "")
            if t < len(e) else "",
            "%.3e" % x[t] if t < len(x) else ""))
    print("\nwall %.1fs" % elapsed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
