"""theLight -- the record player matrix, first record pressed.

THE MASTER ALGORITHM, stated before the record is pressed (RULE 0):

    STATEMENT : N identical points -- 32 pinned bond-shelf seed grains (the
                anvil) and 1968 free grains on a jittered shell at r_rain
                (the rain) -- integrated by the ONE folded Barnes-Hut walk
                (LightEngine.modifier via kernel.VelocityVerlet(use_modifier))
                settle into a compact membrane body around the seed.  The
                walls and bonds are NOT authored material properties: they are
                the modifier M awakening in the leaves wherever grains touch.
    PREDICTION: (a) the rain falls purely under the draw (zero initial
                velocity), (b) contact radiation lights up only at grain-grain
                contact and dissipates as the body packs, (c) the settled body
                has bound-mass fraction > 0.5, an edge-sharp packed lattice,
                and stays bounded inside the rain shell, (d) the folded walk's
                resistance is exact against the two-pass referee (rel err
                <= 1e-4) at every checkpoint.
    FALSIFIER : the body fails to form (bound frac <= 0.5), never settles
                (late cluster-count CV >= 0.20 or bound swing >= 0.15),
                disperses (final radius >= r_rain), never radiates (M never
                awakened), or the fold disagrees with the referee
                (> 1e-4).  Any one of these fires the verdict.

THE RECORD PLAYER MATRIX (the operator's design language):

    The record   -- theLight.record.npz: the trajectory sampled every
                    sample_every ticks, with the M-field colors per grain.
    The needle   -- emit(nums, t): interpolates the record at story-time t
                    (0..1) into a (N, 28) splat buffer for the Chimera GPU
                    pipeline.  Scrubbing t scrubs the physics.
    The deck     -- the HTTP viewer (ChimeraEngine/gallery.py): picks this
                    record from scene_terms(), orbits, pauses, steps.
    The DJ       -- the operator.  Changing t changes the outcome on screen;
                    that is the game.

Units: lu = light units (R_WALL = 0.05, R_BOND = 0.15, R_C = 0.30),
t in ticks, mass = 1, charge = 1 for every point -- no authored properties.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]                       # repo root: story/theZero/theLight -> ../../
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from LightEngine import kernel  # noqa: E402
from LightEngine.constants import (  # noqa: E402
    G, R_WALL, R_BOND, R_C, DT,
)

RECORD_PATH = _HERE / "theLight.record.npz"
NUMBERS_PATH = _HERE / "numbers.json"

# ── the M-field palette (far / bond / wall / seed), 0-1 rgb ─────────
_C_FAR = np.array([0.36, 0.49, 0.60], np.float32)    # pure draw, M -> 1
_C_BOND = np.array([0.20, 0.84, 0.78], np.float32)   # cushion shelf, M = 0
_C_WALL = np.array([1.00, 0.30, 0.37], np.float32)   # contact, M < 0
_C_SEED = np.array([1.00, 0.72, 0.31], np.float32)   # the pinned anvil

# ── buffer layout (ParticleEngine.core.COL) ──────────────────────────
NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20


def derive(parent_nums=None, free=None):
    """Derived quantities for theLight -- computed from the force constants.

    Nothing here is a free parameter: n_total and n_seed are declared run
    sizes (as demo_seed declares N), the geometry is set so the seed sits in
    the bond shelf (R_WALL <= spacing <= R_BOND) and the rain shell gives a
    clear free-fall, and the window is the shell's own free-fall time.
    """
    n_total = 2000
    n_seed = 32
    r_seed_lu = 0.12        # seed ball radius: spacing ~0.075 in the bond shelf
    r_rain_lu = 2.2         # ~1.7x the packed-body radius -> visible fall
    t_ff_count = 2.5        # observe for 2.5 shell free-fall times
    sample_every = 50       # record groove spacing (ticks)
    # shell self-gravity free-fall: t_ff = (pi/2) sqrt(r^3 / (G M/2))
    t_ff = float((np.pi / 2.0) * np.sqrt(r_rain_lu ** 3 / (G * (n_total / 2.0))))
    t_total_ticks = int(np.ceil(t_ff_count * t_ff / DT))
    return {
        "n_total": n_total,
        "n_seed": n_seed,
        "r_seed_lu": r_seed_lu,
        "r_rain_lu": r_rain_lu,
        "t_ff_count": t_ff_count,
        "sample_every": sample_every,
        "dt": DT,
        "t_total_ticks": t_total_ticks,
        "t_total_units": round(t_total_ticks * DT, 3),
        "extent_m": 2.5,          # camera framing: extent * 2.8
        "grain_size": 0.07,       # splat radius ~ half bond spacing
        "seed": 20260806,         # the light-era family seed
        "rng_rain": 7,            # rain jitter seed (continuity with the demo)
        "_units": "lu = light units (R_WALL=0.05); t in ticks; m=q=1",
        "_derived_from": "LightEngine.constants G, R_WALL, R_BOND, R_C, DT",
    }


def derive_commit():
    """Write numbers.json from derive()."""
    d = derive()
    NUMBERS_PATH.write_text(
        json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return d


def _load_numbers() -> dict:
    if NUMBERS_PATH.exists():
        try:
            return json.loads(NUMBERS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return derive_commit()


def _fibonacci_sphere(n: int) -> np.ndarray:
    """n unit vectors spread evenly over the sphere (golden-angle spiral)."""
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - 2.0 * (i + 0.5) / n
    r = np.sqrt(np.clip(1.0 - z * z, 0.0, 1.0))
    th = np.pi * (1.0 + 5.0 ** 0.5) * i
    return np.stack([r * np.cos(th), r * np.sin(th), z], axis=1)


def scenario(nums: dict):
    """The initial state: pinned seed + rain shell, zero velocity everywhere.

    Zero velocity on purpose: the only initial condition is position.  The
    falling is done by the draw; nothing is given a nudge by hand.  The shell
    gets a small tangential blue-noise jitter so it does not collapse as one
    perfect lattice (which would pancake instead of nucleating).
    """
    n_total = int(nums["n_total"])
    n_seed = int(nums["n_seed"])
    r_seed = float(nums["r_seed_lu"])
    r_rain = float(nums["r_rain_lu"])
    rng = np.random.default_rng(int(nums["rng_rain"]))

    seed = _fibonacci_sphere(n_seed) * r_seed
    rain = _fibonacci_sphere(n_total - n_seed) * r_rain
    jit = rng.normal(0.0, 1.0, (n_total - n_seed, 3))
    jit -= (jit * rain).sum(1, keepdims=True) * (rain / (np.linalg.norm(
        rain, axis=1, keepdims=True) + 1e-12))          # into the tangent plane
    amp = 0.03 * rng.random((n_total - n_seed, 1)) ** 0.5
    rain = rain + jit * amp
    rain = rain / (np.linalg.norm(rain, axis=1, keepdims=True) + 1e-12) * r_rain

    pos = np.vstack([seed, rain]).astype(np.float32)
    vel = np.zeros_like(pos)
    pin = np.zeros(len(pos), dtype=bool)
    pin[:n_seed] = True
    return pos, vel, pin


def _mfield_colors(pos: np.ndarray, n_seed: int) -> np.ndarray:
    """Per-grain M-field state, as rgb: far / bond / wall / seed.

    State is read from the nearest-neighbor distance: d < R_WALL is the wall
    (M < 0, radiating contact), R_WALL <= d <= R_BOND is the bond shelf
    (M = 0), d > R_BOND is the far field (M -> 1, pure draw).  Wall grains
    brighten with the depth of contact so impacts read as flashes.
    """
    from scipy.spatial import cKDTree
    d, _ = cKDTree(pos).query(pos, k=2)
    dmin = d[:, 1]
    col = np.zeros((len(pos), 3), np.float32)
    far = dmin > R_BOND
    bond = (dmin >= R_WALL) & (dmin <= R_BOND)
    wall = dmin < R_WALL
    col[far] = _C_FAR
    col[bond] = _C_BOND
    depth = np.clip((R_WALL - dmin[wall]) / R_WALL, 0.0, 1.0)
    col[wall] = _C_WALL * (0.45 + 0.55 * depth[:, None])
    col[:n_seed] = _C_SEED
    return col


def _pair_r2(pos: np.ndarray, chunk: int = 512):
    """Chunked N x N squared-distance blocks (never materialise the full matrix)."""
    pos64 = pos.astype(np.float64)
    n = pos64.shape[0]
    sq = np.einsum("ij,ij->i", pos64, pos64)
    for lo in range(0, n, chunk):
        hi = min(lo + chunk, n)
        yield lo, hi, sq[lo:hi, None] + sq[None, :] - 2.0 * (pos64[lo:hi] @ pos64.T)


def _bound_frac(pos: np.ndarray, rb: float = R_BOND) -> float:
    """Fraction of points with at least one neighbour within rb."""
    n = pos.shape[0]
    if n == 0:
        return 0.0
    rb2 = rb * rb
    bound = np.zeros(n, dtype=bool)
    for lo, hi, r2 in _pair_r2(pos):
        m = r2 <= rb2
        for k in range(hi - lo):
            m[k, lo + k] = False
        bound[lo:hi] = m.any(axis=1)
    return float(bound.sum()) / n


def _system_radius(pos: np.ndarray) -> float:
    c = pos.mean(axis=0)
    return float(np.max(np.linalg.norm(pos - c, axis=1)))


def _cluster_info(pos: np.ndarray, rc: float = R_C) -> tuple[int, int]:
    """Connected components under the resistance cutoff: (count, largest)."""
    n = pos.shape[0]
    if n == 0:
        return 0, 0
    parent = np.arange(n, dtype=np.int64)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    rc2 = rc * rc
    for lo, hi, r2 in _pair_r2(pos):
        m = r2 <= rc2
        for k in range(hi - lo):
            m[k, lo + k] = False
        ii, jj = np.nonzero(m)
        for a, b in zip(ii + lo, jj):
            union(int(a), int(b))
    roots = np.array([find(i) for i in range(n)])
    _, counts = np.unique(roots, return_counts=True)
    return int(len(counts)), int(counts.max())


def _force_checkpoint(pos: np.ndarray, vel: np.ndarray) -> tuple[float, float]:
    """(global_rel, resist_rel) for the folded walk against the two-pass referee.

    Damping is linear in v_rad, so on the SAME state a(2v) - a(v) isolates the
    resistance exactly (the draw cancels bit-exactly); that is the load-bearing
    claim of THE MODIFIER, measured here at full N.
    """
    from LightEngine import modifier
    a_two = kernel.compute_forces(pos, vel, use_cuda=False)
    a_mod, _ = modifier.compute_forces_mod(pos, vel, use_cuda=False)
    nrm = float(np.linalg.norm(a_two))
    global_rel = float(np.linalg.norm(a_mod - a_two)) / max(nrm, 1e-12)
    a_two2 = kernel.compute_forces(pos, 2.0 * vel, use_cuda=False)
    a_mod2, _ = modifier.compute_forces_mod(pos, 2.0 * vel, use_cuda=False)
    d_two = a_two2 - a_two
    d_mod = a_mod2 - a_mod
    scale = float(np.max(np.linalg.norm(d_two, axis=1)))
    resist_rel = float(np.max(np.linalg.norm(d_mod - d_two, axis=1))) / max(scale, 1e-12)
    return global_rel, resist_rel


def _press(nums: dict, force: bool = False):
    """The record press: run the master algorithm, sample the grooves.

    One integration, once, cached to theLight.record.npz.  Every later emit()
    is a needle over this record -- the physics is never re-run per frame.
    """
    if RECORD_PATH.exists() and not force:
        return RECORD_PATH
    import time
    t0 = time.time()

    pos, vel, pin = scenario(nums)
    n = len(pos)
    n_seed = int(nums["n_seed"])
    T = int(nums["t_total_ticks"])
    S = int(nums["sample_every"])
    n_samp = T // S + 1

    sim = kernel.VelocityVerlet(n, use_cuda=False, use_modifier=True)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin)
    sim.compute_acceleration()

    pos_samp = np.empty((n_samp, n, 3), np.float32)
    col_samp = np.empty((n_samp, n, 3), np.float32)
    ticks = np.empty(n_samp, np.int64)
    met = {"bound_frac": [], "clusters": [], "max_cluster": [],
           "radius": [], "power": [], "energy": []}
    ckpt = {"tick": [], "global_rel": [], "resist_rel": []}
    ckpt_every = max(1, T // 8)
    first_impact = None

    for tick in range(T + 1):
        if tick:
            sim.step(DT)
        if tick % S == 0 or tick == T:
            si = tick // S
            ticks[si] = tick
            pos_samp[si] = sim.pos
            col_samp[si] = _mfield_colors(sim.pos, n_seed)
            met["bound_frac"].append(_bound_frac(sim.pos))
            met["radius"].append(_system_radius(sim.pos))
            n_c, mx = _cluster_info(sim.pos, R_C)
            met["clusters"].append(n_c)
            met["max_cluster"].append(mx)
            met["power"].append(float(sim.last_radiated_power))
            met["energy"].append(float(sim.radiated_energy))
            if first_impact is None and sim.last_radiated_power > 1e-9:
                first_impact = tick
        if tick and tick % ckpt_every == 0:
            g, r = _force_checkpoint(sim.pos, sim.vel)
            ckpt["tick"].append(tick)
            ckpt["global_rel"].append(g)
            ckpt["resist_rel"].append(r)

    vd = _verdict(met, ckpt, nums, first_impact)
    np.savez(
        RECORD_PATH,
        ticks=ticks, pos=pos_samp, col=col_samp,
        n_seed=n_seed,
        bound_frac=np.asarray(met["bound_frac"], np.float64),
        clusters=np.asarray(met["clusters"], np.int64),
        max_cluster=np.asarray(met["max_cluster"], np.int64),
        radius=np.asarray(met["radius"], np.float64),
        power=np.asarray(met["power"], np.float64),
        energy=np.asarray(met["energy"], np.float64),
        ckpt_tick=np.asarray(ckpt["tick"], np.int64),
        ckpt_global=np.asarray(ckpt["global_rel"], np.float64),
        ckpt_resist=np.asarray(ckpt["resist_rel"], np.float64),
        first_impact=np.int64(first_impact if first_impact is not None else -1),
        **{f"v_{k}": (np.asarray(v) if isinstance(v, list) else v)
           for k, v in vd.items()},
    )
    return RECORD_PATH


def _verdict(met: dict, ckpt: dict, nums: dict, first_impact) -> dict:
    """The falsifiers, declared before the run (see module header)."""
    # thresholds -- named here, never retuned after a result
    MATTER_BOUND = 0.50
    SETTLED_CV = 0.20
    SETTLED_SWING = 0.15
    FAITH_RESIST = 1e-4

    bf = np.asarray(met["bound_frac"], np.float64)
    radii = np.asarray(met["radius"], np.float64)
    cl = np.asarray(met["clusters"], np.float64)
    pw = np.asarray(met["power"], np.float64)
    en = np.asarray(met["energy"], np.float64)

    q = max(1, len(cl) // 4)
    late_cv = float(cl[-q:].std() / (cl[-q:].mean() + 1e-12))
    late_swing = float(bf[-q:].max() - bf[-q:].min())

    checks = {
        "MATTER (bound_frac > 0.5)": bool(bf[-1] > MATTER_BOUND),
        "SETTLED (late cluster CV < 0.2)": bool(late_cv < SETTLED_CV),
        "SETTLED (late bound swing < 0.15)": bool(late_swing < SETTLED_SWING),
        "BOUNDED (final radius < r_rain)": bool(radii[-1] < float(nums["r_rain_lu"])),
        "AWAKENED (radiated energy > 0)": bool(float(en[-1]) > 0.0 and first_impact is not None),
        "FAITHFUL (fold vs two-pass <= 1e-4)": bool(
            len(ckpt["resist_rel"]) >= 3 and max(ckpt["resist_rel"]) <= FAITH_RESIST),
    }
    values = {
        "final_bound_frac": round(float(bf[-1]), 4),
        "final_radius": round(float(radii[-1]), 4),
        "r_rain": float(nums["r_rain_lu"]),
        "late_cluster_cv": round(late_cv, 4),
        "late_bound_swing": round(late_swing, 4),
        "final_radiated_energy": round(float(en[-1]), 6),
        "first_impact_tick": (first_impact if first_impact is not None else -1),
        "max_resist_rel": round(float(max(ckpt["resist_rel"])), 8) if ckpt["resist_rel"] else 0.0,
        "max_global_rel": round(float(max(ckpt["global_rel"])), 6) if ckpt["global_rel"] else 0.0,
        "checkpoints": len(ckpt["resist_rel"]),
    }
    return {"checks": list(checks.keys()), "ok": [bool(v) for v in checks.values()],
            "verdict": "PASS" if all(checks.values()) else "FAIL",
            **values}


_REC_CACHE = {"mtime_ns": None, "rec": None}


def _load_record(nums: dict) -> dict:
    """The record, loaded once per file on disk -- the needle never re-reads 7 MB per frame."""
    _press(nums)
    m = RECORD_PATH.stat().st_mtime_ns
    if _REC_CACHE["mtime_ns"] != m:
        z = np.load(RECORD_PATH, allow_pickle=False)
        _REC_CACHE["rec"] = {k: z[k] for k in z.files}
        _REC_CACHE["mtime_ns"] = m
    return _REC_CACHE["rec"]


def emit(nums: dict, t: float = 1.0) -> np.ndarray:
    """The needle: the record at story-time t (0..1) as a (N, 28) splat buffer.

    Positions and M-field colours are linearly interpolated between record
    grooves, so scrubbing the story time is smooth and the physics is never
    re-run.  Mass = 1, charge = 1, one kind of point.
    """
    rec = _load_record(nums)
    t = float(np.clip(t, 0.0, 1.0))
    T = int(nums["t_total_ticks"])
    S = int(nums["sample_every"])
    tick_f = t * T
    f = tick_f / S
    i0 = int(np.floor(f))
    i1 = min(i0 + 1, len(rec["pos"]) - 1)
    w = f - i0
    pos = (1.0 - w) * rec["pos"][i0] + w * rec["pos"][i1]
    col = ((1.0 - w) * rec["col"][i0] + w * rec["col"][i1]).astype(np.float32)

    n = pos.shape[0]
    buf = np.zeros((n, NCOLS), dtype=np.float32)
    buf[:, PX:PZ + 1] = pos
    buf[:, 9] = 1.0            # mass -- identical points
    buf[:, 10] = -1.0          # immortal (the pipeline does not age them)
    buf[:, TYPE] = 3.0         # SOLID
    buf[:, CR:CB + 1] = col
    buf[:, ALPHA] = 0.9
    buf[:, SIZE] = float(nums.get("grain_size", 0.07))
    # ── THE SOLO CHANNEL (the DJ's dial, set from the deck's keyboard) ─────────────
    # One matter state at a time: everything else is dimmed so the chosen state's
    # grains read as a shape. The state machine is the matrix itself -- every row is
    # classified seed / wall / bond / far by its contact distance -- and soloing is
    # how you LOOK at one state's population while the needle runs.
    solo = _DECK.get("solo")
    if solo is not None:
        from scipy.spatial import cKDTree
        d, _ = cKDTree(pos).query(pos, k=2)
        dmin = d[:, 1]
        n_seed = int(nums["n_seed"])
        is_seed = np.arange(n) < n_seed
        free = ~is_seed
        keep = {"seed": is_seed,
                "wall": free & (dmin < R_WALL),
                "bond": free & (dmin >= R_WALL) & (dmin <= R_BOND),
                "far": free & (dmin > R_BOND)}[solo]
        col = np.where(keep[:, None], col, col * 0.16)
        buf[:, CR:CB + 1] = col
        buf[:, ALPHA] = np.where(keep, 0.9, 0.4)
    return np.ascontiguousarray(buf)


def sun_direction(t: float = 1.0, nums: dict | None = None):
    """A gentle light from the upper-left-front, constant across the story time."""
    s = np.array([-0.35, 0.28, 0.89], dtype=np.float64)
    return s / float(np.linalg.norm(s))


def verdict(nums: dict | None = None) -> dict:
    """The record's verdict, readable at any time."""
    nums = nums or _load_numbers()
    z = np.load(RECORD_PATH, allow_pickle=False)
    out = {}
    for k in z.files:
        if not k.startswith("v_"):
            continue
        a = z[k]
        # a 0-d array can hold a float, an int, a bool or a str ('PASS') -- int() on
        # every scalar was a data bug waiting on the first string verdict.
        out[k[len("v_"):]] = a.item() if a.ndim == 0 else a.tolist()
    return out


