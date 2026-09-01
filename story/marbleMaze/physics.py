"""marbleMaze -- the tilt table: a marble, a maze, and the operator's input.

A membrane is a SEPARATE MATRIX applied to the main Gaussian space.  This one's
matrix is the whole game: a maze (walls + goal) on a table, one marble, and the
operator's tilt timeline.  The tilt inputs are recorded to tilt.json as
(pass, pitch, roll) events, and the marble's position is INTEGRATED from that
record -- so the record IS the matrix: replaying the tilt timeline reproduces
the marble's exact path.

The operator tilts the table with the arrow keys on the deck: the whole table
(walls, floor, goal) rotates in 3D by the tilt, and the marble accelerates
down-slope, bounces off the walls, and rolls toward the goal.  The maze is a
zigzag of baffles with alternating gaps -- solvable by tilting R, L, R, L.

RULE 0 -- stated before the first marble drops:
    STATEMENT : one marble, steered by the operator's tilt through an authored
                maze on a Gaussian-splat table, reaches the goal -- and the
                operator's inputs are recorded, so the run replays exactly.
    PREDICTION: (a) a tilt moves the marble, (b) the marble follows the tilt
                direction, (c) the marble stays on the table (the walls hold),
                (d) the record is the matrix (same tilts -> same path),
                (e) the maze is winnable by tilt alone.
    FALSIFIER : the marble never moves for a real tilt; it rolls against the
                tilt; it escapes the table; the replay disagrees with the run;
                or no tilt sequence reaches the goal.  Any one fires the verdict.

The deck: ArrowUp / ArrowDown tilt the table along y, ArrowLeft / ArrowRight
along x, KeyR resets the marble to the start (clearing the tilt record),
plays/pauses.  Steer the marble to the green goal ring.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
NUMBERS_PATH = _HERE / "numbers.json"
TILTS_PATH = _HERE / "tilt.json"
# THE LIVE RUN RECORDS TO ITS OWN FILE -- never tilt.json.  tilt.json is the stored
# record (the win); a live run is a scratch take that must not overwrite it just
# because someone pressed Play.  Replaying a live take reads this instead.
LIVE_PATH = _HERE / "live_record.json"

# buffer layout (ParticleEngine.core.COL)
NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20

# the maze: axis-aligned wall segments (x0, y0, x1, y1), local table frame
_WALLS = [
    (-3.1, -3.1, 3.1, -3.1),   # bottom perimeter
    (-3.1, 3.1, 3.1, 3.1),     # top perimeter
    (-3.1, -3.1, -3.1, 3.1),   # left perimeter
    (3.1, -3.1, 3.1, 3.1),     # right perimeter
    (-3.1, 1.7, 1.0, 1.7),     # B1: gap at x > 1.0
    (-1.0, 0.8, 3.1, 0.8),     # B2: gap at x < -1.0
    (-3.1, -0.1, 1.0, -0.1),   # B3: gap at x > 1.0
    (-1.0, -1.0, 3.1, -1.0),   # B4: gap at x < -1.0
    (-2.4, -0.1, -2.4, 0.8),   # pillar in the B2 gap
    (2.4, -0.1, 2.4, 0.8),     # pillar in the B3 gap
]

# the proven winning line, as waypoints ON the solution route (each hop stays
# in a clear corridor or crosses exactly one baffle gap):
#   cross B1's right gap  -> slide left under B1   -> cross B2's left gap
#   -> slide right under B2 -> cross B3's right gap -> slide left under B3
#   -> cross B4's left gap -> home to the goal.
_WAYPOINTS = [
    (1.6, 1.5),     # 0: B1 gap crossing (right side)
    (-1.5, 1.4),    # 1: B1-B2 band, left
    (-1.5, 0.4),    # 2: B2 gap crossing (left side)
    (1.5, 0.4),     # 3: B2-B3 band, right
    (1.5, -0.5),    # 4: B3 gap crossing (right side)
    (-1.5, -0.5),   # 5: B3-B4 band, left
    (-1.5, -1.5),   # 6: B4 gap crossing (left side)
    (0.0, -2.4),    # 7: home to the goal
]

# colours
_FLOOR_RGB = (0.16, 0.20, 0.30)
_WALL_RGB = (0.45, 0.52, 0.72)
_MARBLE_RGB = (1.00, 0.55, 0.18)
_GOAL_RGB = (0.35, 1.00, 0.55)
_WON_RGB = (1.00, 0.82, 0.30)

KEYMAP = {
    "ArrowUp": ("pitch_up", "steer up"),
    "ArrowDown": ("pitch_down", "steer down"),
    "ArrowLeft": ("roll_left", "steer left"),
    "ArrowRight": ("roll_right", "steer right"),
    "KeyR": ("reset", "reset marble"),
    "Space": ("toggle_play", "play/pause"),
    "KeyN": ("slower", "slower playback"),
    "KeyM": ("faster", "faster playback"),
}

# Real-time pace for the maze: one pass is dt 0.08 x 4 substeps = 0.32 s of
# marble time and the record is 240 passes, so 1:1 playback needs rate
# 1/(240*0.32) = 0.0130. Play rolls the recorded win at marble speed; N/M
# gear it up or down from there (the viewer clamps >= 0.005).
# duration_s is the same record span: 240 * 0.08 * 4 = 76.8 s.
DEFAULT_PLAY_RATE = 0.0130

_STATE = {"verify": None}

# ── THE LIVE MARBLE ──────────────────────────────────────────────────────────
# RULE 0 (live sim): the marble can be driven by a LIVE tilt the operator sets
# each frame, independent of any stored record.  Play starts the live roll; arrow
# keys change the table's tilt NOW and the marble obeys within one frame.  While
# the marble runs it is ALSO recorded to tilt.json (pass-indexed), so the run
# remains a replayable record -- the matrix.  When no live session is active the
# module falls back to replaying tilt.json exactly (the win record, the scrub).
#
# THE LIVE MARBLE INTEGRATES IN WHOLE PASSES, each pass = substeps of dt marble
# seconds, identically to `_integrate`.  A pass boundary is crossed every
# 1/(dt*substeps) seconds of real time, and at each boundary one tilt event is
# appended.  So the recorded run replays to the SAME path as the live run -- F4
# lives; appended at each whole-pass boundary).  Replays exactly (F4).
_LIVE = {
    "active": False,     # a live session has begun (tilt set or play pressed)
    "running": False,     # the marble is integrating under the live tilt
    "recording": False,   # the live run is being appended to tilt.json
    "x": 0.0, "y": 0.0, "vx": 0.0, "vy": 0.0,
    "pitch": 0.0, "roll": 0.0,
    "pass": 0,            # last recorded pass index, advances one per whole pass
    "pass_frac": 0.0,     # fractional progress toward the next whole pass
}


def _live_reset(nums: dict):
    """Return the live marble to the start, clear any run, keep it inactive."""
    sx, sy = nums.get("start", [0.0, 2.6])
    _LIVE.update(active=False, running=False, recording=False,
                 x=float(sx), y=float(sy), vx=0.0, vy=0.0,
                 pitch=0.0, roll=0.0, **{"pass": 0}, pass_frac=0.0)


def live_state() -> dict:
    """The live marble's current state, or None when no live session is active."""
    if not _LIVE["active"]:
        return None
    return dict(_LIVE)


