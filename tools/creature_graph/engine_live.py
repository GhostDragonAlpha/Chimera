"""Read-only client for the live engine, plus the verified-instances cross-check.

The engine serves GET /tick_state on 127.0.0.1:8107. This module is GET-only,
light-polling (one request per call), never POSTs -- the standing fleet rule.
The cross-check asks: do the graph's VERIFIED compartment instances match what
the engine actually serves right now?
"""

import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ENGINE_URL = "http://127.0.0.1:8107/tick_state"
TOL = 1e-4  # relative tolerance on float compares


def fetch_tick_state(url: str = ENGINE_URL, timeout: float = 5.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _close(a, b) -> bool:
    try:
        return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a) - float(b)) <= TOL * max(1.0, abs(float(a)), abs(float(b)))
    except (TypeError, ValueError):
        return False


def cross_check(g, tick: dict) -> dict:
    """Compare the graph's verified height-band compartment instances against
    the live engine cells. The 4 built compartments are height-band cuts at the
    measured joint heights (ankle 0.338, knee 1.903, hip 3.415)."""
    verified = [o for o in g.objects.values()
                if o.get("classification") == "type.A1"
                and o["status"] == "verified"]
    verified.sort(key=lambda o: (o.get("spatial") or {}).get("band_y", [0, 0])[0])
    report = {
        "engine_url": ENGINE_URL,
        "engine_ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine_ticks": tick.get("ticks"),
        "graph_verified_instances": [o["id"] for o in verified],
        "checks": [],
        "pass": True,
    }

    def check(name, ok, detail=""):
        report["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            report["pass"] = False

    cells = tick.get("cells") or []
    check("n_cells matches verified instance count",
          tick.get("n_cells") == len(verified) == len(cells),
          f"engine n_cells={tick.get('n_cells')} engine cells={len(cells)} graph verified={len(verified)}")
    check("sealed", tick.get("sealed") is True, f"sealed={tick.get('sealed')}")
    check("no seal refusal", not tick.get("seal_refusal"), f"seal_refusal={tick.get('seal_refusal')!r}")
    conservation = tick.get("conserve_pct")
    try:
        valid = conservation is not None and not isinstance(conservation, bool) and math.isfinite(float(conservation))
        conservation_ok = valid and abs(float(conservation)) < 0.01
    except (TypeError, ValueError):
        conservation_ok = False
    check("conservation ~0", conservation_ok,
          "missing conserve_pct" if conservation is None else f"conserve_pct={conservation!r}")

    sum_v0 = 0.0
    matched = {r["graph_id"]: r for r in map_cells_to_instances(g, tick)}
    for obj in verified:
        band = (obj.get("spatial") or {}).get("band_y")
        row = matched[obj["id"]]
        index = row["engine_cell_index"]
        if index is None:
            check(f"{obj['id']} has a live cell at its band", False,
                  row["match"])
            continue
        cell = cells[index]
        sp = obj.get("spatial") or {}
        ok_v0 = _close(cell.get("v0"), sp.get("v0_m3"))
        check(f"{obj['id']} band matches live cell {index}", True,
              f"graph {band} = live [{cell.get('ylo')}, {cell.get('yhi')}]")
        check(f"{obj['id']} v0 matches live cell {index}", ok_v0,
              f"graph {sp.get('v0_m3')} vs live {cell.get('v0')}")
        check(f"{obj['id']} live cell not degenerate", cell.get("degenerate") is False,
              f"degenerate={cell.get('degenerate')}")
        try:
            sum_v0 += float(cell.get("v0"))
        except (TypeError, ValueError):
            sum_v0 = float("nan")
    check("sum v0 == V_whole", _close(sum_v0, tick.get("V_whole")),
          f"sum={sum_v0} vs V_whole={tick.get('V_whole')}")
    return report


def write_snapshot(report: dict, evidence_dir: str) -> str:
    os.makedirs(evidence_dir, exist_ok=True)
    path = os.path.join(evidence_dir, "engine_snapshot_tick_state.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    return path


# ---------------------------------------------------------------------------
# Inspection with consistent IDs + timestamps (acceptance 9, graph side)
# ---------------------------------------------------------------------------

import time  # noqa: E402

SNAP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "live_snapshots")


def _band_match(cell: dict, band) -> bool:
    """Match a live cell to a graph instance by BAND GEOMETRY (ylo/yhi), not by
    the engine's internal cell order -- the cut order is an engine detail; the
    band planes are the stable geometric identity."""
    if not band or len(band) != 2:
        return False
    return _close(cell.get("ylo"), band[0]) and _close(cell.get("yhi"), band[1])


def map_cells_to_instances(g, tick: dict) -> list:
    """Join the live per-cell state to VERIFIED compartment instances by stable
    graph ids (bands matched by geometry). Every row carries the SAME ids + the
    engine timestamps, so a structure, its pressure, and any intervention record
    join unambiguously (acceptance 9)."""
    verified = [o for o in g.objects.values()
                if o.get("classification") == "type.A1"
                and o["status"] == "verified"]
    verified.sort(key=lambda o: (o.get("spatial") or {}).get("band_y", [0, 0])[0])
    cells = tick.get("cells") or []
    candidates = {obj["id"]: [i for i,c in enumerate(cells)
                  if _band_match(c, (obj.get("spatial") or {}).get("band_y"))]
                  for obj in verified}
    owners = {}
    for oid, indices in candidates.items():
        for i in indices:
            owners.setdefault(i, []).append(oid)
    rows = []
    for obj in verified:
        indices = candidates[obj["id"]]
        contested = any(len(owners[i]) > 1 for i in indices)
        unique = len(indices) == 1 and not contested
        index = indices[0] if unique else None
        cell = cells[index] if unique else {}
        match = ("by band geometry" if unique else
                 f"ambiguous: {len(indices)} candidates; shared assignment={contested}"
                 if indices else "NO LIVE CELL")
        rows.append({
            "graph_id": obj["id"], "engine_cell_index": index,
            "band_y": (obj.get("spatial") or {}).get("band_y"),
            "v0_m3": (obj.get("spatial") or {}).get("v0_m3"),
            "live_V_m3": cell.get("V"), "live_P_pa": cell.get("P"),
            "degenerate": cell.get("degenerate"), "match": match,
            "candidate_count": len(indices), "candidate_indices": indices,
            "ts_us": tick.get("ts_us"), "ticks": tick.get("ticks"),
            "sampling_hz": tick.get("sampling_hz"),
        })
    return rows


def fetch_with_latency(url: str = ENGINE_URL, timeout: float = 5.0) -> tuple:
    """One light GET + its measured wall-clock latency (report the measurement,
    not a claim). Returns (tick, latency_ms)."""
    t0 = time.perf_counter()
    tick = fetch_tick_state(url, timeout)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return tick, latency_ms


def write_inspection(g, tick: dict, latency_ms: float,
                     selected_id: str, intervention_note: str = "") -> str:
    """Persist one inspection record joining the SELECTED structure, its live
    pressure, and any intervention by consistent ids + timestamps. Graph-side
    only: nothing here can modify engine coordinates."""
    rows = map_cells_to_instances(g, tick)
    rec = {
        "record": "inspection",
        "utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "engine": {"url": ENGINE_URL, "ticks": tick.get("ticks"),
                   "ts_us": tick.get("ts_us"),
                   "get_latency_ms": round(latency_ms, 3),
                   "sampling_hz": tick.get("sampling_hz"),
                   "limits": "one light GET per call; REST snapshot latency is "
                             "not the tick path; no /frame, no LLM roundtrip"},
        "selected": selected_id,
        "intervention": intervention_note,
        "cells": rows,
    }
    os.makedirs(SNAP_DIR, exist_ok=True)
    path = os.path.join(SNAP_DIR, f"inspection_{tick.get('ticks', 0)}_{int(time.time())}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1, ensure_ascii=False)
    return path