# ── THE DECK -- the state machine the operator keys against ─────────────────────────
# The buffer rows ARE the states (seed / wall / bond / far); the modifier M is the
# transition law between them (contact -> M < 0 wall, R_WALL <= d <= R_BOND -> M = 0
# bond shelf, beyond -> M -> 1 far field). The keyboard AFFECTS that machine: the
# solo channel picks the state to read, the needle scrubs / plays it down its movie,
# and the fps HUD proves what changing the state costs to render.
_DECK = {"solo": None}          # the solo channel: "seed" | "wall" | "bond" | "far" | None

KEYMAP = {
    "Space":      ("toggle_play", "play / pause the record"),
    "ArrowLeft":  ("t_back",      "needle one groove earlier"),
    "ArrowRight": ("t_fwd",       "needle one groove later"),
    "KeyR":       ("t_zero",      "needle to the start (t = 0)"),
    "KeyS":       ("solo_seed",   "solo the seed -- the pinned anvil"),
    "KeyW":       ("solo_wall",   "solo the radiating walls, M < 0"),
    "KeyB":       ("solo_bond",   "solo the bond shelf, M = 0"),
    "KeyF":       ("solo_far",    "solo the far field, M -> 1"),
    "KeyX":       ("solo_none",   "show every state"),
    "KeyN":       ("slower",      "play at half speed"),
    "KeyM":       ("faster",      "play at double speed"),
}


