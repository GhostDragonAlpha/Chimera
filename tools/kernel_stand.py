#!/usr/bin/env python
"""kernel_stand.py -- M2: the packet bear STANDS under gravity, or tips. Data either way.

Doctrine (docs/THE_KERNEL.md): DRAW = gravity; RESISTANCE = the floor's wall.
THE_TRANSLATION law 4: for the standing test the skeleton is locked (rigid
reduction -- each part's packets ride its bone frame; joints fixed), so the
bear integrates as ONE rigid body whose contact with the floor is the SUM
over its real packets. No collision mesh, no placement cheats.

PRE-REGISTERED before this run (do not edit after):
  - Pose: legs rotated about hip pivots (capsule a-end) by the bind angle 85 deg
    around the hip X axis so feet point down; feet/arms ride their groups.
  - Floor: y=0. Wall law: F = K_S * penetration on each packet with y < 0
    (spring-wall = kernel wall at p=1 in penetration depth).
  - K_S DERIVED: total weight W = M*g ~ 24.6 N must be carried at equilibrium
    penetration delta <= 0.5 mm by the ~N_contact packets in the feet:
    K_S = W / (N_eff * delta). N_eff measured from the posed cloud (packets
    within 5 mm of the floor), not guessed.
  - dt DERIVED: resolve the FASTEST wall oscillator that can engage. Each
    packet is its own spring against the wall: omega_p = sqrt(K_S / m_p).
    The wall only ever touches the contact band (rest y within 8 cm of the
    sole -- at the 5 deg tilt bound a 0.3 m body drops other parts by at
    most 0.3*(1-cos5) = 1.1 mm, so 8 cm cannot be reached), so
    dt = 0.1 * 2*pi / sqrt(K_S / m_min_band), m_min_band = lightest packet
    in the band. Semi-implicit Euler is stable for omega*dt < 2; 0.63 OK.

RUN LOG (falsifier record, appended as runs happen):
  RUN 1 (2026-08-22): BLEW UP -- bear launched 9.8 m, tilt 149 deg.
    Cause found BEFORE rerun: the dt derivation used the WHOLE-BODY
    oscillator omega = sqrt(K_S*N_eff/M) = 140 rad/s, but each packet
    oscillates against its own wall spring at sqrt(K_S/m_p) ~ 3200 rad/s
    -> omega*dt = 14.4, far outside the stability bound -> numeric
    explosion, NOT a physical tip. The physics falsifier (tips/sinks) did
    NOT fire; the dt derivation was wrong. Fixed as above; rerun.
  RUN 2 (2026-08-22): TIPPED backward, tilt 66 deg, still airborne at 3 s.
    TWO causes measured before rerun:
    (a) PHYSICAL -- the pre-registered falsifier FIRED. Statics: COM at
        z=-3.8 mm sits 0.3 mm BEHIND the heel line (contact patch z in
        [-3.5, +29.9] mm). Statically unstable; it fell on its back.
        Successor (as pre-registered): shift the stance, DERIVED from the
        measurement: sweep of the hip angle shows 90 deg (legs VERTICAL --
        also the zero-hip-torque pose under gravity) moves the patch to
        [-11.9, +21.2] mm, COM 7.8 mm inside. 85 deg had been inherited
        from bind_bear's measurement of a DIFFERENT body; corrected.
    (b) MISSING PHYSICS -- the spring wall is conservative: with no
        dissipation the bear bounces forever and PASS(d) "settled" is
        unreachable. First fix attempt (per-packet critical damping
        C_p = 2*sqrt(K_S*m_p)) FAILED by measurement: the wall engages
        progressively (toe pole first), so at impact only ~100 packets
        carry the dashpot -- C_tot ~ 3.5 N.s/m against a 0.78 kg.m/s
        impact -> full-speed rebound (v_y -0.32 -> +0.35 m/s) plus a
        1.4 N.m torque transient through the off-COM toe point -> the
        bear left the floor spinning at 1.49 rad/s and tumbled.
        The damping must act on the AGGREGATE body modes, because the
        rigid reduction (law 4) makes the internal bonds infinitely
        stiff: dissipation at the wall acts on the body's 6 DOF, not on
        any packet's own mass. RUN 3 derivation (body-level Kelvin-Voigt,
        all constants from measured geometry, active only while touching,
        clamped so the wall never pulls):
          normal:  c_n  = 2*sqrt(K_tot*M),  K_tot = K_S*N_eff
          rocking: K_rock,x = K_S*sum(dz_i^2), K_rock,z = K_S*sum(dx_i^2)
                   over the equilibrium contact band (measured);
                   c_r,axis = 2*sqrt(K_rock*I_axis)  (critical per mode)
          Stability: (c_n/M)*dt = 0.022 << 2; (c_r/I)*dt = 0.015 << 2.
  RUN 3 (2026-08-22): STILL TIPPED (147 deg, sank 244 mm once past the
    band). Constitutive press test measured the truth:
      - equilibrium sink 3.5 mm (sole engages PROGRESSIVELY, not the 0.5 mm
        the K_S derivation assumed -- the "foot" is an ELLIPSOID and the
        90-deg hip pose stands the bear on its TOE POLE: a point contact),
      - at equilibrium the wall's pitch torque is -0.2 N.m with NO tilt:
        the pressure centroid sits 8.1 mm ahead of the COM -> permanent
        tipping moment,
      - tilt sweep: rocking stiffness d_tau/d_theta > 0 -- statically
        UNSTABLE in pitch. This is geometry, not integration: a body whose
        COM (190 mm up) rides a contact with 33-43 mm curvature radius is
        an inverted pendulum; no passive floor can hold it.
    Successor (derived, two parts):
      (a) ANKLE DORSIFLEXION: bind legs point forward (sitting bear); hip
          flexion of 90 deg leaves the foot pointing DOWN (toe pole). The
          ankle must dorsiflex the same 90 deg so the foot's long axis is
          horizontal -- how any standing body's foot meets a floor.
      (b) FLAT SOLE: passive standing needs a flat contact patch containing
          the COM projection with margin. Derived size: patch must cover
          COM_z=-4.1 mm vs foot-center projection with >=10 mm margin ->
          flat half-width >= ~19 mm -> clip the foot ellipsoid at
          y = c_y - 0.8*r_y (flat 33 x 38 mm). Recorded in cad_core PRIMS
          as sole=0.8 on the feet; the sampler re-verifies conservation.
  RUN 4 (2026-08-22): STILL TIPPED -- slowly forward this time (65 deg in
    3 s). Statics were centered (zero-tilt residual 0.02 N.m, sampling
    noise) yet the sim tilt grew monotonically from 0.04 deg. The rock
    curve settled it: d_tau/d_theta = +2.5 N.m/rad > 0 -- statically
    UNSTABLE even with flat soles. Cause: the classic inverted-pendulum
    term. Rotating the body by theta about its COM swings the sole
    backward under it, so the wall's up-force acts h*theta behind the COM
    line: a TIPPING moment W*h*theta = 24.6*0.165*theta = +4.05*theta.
    The flat patch's restoring term (spring rocking stiffness
    K_rock = K_S*sum(dz^2) over the engaged sole, measured ~1.5) was too
    weak to cancel it. Stability condition:
        K_S * sum(dz^2)  >  W * h          (rocking beats top-heaviness)
    Successor: K_S is no longer derived from an arbitrary 0.5 mm sink --
    it is derived FROM THE STABILITY CONDITION with a 2x margin:
        K_S = 2 * W * h / sum(dz^2), iterated quasi-statically because the
        engaged set (and hence sum(dz^2)) depends on K_S itself. Converged
    value is computed in code below at runtime, then dt follows from the
    fastest wall oscillator as before.
  RUN 5 (2026-08-22): PASS -- THE BEAR STANDS. K_S converged to 487.5 N/m
    (K_rock = 8.24 N.m/rad >= 2x W*h = 8.24); 159 sole packets engaged at
    a 0.69 mm equilibrium sink. Settled metrics: penetration 0.705 mm,
    tilt 0.05 deg, COM drift 0.00 mm, final-0.5s motion 0.000 mm. The wall
    dashpots dissipate the 5 mm drop energy (~12 mJ) by design -- energy
    is not conserved across the settle, and should not be.
  - Start: lowest packet 5 mm above the floor, bear upright, zero velocity.
  - PASS: after 3 s settle, (a) max penetration < 1.0 mm, (b) COM horizontal
    drift < 5 mm from start, (c) tilt angle < 5 deg, (d) net motion over the
    final 0.5 s < 1 mm (settled, not bouncing).
  - FAIL (falsifier): it tips (tilt >= 5 deg) or penetrates >= 1 mm ->
    the standing pose is not balanced on these feet; successor = widen stance
    or shift COM, DERIVED from the measured torque, recorded in the doc.

  .venv-gs/Scripts/python.exe tools/kernel_stand.py
Output: metrics + .tmp/kernel_stand.png (front/side of the settled cloud).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
NPZ = ROOT / "models" / "cad_bear" / "bear_packets.npz"

G = 9.81
LEG_ANGLE = np.deg2rad(90.0)   # derived: vertical legs -- zero hip torque; COM 7.8mm inside patch (RUN 2 fix)
HIP_L = np.array([0.048, -0.095, 0.010])
HIP_R = np.array([-0.048, -0.095, 0.010])
ANKLE_L = np.array([0.058, -0.098, 0.075])   # leg capsule b-end (bind frame)
ANKLE_R = np.array([-0.058, -0.098, 0.075])
START_GAP = 0.005
DELTA_EQ = 0.0005                # derived equilibrium penetration, m
SETTLE_T = 3.0


def pose_standing(pos: np.ndarray, parts: np.ndarray) -> np.ndarray:
    """Standing pose, derived (RUN 3 successor): hip flexion +90 deg about the
    hip pivot AND ankle dorsiflexion -90 deg about the ankle (leg b-end), so
    the legs hang vertical (zero hip torque) and the flat soles face the
    floor. Rotations about parallel X axes: dorsiflex in bind, then flex."""
    out = pos.copy()
    for hip, ankle, leg, foot in (
            (HIP_L, ANKLE_L, "leg_L", "foot_L"),
            (HIP_R, ANKLE_R, "leg_R", "foot_R")):
        fm = np.isin(parts, [foot])
        q = out[fm] - ankle                     # dorsiflex -90 about ankle
        out[fm, 1] = ankle[1] + q[:, 2] * 1.0   # R_x(-90): y' = z, z' = -y
        out[fm, 2] = ankle[2] - q[:, 1] * 1.0
        mask = np.isin(parts, [leg, foot])      # hip flexion +90 about hip
        q = out[mask] - hip
        c, s = np.cos(LEG_ANGLE), np.sin(LEG_ANGLE)
        y = q[:, 1] * c - q[:, 2] * s
        z = q[:, 1] * s + q[:, 2] * c
        out[mask, 1] = y + hip[1]
        out[mask, 2] = z + hip[2]
    return out


def main() -> int:
    d = np.load(NPZ)
    pos = d["pos"].astype(np.float64)
    mass = d["mass"].astype(np.float64)
    parts = d["part"]
    M = float(mass.sum())

    pos = pose_standing(pos, parts)
    pos[:, 1] -= pos[:, 1].min() - START_GAP   # lowest packet 5 mm over floor

    # derived wall stiffness (RUN 4): from the ROCKING-STABILITY condition,
    # not an arbitrary sink depth. Quasi-static iteration:
    #   given K_S, find the sink where the wall carries W, measure the
    #   engaged sole's sum(dz^2); require K_S*sum(dz^2) = 2*W*h (2x margin
    #   over the inverted-pendulum term W*h). Iterate: engagement depends
    #   on K_S. h = COM height above the sole.
    W = M * G
    pos0 = pos.copy()
    pos0[:, 1] -= START_GAP                     # sole exactly at the floor
    com0s = np.average(pos0, axis=0, weights=mass)
    h_com = float(com0s[1])                     # COM height over the sole
    K_S = W / (500 * 0.001)                     # seed
    for _ in range(8):
        # quasi-static equilibrium sink for this K_S
        lo_s, hi_s = 0.0, 0.02
        for _ in range(40):
            mid = 0.5 * (lo_s + hi_s)
            pen = np.maximum(0.0, mid - np.maximum(0.0, pos0[:, 1]))
            if (K_S * pen).sum() >= W:
                hi_s = mid
            else:
                lo_s = mid
        pen = np.maximum(0.0, hi_s - np.maximum(0.0, pos0[:, 1]))
        engaged = pen > 0
        dz = pos0[engaged, 2] - np.average(pos0[engaged, 2],
                                           weights=mass[engaged])
        sdz2 = float((dz ** 2).sum())
        K_new = 2.0 * W * h_com / sdz2
        if abs(K_new - K_S) / K_S < 0.02:
            K_S = K_new
            break
        K_S = K_new
    DELTA_EQ_RUN = float(W / (K_S * max(int(engaged.sum()), 1)))
    n_eff = int(engaged.sum())
    print(f"stability-derived wall: K_S={K_S:.1f} N/m  engaged={n_eff}  "
          f"eq.sink={hi_s*1000:.3f} mm  sum(dz^2)={sdz2:.4f} m^2  "
          f"K_rock={K_S*sdz2:.2f} vs W*h={W*h_com:.2f} N.m/rad")
    # contact band: only packets within 8 cm of the sole can ever touch
    y_min = float(pos[:, 1].min())
    band = pos[:, 1] < y_min + 0.08
    m_min = float(mass[band].min())
    omega = np.sqrt(K_S / m_min)              # fastest engaging oscillator
    dt = 0.1 * 2 * np.pi / omega
    steps = int(SETTLE_T / dt)
    print(f"M={M:.3f} kg  K_S={K_S:.3e} N/m per packet  "
          f"band={int(band.sum())}  m_min={m_min:.2e} kg  "
          f"dt={dt:.2e} s  steps={steps}")

    # rigid-body state
    com = np.average(pos, axis=0, weights=mass)
    rel = pos - com
    I = np.zeros((3, 3))                      # inertia tensor about COM (rest)
    I[0, 0] = np.sum(mass * (rel[:, 1]**2 + rel[:, 2]**2))
    I[1, 1] = np.sum(mass * (rel[:, 0]**2 + rel[:, 2]**2))
    I[2, 2] = np.sum(mass * (rel[:, 0]**2 + rel[:, 1]**2))
    I[0, 1] = I[1, 0] = -np.sum(mass * rel[:, 0] * rel[:, 1])
    I[0, 2] = I[2, 0] = -np.sum(mass * rel[:, 0] * rel[:, 2])
    I[1, 2] = I[2, 1] = -np.sum(mass * rel[:, 1] * rel[:, 2])

    R = np.eye(3)                             # orientation
    v = np.zeros(3)                           # linear velocity
    wv = np.zeros(3)                          # angular velocity (world)
    com0 = com.copy()
    track = []

    rel_band = rel[band]
    mass_band = mass[band]
    # body-level Kelvin-Voigt constants, derived from measured geometry (RUN 3):
    # normal bounce mode: M on K_tot = K_S*N_eff -> critical dashpot c_n
    K_tot = K_S * n_eff
    c_n = 2.0 * np.sqrt(K_tot * M)
    # rocking modes: pitch (about x) / roll (about z); wall gives
    # K_rock,x = K_S*sum(dz^2), K_rock,z = K_S*sum(dx^2) over the engaged band
    sole = pos[:, 1] < y_min + 2 * DELTA_EQ          # equilibrium engagement band
    dx = pos[sole, 0] - np.average(pos[sole, 0], weights=mass[sole])
    dz = pos[sole, 2] - np.average(pos[sole, 2], weights=mass[sole])
    K_rock_x = K_S * float((dz ** 2).sum())          # pitch stiffness
    K_rock_z = K_S * float((dx ** 2).sum())          # roll stiffness
    c_r = np.array([2.0 * np.sqrt(K_rock_x * I[0, 0]), 0.0,
                    2.0 * np.sqrt(K_rock_z * I[2, 2])])
    print(f"K_tot={K_tot:.3e} N/m  c_n={c_n:.2f} N.s/m  "
          f"K_rock=({K_rock_x:.2f},{K_rock_z:.2f}) N.m/rad  c_r={c_r.round(3)}")
    for k in range(steps):
        # only the contact band can touch the wall; gravity's torque about
        # the COM is exactly zero (sum m_i r_i = 0), so torque = wall only
        wb = (R @ rel_band.T).T + com         # band world positions
        pen = -wb[:, 1]
        contact = pen > 0
        Fnet = np.array([0.0, -M * G, 0.0])   # DRAW: gravity (whole body)
        tau = np.zeros(3)
        if contact.any():                     # RESISTANCE: the floor's wall
            r = wb[contact] - com
            Fy = K_S * pen[contact]           # pure spring per packet...
            Fnet[1] += max(0.0, float(Fy.sum()) - c_n * v[1])  # body dashpot, no pull
            tau = np.cross(r,
                           np.column_stack([np.zeros(contact.sum()),
                                            Fy, np.zeros(contact.sum())])).sum(0)
            tau -= c_r * wv                   # critical rocking dashpot
        v += (Fnet / M) * dt
        com += v * dt
        Iw = R @ I @ R.T                      # inertia in the world frame
        wv += np.linalg.solve(Iw, tau) * dt
        # integrate orientation: exponential map of wv*dt
        th = np.linalg.norm(wv) * dt
        if th > 0:
            ax = wv / np.linalg.norm(wv)
            Km = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
            dR = np.eye(3) + np.sin(th) * Km + (1 - np.cos(th)) * Km @ Km
            R = dR @ R
        if k % max(1, steps // 60) == 0:
            track.append((k * dt, com.copy(), R.copy(),
                          float(pen.max()) if contact.any() else 0.0))

    # metrics
    world = (R @ rel.T).T + com
    pen_max = float((-world[:, 1]).max())
    up = R @ np.array([0, 1.0, 0])
    tilt = float(np.rad2deg(np.arccos(np.clip(up[1], -1, 1))))
    drift = float(np.linalg.norm(com[[0, 2]] - com0[[0, 2]]))
    half = len(track) - int(0.5 / SETTLE_T * len(track))
    tail = track[max(half - 1, 0):]
    move = max(float(np.linalg.norm(t[1] - tail[0][1])) for t in tail) if tail else 0.0

    ok = pen_max < 0.001 and tilt < 5.0 and drift < 0.005 and move < 0.001
    print(f"penetration_max = {pen_max*1000:.3f} mm  (<1.0)")
    print(f"tilt            = {tilt:.2f} deg  (<5)")
    print(f"COM drift       = {drift*1000:.2f} mm  (<5)")
    print(f"final-0.5s move = {move*1000:.3f} mm  (<1)")
    print("M2 NUMBERS:", "PASS -- THE BEAR STANDS" if ok else "FALSIFIER FIRED -- it tips or sinks")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 6))
    for ax, (a1, a2, t) in zip(axes, [(0, 1, "front"), (2, 1, "side")]):
        ax.scatter(world[:, a1], world[:, a2], s=0.3, c="peru", rasterized=True)
        ax.axhline(0, color="k", lw=1)
        ax.set_aspect("equal"); ax.set_title(f"settled {t}, tilt={tilt:.1f} deg")
    plt.tight_layout(); plt.savefig(ROOT / ".tmp" / "kernel_stand.png", dpi=110)
    print("WROTE .tmp/kernel_stand.png")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
