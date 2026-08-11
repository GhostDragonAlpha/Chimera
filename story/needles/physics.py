"""needles -- one million needles, each on its own groove, switched by the deck.

A membrane is a SEPARATE MATRIX applied to the main Gaussian space.  This one's
matrix is tiny: 1M groove specs (40 MB) + a switch timeline -- not 1M x T
recorded frames (432 MB).  Positions are a closed-form law of the pass clock
(ChimeraEngine/needle_law.py), so replay is free: the record IS the matrix.

A SWITCH is an input event from the deck (KeyQ) that reroutes a block of
needles onto another rail -- and the law CONNECTS the rails: the target rail's
phase is solved so it passes through each needle's position at the throw
instant.  A switch is a railroad join, not a teleport.

RULE 0 -- stated before the deck is opened:
    STATEMENT : 1,000,000 needles, each born on its own closed-form rail, can
                share ONE Gaussian frame inside the wallet; an operator key
                THROWS a switch that reroutes a block onto a new rail through
                the needles' current positions -- no teleport, no lookup table.
    PREDICTION: (a) every needle moves each pass, (b) the throw is a join
                (position continuity), (c) the frame stays under the wallet at
                the viewer's 1M-splat limit, (d) reloading the matrix reproduces
                the run.
    FALSIFIER : a needle stops moving; a throw teleports a needle
                (discontinuity > 1e-2); the frame busts the wallet; or the
                reloaded matrix disagrees with the recorded run (> 1e-3).
                Any one of these fires the verdict.

The deck: KeyQ throws the next mood onto the next block (the operator joins the
matrix), KeyR returns to the recorded seed timeline.  Live throws are written
back to switches.json -- the deck is part of the record.

The same code the standalone experiment used, run live: `million_needles.py`
wrote `matrix_out/needles`; this membrane owns a copy in its own folder and
lives in the viewer's scene list like any other term.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]                       # story/needles -> repo root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ChimeraEngine import needle_law  # noqa: E402
from ChimeraEngine.needle_law import (  # noqa: E402
    T_ORBIT, T_STREAM, T_PLANE, T_SHELL, positions, apply_switch, make_grooves,
)

NUMBERS_PATH = _HERE / "numbers.json"
SWITCHES_PATH = _HERE / "switches.json"
POS_SAMPLE_PATH = _HERE / "pos_sample.npz"

# ── buffer layout (ParticleEngine.core.COL) ──────────────────────────
NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20

# ── the four rails the operator can throw onto (the run's mood table) ──
MOODS = [
    ("stream", "angry-mood", [1.0, 6.0, 0.02, 0.0, 0.3, 0.0, 0.03, 0.0, 0.0, 0.0]),
    ("orbit", "happy-mood", [0.0, 8.0, 0.03, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ("plane", "disc", [2.0, 7.0, 0.025, 0.0, 0.8, 0.0, 0.04, 0.0, 0.0, 0.0]),
    ("shell", "shell", [3.0, 9.0, 0.02, 1.3, 0.6, 0.0, 0.01, 0.0, 0.0, 0.0]),
]
KEYMAP = {
    "Space": ("toggle_play", "play/pause"),
    "KeyW": ("t_fwd", "next pass"),
    "KeyS": ("t_back", "prev pass"),
    "KeyQ": ("switch", "throw next mood"),
    "KeyR": ("reset", "back to the seed timeline"),
}

# how far the recorded timeline reaches (its last block ends), so live throws
# start where the record left off and walk forward
_START_FRONTIER = 700_000

# the working matrix state -- rebuilt lazily and only when the frontier moves
_STATE = {"grooves": None, "frontier": None, "verify": None}


def _load_numbers() -> dict:
    return json.loads(NUMBERS_PATH.read_text())


def _load_switches() -> list[dict]:
    try:
        return json.loads(SWITCHES_PATH.read_text())
    except Exception:
        return []


def _seed_grooves(nums: dict) -> np.ndarray:
    n = int(nums.get("n_needles", 1_000_000))
    seed = int(nums.get("seed", 7))
    return make_grooves(n, seed=seed)


def _clock(nums: dict, t: float) -> float:
    return float(nums.get("k_start", 2.0)) + float(np.clip(t, 0.0, 1.0)) * (
        float(nums.get("k_end", 35.0)) - float(nums.get("k_start", 2.0)))


def _grooves_at(nums: dict, k: float) -> np.ndarray:
    """The matrix replayed to pass k: seed grooves + every switch thrown by then.

    The working copy is cached and only rebuilt when the number of applied
    events changes, so scrubbing within a pass costs one `positions()` call.
    """
    evs = [e for e in sorted(_load_switches(), key=lambda e: e["pass"])
           if float(e["pass"]) <= k]
    frontier = len(evs)
    if _STATE["frontier"] != frontier or _STATE["grooves"] is None:
        g = _seed_grooves(nums)
        for e in evs:
            apply_switch(g, e, float(e["pass"]))
        _STATE["grooves"] = g
        _STATE["frontier"] = frontier
    return _STATE["grooves"]


def emit(nums: dict, t: float = 1.0) -> np.ndarray:
    """The frame: all 1M needles at pass k as a (N, 28) splat buffer.

    Positions come from the closed-form law at the current clock -- the physics
    is never pre-recorded.  Each needle's colour is its rail family's.
    """
    nums = nums or _load_numbers()
    k = _clock(nums, t)
    g = _grooves_at(nums, k)
    pos = positions(g, k)
    n = pos.shape[0]

    buf = np.zeros((n, NCOLS), dtype=np.float32)
    buf[:, PX:PZ + 1] = pos
    buf[:, 9] = 1.0            # mass -- identical points
    buf[:, 10] = -1.0          # immortal (the pipeline does not age them)
    buf[:, TYPE] = 3.0         # SOLID
    buf[:, ALPHA] = 0.9
    buf[:, SIZE] = float(nums.get("needle_size", 0.045))
    for t_, rgb in needle_law.COLOR.items():
        m = g[:, 0] == t_
        buf[m, CR] = rgb[0]
        buf[m, CG] = rgb[1]
        buf[m, CB] = rgb[2]
    return np.ascontiguousarray(buf)


def _verify(nums: dict) -> dict:
    """The membrane's own F4: reload the matrix, re-walk the clock, compare.

    The record IS the matrix -- a reload must reproduce the recorded run.
    Computed once per module load and reported by the state readout.
    """
    if _STATE["verify"] is not None:
        return _STATE["verify"]
    out = {"error": None, "sample": None}
    try:
        g = _seed_grooves(nums)
        for e in sorted(_load_switches(), key=lambda e: e["pass"]):
            apply_switch(g, e, float(e["pass"]))
        k_end = float(nums.get("k_end", 35.0))
        sample_idx = np.arange(0, g.shape[0], 1000)
        pos = positions(g, k_end)[sample_idx]
        ref = np.load(POS_SAMPLE_PATH)["pos"][-1]
        n = min(len(sample_idx), len(ref))
        err = float(np.abs(pos[:n] - ref[:n]).max())
        out = {"error": err, "sample": n}
    except Exception as e:
        out = {"error": str(e), "sample": 0}
    _STATE["verify"] = out
    return out


def handle_key(code: str, down: bool = True, t: float = 1.0,
               nums: dict | None = None) -> dict | None:
    """The deck's controls: a keycode + the current t -> a viewer command.

    KeyQ THROWS a switch: a block of needles leaves its rail and joins the next
    mood's rail through their current positions -- the operator is an input.
    The throw is written into switches.json, so the deck is part of the record.
    KeyR returns to the recorded seed timeline (live throws stripped).
    """
    if not down or code not in KEYMAP:
        return None
    nums = nums or _load_numbers()
    action = KEYMAP[code][0]
    if action == "toggle_play":
        return {"cmd": "toggle_play"}
    if action == "t_fwd":
        return {"cmd": "time", "t": float(np.clip(t + 1.0 / max(1, int(nums.get("frames", 34))), 0.0, 1.0))}
    if action == "t_back":
        return {"cmd": "time", "t": float(np.clip(t - 1.0 / max(1, int(nums.get("frames", 34))), 0.0, 1.0))}
    if action == "reset":
        live_only = [e for e in _load_switches() if not e.get("live")]
        SWITCHES_PATH.write_text(json.dumps(live_only, indent=2))
        _STATE["grooves"] = None
        _STATE["frontier"] = None
        return {"cmd": "switch", "name": "reset"}
    if action == "switch":
        return _throw_live(nums, t)
    return None


def _throw_live(nums: dict, t: float) -> dict:
    """Throw the next mood onto the next block, at the operator's current pass."""
    sw = _load_switches()
    live = [e for e in sw if e.get("live")]
    n_all = int(nums.get("n_needles", 1_000_000))
    n_throw = int(nums.get("live_throw_n", 150_000))
    kind, name, target = MOODS[len(live) % len(MOODS)]
    lo = (_START_FRONTIER + sum(int(e["n"]) for e in live)) % max(1, n_all - n_throw)
    k = _clock(nums, t)
    ev = {"pass": float(k), "lo": int(lo), "n": n_throw,
          "target": target, "name": name, "live": True}
    sw.append(ev)
    SWITCHES_PATH.write_text(json.dumps(sw, indent=2))
    _STATE["grooves"] = None
    _STATE["frontier"] = None
    return {"cmd": "switch", "name": name, "pass": round(float(k), 2), "n": n_throw}