def _groove(nums: dict) -> float:
    """Story-time width of one record groove (one sampled frame)."""
    return float(int(nums.get("sample_every", 50))) / max(1, int(nums["t_total_ticks"]))


def set_solo(state):
    _DECK["solo"] = state


def handle_key(code: str, down: bool = True, t: float = 1.0,
               nums: dict | None = None) -> dict | None:
    """The DJ's controls: a keycode + the needle's current t -> a viewer command.

    Returns None when the key is not bound (or is a key-up): the deck ignores it.
    Commands: toggle_play | time (t) | solo (state) | rate (x).
    """
    if not down or code not in KEYMAP:
        return None
    nums = nums or _load_numbers()
    action = KEYMAP[code][0]
    if action == "toggle_play":
        return {"cmd": "toggle_play"}
    if action == "t_back":
        return {"cmd": "time", "t": float(np.clip(t - _groove(nums), 0.0, 1.0))}
    if action == "t_fwd":
        return {"cmd": "time", "t": float(np.clip(t + _groove(nums), 0.0, 1.0))}
    if action == "t_zero":
        return {"cmd": "time", "t": 0.0}
    if action == "slower":
        return {"cmd": "rate", "x": 0.5}
    if action == "faster":
        return {"cmd": "rate", "x": 2.0}
    if action.startswith("solo_"):
        state = None if action == "solo_none" else action[len("solo_"):]
        return {"cmd": "solo", "state": state}
    return None