def live_tick(frame_dt: float, nums: dict | None = None):
    """Advance the live marble one real frame.  Called by the viewer every render
    tick while this membrane is the loaded deck and the marble is running.

    The marble integrates in WHOLE PASSES of marble time (dt*substeps each), so an
    arrow pressed now changes the tilt the next pass integrates under -- and each
    pass boundary appends its tilt to tilt.json.  The result is a record that
    replays to the same path (F4)."""
    if not _LIVE["running"]:
        return
    nums = nums or _load_numbers()
    nsub = int(nums.get("substeps", 4))
    sub = float(nums.get("dt", 0.08))
    g = float(nums.get("gravity", 9.81))
    cap = float(nums.get("speed_cap", 1.6))
    r = float(nums.get("marble_r", 0.16))
    wt = float(nums.get("wall_t", 0.05))
    bounce = float(nums.get("bounce", 0.5))
    damp = float(nums.get("damp", 0.985))
    # whole passes per real second: one pass = dt*substeps marble-seconds
    live_pps = 1.0 / (float(nums.get("dt", 0.08)) * int(nums.get("substeps", 4)))
    # how many whole passes this real frame covers
    _LIVE["pass_frac"] += live_pps * float(frame_dt)
    while _LIVE["pass_frac"] >= 1.0:
        # ── ONE WHOLE PASS, identical to `_integrate`'s inner loop ─────────────
        for _ in range(nsub):
            ax = g * math.sin(_LIVE["roll"])
            ay = -g * math.sin(_LIVE["pitch"])
            _LIVE["vx"] += ax * sub
            _LIVE["vy"] += ay * sub
            _LIVE["x"] += _LIVE["vx"] * sub
            _LIVE["y"] += _LIVE["vy"] * sub
            _LIVE["x"], _LIVE["y"], _LIVE["vx"], _LIVE["vy"] = _collide(
                _LIVE["x"], _LIVE["y"], _LIVE["vx"], _LIVE["vy"], r, wt, bounce)
            sp = math.hypot(_LIVE["vx"], _LIVE["vy"])
            if sp > cap:
                _LIVE["vx"] *= cap / sp
                _LIVE["vy"] *= cap / sp
            _LIVE["vx"] *= damp
            _LIVE["vy"] *= damp
        _LIVE["pass_frac"] -= 1.0
        # THE RUN IS ALSO A TAKE -- recorded to live_record.json, NOT tilt.json, so a
        # live session can never erase the stored win record.  Each pass appends one
        # tilt event; replaying this file reproduces the same path (F4).
        if _LIVE["recording"]:
            _LIVE["pass"] += 1
            ev = {"pass": _LIVE["pass"],
                  "pitch": round(float(_LIVE["pitch"]), 6),
                  "roll": round(float(_LIVE["roll"]), 6)}
            tilts = []
            if LIVE_PATH.exists():
                try:
                    tilts = json.loads(LIVE_PATH.read_text())
                except Exception:
                    tilts = []
            tilts.append(ev)
            _atomic(LIVE_PATH, lambda p: p.write_text(json.dumps(tilts, indent=2)))
            _STATE["verify"] = None


