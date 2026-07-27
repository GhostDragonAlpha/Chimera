"""gait — DOES IT WALK, OR DOES IT JUST ARRIVE?

`distance = 13.52 body lengths` is not a gait. It is a receipt. The trainer will hand
you that receipt for a walk, for a bound, for a chaotic seizure that happens to drift
downfield, and for a creature dragging its face along the floor — and the score cannot
tell you which one you got. This module can.

THE FOOT IS NOT DESIGNED. IT IS DISCOVERED.
-------------------------------------------
Nothing in this project ever told the creature it has feet. The body came out of an
L-system; the brain came out of a GA. So this analyzer is not allowed to be handed a
list of feet — it has to FIND them, and the definition it uses is behavioural:

    a FOOT is a link that touches the ground SOME of the time.

Which immediately gives us the two failure modes for free, as the two ends of that
range. A link in contact ~100% of the time is not a foot, it is a SLED — the creature
is dragging. A link in contact ~0% of the time is not a foot, it is cargo.

WHAT SEPARATES A WALK FROM A BOUND (this is measured, not eyeballed)
-------------------------------------------------------------------
Biomechanists classify gaits from a HILDEBRAND / footfall diagram: for every foot, when
is it in STANCE (down) and when in SWING (up)? Everything follows from that one picture.

    DUTY FACTOR   fraction of the cycle a foot spends in stance.
                  > 0.5 -> a WALK (feet are down more than they are up).
                  < 0.5 -> a RUN/BOUND.
    SUSPENSION    fraction of time with ZERO feet down.
                  A walk NEVER has a suspension phase. A bound is DEFINED by one.
    SUPPORT       how many feet are down at once. A walk keeps >=2, usually >=3.
    PERIODICITY   a gait REPEATS. This is the one that catches the impostor: a body
                  can thrash chaotically and still travel, and every other number here
                  will look defensible. Autocorrelation of the footfall signal tells
                  you whether there is a CYCLE at all, or just noise that drifts.

PERIODICITY IS THE MEASURE THE OBJECTIVE NEVER HAD. Nothing in brain.json rewards
rhythm, so nothing has ever stopped the brain from being a seizure with good PR.

Usage:
    python -m core.gait --trained docs/objectives/brain.trained.json
    python -m core.gait --trained ... --png docs/objectives/brain.gait.png
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

# Sampled every step (the measure() loop samples contact only every 8th; for a gait
# diagram that is far too coarse — an 8-step stride would vanish entirely).
CONTACT_EVERY = 2

_UNSET = object()


# --- replay: run the trained brain and WATCH THE FEET --------------------------

def replay(weights, steps=None, contact_every=CONTACT_EVERY) -> dict:
    """Re-run the trained brain on the fixed body, recording a full contact trace.

    This deliberately re-implements the sim loop from brain_cpu.measure() rather than
    importing it, because measure() reports SUMMARY FACTS and throws the time series
    away — and the time series is the entire object of interest here. It is held to
    the same physics (same DT, same SETTLE, same torque, same friction) so that what
    is analyzed IS what was scored. If those ever drift apart, this file is lying.
    """
    import pybullet as p

    from core.trainables import brain_cpu as B
    from core.trainables.walker import DT, SETTLE_STEPS, SIM_STEPS, _build, _client

    steps = SIM_STEPS if steps is None else steps
    bones, size = B._bones()
    nj = len(bones) - 1
    n_in, _, _ = B.shape()

    w = np.asarray(weights, dtype=np.float64)
    o1 = n_in * B.N_HID
    W1 = w[:o1].reshape(B.N_HID, n_in)
    b1 = w[o1:o1 + B.N_HID]
    o2 = o1 + B.N_HID
    W2 = w[o2:o2 + B.N_HID * nj].reshape(nj, B.N_HID)
    b2 = w[o2 + B.N_HID * nj:]

    c = _client()
    p.resetSimulation(physicsClientId=c)
    p.setGravity(0, 0, -9.81, physicsClientId=c)
    p.setTimeStep(DT, physicsClientId=c)
    gid = p.createMultiBody(0, p.createCollisionShape(p.GEOM_PLANE, physicsClientId=c),
                            physicsClientId=c)
    p.changeDynamics(gid, -1, lateralFriction=1.0, physicsClientId=c)

    zmin = min(min(b.p0[2], b.p1[2]) for b in bones)
    uid = _build(p, c, bones, lift=-zmin + 0.05)
    for j in range(nj):
        p.changeDynamics(uid, j, lateralFriction=1.2, physicsClientId=c)
    p.changeDynamics(uid, -1, lateralFriction=1.2, physicsClientId=c)

    for _ in range(SETTLE_STEPS):
        p.stepSimulation(physicsClientId=c)

    start = p.getBasePositionAndOrientation(uid, physicsClientId=c)[0]
    obs = np.empty(n_in)
    JOINTS = list(range(nj))
    FORCES = [B.TORQUE] * nj

    # link -1 is the BASE, and the base can absolutely be a foot (or a sled). Index it
    # at column 0 so nothing about the creature's anatomy is assumed.
    links = [-1] + list(range(nj))
    col = {L: i for i, L in enumerate(links)}
    contact, track, times = [], [], []

    for step in range(steps):
        st = p.getJointStates(uid, JOINTS, physicsClientId=c)
        for j in range(nj):
            obs[j] = st[j][0]
            obs[nj + j] = st[j][1] * 0.1
        pos, orn = p.getBasePositionAndOrientation(uid, physicsClientId=c)
        m = p.getMatrixFromQuaternion(orn)
        obs[2 * nj + 0], obs[2 * nj + 1], obs[2 * nj + 2] = m[2], m[5], m[8]
        t = step * DT
        obs[2 * nj + 3] = math.sin(6.2831853 * t)
        obs[2 * nj + 4] = math.cos(6.2831853 * t)

        act = np.tanh(W2 @ np.tanh(W1 @ obs + b1) + b2) * B.TARGET_AMP
        p.setJointMotorControlArray(uid, JOINTS, p.POSITION_CONTROL,
                                    targetPositions=[float(x) for x in act],
                                    forces=FORCES, physicsClientId=c)
        p.stepSimulation(physicsClientId=c)

        if step % contact_every == 0:
            row = np.zeros(len(links), dtype=np.int8)
            for cp in p.getContactPoints(bodyA=uid, bodyB=gid, physicsClientId=c):
                i = col.get(cp[3])          # cp[3] = linkIndexA
                if i is not None:
                    row[i] = 1
            contact.append(row)
            pos = p.getBasePositionAndOrientation(uid, physicsClientId=c)[0]
            track.append(pos)
            times.append(t)

    end = p.getBasePositionAndOrientation(uid, physicsClientId=c)[0]
    return {
        "contact": np.asarray(contact),           # (T, n_links) 0/1
        "links": links,
        "track": np.asarray(track),
        "times": np.asarray(times),
        "size": size,
        "n_bones": len(bones),
        "net": math.dist(end[:2], start[:2]),
        "distance": math.dist(end[:2], start[:2]) / size,
        "uid": uid, "gid": gid, "client": c,
        "dt_sample": DT * contact_every,
    }


# --- analyze: the numbers that separate a walk from an impostor ----------------

def _periodicity(sig: np.ndarray, dt: float, lo=0.15, hi=2.0) -> tuple:
    """Is there a CYCLE in here, or is this just noise that happens to travel?

    Autocorrelation of the (mean-removed) support signal. The height of the best peak
    within a plausible stride window IS the answer: ~1.0 is a metronome, ~0.0 is a
    seizure. Returns (strength 0..1, period seconds).

    This is the measure that catches the impostor no other measure can see."""
    x = sig.astype(np.float64)
    x -= x.mean()
    n = len(x)
    if n < 16 or not np.any(x):
        return 0.0, 0.0
    ac = np.correlate(x, x, mode="full")[n - 1:]
    if ac[0] <= 0:
        return 0.0, 0.0
    ac = ac / ac[0]
    klo, khi = max(2, int(lo / dt)), min(n - 1, int(hi / dt))
    if khi <= klo:
        return 0.0, 0.0
    k = klo + int(np.argmax(ac[klo:khi]))
    return float(max(0.0, ac[k])), float(k * dt)


def analyze(tr: dict, foot_lo=0.03, sled_hi=0.92) -> dict:
    C = tr["contact"]                             # (T, L)
    T = len(C)
    duty_all = C.mean(axis=0)                     # per-link stance fraction

    feet, sleds, cargo = [], [], []
    for i, L in enumerate(tr["links"]):
        d = float(duty_all[i])
        if d >= sled_hi:
            sleds.append((L, d))                  # never lifts: a SLED, not a foot
        elif d >= foot_lo:
            feet.append((L, d))                   # touches sometimes: a FOOT
        else:
            cargo.append((L, d))                  # never touches: cargo

    fi = [tr["links"].index(L) for L, _ in feet]
    support = C[:, fi].sum(axis=1) if fi else np.zeros(T)
    down_any = C.sum(axis=1)                      # includes sleds — TRUE airborne test

    per, period = _periodicity(support if fi else down_any, tr["dt_sample"])

    duties = [d for _, d in feet]
    return {
        "n_feet": len(feet),
        "feet": feet,
        "sleds": sleds,
        "n_cargo": len(cargo),
        "duty_mean": float(np.mean(duties)) if duties else 0.0,
        "duty_min": float(np.min(duties)) if duties else 0.0,
        "duty_max": float(np.max(duties)) if duties else 0.0,
        "support_mean": float(support.mean()),
        "support_min": int(support.min()) if T else 0,
        "suspension_frac": float((down_any == 0).mean()),
        "drag_frac": float(sum(d for _, d in sleds)),
        "periodicity": per,
        "period_s": period,
        "distance": tr["distance"],
        "classification": _classify(feet, sleds, down_any, support, per),
    }


def _classify(feet, sleds, down_any, support, per) -> str:
    """Deliberately conservative, and it is allowed to say the unflattering thing."""
    susp = float((down_any == 0).mean())
    duty = float(np.mean([d for _, d in feet])) if feet else 0.0
    if not feet:
        return "NO GAIT — nothing that could be called a foot ever leaves the ground"
    if per < 0.30:
        return (f"NOT A GAIT — periodicity {per:.2f}: there is no repeating cycle here. "
                f"This is thrashing that happens to travel.")
    if sleds:
        return (f"DRAG / SCRAMBLE — {len(sleds)} link(s) never leave the ground. "
                f"The creature is a sled with twitching parts.")
    if susp > 0.25:
        return f"BOUND / BALLISTIC — airborne {susp:.0%} of the time. This is artillery."
    if susp > 0.05:
        return f"RUN / TROT — a real flight phase ({susp:.0%}), duty {duty:.2f}."
    if duty >= 0.5 and float(support.min()) >= 1:
        return f"WALK — duty {duty:.2f}, never fully airborne, always supported."
    return f"UNCLASSIFIED — duty {duty:.2f}, suspension {susp:.0%}, periodicity {per:.2f}."


# --- the Hildebrand diagram, in a terminal -------------------------------------

def diagram(tr: dict, a: dict, width=96) -> str:
    C, T = tr["contact"], len(tr["contact"])
    rows, order = [], [L for L, _ in a["feet"]] + [L for L, _ in a["sleds"]]
    for L in order:
        i = tr["links"].index(L)
        line = "".join("#" if C[min(T - 1, int(x * T / width)), i] else "."
                       for x in range(width))
        tag = "SLED" if L in [s for s, _ in a["sleds"]] else "foot"
        name = "base" if L == -1 else f"L{L:<3d}"
        rows.append(f"  {name} {tag}  |{line}|  duty {C[:, i].mean():.2f}")

    sup = C[:, [tr["links"].index(L) for L, _ in a["feet"]]].sum(axis=1) \
        if a["feet"] else np.zeros(T)
    bar = "".join(str(min(9, int(sup[min(T - 1, int(x * T / width))])))
                  for x in range(width))
    rows.append(f"  {'':>10}  |{bar}|  feet down")
    span = tr["times"][-1] if len(tr["times"]) else 0.0
    rows.append(f"  {'':>10}   0s{' ' * (width - 8)}{span:.1f}s")
    return "\n".join(rows)


# --- the witness: an actual picture --------------------------------------------

def render(tr: dict, weights, out: Path, n=6, w=320, h=240) -> Path:
    """A strip of side-on frames. pybullet's TinyRenderer works in DIRECT mode, so this
    is headless — no GUI, no window, no display. The camera TRACKS the creature, so a
    body that has fallen over and is being dragged looks like exactly that."""
    import pybullet as p
    from PIL import Image

    from core.trainables.walker import DT, SETTLE_STEPS, SIM_STEPS, _build, _client
    from core.trainables import brain_cpu as B

    bones, size = B._bones()
    nj = len(bones) - 1
    n_in, _, _ = B.shape()
    w_ = np.asarray(weights, dtype=np.float64)
    o1 = n_in * B.N_HID
    W1 = w_[:o1].reshape(B.N_HID, n_in); b1 = w_[o1:o1 + B.N_HID]
    o2 = o1 + B.N_HID
    W2 = w_[o2:o2 + B.N_HID * nj].reshape(nj, B.N_HID); b2 = w_[o2 + B.N_HID * nj:]

    c = _client()
    p.resetSimulation(physicsClientId=c)
    p.setGravity(0, 0, -9.81, physicsClientId=c)
    p.setTimeStep(DT, physicsClientId=c)
    gid = p.createMultiBody(0, p.createCollisionShape(p.GEOM_PLANE, physicsClientId=c),
                            physicsClientId=c)
    p.changeDynamics(gid, -1, lateralFriction=1.0, physicsClientId=c)
    zmin = min(min(b.p0[2], b.p1[2]) for b in bones)
    uid = _build(p, c, bones, lift=-zmin + 0.05)
    for j in range(nj):
        p.changeDynamics(uid, j, lateralFriction=1.2, physicsClientId=c)
    p.changeDynamics(uid, -1, lateralFriction=1.2, physicsClientId=c)
    for _ in range(SETTLE_STEPS):
        p.stepSimulation(physicsClientId=c)

    obs = np.empty(n_in); JOINTS = list(range(nj)); FORCES = [B.TORQUE] * nj
    grab = {int(k * (SIM_STEPS - 1) / (n - 1)) for k in range(n)}
    proj = p.computeProjectionMatrixFOV(50, w / h, 0.1, 60, physicsClientId=c)
    shots = []

    for step in range(SIM_STEPS):
        st = p.getJointStates(uid, JOINTS, physicsClientId=c)
        for j in range(nj):
            obs[j] = st[j][0]; obs[nj + j] = st[j][1] * 0.1
        pos, orn = p.getBasePositionAndOrientation(uid, physicsClientId=c)
        m = p.getMatrixFromQuaternion(orn)
        obs[2 * nj + 0], obs[2 * nj + 1], obs[2 * nj + 2] = m[2], m[5], m[8]
        t = step * DT
        obs[2 * nj + 3] = math.sin(6.2831853 * t); obs[2 * nj + 4] = math.cos(6.2831853 * t)
        act = np.tanh(W2 @ np.tanh(W1 @ obs + b1) + b2) * B.TARGET_AMP
        p.setJointMotorControlArray(uid, JOINTS, p.POSITION_CONTROL,
                                    targetPositions=[float(x) for x in act],
                                    forces=FORCES, physicsClientId=c)
        p.stepSimulation(physicsClientId=c)

        if step in grab:
            d = max(2.5, size * 3.0)
            view = p.computeViewMatrix([pos[0] - 0.2 * d, pos[1] - d, pos[2] + 0.35 * d],
                                       list(pos), [0, 0, 1], physicsClientId=c)
            img = p.getCameraImage(w, h, view, proj,
                                   renderer=p.ER_TINY_RENDERER, physicsClientId=c)[2]
            shots.append(np.reshape(np.asarray(img, dtype=np.uint8), (h, w, 4))[:, :, :3])

    strip = Image.new("RGB", (w * len(shots), h))
    for i, s in enumerate(shots):
        strip.paste(Image.fromarray(s), (i * w, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    strip.save(out)
    return out


_PYBULLET_OBJECTIVES = {"brain", "walker"}


def engine_of(blob: dict) -> str:
    """Which physics ACTUALLY SCORED this artifact? -> 'pybullet' | 'mujoco' | 'unknown'

    THE GUARD THIS FILE PROMISED AND NEVER HAD (added 2026-07-16 after it convicted the
    studio's only real walker).

    This module replays through pybullet at brain_cpu.TORQUE = 22.0 N.m. brain_gpu trains
    through core.mjcf at mjcf.TORQUE = 2.0 -- 11x lower (35.4 vs 3.2 N.m/kg on the 0.622kg
    body; a human hip is ~3). Both artifacts carry len(w)=1744, so NOTHING ERRORS. The
    replay just flings the creature and prints a confident lie:

        brain_gpu.trained.json, as MuJoCo scored it :  periodicity 0.78, duty 0.54,
                                                        airborne 7%   -> a WALK
        the same weights, replayed here             :  periodicity 0.14, duty 0.05,
                                                        airborne 85%  -> "NOT A GAIT"

    By this file's OWN classifier the MuJoCo numbers are a walk. The fraud-detector was
    convicting the best thing the studio has made. core/gait_mj.py already knew --
    "Judging a MuJoCo-trained brain with a pybullet replay would be judging a different
    creature. WHAT IS SCORED AND WHAT IS WITNESSED MUST BE THE SAME THING" -- but knowing
    was never enforced, and nothing stopped the wrong tool from running.

    Detected STRUCTURALLY, not by filename: brain_gpu.measure() is the only domain that
    computes `robustness`/`distance_worst` (N randomized restarts, keep the worst), so
    their presence is a positive fingerprint of the MuJoCo path. A name check would rot
    the first time an objective is renamed; a fingerprint of the measurement itself will
    not.

    Fails CLOSED on 'unknown': doctrine is "a gate fails -> exit non-zero -> halt; never
    fake a default." An unprovable provenance is exactly when a confident number is most
    dangerous.
    """
    m = blob.get("measures") or {}
    if "robustness" in m or "distance_worst" in m:
        return "mujoco"
    obj = str(blob.get("objective", ""))
    if obj.endswith("_gpu") or obj.endswith("_mj"):
        return "mujoco"
    if obj in _PYBULLET_OBJECTIVES:
        return "pybullet"
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--trained", required=True, help="docs/objectives/brain.trained.json")
    ap.add_argument("--png", default=None, help="also render a frame strip here")
    ap.add_argument("--force-wrong-engine", action="store_true",
                    help="analyze anyway after the engine guard refuses. The number you "
                         "get will be about a creature that does not exist.")
    a = ap.parse_args()

    blob = json.loads(Path(a.trained).read_text(encoding="utf-8"))
    weights = blob["genome"]["w"]

    eng = engine_of(blob)
    if eng != "pybullet" and not a.force_wrong_engine:
        from core.trainables import brain_cpu as _B
        try:
            from core import mjcf as _M
            mj_t = _M.TORQUE
        except Exception:
            mj_t = "?"
        print(f"\n!! ENGINE GUARD - refusing to analyze {Path(a.trained).name}")
        print(f"   provenance: {eng.upper()}"
              + ("  (it records robustness/distance_worst -> N-restart MuJoCo path)"
                 if eng == "mujoco" else "  (cannot prove what scored it)"))
        print(f"   this file replays through PYBULLET at TORQUE={_B.TORQUE} N.m; "
              f"the MuJoCo path trains at {mj_t} N.m.")
        print("   Replaying it here would fling the creature and report a gait it never had.")
        print("   WHAT IS SCORED AND WHAT IS WITNESSED MUST BE THE SAME THING.\n")
        print(f"   Use the witness that matches the physics:")
        print(f"     python -m core.gait_mj --trained {a.trained}"
              + (f" --png {a.png}" if a.png else ""))
        print("   (--force-wrong-engine overrides; the result is about a different creature.)\n")
        return 2

    tr = replay(weights)
    g = analyze(tr)

    print(f"\nGAIT  {Path(a.trained).name}")
    print(f"  {tr['n_bones']} bones, travelled {g['distance']:.2f} body lengths\n")
    print(diagram(tr, g))
    print(f"\n  feet discovered       {g['n_feet']}   (of {tr['n_bones']} links; "
          f"{g['n_cargo']} never touch)")
    print(f"  duty factor           {g['duty_mean']:.2f}   "
          f"(>0.50 = a walk, <0.50 = a run)")
    print(f"  feet down (mean)      {g['support_mean']:.2f}, minimum {g['support_min']}")
    print(f"  suspension            {g['suspension_frac']:.1%}   "
          f"(a WALK is never fully airborne)")
    print(f"  PERIODICITY           {g['periodicity']:.2f}   "
          f"(1.0 = a metronome, 0.0 = a seizure)")
    if g["period_s"]:
        print(f"  stride period         {g['period_s']:.2f}s")
    if g["sleds"]:
        print(f"  !! SLEDS              {[L for L, _ in g['sleds']]} — never leave the ground")
    print(f"\n  {g['classification']}\n")

    if a.png:
        print(f"  -> {render(tr, weights, Path(a.png))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