def state_readout(nums: dict, t: float = 1.0) -> dict:
    """The matrix as a state machine: how many needles ride each rail now."""
    nums = nums or _load_numbers()
    k = _clock(nums, t)
    sw = _load_switches()
    live = [e for e in sw if e.get("live")]
    g = _grooves_at(nums, k)
    counts = needle_law.groove_counts(g)
    names = {e["name"]: e["pass"] for e in sw}
    return {
        "t": round(t, 4),
        "pass": round(k, 2),
        "n_total": int(g.shape[0]),
        "switches": sum(1 for e in sw if float(e["pass"]) <= k),
        "recorded": sum(1 for e in sw if not e.get("live")),
        "live": len(live),
        "timeline": names,
        "types": {"orbit": counts[0], "stream": counts[1],
                  "plane": counts[2], "shell": counts[3]},
        "replay": _verify(nums),
        "keymap": [{"key": kk, "action": a, "label": l} for kk, (a, l) in KEYMAP.items()],
    }


if __name__ == "__main__":
    nums = _load_numbers()
    buf = emit(nums, 0.5)
    print(f"emit(t=0.5): buffer {buf.shape}  positions range "
          f"{float(buf[:, PX:PZ+1].min()):.2f}..{float(buf[:, PX:PZ+1].max()):.2f}")
    print(json.dumps(state_readout(nums, 0.5), indent=1))