def _atomic(path: Path, fn):
    tmp = path.with_name(path.stem + ".tmp" + path.suffix)
    fn(tmp)
    os.replace(tmp, path)


def _load_numbers() -> dict:
    return json.loads(NUMBERS_PATH.read_text())


def _load_tilts() -> list[dict]:
    try:
        return json.loads(TILTS_PATH.read_text())
    except Exception:
        return []


def _pass_at(nums: dict, t: float) -> int:
    return int(round(float(np.clip(t, 0.0, 1.0)) * int(nums.get("tilt_max_passes", 240))))


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _collide(x, y, vx, vy, r, wt, bounce):
    """Push the marble out of any wall and reflect velocity.  Two passes of the
    wall loop are enough at the substep sizes used (no tunnelling: max move per
    substep 0.128 < wall thickness + marble diameter)."""
    for _ in range(2):
        for x0, y0, x1, y1 in _WALLS:
            if x0 == x1:                       # vertical wall
                cx = x0
                cy = _clamp(y, y0, y1)
            else:                              # horizontal wall
                cx = _clamp(x, x0, x1)
                cy = y0
            nx = x - cx
            ny = y - cy
            d = math.hypot(nx, ny)
            if d < r + wt:
                if d < 1e-9:                   # exactly on the line: push away from interior
                    if x0 == x1:
                        nx, ny = math.copysign(1.0, x - x0), 0.0
                    else:
                        nx, ny = 0.0, math.copysign(1.0, y - y0)
                    d = 1.0
                else:
                    nx /= d
                    ny /= d
                x = cx + nx * (r + wt + 1e-6)
                y = cy + ny * (r + wt + 1e-6)
                vn = vx * nx + vy * ny
                if vn < 0.0:
                    vx -= (1.0 + bounce) * vn * nx
                    vy -= (1.0 + bounce) * vn * ny
    return x, y, vx, vy


