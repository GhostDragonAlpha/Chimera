"""gait_mj — WITNESS the winner, in the physics it was actually trained in.

core/gait.py replays through pybullet. Everything trained after 2026-07-14 is trained in
MuJoCo, and the two are NOT the same physics — pybullet has self-collision off by default
and a constraint-based servo that CONTAINS violence; MuJoCo has neither. Judging a
MuJoCo-trained brain with a pybullet replay would be judging a different creature.

    WHAT IS SCORED AND WHAT IS WITNESSED MUST BE THE SAME THING.

So this file replays through core.mjcf — the exact model brain_gpu trains against — and
prints the Hildebrand footfall diagram, the duty factors, and the PERIODICITY. It also
renders a frame strip, because a number is not a witness (H-14: verified-by-injection is
not playable) and 'periodicity 0.62' is still just a number until you watch the thing walk.

A FOOT IS DISCOVERED, NOT DECLARED. Nothing ever told this creature it has feet, so a foot
is defined behaviourally: a link that touches the ground SOME of the time. That definition
hands you both failure modes for free, as the two ends of the range — a link down ~100% of
the time is not a foot, it is a SLED; a link down ~0% is cargo.

    python -m core.gait_mj --trained docs/objectives/brain_gpu.trained.json --png out.png
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

import numpy as np

from core import mjcf
from core.trainables.brain_cpu import N_HID, TARGET_AMP, _bones, shape
from core.trainables.walker import DT, SETTLE_STEPS, SIM_STEPS

CONTACT_EPS = 0.006
SAMPLE_EVERY = 2


def _mlp(w, n_in, nj):
    w = np.asarray(w, dtype=np.float64)
    o1 = n_in * N_HID
    W1 = w[:o1].reshape(N_HID, n_in)
    b1 = w[o1:o1 + N_HID]
    o2 = o1 + N_HID
    W2 = w[o2:o2 + N_HID * nj].reshape(nj, N_HID)
    b2 = w[o2 + N_HID * nj:]
    return W1, b1, W2, b2


def replay(weights, dz=0.0, render=0):
    """One creature, one rollout, in the trained physics. Returns the full contact trace."""
    import mujoco

    bones, size = _bones()
    zmin = min(min(b.p0[2], b.p1[2]) for b in bones)
    mjm = mujoco.MjModel.from_xml_string(
        mjcf.from_bones(bones, lift=-zmin + 0.05 + dz, dt=DT))
    mjcf.check(mjm, len(bones))
    mjd = mujoco.MjData(mjm)
    mujoco.mj_forward(mjm, mjd)

    nj, n_in = mjm.nu, shape()[0]
    W1, b1, W2, b2 = _mlp(weights, n_in, nj)
    nb = mjm.ngeom - 1                       # geom 0 is the floor

    for _ in range(SETTLE_STEPS):
        mujoco.mj_step(mjm, mjd)

    start = mjd.qpos[:2].copy()
    prev, path = start.copy(), 0.0
    contact, zs, times, shots = [], [], [], []
    grab = ({int(k * (SIM_STEPS - 1) / (render - 1)) for k in range(render)}
            if render else set())
    rend = None
    if render:
        try:
            rend = mujoco.Renderer(mjm, height=260, width=340)
        except Exception as e:            # no GL context on this box; the diagram still stands
            print(f"  (no renderer: {type(e).__name__}: {str(e)[:60]})")
            rend = None

    obs = np.empty(n_in)
    for step in range(SIM_STEPS):
        obs[:nj] = mjd.qpos[7:7 + nj]
        obs[nj:2 * nj] = mjd.qvel[6:6 + nj] * 0.1
        obs[2 * nj:2 * nj + 3] = mjd.xmat[1].reshape(3, 3)[:, 2]   # the body's up-vector
        t = step * DT
        obs[2 * nj + 3] = math.sin(6.2831853 * t)
        obs[2 * nj + 4] = math.cos(6.2831853 * t)
        mjd.ctrl[:] = np.tanh(W2 @ np.tanh(W1 @ obs + b1) + b2) * TARGET_AMP
        mujoco.mj_step(mjm, mjd)
        if not np.all(np.isfinite(mjd.qpos)):
            break

        if step % SAMPLE_EVERY == 0:
            # Ground contact, GEOMETRICALLY — the same derivation brain_gpu's kernel uses,
            # so the footfall we look at is the footfall that was scored. A capsule's axis
            # is its local z, so its lowest world point is
            #     centre_z - |axis_z| * half_length - radius.
            row = np.zeros(nb, dtype=np.int8)
            for g in range(1, mjm.ngeom):
                R = mjd.geom_xmat[g].reshape(3, 3)
                r, hl = mjm.geom_size[g][0], mjm.geom_size[g][1]
                low = mjd.geom_xpos[g][2] - abs(R[2, 2]) * hl - r
                row[g - 1] = 1 if low < CONTACT_EPS else 0
            contact.append(row)
            path += float(np.linalg.norm(mjd.qpos[:2] - prev))
            prev = mjd.qpos[:2].copy()
            zs.append(mjd.qpos[2])
            times.append(t)

        if rend is not None and step in grab:
            cam = mujoco.MjvCamera()
            cam.lookat[:] = mjd.qpos[:3]
            cam.distance = max(2.0, size * 3.2)
            cam.azimuth, cam.elevation = 90, -12
            rend.update_scene(mjd, camera=cam)
            shots.append(rend.render())

    end = mjd.qpos[:2].copy()
    net = float(np.linalg.norm(end - start))
    return {
        "contact": np.asarray(contact), "times": np.asarray(times),
        "size": size, "n_bones": nb, "net": net, "distance": net / size,
        "straightness": net / max(path, 1e-6),
        "torso_z": float(np.mean(zs)) / size if zs else 0.0,
        "dt_sample": DT * SAMPLE_EVERY, "shots": shots,
    }


def periodicity(sig, dt, lo=0.15, hi=2.0):
    x = np.asarray(sig, dtype=np.float64)
    x = x - x.mean()
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


def analyze(tr, foot_lo=0.03, sled_hi=0.92):
    C = tr["contact"]
    if not len(C):
        return {"classification": "DEAD — the rollout diverged", "n_feet": 0,
                "feet": [], "sleds": [], "periodicity": 0.0, "duty_mean": 0.0,
                "support_mean": 0.0, "suspension": 1.0, "period_s": 0.0}
    duty = C.mean(axis=0)
    feet = [(i, float(d)) for i, d in enumerate(duty) if foot_lo <= d < sled_hi]
    sleds = [(i, float(d)) for i, d in enumerate(duty) if d >= sled_hi]
    fi = [i for i, _ in feet]
    support = C[:, fi].sum(axis=1) if fi else np.zeros(len(C))
    down_any = C.sum(axis=1)
    per, T = periodicity(support if fi else down_any, tr["dt_sample"])
    dm = float(np.mean([d for _, d in feet])) if feet else 0.0
    susp = float((down_any == 0).mean())

    if not feet:
        cls = "NO GAIT — nothing that could be called a foot ever leaves the ground"
    elif per < 0.30:
        cls = (f"NOT A GAIT — periodicity {per:.2f}: no repeating cycle. "
               f"Thrashing that happens to travel.")
    elif sleds:
        cls = (f"DRAG / SCRAMBLE — {len(sleds)} link(s) never leave the ground. "
               f"A sled with twitching parts.")
    elif susp > 0.25:
        cls = f"BOUND / BALLISTIC — airborne {susp:.0%}. This is artillery."
    elif susp > 0.05:
        cls = f"RUN / TROT — a real flight phase ({susp:.0%}), duty {dm:.2f}."
    elif dm >= 0.5 and support.min() >= 1:
        cls = f"WALK — duty {dm:.2f}, never fully airborne, always supported."
    else:
        cls = f"UNCLASSIFIED — duty {dm:.2f}, suspension {susp:.0%}, period. {per:.2f}."

    return {"n_feet": len(feet), "feet": feet, "sleds": sleds, "periodicity": per,
            "period_s": T, "duty_mean": dm, "support_mean": float(support.mean()),
            "suspension": susp, "classification": cls}


def diagram(tr, a, width=92):
    C, T = tr["contact"], len(tr["contact"])
    if not T:
        return "  (no trace)"
    rows = []
    for i, _ in a["feet"] + a["sleds"]:
        line = "".join("#" if C[min(T - 1, int(x * T / width)), i] else "."
                       for x in range(width))
        tag = "SLED" if i in [s for s, _ in a["sleds"]] else "foot"
        rows.append(f"  L{i:<3d} {tag}  |{line}|  duty {C[:, i].mean():.2f}")
    fi = [i for i, _ in a["feet"]]
    sup = C[:, fi].sum(axis=1) if fi else np.zeros(T)
    bar = "".join(str(min(9, int(sup[min(T - 1, int(x * T / width))])))
                  for x in range(width))
    rows.append(f"  {'':>9}  |{bar}|  feet down")
    span = tr["times"][-1] if len(tr["times"]) else 0.0
    rows.append(f"  {'':>9}   0s{' ' * (width - 8)}{span:.1f}s")
    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--trained", required=True)
    ap.add_argument("--png", default=None)
    ap.add_argument("--frames", type=int, default=6)
    a = ap.parse_args()

    os.environ.setdefault("MUJOCO_GL", "egl")
    w = json.loads(Path(a.trained).read_text(encoding="utf-8"))["genome"]["w"]

    tr = replay(w, render=a.frames if a.png else 0)
    g = analyze(tr)

    print(f"\nGAIT (MuJoCo — the physics it was trained in)  {Path(a.trained).name}")
    print(f"  {tr['n_bones']} bones, travelled {tr['distance']:.2f} body lengths\n")
    print(diagram(tr, g))
    print(f"\n  feet discovered   {g['n_feet']} of {tr['n_bones']} links")
    print(f"  duty factor       {g['duty_mean']:.2f}   (>0.50 = a walk, <0.50 = a run)")
    print(f"  feet down (mean)  {g['support_mean']:.2f}")
    print(f"  suspension        {g['suspension']:.1%}   (a WALK is never fully airborne)")
    print(f"  PERIODICITY       {g['periodicity']:.2f}   (1.0 = metronome, 0.0 = seizure)")
    if g["period_s"]:
        print(f"  stride period     {g['period_s']:.2f}s")
    print(f"  torso height      {tr['torso_z']:.3f} body lengths  "
          f"(0.03 = lying down and squirming)")
    print(f"  straightness      {tr['straightness']:.2f}")
    if g["sleds"]:
        print(f"  !! SLEDS          {[i for i, _ in g['sleds']]} — never leave the ground")
    print(f"\n  {g['classification']}\n")

    # ROBUSTNESS, on the spot: a real gait shrugs off a nudge that a lottery ticket cannot.
    print("  ROBUSTNESS — the same brain, from perturbed starts:")
    base = tr["distance"]
    for dz in (1e-6, 1e-3, 1e-2):
        d = replay(w, dz=dz)["distance"]
        print(f"    start z +{dz:<7.0e} m -> {d:6.2f} body lengths  "
              f"({(d - base):+.2f} vs {base:.2f})")

    if a.png and tr["shots"]:
        from PIL import Image
        h, wpx = tr["shots"][0].shape[:2]
        strip = Image.new("RGB", (wpx * len(tr["shots"]), h))
        for i, s in enumerate(tr["shots"]):
            strip.paste(Image.fromarray(s), (i * wpx, 0))
        Path(a.png).parent.mkdir(parents=True, exist_ok=True)
        strip.save(a.png)
        print(f"\n  -> {a.png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