def state_readout(nums: dict, t: float = 1.0) -> dict:
    """The matrix, processed as a state machine: how many rows are in each state now.

    Every grain is a row; every row's state is decided by its contact distance to its
    nearest neighbour (the same classification the M-field colours render). The counts
    are read at the INTERPOLATED position -- the very positions on screen -- so the
    HUD and the frame never disagree about what state the matrix is in.
    """
    rec = _load_record(nums)
    t = float(np.clip(t, 0.0, 1.0))
    T = int(nums["t_total_ticks"])
    S = int(nums["sample_every"])
    f = t * T / S
    i0 = int(np.floor(f))
    i1 = min(i0 + 1, len(rec["pos"]) - 1)
    w = f - i0
    pos = (1.0 - w) * rec["pos"][i0] + w * rec["pos"][i1]

    from scipy.spatial import cKDTree
    d, _ = cKDTree(pos).query(pos, k=2)
    dmin = d[:, 1]
    n = len(pos)
    n_seed = int(nums["n_seed"])
    is_seed = np.arange(n) < n_seed
    free = ~is_seed
    return {
        "t": round(t, 4),
        "tick": int(round(t * T)),
        "n_total": n,
        "solo": _DECK.get("solo"),
        "states": {
            "seed": int(is_seed.sum()),
            "wall": int((free & (dmin < R_WALL)).sum()),
            "bond": int((free & (dmin >= R_WALL) & (dmin <= R_BOND)).sum()),
            "far": int((free & (dmin > R_BOND)).sum()),
        },
        "keymap": [{"key": k, "action": a, "label": l} for k, (a, l) in KEYMAP.items()],
    }


if __name__ == "__main__":
    nums = _load_numbers()
    derive_commit()
    print(f"derived numbers committed -> {NUMBERS_PATH}")
    print(f"n_total={nums['n_total']}  n_seed={nums['n_seed']}  "
          f"t_total_ticks={nums['t_total_ticks']}  "
          f"t_total_units={nums['t_total_units']}")