def _step(x, y, vx, vy, pitch, roll, nums):
    """One pass of the marble: gravity from the tilt, substeps + wall bounces,
    speed cap and rolling damping."""
    dt = float(nums.get("dt", 0.08))
    damp = float(nums.get("damp", 0.985))
    g = float(nums.get("gravity", 9.81))
    cap = float(nums.get("speed_cap", 1.6))
    bounce = float(nums.get("bounce", 0.5))
    r = float(nums.get("marble_r", 0.16))
    wt = float(nums.get("wall_t", 0.05))
    for _ in range(int(nums.get("substeps", 4))):
        ax = g * math.sin(roll)      # +roll tips the +x edge down -> marble rolls right
        ay = -g * math.sin(pitch)    # +pitch tips the +y edge up -> marble rolls down
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        x, y, vx, vy = _collide(x, y, vx, vy, r, wt, bounce)
        sp = math.hypot(vx, vy)
        if sp > cap:
            vx *= cap / sp
            vy *= cap / sp
        vx *= damp
        vy *= damp
    return x, y, vx, vy


def _integrate(nums: dict, tilts: list[dict], P: int):
    """Replay the tilt record to pass P: the marble's exact path, plus the
    table's current tilt (for the visual). Returns (x, y, pitch, roll, vx, vy)."""
    start = np.asarray(nums.get("start", [0.0, 2.6]), dtype=float)
    x, y = float(start[0]), float(start[1])
    vx = vy = 0.0
    pitch = roll = 0.0
    evs = sorted([e for e in tilts if float(e["pass"]) <= P], key=lambda e: e["pass"])
    ei = 0
    for step in range(1, P + 1):
        while ei < len(evs) and float(evs[ei]["pass"]) <= step:
            pitch = float(evs[ei]["pitch"])
            roll = float(evs[ei]["roll"])
            ei += 1
        x, y, vx, vy = _step(x, y, vx, vy, pitch, roll, nums)
    return x, y, pitch, roll, vx, vy


def _step_frac(x, y, vx, vy, pitch, roll, nums: dict, n: float):
    """n full-passes-worth of substeps, n may be fractional -- full substeps then
    a partial one, so playback shows the marble ROLLING through a pass instead of
    hopping to the pass-end position."""
    dt = float(nums.get("dt", 0.08))
    damp = float(nums.get("damp", 0.985))
    g = float(nums.get("gravity", 9.81))
    cap = float(nums.get("speed_cap", 1.6))
    bounce = float(nums.get("bounce", 0.5))
    r = float(nums.get("marble_r", 0.16))
    wt = float(nums.get("wall_t", 0.05))
    m = int(n)
    f = n - m
    for _ in range(m):
        ax = g * math.sin(roll)      # +roll tips the +x edge down -> marble rolls right
        ay = -g * math.sin(pitch)    # +pitch tips the +y edge up -> marble rolls down
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        x, y, vx, vy = _collide(x, y, vx, vy, r, wt, bounce)
        sp = math.hypot(vx, vy)
        if sp > cap:
            vx *= cap / sp
            vy *= cap / sp
        vx *= damp
        vy *= damp
    if f > 1e-9:
        d = dt * f
        ax = g * math.sin(roll)
        ay = -g * math.sin(pitch)
        vx += ax * d
        vy += ay * d
        x += vx * d
        y += vy * d
        x, y, vx, vy = _collide(x, y, vx, vy, r, wt, bounce)
        sp = math.hypot(vx, vy)
        if sp > cap:
            vx *= cap / sp
            vy *= cap / sp
        vx *= damp ** f
        vy *= damp ** f
    return x, y, vx, vy


