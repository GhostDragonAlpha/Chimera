"""
THE QUEUE — fill the GPU with authored concepts and write the ledger.

Reads LightEngine/categories.json, validates that every concept carries a
pre-registered falsifier_ref, packs uniform-N batches, measures the card's
batch size, runs each batch for the declared window, and writes
LightEngine/output/ledger.json.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
import math
import time
import datetime
import numpy as np
from typing import Any

from LightEngine import kernel, seed_structures
from LightEngine.demo_ensemble import (
    build_world,
    _world_verdict,
    _structure_persistence_metrics,
    OUTPUT_DIR,
    R_SHELL,
    R_DISK,
    F_CORE,
)
from LightEngine.demo_seed import (
    structureless_start,
    cluster_count_and_sizes,
    bound_mass_fraction,
    edge_sharpness,
    system_radius,
    shell_disk_metrics,
    core_bound_fraction,
    METRIC_R_INNER,
    METRIC_R_OUTER,
    FLICKER_CV_THRESHOLD,
    BOX,
    DT,
    VEL_SIGMA,
    R_WALL,
    R_BOND,
    R_C,
    G,
)

CATEGORY_PATH = os.path.join(os.path.dirname(__file__), "categories.json")
LEDGER_PATH = os.path.join(OUTPUT_DIR, "ledger.json")
DEFAULT_TICKS = 100000
BENCHMARK_TICKS = 2000
BENCHMARK_N = 4096


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_manifest(path: str) -> list[dict[str, Any]]:
    """Load and validate the categories manifest."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("manifest must be a JSON list")
    for entry in data:
        _validate_entry(entry)
    return data


def _validate_entry(entry: dict[str, Any]) -> None:
    """REFUSE any concept without a pre-registered falsifier_ref."""
    required = ["id", "category", "structure", "geometry", "seed", "n", "falsifier_ref"]
    missing = [k for k in required if k not in entry]
    if missing:
        raise ValueError(
            f"manifest entry {entry.get('id', '?')} missing fields: {missing}"
        )
    if not entry.get("falsifier_ref"):
        raise ValueError(
            f"manifest entry {entry['id']} has no falsifier_ref — "
            "queue refuses to run an un-falsified concept"
        )
    if not isinstance(entry["n"], int) or entry["n"] <= 0:
        raise ValueError(f"manifest entry {entry['id']} has invalid n={entry['n']}")


def group_by_n(entries: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    """Group batch-runnable entries by uniform N (mixed-N batches are forbidden)."""
    groups: dict[int, list[dict[str, Any]]] = {}
    for e in entries:
        if e.get("runner") == "solo":
            continue
        n = int(e["n"])
        groups.setdefault(n, []).append(e)
    # deterministic order
    return {n: groups[n] for n in sorted(groups)}


def _build_cushion_cube(side: int, spacing: float, seed: int):
    """Ordered cubic lattice printed at cushion equilibrium spacing."""
    rng = np.random.default_rng(seed)
    s = int(side)
    if s < 2:
        raise ValueError("cushion_cube side must be >= 2")
    offsets = (np.arange(s, dtype=np.float64) - (s - 1) / 2.0) * spacing
    gx, gy, gz = np.meshgrid(offsets, offsets, offsets, indexing="ij")
    pos = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)
    jitter = rng.normal(0.0, R_WALL * 0.01, size=pos.shape)
    pos += jitter
    vel = np.zeros_like(pos)
    return pos.astype(np.float32), vel.astype(np.float32)


def _build_packed_bed(n: int, spacing: float, seed: int):
    """Uniform random fill at the given point spacing (bond density default)."""
    # volume per point = spacing^3; box edge chosen to match that density
    box = ((n * spacing ** 3) ** (1.0 / 3.0)) * 1.0
    # cold start with tiny velocity dispersion so it is not artificially hot
    pos, vel = structureless_start(n, box, VEL_SIGMA * 0.05, seed)
    return pos, vel


