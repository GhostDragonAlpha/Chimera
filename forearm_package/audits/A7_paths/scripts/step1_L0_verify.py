"""A7 step 1 - per-tendon L0 verification (stored vs independently recomputed).

Law under test (baseline_snapshot/code/DERIVATION.md section 7):
    a tendon path is an ordered list of fitted global points s0..sK;
    rest length L0 = sum_{j<K} |s_{j+1} - s_j|.
Reference implementation (baseline_snapshot/code/compiler.py lines 80-81, _pl):
    float(sum(np.linalg.norm(pts[i+1] - pts[i]) for i in range(len(pts)-1)))
Rest length assigned at compile time (compiler.py line 512):
    rest_length = _pl(pts) if complete else float("nan")   (NaN exports as null)

This script reads ONLY:
    baseline_snapshot/runs/actual_monkey_fit.json
    baseline_snapshot/runs/attachment_candidates.json
and writes receipts under audits/A7_paths/receipts/. It never writes the baseline.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
OUT = Path(r"E:\PythonChimera\forearm_package\audits\A7_paths\receipts")

FIT = json.loads((BASE / "runs" / "actual_monkey_fit.json").read_text(encoding="utf-8"))
CAND = json.loads((BASE / "runs" / "attachment_candidates.json").read_text(encoding="utf-8"))


def pl(pts: list[list[float]]) -> float:
    """Independent reimplementation of DERIVATION.md section 7 / compiler._pl.
    Summation order identical to compiler.py line 81: left-to-right over consecutive pairs."""
    total = 0.0
    for i in range(len(pts) - 1):
        d = np.asarray(pts[i + 1], dtype=np.float64) - np.asarray(pts[i], dtype=np.float64)
        total += float(np.linalg.norm(d))
    return total


def main() -> None:
    sites_by_name = {s["name"]: s for s in FIT["sites"]}
    tendons = FIT["tendons"]

    # ---- the 32 forearm sites, straight from the candidates packet -------------
    sites32: list[str] = []
    for body in ("radius", "radius_l"):
        for rec in CAND["bodies"][body]["candidates"]:
            sites32.append(rec["site_id"])
    assert len(sites32) == 32, f"expected 32 candidate sites, got {len(sites32)}"
    assert len(set(sites32)) == 32, "duplicate site ids in candidates packet"

    # ---- tendons touching the 32 sites: fit-packet scan vs packet membership ----
    touching: list[str] = []
    membership_packet: dict[str, list[str]] = {}
    for body in ("radius", "radius_l"):
        for rec in CAND["bodies"][body]["candidates"]:
            for m in rec["tendon_membership"]:
                membership_packet.setdefault(m["tendon"] if isinstance(m, dict) else m, []).append(rec["site_id"])
    for t in tendons:
        hit = [s for s in t["sites"] if s in set(sites32)]
        if hit:
            touching.append(t["name"])
    touch_set = set(touching)
    mem_set = set(membership_packet.keys())
    membership_cross = {
        "n_tendons_touching_fit_packet_scan": len(touch_set),
        "n_tendons_named_in_candidates_membership": len(mem_set),
        "in_scan_not_in_membership": sorted(touch_set - mem_set),
        "in_membership_not_in_scan": sorted(mem_set - touch_set),
    }

    # ---- per-tendon verification, ALL 120 tendons (census) ----------------------
    rows = []
    n_none = 0
    max_rel_dev = 0.0
    max_rel_dev_name = None
    n_exact = 0
    n_derived = 0
    points_match_sites = True
    for t in tendons:
        pts = t["points"]
        stored = t.get("rest_length")
        # consistency: packet points must equal the path sites' fitted_pos_global
        for sn, p in zip(t["sites"], pts):
            sp = sites_by_name[sn]["fitted_pos_global"]
            if sp is None:
                if p is not None:
                    points_match_sites = False
                continue
            if p is None or any(abs(a - b) > 0.0 for a, b in zip(p, sp)):
                points_match_sites = False
        # recompute: skip chains containing unresolved (null) points
        if any(p is None for p in pts):
            recomputed = None
            rel_dev = None
            abs_dev = None
            n_none += 1
        else:
            recomputed = pl(pts)
            if stored is None:
                rel_dev = None
                abs_dev = None
            else:
                abs_dev = abs(recomputed - stored)
                rel_dev = abs_dev / abs(stored) if stored != 0.0 else abs_dev
                max_rel_dev = max(max_rel_dev, rel_dev)
                if rel_dev == 0.0:
                    n_exact += 1
                elif max_rel_dev == rel_dev:
                    max_rel_dev_name = t["name"]
        if t["status"] == "derived":
            n_derived += 1
        rows.append({
            "tendon": t["name"],
            "n_points": len(pts),
            "status": t["status"],
            "stored_rest_length_m": stored,
            "recomputed_L0_m": recomputed,
            "abs_dev_m": abs_dev,
            "rel_dev": rel_dev,
            "touches_32": t["name"] in touch_set,
        })

    touch_rows = [r for r in rows if r["touches_32"]]
    n_touch_derived = sum(1 for r in touch_rows if r["status"] == "derived")
    n_touch_none = sum(1 for r in touch_rows if r["stored_rest_length_m"] is None)
    max_rel_touch = max((r["rel_dev"] for r in touch_rows if r["rel_dev"] is not None), default=None)

    receipt = {
        "law": "L0 = sum_j |s_{j+1}-s_j| over fitted global points (DERIVATION.md section 7; compiler._pl)",
        "n_tendons_packet": len(tendons),
        "n_sites_packet": len(FIT["sites"]),
        "sites32": sites32,
        "membership_cross": membership_cross,
        "census_all_120": {
            "n_status_derived": n_derived,
            "n_rest_length_null": n_none,
            "n_exact_bit_identical_recompute": n_exact,
            "max_rel_dev": max_rel_dev,
            "max_rel_dev_tendon": max_rel_dev_name,
            "points_match_site_records": points_match_sites,
        },
        "census_touching_32": {
            "n_tendons": len(touch_rows),
            "n_status_derived": n_touch_derived,
            "n_rest_length_null": n_touch_none,
            "max_rel_dev": max_rel_touch,
        },
        "rows_all": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step1_L0_receipt.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")

    # ---- human table: tendons touching the 32 ----------------------------------
    lines = [
        "A7 step1 - tendons touching the 32 forearm sites: stored vs recomputed L0",
        f"touching tendons: {len(touch_rows)} of {len(tendons)}; "
        f"derived(rest_length set): {n_touch_derived}; null(incomplete path): {n_touch_none}",
        f"max |rel dev| over ALL 120 recomputable: {max_rel_dev!r} (tendon {max_rel_dev_name!r}); "
        f"exact(bit-identical): {n_exact}",
        "",
        "tendon, n_pts, status, stored_L0_m, recomputed_L0_m, abs_dev_m, rel_dev",
    ]
    for r in touch_rows:
        lines.append(
            f"{r['tendon']}, {r['n_points']}, {r['status']}, "
            f"{r['stored_rest_length_m']}, {r['recomputed_L0_m']}, {r['abs_dev_m']}, {r['rel_dev']}"
        )
    (OUT / "step1_L0_table.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({k: v for k, v in receipt.items() if k != "rows_all" and k != "sites32"}, indent=1))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