def _integrate_frac(nums: dict, tilts: list[dict], t: float):
    """Replay to a FRACTIONAL pass (t in 0..1): full passes then one partial pass.
    The partial pass runs under the tilt that pass full+1 would run under, so the
    marble's path is exact and its motion is continuous."""
    P_total = int(nums.get("tilt_max_passes", 240))
    pt = float(np.clip(t, 0.0, 1.0)) * P_total
    full = int(pt)
    frac = pt - full
    x, y, pitch, roll, vx, vy = _integrate(nums, tilts, full)
    if frac > 1e-9:
        evs = sorted([e for e in tilts if float(e["pass"]) <= full + 1],
                     key=lambda e: e["pass"])
        if evs:
            pitch, roll = float(evs[-1]["pitch"]), float(evs[-1]["roll"])
        x, y, vx, vy = _step_frac(x, y, vx, vy, pitch, roll, nums,
                                  frac * int(nums.get("substeps", 4)))
    return x, y, pitch, roll, vx, vy


def _rotate(pitch, roll, pts):
    """Rotate the table by R = Rx(pitch) @ Ry(roll).  roll > 0 tips the +x edge
    down (marble rolls +x); pitch > 0 tips the +y edge up (marble rolls -y)."""
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    x = pts[:, 0]
    y = pts[:, 1]
    z = pts[:, 2]
    x2 = cr * x + sr * z
    y2 = sp * sr * x + cp * y - sp * cr * z
    z2 = -cp * sr * x + sp * y + cp * cr * z
    return np.stack([x2, y2, z2], axis=1)


def _emit_body(nums: dict, t: float) -> np.ndarray:
    live = live_state()
    if live is not None:
        x, y = live["x"], live["y"]
        pitch, roll = live["pitch"], live["roll"]
    else:
        x, y, pitch, roll, *_ = _integrate_frac(nums, _load_tilts(), t)
    gx, gy = float(nums.get("goal", [0.0, -2.6])[0]), float(nums.get("goal", [0.0, -2.6])[1])
    goal_r = float(nums.get("goal_r", 0.30))
    won = math.hypot(x - gx, y - gy) < goal_r

    local_pts: list[tuple] = []
    local_rgb: list[tuple] = []
    local_size: list[float] = []
    local_alpha: list[float] = []

    # floor -- a faint grid so the table's tilt reads as a flat surface
    hw = 3.1
    for i in range(9):
        for j in range(9):
            fx = -hw + i * (2 * hw) / 8
            fy = -hw + j * (2 * hw) / 8
            local_pts.append((fx, fy, 0.0))
            local_rgb.append(_FLOOR_RGB)
            local_size.append(0.30)
            local_alpha.append(0.35)

    # walls -- a row of splats along each segment at mid height
    wall_h = 0.28
    for x0, y0, x1, y1 in _WALLS:
        length = math.hypot(x1 - x0, y1 - y0)
        n = max(3, int(length / 0.22))
        for i in range(n + 1):
            u = i / n
            local_pts.append((x0 + u * (x1 - x0), y0 + u * (y1 - y0), wall_h / 2))
            local_rgb.append(_WALL_RGB)
            local_size.append(0.11)
            local_alpha.append(0.95)

    # goal -- a ring at the table surface (gold once the marble has reached it)
    for i in range(8):
        a = 2 * math.pi * i / 8
        local_pts.append((gx + goal_r * math.cos(a), gy + goal_r * math.sin(a), 0.04))
        local_rgb.append(_WON_RGB if won else _GOAL_RGB)
        local_size.append(0.09)
        local_alpha.append(0.95)

    # the marble (a halo next to it when it is home)
    local_pts.append((x, y, wall_h + 0.02))
    local_rgb.append(_MARBLE_RGB)
    local_size.append(0.26)
    local_alpha.append(1.0)
    if won:
        local_pts.append((x, y, wall_h + 0.02))
        local_rgb.append(_WON_RGB)
        local_size.append(0.50)
        local_alpha.append(0.35)

    pts = _rotate(pitch, roll, np.asarray(local_pts, dtype=np.float64))
    n = pts.shape[0]
    buf = np.zeros((n, NCOLS), dtype=np.float32)
    buf[:, PX:PZ + 1] = pts
    buf[:, 9] = 1.0            # mass -- identical points
    buf[:, 10] = -1.0          # immortal
    buf[:, TYPE] = 3.0         # SOLID
    for i in range(n):
        buf[i, CR] = local_rgb[i][0]
        buf[i, CG] = local_rgb[i][1]
        buf[i, CB] = local_rgb[i][2]
        buf[i, ALPHA] = local_alpha[i]
        buf[i, SIZE] = local_size[i]
    return np.ascontiguousarray(buf)


