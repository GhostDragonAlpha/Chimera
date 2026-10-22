"""Workshop board feed (WC-PLAY-1) — the live objective verdict, display only.

Reads the running engine's GET /tick_b2_state (GET-only: this tool NEVER
POSTs to the engine — the player's clicks and keys own every mutation) and
writes the objective verdict into the engine's studio_board.v1 file, the same
shape workshop_challenge1.py's board() writer uses, ATOMICALLY (tmp +
os.replace, so the engine never reads a half-written board).

The verdict is the workshop objective law, evaluated OUTSIDE the engine as a
display accessory (no second evaluator lives in the engine):

  HELD  green : the newest crate part exists AND its COM is inside the
                marked region AND its bottom rests >= min-clearance above
                the hazard slab top.
  LOST   red  : otherwise, with the actionable line:
                no crate            -> "place a crate"
                COM outside region  -> "remove the crate and centre it over
                                        its support"
                clearance below the band -> the same centring line (the
                crate is on or sunken to the hazard).

UPRIGHT LAW (stated on the board): the crate's bottom is measured as
COM y minus half its authored height — the driver's documented upright
approximation (workshop_challenge1.py check()), valid while the crate stands
unrotated; a leaning crate reads optimistic, so the board names the
approximation instead of pretending a tilt-corrected metric.

The slab top is tracked live (the slab sinks mm-scale under the build's
weight): slab top = slab COM y + half its authored height, read from the
telemetry; pass --slab-top-m to pin a constant instead.

Run:  python tools/construction_packet/workshop_board_feed.py \
          --port 8840 --board ABS\\studio_board.json
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
from pathlib import Path


def fetch_state(port: int, timeout: float = 4.0) -> dict:
    with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/tick_b2_state", timeout=timeout) as r:
        return json.loads(r.read().decode())


def newest_crate(parts: list, prefix: str):
    """The newest crate part: the highest numeric kit suffix (crate_1 >
    crate_0), falling back to the LAST list position (b2 place appends)."""
    best = None
    best_key = None
    for i, p in enumerate(parts):
        pid = p.get("id", "")
        if not pid.startswith(prefix):
            continue
        suffix = pid[len(prefix):].lstrip("_")
        try:
            key = (1, int(suffix), i)
        except ValueError:
            key = (0, 0, i)
        if best_key is None or key > best_key:
            best_key, best = key, p
    return best


def verdict(parts: list, region, slab_top: float, min_clear: float,
            crate_half_m: float, tilt_min_up_y: float = 0.9848):
    """(held, clearance_m, in_region, tipped, has_crate, action) — the
    workshop_challenge1 driver's predicate, all three clauses: COM inside
    the region AND bottom clearance AND not tipped. The tilt clause is the
    driver's own (up-axis y < 0.9848, 10 deg band) — MEASURED reason: a
    crate lying on the hazard after a topple holds ~+15 mm of axis-aligned
    "clearance" (its side rests on the slab), so the upright approximation
    alone would read HELD over a lost load."""
    crate = newest_crate(parts, "crate")
    if crate is None:
        return False, None, False, False, False, "place a crate"
    com = crate["com_m"]
    in_region = (region[0] <= com[0] <= region[1]
                 and region[2] <= com[2] <= region[3])
    bottom = com[1] - crate_half_m          # the upright approximation
    clear = bottom - slab_top
    q = crate.get("pose_q_wxyz", [1.0, 0.0, 0.0, 0.0])
    up_y = 1 - 2 * (q[1] * q[1] + q[3] * q[3])   # world y of the up-axis
    tipped = up_y < tilt_min_up_y
    held = in_region and clear >= min_clear and not tipped
    if held:
        action = ""
    else:
        # challenge 1's ACTION line for every named failure class
        action = "remove the crate and centre it over its support"
    return held, clear, in_region, tipped, True, action


LAW = ("objective law: the newest crate's COM stays inside the marked "
       "region x {x0:.2f}..{x1:.2f} m, {z0:+.2f}..{z1:+.2f} m with its "
       "bottom >= {min_mm:.0f} mm above the slab top and its up-axis "
       "within 10 deg of vertical (up_y >= 0.9848, the driver's tipped "
       "band); bottom is COM y minus half the crate's authored height "
       "({half_mm:.0f} mm) -- the upright approximation, valid while the "
       "crate stands unrotated (a leaning crate defeats the axis-aligned "
       "clearance metric, so tilt is checked separately); the load path "
       "is the admitted contact physics only")


def board_doc(held: bool, cell: str, law: str) -> dict:
    return {"standing": "MATTER WORKSHOP - live objective",
            "updated": "workshop board feed (WC-PLAY-1)",
            "stages": [{"id": "WS3",
                        "name": "Salvage over the hazard",
                        "status": "green" if held else "blocked",
                        "law": law,
                        "tool": "Tab place mode | Enter commit | F weld | "
                                "X remove | F9 save | F10 load",
                        "artifact": "live verdict chip + clearance readout",
                        "falsifier": "crate bottom below the clearance band "
                                     "at settle (on the hazard) or COM out "
                                     "of the region",
                        "cell": cell}]}


def board_write(path: Path, doc: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--board", required=True)
    ap.add_argument("--slab", default="hazard_pad")
    ap.add_argument("--crate-prefix", default="crate")
    ap.add_argument("--region", default="0.54,0.70,-0.05,0.05",
                    help="x0,x1,z0,z1 of the marked region, metres")
    ap.add_argument("--slab-top-m", type=float, default=None,
                    help="pin the slab top height (default: track it live "
                         "from the slab COM + --slab-half-m)")
    ap.add_argument("--slab-half-m", type=float, default=0.02,
                    help="half the slab's authored height (the kit pad is "
                         "0.04 m tall)")
    ap.add_argument("--crate-half-m", type=float, default=0.025,
                    help="half the crate's authored height (the kit crate "
                         "is 0.05 m tall)")
    ap.add_argument("--min-clearance-m", type=float, default=0.004)
    ap.add_argument("--interval", type=float, default=0.5)
    args = ap.parse_args(argv)

    region = [float(v) for v in args.region.split(",")]
    assert len(region) == 4, "--region wants x0,x1,z0,z1"
    board_path = Path(args.board).resolve()
    law = LAW.format(x0=region[0], x1=region[1], z0=region[2], z1=region[3],
                     min_mm=args.min_clearance_m * 1000.0,
                     half_mm=args.crate_half_m * 1000.0)
    print(f"board feed: port {args.port} -> {board_path} every "
          f"{args.interval}s", flush=True)

    t_last_ok = 0.0
    while True:
        try:
            st = fetch_state(args.port)
            parts = st.get("parts", [])
            slab = next((p for p in parts if p.get("id") == args.slab), None)
            slab_top = (args.slab_top_m if args.slab_top_m is not None else
                        (slab["com_m"][1] + args.slab_half_m if slab
                         else 0.0))
            held, clear, in_region, tipped, has_crate, action = verdict(
                parts, region, slab_top, args.min_clearance_m,
                args.crate_half_m)
            if not has_crate:
                cell = "LOST: no crate in the scene. ACTION: " + action
            elif held:
                cell = (f"HELD: crate {clear * 1000:.0f} mm above the hazard "
                        f"slab, inside the marked region.")
            else:
                if tipped:
                    why = "the crate TIPPED off its support"
                elif not in_region:
                    why = "crate COM outside the marked region"
                else:
                    why = (f"clearance {clear * 1000:.0f} mm is below the "
                           f"{args.min_clearance_m * 1000:.0f} mm band")
                cell = f"LOST: {why}. ACTION: {action}."
            board_write(board_path, board_doc(held, cell, law))
            t_last_ok = time.time()
        except Exception as e:                      # engine not up yet: keep
            if time.time() - t_last_ok > 10.0:      # polling, never crash
                print(f"board feed: waiting for engine: {e}", flush=True)
                t_last_ok = time.time()
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