def build_entry_world(entry: dict[str, Any]) -> tuple[str, str, np.ndarray, np.ndarray, int]:
    """Return (id, structure, pos, vel, actual_n) for a manifest entry."""
    structure = entry["structure"]
    geom = entry.get("geometry", {})
    n = int(entry["n"])
    seed = int(entry["seed"])

    if structure == "cushion_cube":
        side = int(geom.get("side", 2))
        spacing = float(geom.get("spacing", 0.0484))
        pos, vel = _build_cushion_cube(side, spacing, seed)
        actual_n = pos.shape[0]
        return entry["id"], structure, pos, vel, actual_n

    if structure == "packed_bed":
        spacing = float(geom.get("density_spacing", R_BOND))
        pos, vel = _build_packed_bed(n, spacing, seed)
        return entry["id"], structure, pos, vel, n

    # delegate to the existing demo_ensemble builder; tag with our concept id
    spec = {"structure": structure, "seed": seed, "tag": entry["id"]}
    tag, struct, pos, vel, actual_n = build_world(spec, n)
    return entry["id"], struct, pos, vel, actual_n


def benchmark_w(ticks: int = BENCHMARK_TICKS, n: int = BENCHMARK_N):
    """
    Measure EnsembleVerlet throughput for W in {8, 16, 32} at fixed N.
    Returns (chosen_W, measurements) where chosen_W is the largest W whose
    per-world time does not regress more than 20% vs W=8.
    """
    print("=" * 70)
    print("QUEUE BENCHMARK — measuring batch-size scaling on this card")
    print(f"N={n}, ticks={ticks}, W candidates={{8,16,32}}")
    print("-" * 70)
    measurements = {}
    baseline_per_world = None
    for W in (8, 16, 32):
        pos_list = []
        vel_list = []
        for w in range(W):
            pos, vel = structureless_start(n, BOX, VEL_SIGMA, seed=w)
            pos_list.append(pos)
            vel_list.append(vel)
        stacked_pos = np.stack(pos_list, axis=0)
        stacked_vel = np.stack(vel_list, axis=0)

        ens = kernel.EnsembleVerlet(W, n)
        ens.set_all(stacked_pos, stacked_vel)
        ens.compute_acceleration()

        t0 = time.perf_counter()
        for _ in range(ticks):
            ens.step(DT)
        wall = time.perf_counter() - t0

        per_world_tick = wall / (ticks * W)
        per_world_tick_ms = per_world_tick * 1000.0
        if baseline_per_world is None:
            baseline_per_world = per_world_tick
        regression = per_world_tick / baseline_per_world
        measurements[W] = {
            "wall_seconds": wall,
            "per_world_tick_ms": per_world_tick_ms,
            "regression_vs_w8": regression,
        }
        print(f"  W={W:2d}: wall={wall:.3f}s  per-world/tick={per_world_tick_ms:.4f}ms  "
              f"regression={regression:.3f}x")

    chosen = 8
    for W in (8, 16, 32):
        if measurements[W]["regression_vs_w8"] <= 1.20:
            chosen = W
    print(f"  chosen batch size W={chosen}")
    print("=" * 70)
    return chosen, measurements


def _init_world_metrics() -> dict[str, list]:
    return {
        "tick": [],
        "clusters": [],
        "max_cluster": [],
        "bound_frac": [],
        "edge": [],
        "radius": [],
        "radiated_energy": [],
        "radiated_power": [],
        "shell_radius_mean": [],
        "shell_radius_std": [],
        "core_bound_frac": [],
        "z_disp": [],
        "bond_retention": [],
    }