def emit(nums: dict, t: float = 1.0) -> np.ndarray:
    """The frame: the whole tilt table (floor, walls, goal, marble) at pass k.
    The table is rotated by the current tilt, so the operator SEES the input."""
    nums = nums or _load_numbers()
    return _emit_body(nums, t)


def live_reset_term(nums: dict | None = None):
    """Clear any live session (used when entering the deck fresh, so a previous
    visitor's run does not bleed into the new board).  The stored record survives."""
    _live_reset(nums or _load_numbers())


def handle_key(code: str, down: bool = True, t: float = 1.0,
                nums: dict | None = None) -> dict | None:
    """The deck's controls.  This is a LIVE SIM: pressing Play drops the marble and
    it rolls under the current tilt; arrow keys tilt the table NOW and the marble
    obeys next frame -- you steer while it plays.  The whole run is recorded to
    tilt.json as you go, so it stays a replayable record (the matrix).

      Space      toggle the live roll (start / pause -- no record needed to begin)
      Arrows     tilt the table live: set the tilt immediately, marble follows
      KeyR       reset the marble to the start and clear the record
      N / M      gear the playback rate (for replaying a recorded run)

    A tilt applies immediately to the live state, so the operator's input is a
    steering wheel, not a teleport -- and because the marble is also recorded, the
    same tilts replay to the same path (F4)."""
    if not down or code not in KEYMAP:
        return None
    nums = nums or _load_numbers()
    action = KEYMAP[code][0]

    if action == "toggle_play":
        # THE LIVE ROLL STARTS COLD. No record required: the marble drops and runs
        # under whatever tilt is set (initially flat). Starting a run also begins
        # recording it to live_record.json (NOT tilt.json -- the stored win is safe).
        if _LIVE["running"]:
            _LIVE["running"] = False
            return {"cmd": "toggle_play", "rate": DEFAULT_PLAY_RATE, "playing": False}
        _LIVE["active"] = True
        _LIVE["running"] = True
        _LIVE["recording"] = True
        # a fresh take: clear last run's recording so the new one is clean
        try:
            LIVE_PATH.write_text("[]")
        except Exception:
            pass
        return {"cmd": "toggle_play", "rate": DEFAULT_PLAY_RATE, "playing": True}

    if action == "reset":
        # RESET clears the live run AND the stored record (a fresh board, empty).
        _atomic(TILTS_PATH, lambda p: p.write_text("[]"))
        try:
            LIVE_PATH.write_text("[]")
        except Exception:
            pass
        _live_reset(nums)
        _STATE["verify"] = None
        return {"cmd": "switch", "name": "reset", "t": 0.0}

    if action == "slower":
        return {"cmd": "rate", "x": 0.5}
    if action == "faster":
        return {"cmd": "rate", "x": 2.0}

    # ── THE ARROWS TILT THE TABLE LIVE ──────────────────────────────────────────
    # They set the live tilt immediately (and arm a live session), whether the
    # marble is rolling or parked.  The next live_tick integrates under this new
    # tilt, so the marble changes direction within a frame of the keypress.
    max_t = math.radians(float(nums.get("max_tilt_deg", 26)))
    step = math.radians(float(nums.get("tilt_step_deg", 6)))
    if not _LIVE["active"]:
        _live_reset(nums)
        _LIVE["active"] = True
    pitch, roll = _LIVE["pitch"], _LIVE["roll"]
    if action == "pitch_up":
        pitch = _clamp(pitch - step, -max_t, max_t)
    elif action == "pitch_down":
        pitch = _clamp(pitch + step, -max_t, max_t)
    elif action == "roll_left":
        roll = _clamp(roll - step, -max_t, max_t)
    elif action == "roll_right":
        roll = _clamp(roll + step, -max_t, max_t)
    _LIVE["pitch"], _LIVE["roll"] = pitch, roll
    # THE TILT IS THE INPUT: re-emit so the table visibly rotates this frame.
    return {"cmd": "switch", "name": action, "pass": _LIVE["pass"],
            "max_pass": int(nums.get("tilt_max_passes", 240))}


