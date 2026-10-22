"""Workshop board feed (WC-OBJ-1) — the live objective verdict, display only.

Reads the running engine's GET /tick_b2_state (GET-only: this tool NEVER
POSTs to the engine — the player's clicks and keys own every mutation) and
writes the objective verdict into the engine's studio_board.v1 file, the same
shape workshop_challenge1.py's board() writer uses, ATOMICALLY (tmp +
os.replace, so the engine never reads a half-written board).

The verdict is the workshop objective law, evaluated OUTSIDE the engine as a
display accessory (no second evaluator lives in the engine):

  HELD   green : the newest crate part exists AND the sample is FRESH (the
                 engine's physical clock advanced since the previous poll
                 and the sim is not paused) AND its COM is inside the
                 marked region AND every corner of the crate box that
                 projects onto the pad-top footprint rests >= min-clearance
                 above the live slab top.
  LOST    red  : otherwise (a measured failure), with the actionable line:
                 no crate            -> "place a crate"
                 crate TIPPED        -> "remove the crate and centre it
                                        over its support"
                 corner on the hazard-> the same centring line
                 COM outside region  -> the same centring line
  PAUSED/STALE  : the physical clock is paused or has not advanced since
                 the previous poll — no HELD can be ruled from an old
                 sample. This chip is NOT a physics LOST: the last measured
                 state is frozen, and a measured failure keeps its LOST
                 wording until the clock moves again.

CORNER LAW (stated on the board): the crate's 8 corners are COM-relative
half-extents rotated by the crate's live pose quaternion, so a leaning
crate is judged by its true lowest in-footprint corner — a tilted crate
resting a corner ON the pad reads LOST, not optimistic HELD (the old
axis-aligned COM-bottom approximation could be defeated by a ~4.6 deg
tilt: worst corner drop 0.05*sin(tilt) exceeds the 4 mm band at 10 deg).
Corners whose x/z project OUTSIDE the pad-top footprint do not count —
that is the declared footprint-projection rule. Mild tilt is legal: the
upright gate is gone from the HELD predicate; tip detection remains only
to choose the LOST wording/ACTION.

FRESHNESS LAW: steps and paused are read from /tick_b2_state each poll.
HELD requires the newest physical sample: steps advanced since the
previous poll AND not paused. A paused or step-stalled poll shows the
distinct PAUSED/STALE chip. If steps go backwards (a re-admit reset the
clock), freshness tracking restarts from that reading.

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

# The driver's tipped band (up-axis y < 0.9848 == >10 deg from vertical).
# Kept ONLY to word the LOST reason/ACTION — no longer a HELD clause.
TILT_MIN_UP_Y = 0.9848


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


def rot_q(q, v):
    """Rotate v by unit quaternion q (w,x,y,z, w-first): R v via q -> rows.
    Same convention as b2_scene_gen._rot_com (tools/construction_packet/
    b2_scene_gen.py)."""
    w, x, y, z = q
    r = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(r[i][j] * v[j] for j in range(3)) for i in range(3))


def corner_clearance(com, q, half, slab_top, min_clear, footprint):
    """Lowest clearance above the slab top among the crate's 8 corners whose
    world x/z project inside the pad-top footprint.

    (clear or None, in_region_not_counted: n_in_footprint, worst_local)
    clear is None when NO corner projects into the footprint (nothing to
    judge — the COM-in-region clause still applies separately)."""
    fx0, fx1, fz0, fz1 = footprint
    worst = None
    worst_local = None
    n_in = 0
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                local = (sx * half[0], sy * half[1], sz * half[2])
                world = rot_q(q, local)
                x, y, z = com[0] + world[0], com[1] + world[1], com[2] + world[2]
                if not (fx0 <= x <= fx1 and fz0 <= z <= fz1):
                    continue           # footprint-projection rule: not counted
                n_in += 1
                clear = y - slab_top
                if worst is None or clear < worst:
                    worst, worst_local = clear, local
    return worst, n_in, worst_local


def verdict(parts: list, region, slab_top: float, min_clear: float,
            half, footprint, tilt_min_up_y: float = TILT_MIN_UP_Y):
    """dict with the corner-rule predicate:
      held_physics : COM inside region AND every in-footprint corner
                     >= min_clear above the slab top (NO tilt clause —
                     mild tilts are legal per GAME_PLAN §5.1).
      min_clear_m  : worst in-footprint corner clearance (None if no corner
                     projects into the footprint).
      tipped       : up-axis y below the driver's band — wording only.
      action       : "" when held, else challenge 1's centring line (or the
                     place-a-crate line when there is no crate)."""
    out = {"held_physics": False, "min_clear_m": None, "n_corners": 0,
           "worst_local": None, "in_region": False, "tipped": False,
           "has_crate": False, "action": ""}
    crate = newest_crate(parts, "crate")
    if crate is None:
        out["action"] = "place a crate"
        return out
    out["has_crate"] = True
    com = crate["com_m"]
    out["in_region"] = (region[0] <= com[0] <= region[1]
                        and region[2] <= com[2] <= region[3])
    q = crate.get("pose_q_wxyz", [1.0, 0.0, 0.0, 0.0])
    up_y = 1 - 2 * (q[1] * q[1] + q[3] * q[3])   # world y of the up-axis
    out["tipped"] = up_y < tilt_min_up_y
    clear, n_in, worst_local = corner_clearance(
        com, q, half, slab_top, min_clear, footprint)
    out["min_clear_m"] = clear
    out["n_corners"] = n_in
    out["worst_local"] = worst_local
    out["held_physics"] = out["in_region"] and clear is not None \
        and clear >= min_clear
    if not out["held_physics"]:
        # challenge 1's ACTION line for every named failure class
        out["action"] = "remove the crate and centre it over its support"
    return out


LAW = ("objective law, measured at the newest physical sample: HELD only "
       "while the engine's step counter advances (paused or step-stalled "
       "polls show a stale chip, not a ruling); the newest crate's COM is "
       "inside the marked region x {x0:.2f}..{x1:.2f} m, {z0:+.2f}..{z1:+.2f} m, "
       "and every corner of the crate box ({hx_mm:.0f} x {hy_mm:.0f} x "
       "{hz_mm:.0f} mm half-extents about the COM, rotated by the crate's "
       "live pose) whose x/z projects inside the pad-top footprint "
       "x {fx0:.2f}..{fx1:.2f} m, z {fz0:+.2f}..{fz1:+.2f} m sits "
       ">= {min_mm:.0f} mm above the live slab top (corners projecting "
       "outside the footprint do not count; mild tilt is legal); supports "
       "may stand on the pad — only the crate's own corners are judged "
       "here, until gap row 4 decides otherwise; the load path is the "
       "admitted contact physics only")


def board_doc(held: bool, cell: str, law: str,
              status: str = None) -> dict:
    if status is None:
        status = "green" if held else "blocked"
    return {"standing": "MATTER WORKSHOP - live objective",
            "updated": "workshop board feed (WC-OBJ-1)",
            "stages": [{"id": "WS3",
                        "name": "Salvage over the hazard",
                        "status": status,
                        "law": law,
                        "tool": "Tab place mode | Enter commit | F weld | "
                                "X remove | F9 save | F10 load",
                        "artifact": "live verdict chip + clearance readout",
                        "falsifier": "a crate corner resting on the hazard "
                                     "slab at the newest physical sample, "
                                     "or COM out of the region",
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
    ap.add_argument("--crate-half-extents-m",
                    default="0.05,0.025,0.025",
                    help="hx,hy,hz half-extents of the crate box about its "
                         "COM, metres (kit crate is 0.1 x 0.05 x 0.05)")
    ap.add_argument("--pad-footprint", default="0.48,0.76,-0.08,0.08",
                    help="x0,x1,z0,z1 of the pad TOP footprint, metres: "
                         "corners projecting inside are judged, outside "
                         "are not counted")
    ap.add_argument("--slab-top-m", type=float, default=None,
                    help="pin the slab top height (default: track it live "
                         "from the slab COM + --slab-half-m)")
    ap.add_argument("--slab-half-m", type=float, default=0.02,
                    help="half the slab's authored height (the kit pad is "
                         "0.04 m tall)")
    ap.add_argument("--min-clearance-m", type=float, default=0.004)
    ap.add_argument("--interval", type=float, default=0.5)
    args = ap.parse_args(argv)

    region = [float(v) for v in args.region.split(",")]
    assert len(region) == 4, "--region wants x0,x1,z0,z1"
    half = [float(v) for v in args.crate_half_extents_m.split(",")]
    assert len(half) == 3, "--crate-half-extents-m wants hx,hy,hz"
    footprint = [float(v) for v in args.pad_footprint.split(",")]
    assert len(footprint) == 4, "--pad-footprint wants x0,x1,z0,z1"
    board_path = Path(args.board).resolve()
    law = LAW.format(x0=region[0], x1=region[1], z0=region[2], z1=region[3],
                     hx_mm=half[0] * 1000.0, hy_mm=half[1] * 1000.0,
                     hz_mm=half[2] * 1000.0,
                     fx0=footprint[0], fx1=footprint[1],
                     fz0=footprint[2], fz1=footprint[3],
                     min_mm=args.min_clearance_m * 1000.0)
    print(f"board feed: port {args.port} -> {board_path} every "
          f"{args.interval}s", flush=True)

    t_last_ok = 0.0
    last_steps = None
    while True:
        try:
            st = fetch_state(args.port)
            parts = st.get("parts", [])
            steps = int(st.get("steps", 0))
            paused = bool(st.get("paused", False))
            # freshness: HELD needs the NEWEST physical sample — steps must
            # have advanced since the previous poll and the sim not paused.
            if last_steps is None:
                fresh = False            # first poll: no advance observed yet
            elif steps < last_steps:
                last_steps = steps       # re-admit reset the clock: restart
                fresh = False            # freshness tracking from here
            else:
                fresh = (not paused) and steps > last_steps
            last_steps = max(last_steps if last_steps is not None else steps,
                             steps)
            slab = next((p for p in parts if p.get("id") == args.slab), None)
            slab_top = (args.slab_top_m if args.slab_top_m is not None else
                        (slab["com_m"][1] + args.slab_half_m if slab
                         else 0.0))
            v = verdict(parts, region, slab_top, args.min_clearance_m,
                        half, footprint)
            stale = (paused or not fresh)
            if not v["has_crate"]:
                cell = "LOST: no crate in the scene. ACTION: " + v["action"]
                status = "blocked"
            elif stale and v["held_physics"]:
                # stale/paused chip: NOT a HELD, NOT a physics LOST — the
                # frozen sample may not rule "held".
                if paused:
                    cell = (f"PAUSED: physics clock stopped (steps {steps}) "
                            f"— no fresh sample to rule HELD. ACTION: none; "
                            f"resume the simulation.")
                else:
                    cell = (f"STALE: no engine step since the last poll "
                            f"(steps {steps}) — the verdict waits for the "
                            f"newest physical sample.")
                status = "amber"
            elif v["held_physics"] and fresh:
                cell = (f"HELD: crate's worst in-footprint corner "
                        f"{v['min_clear_m'] * 1000:.0f} mm above the hazard "
                        f"slab, inside the marked region.")
                status = "green"
            else:
                if v["tipped"]:
                    why = "the crate TIPPED off its support"
                elif not v["in_region"]:
                    why = "crate COM outside the marked region"
                elif v["min_clear_m"] is None:
                    why = ("no crate corner projects onto the pad-top "
                           "footprint, and the COM is outside the region")
                else:
                    why = (f"a crate corner rests on the hazard slab "
                           f"(worst in-footprint corner "
                           f"{v['min_clear_m'] * 1000:.0f} mm above the slab "
                           f"top, below the "
                           f"{args.min_clearance_m * 1000:.0f} mm band)")
                cell = f"LOST: {why}. ACTION: {v['action']}."
                status = "blocked"
            board_write(board_path, board_doc(v["held_physics"] and fresh,
                                              cell, law, status))
            t_last_ok = time.time()
        except Exception as e:                      # engine not up yet: keep
            if time.time() - t_last_ok > 10.0:      # polling, never crash
                print(f"board feed: waiting for engine: {e}", flush=True)
                t_last_ok = time.time()
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