def _concept_verdict(standard_verdict: str, expected: str | None,
                     final_max: int, final_bound: float, cluster_cv: float,
                     n: int) -> tuple[str, str | None]:
    """
    Translate the standard falsifier verdict for a concept with a declared
    expectation.  Intended-equilibrium concepts ("mono_condensed"): one bound
    cluster IS the prediction, not a failure — SETTLED uses the standard
    falsifier's own numbers (0.95 cluster frac, FLICKER_CV_THRESHOLD) so no
    new thresholds are authored.  Returns (verdict, standard_verdict_or_None).
    """
    if expected == "mono_condensed" and standard_verdict == "COLLAPSE":
        if (final_max >= 0.95 * n and final_bound >= 0.9
                and cluster_cv <= FLICKER_CV_THRESHOLD):
            return "SETTLED", standard_verdict
    return standard_verdict, None


def run_batch(
    batch: list[dict[str, Any]],
    n: int,
    ticks: int,
    batch_id: str,
    diagnostic_note: str | None = None,
) -> list[dict[str, Any]]:
    """Run one uniform-N batch and return per-concept ledger rows."""
    W = len(batch)
    ids, structures, pos_list, vel_list = [], [], [], []
    for entry in batch:
        cid, struct, pos, vel, actual_n = build_entry_world(entry)
        if actual_n != n:
            raise ValueError(
                f"concept {cid}: actual N={actual_n} does not match batch N={n}"
            )
        ids.append(cid)
        structures.append(struct)
        pos_list.append(pos)
        vel_list.append(vel)

    stacked_pos = np.stack(pos_list, axis=0)
    stacked_vel = np.stack(vel_list, axis=0)
    ens = kernel.EnsembleVerlet(W, n)
    ens.set_all(stacked_pos, stacked_vel)
    ens.compute_acceleration()

    metrics_per_world = [_init_world_metrics() for _ in range(W)]
    sample_every = max(1, ticks // 40)

    note_str = f" ({diagnostic_note})" if diagnostic_note else ""
    print(f"\nBATCH {batch_id}: W={W}, N={n}, ticks={ticks}{note_str}")
    print(f"concepts: {', '.join(ids)}")

    t0 = time.perf_counter()
    for tick in range(1, ticks + 1):
        ens.step(DT)
        if tick % sample_every == 0 or tick == ticks:
            ens.sync_from_device()
            for w in range(W):
                pos_w = ens.pos[w]
                mw = metrics_per_world[w]
                n_clust, sizes = cluster_count_and_sizes(pos_w, R_C)
                bound_frac = bound_mass_fraction(pos_w, R_BOND)
                edge = edge_sharpness(pos_w, METRIC_R_INNER, METRIC_R_OUTER)
                rad = system_radius(pos_w)
                n_core = int(F_CORE * n) if structures[w] in ("core_shell", "disk") else 0
                persist, _ = _structure_persistence_metrics(pos_w, structures[w], n_core)

                mw["tick"].append(tick)
                mw["clusters"].append(n_clust)
                mw["max_cluster"].append(int(sizes.max()))
                mw["bound_frac"].append(bound_frac)
                mw["edge"].append(edge)
                mw["radius"].append(rad)
                mw["radiated_energy"].append(float(ens.radiated_energy[w]))
                mw["radiated_power"].append(float(ens.last_radiated_power[w]))
                mw["shell_radius_mean"].append(persist.get("shell_radius_mean", 0.0))
                mw["shell_radius_std"].append(persist.get("shell_radius_std", 0.0))
                mw["core_bound_frac"].append(persist.get("core_bound_frac", 0.0))
                mw["z_disp"].append(persist.get("z_disp", 0.0))
                mw["bond_retention"].append(persist.get("bond_retention", 0.0))
    wall = time.perf_counter() - t0

    rows = []
    for w in range(W):
        mw = metrics_per_world[w]
        verdict, reasons, final_max, final_bound, final_radius, cluster_cv, bound_swing = \
            _world_verdict(mw, n)
        standard_verdict = verdict
        verdict, recorded_standard = _concept_verdict(
            verdict, batch[w].get("expected"), final_max, final_bound,
            cluster_cv, n)
        if recorded_standard is not None:
            reasons = (["intended mono-condensed equilibrium held "
                        "(standard verdict recorded as evidence)"]
                       + reasons)
        rows.append({
            "id": ids[w],
            "batch_id": batch_id,
            "verdict": verdict,
            "standard_verdict": recorded_standard or standard_verdict,
            "reasons": reasons,
            "metrics": {
                "final_max_cluster": final_max,
                "final_bound_frac": final_bound,
                "final_radius": final_radius,
                "cluster_cv_late": cluster_cv,
                "bound_swing_late": bound_swing,
                "radiated_energy": mw["radiated_energy"][-1],
                "radiated_power": mw["radiated_power"][-1],
                "shell_radius_mean": mw["shell_radius_mean"][-1] if mw["shell_radius_mean"] else 0.0,
                "shell_radius_std": mw["shell_radius_std"][-1] if mw["shell_radius_std"] else 0.0,
                "core_bound_frac": mw["core_bound_frac"][-1] if mw["core_bound_frac"] else 0.0,
                "z_disp": mw["z_disp"][-1] if mw["z_disp"] else 0.0,
                "bond_retention": mw["bond_retention"][-1] if mw["bond_retention"] else 0.0,
            },
            "n": n,
            "ticks": ticks,
            "wall_seconds": wall,
            "timestamp": _now(),
            "diagnostic_note": diagnostic_note,
        })
    print(f"  batch wall time: {wall:.3f}s  ({wall/ticks*1e3:.3f} ms/tick total)")
    for r in rows:
        print(f"  VERDICT [{r['id']}]: {r['verdict']}")
    return rows


def run_solo_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Record a solo-routed concept as queued without executing it in batch."""
    return {
        "id": entry["id"],
        "batch_id": "solo",
        "verdict": "QUEUED_SOLO",
        "reasons": ["runner is 'solo'; not executed by the batch queue"],
        "metrics": {},
        "n": int(entry["n"]),
        "ticks": 0,
        "wall_seconds": 0.0,
        "timestamp": _now(),
        "diagnostic_note": None,
    }


def write_ledger(rows: list[dict[str, Any]], path: str) -> None:
    """Append rows to the ledger JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ledger: list[dict[str, Any]] = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        except Exception:
            ledger = []
    ledger.extend(rows)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="THE QUEUE — batched concept training")
    parser.add_argument("--manifest", type=str, default=CATEGORY_PATH,
                        help="path to categories.json")
    parser.add_argument("--ticks", type=int, default=DEFAULT_TICKS,
                        help="observation window per batch (default 100k)")
    parser.add_argument("--diagnostic-note", type=str, default=None,
                        help="note for truncated diagnostic runs")
    parser.add_argument("--skip-benchmark", action="store_true",
                        help="use W=8 without measuring (not recommended)")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    batch_entries = [e for e in manifest if e.get("runner") != "solo"]
    solo_entries = [e for e in manifest if e.get("runner") == "solo"]

    if args.skip_benchmark:
        chosen_w = 8
        measurements = {}
        print("WARNING: --skip-benchmark selected; using W=8 unmeasured")
    else:
        chosen_w, measurements = benchmark_w()

    groups = group_by_n(batch_entries)
    if not groups and not solo_entries:
        print("No runnable concepts in manifest.")
        return

    all_rows: list[dict[str, Any]] = []
    batch_counter = 0
    for n, entries in groups.items():
        for i in range(0, len(entries), chosen_w):
            batch = entries[i:i + chosen_w]
            batch_counter += 1
            batch_id = f"N{n}_B{batch_counter}"
            rows = run_batch(batch, n, args.ticks, batch_id, args.diagnostic_note)
            all_rows.extend(rows)

    for entry in solo_entries:
        all_rows.append(run_solo_entry(entry))

    write_ledger(all_rows, LEDGER_PATH)

    print("\n" + "=" * 70)
    print(f"QUEUE DONE — {len(all_rows)} concepts recorded")
    print(f"ledger: {LEDGER_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