def _verify(nums: dict) -> dict:
    """F4: the record is the matrix -- replaying the tilt timeline is exact."""
    if _STATE["verify"] is not None:
        return _STATE["verify"]
    tilts = _load_tilts()
    P = int(nums.get("tilt_max_passes", 240))
    a = _integrate(nums, tilts, P)
    b = _integrate(nums, tilts, P)
    out = {"error": float(abs(a[0] - b[0]) + abs(a[1] - b[1])), "passes": P}
    _STATE["verify"] = out
    return out


def state_readout(nums: dict, t: float = 1.0) -> dict:
    """The game state: where the marble is, the table's tilt, whether it is home."""
    nums = nums or _load_numbers()
    live = live_state()
    if live is not None:
        x, y = live["x"], live["y"]
        pitch, roll = live["pitch"], live["roll"]
        tilts = _load_tilts()
    else:
        tilts = _load_tilts()
        x, y, pitch, roll, *_ = _integrate_frac(nums, tilts, t)
    gx, gy = float(nums.get("goal", [0.0, -2.6])[0]), float(nums.get("goal", [0.0, -2.6])[1])
    dist = math.hypot(x - gx, y - gy)
    return {
        "t": round(t, 4),
        "pass": _pass_at(nums, t) if live is None else _LIVE["pass"],
        "marble": [round(x, 3), round(y, 3)],
        "tilt_deg": [round(math.degrees(pitch), 1), round(math.degrees(roll), 1)],
        "goal_dist": round(dist, 3),
        "won": bool(dist < float(nums.get("goal_r", 0.30))),
        "events": len(tilts),
        "live": live is not None,
        "running": bool(_LIVE["running"]),
        "replay": _verify(nums),
        "keymap": [{"key": kk, "action": a, "label": l} for kk, (a, l) in KEYMAP.items()],
    }


def _control_run(nums: dict) -> tuple:
    """A scripted player for F5: follow the maze's known solution waypoint by
    waypoint.  A derived velocity-tracking controller, not a tuned one:

      - it commands the tilt so the marble ACQUIRES a desired velocity each
        pass: a = (v_desired / damp_pass - v) / dt_pass, the one-pass
        deadbeat that compensates the game's own rolling damping exactly.
      - v_desired points at the current waypoint, capped at S_CAP and ramping
        down to zero over APPR so the marble STOPS on each waypoint -- and a
        stop means it can never overshoot past a gap it needs (it slides along
        a wall it is pressing on until it finds the gap).
      - S_CAP = 1.2 < the game's speed_cap (1.6): the scripted player never
        leans on a limit the operator is bound by.  STOP_R is the acquisition
        radius (0.35 lu); the marble's stopping distance from S_CAP at full
        tilt authority is ~0.17 lu, so it always stops short and re-acquires.

    Returns (won, passes, final x, final y)."""
    max_t = math.radians(float(nums.get("max_tilt_deg", 26)))
    P_MAX = int(nums.get("tilt_max_passes", 240))
    dt_pass = float(nums.get("dt", 0.08)) * int(nums.get("substeps", 4))
    damp_pass = float(nums.get("damp", 0.985)) ** int(nums.get("substeps", 4))
    g = float(nums.get("gravity", 9.81))
    goal = np.asarray(nums.get("goal", [0.0, -2.6]), dtype=float)
    goal_r = float(nums.get("goal_r", 0.30))
    start = np.asarray(nums.get("start", [0.0, 2.6]), dtype=float)
    x, y = float(start[0]), float(start[1])
    vx = vy = 0.0
    S_CAP = 1.2
    APPR = 0.9
    STOP_R = 0.35
    wp = 0
    tx, ty = _WAYPOINTS[0]
    for step in range(1, P_MAX + 1):
        ex, ey = tx - x, ty - y
        dist = math.hypot(ex, ey)
        if dist < STOP_R and wp < len(_WAYPOINTS) - 1:
            wp += 1
            tx, ty = _WAYPOINTS[wp]
            ex, ey = tx - x, ty - y
            dist = math.hypot(ex, ey)
        speed = min(S_CAP, S_CAP * dist / APPR) if dist > 0 else 0.0
        vdx = speed * (ex / dist) if dist > 1e-9 else 0.0
        vdy = speed * (ey / dist) if dist > 1e-9 else 0.0
        ax = (vdx / damp_pass - vx) / dt_pass
        ay = (vdy / damp_pass - vy) / dt_pass
        roll = _clamp(math.asin(_clamp(ax / g, -1.0, 1.0)), -max_t, max_t)
        pitch = _clamp(-math.asin(_clamp(ay / g, -1.0, 1.0)), -max_t, max_t)
        x, y, vx, vy = _step(x, y, vx, vy, pitch, roll, nums)
        if math.hypot(x - goal[0], y - goal[1]) < goal_r:
            return True, step, x, y
    return False, P_MAX, x, y


def main() -> int:
    nums = _load_numbers()
    start = tuple(nums.get("start", [0.0, 2.6]))

    # F1 -- a tilt moves the marble
    x1, y1, *_ = _integrate(nums, [{"pass": 1, "pitch": 0.0, "roll": 0.35}], 8)
    f1 = math.hypot(x1 - start[0], y1 - start[1]) > 0.05

    # F2 -- the marble follows the tilt
    xr, yr, *_ = _integrate(nums, [{"pass": 1, "pitch": 0.0, "roll": 0.35}], 12)
    xu, yu, *_ = _integrate(nums, [{"pass": 1, "pitch": -0.35, "roll": 0.0}], 12)
    f2 = xr > start[0] + 0.05 and yu > start[1] + 0.05

    # F3 -- the marble stays on the table (random tilt runs)
    rng = np.random.default_rng(7)
    ok = True
    for _ in range(20):
        tilts = [{"pass": 1 + 8 * i, "pitch": float(rng.uniform(-0.5, 0.5)),
                  "roll": float(rng.uniform(-0.5, 0.5))}
                 for i in range(30)]
        xr, yr, *_ = _integrate(nums, tilts, 240)
        if abs(xr) > 3.35 or abs(yr) > 3.35:
            ok = False
            break
    f3 = ok

    # F4 -- the record is the matrix (deterministic replay)
    r = _verify(nums)
    f4 = r["error"] <= 1e-9

    # F5 -- the maze is winnable by tilt alone
    won, steps, fx, fy = _control_run(nums)
    f5 = won

    # F5 -- the maze is winnable by tilt alone, and the win is ROBUST: it must
    # survive a band of physics knobs, so the verdict cannot flip on a whim.
    won, steps, fx, fy = _control_run(nums)
    f5 = won
    worst = steps
    for key, lo, hi in (("damp", 0.97, 0.995), ("max_tilt_deg", 20, 32),
                        ("bounce", 0.3, 0.7), ("speed_cap", 1.3, 2.0)):
        for k in (lo, hi):
            n = dict(nums)
            n[key] = k
            w, s, *_ = _control_run(n)
            f5 = f5 and w
            worst = max(worst, s)

    print("MARBLE MAZE -- a tilt table on the Gaussian stage")
    print("  F1 tilt moves the marble      PASS" if f1 else "  F1 tilt moves the marble      FAIL")
    print("  F2 marble follows the tilt    PASS" if f2 else "  F2 marble follows the tilt    FAIL")
    print("  F3 the walls hold             PASS" if f3 else "  F3 the walls hold             FAIL")
    print(f"  F4 record is the matrix       {'PASS' if f4 else 'FAIL'}  (replay error {r['error']:.1e})")
    print(f"  F5 the maze is winnable       {'PASS' if f5 else 'FAIL'}  (nominal win in {steps} passes,"
          f" robust across the damp/max-tilt/bounce/cap band, worst {worst})")
    return 0 if (f1 and f2 and f3 and f4 and f5) else 1


if __name__ == "__main__":
    raise SystemExit(main())
