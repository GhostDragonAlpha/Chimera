#!/usr/bin/env python3
"""THE HEIGHT-HOLD DERIVATION (wave 27, receipt_wave27.json): the constants of
THE HIND EXTENSION LAW -- the height-hold feed-forward that owns the sinking
shoulder.

THE MEMBRANE (measured on the byte-reproduced wave-26 baseline, see the
receipt): the assembly descends at ~0.4g net through the whole walked life;
the shoulder sink decomposes into the BASE drop (110%) plus the pitch
coupling (-10%); the drop is the hind stance equilibrium fold (the wave-23
deflection physics: error = tau_load/kp growing with the recede lever), NOT
the designed tables (2.6 mm of the 78.4 mm).  The law: at a derived height
emergency the hind stance targets take ff = tau_applied/kp (the machinery's
own last torque over its own gain), so the actual returns to the designed
pose where the wave-8 load book closes (0.881 <= 1).

This script derives the emergency's two constants from the scene's OWN model
bytes plus the reproduced baseline trace:

  h_crit   -- the shoulder-min height at which the adopted seat (the wave-24
              maximum-authority construction, the machinery's exact rule:
              the +/- 1 mm authority sample, the 42-step bisection to
              D = dmax, branch -1) first exits the joint walls on the
              reproduced baseline.  Validated against the run's own F-G23
              first violations (L@104, R@98).
  tau_settle -- THE QUALIFIED SERVO'S OWN DECAY CONSTANT: the ff makes the
              hind target the designed pose, so the actual's error decays at
              the qualified PD's envelope e^(-zeta*omega_n*t) -- the
              derivation's own constants (zeta 0.8, f_s 4.0 Hz), zero new
              free numbers.  The stop distance is the envelope's integral:
              v_fire * tau_settle.

  kSinkRateMax -- the max measured per-tick shoulder-min sink on the
              reproduced baseline [60,105] (the mined constant, the
              wave-26 kDiveRateMax pattern).

THE FLOOR (the turnaround arithmetic, the wave-26 kWaitFloor shape):
  kHeightFloor = 2*kSinkRateMax + kSinkRateMax*tau_settle_ticks
  -- one full sink-tick of pre-fire integration, one full sink-tick of
  standing margin, plus the envelope's stop distance at the worst measured
  rate.  At the worst fire the seat-critical height is never crossed, by
  the envelope's construction.

Outputs derived_height_hold.json (the scene authors the recipe keys from
it; the controller consumes the keys, absent -> byte-identical legacy).
"""
import json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VAL = Path(__file__).resolve().parent
SCENE = ROOT / '.tmp' / 'gait-walker' / 'scene.json'
TRACE = ROOT / '.tmp' / 'baseline_trace.log'

# ---------------------------------------------------------------- fore chain
# The machinery's own bytes (the F-G23 chain census line / the scene model):
L1 = 0.125          # fore_L1_ (humerus)
RHO = 0.136324      # fore_rho_ (the paw polar radius: |(0.031, -0.132753)|)
BETA = math.atan2(-0.132753, 0.031)   # fore_beta_
MOUNT = (0.2689, -0.1331)             # fore_mount_local_ (pelvis frame)
WALL = 1.600                          # the scene joint walls, sh and el
BRANCH = -1                           # ik_branch_ (both legs, wave-23)
DMAX = L1 + RHO
TICK_HZ = 300.0
ZETA, FS_HZ = 0.8, 4.0                # the qualified PD's own constants
OMEGA_N = 2 * math.pi * FS_HZ
TAU_SETTLE_S = 1.0 / (ZETA * OMEGA_N)  # the error envelope's time constant
TAU_SETTLE_TICKS = TAU_SETTLE_S * TICK_HZ

def pelvis_origin(sh_world, pitch):
    c, s = math.cos(pitch), math.sin(pitch)
    return (sh_world[0] - (c * MOUNT[0] - s * MOUNT[1]),
            sh_world[1] - (s * MOUNT[0] + c * MOUNT[1]))

def to_shoulder_local(p_world, sh_world, pitch):
    """fore_ik's exact read: (R^T (paw - pelvis_origin)) - mount."""
    c, s = math.cos(pitch), math.sin(pitch)
    ox, oy = pelvis_origin(sh_world, pitch)
    rx, ry = p_world[0] - ox, p_world[1] - oy
    return (c * rx + s * ry - MOUNT[0], -s * rx + c * ry - MOUNT[1])

def fore_ik_raw(dx, dy):
    """fore_ik_at's exact math (unclamped), shoulder-local pelvis frame."""
    D = math.hypot(dx, dy)
    if D > DMAX * (1 - 1e-12) or D < abs(L1 - RHO) + 1e-9:
        Dc = min(max(D, abs(L1 - RHO) + 1e-9), DMAX * (1 - 1e-12))
        dx, dy, D = dx * Dc / D, dy * Dc / D, Dc
    ca = (D * D + L1 * L1 - RHO * RHO) / (2.0 * D * L1)
    th1 = math.atan2(dy, dx) + BRANCH * math.acos(max(-1.0, min(1.0, ca)))
    q1 = th1 + math.pi / 2
    ex, ey = dx - L1 * math.cos(th1), dy - L1 * math.sin(th1)
    q2 = math.atan2(ey, ex) - q1 - BETA
    return q1, q2, D

def headroom(dx, dy):
    q1, q2, D = fore_ik_raw(dx, dy)
    return min(WALL - abs(q1), WALL - abs(q2)), q1, q2, D

def seat_for(paw_world, sh_world, pitch):
    """THE WAVE-24 SEAT, the machinery's exact construction, at a state."""
    lx, ly = to_shoulder_local(paw_world, sh_world, pitch)
    hp, *_ = headroom(lx + 1e-3, ly)
    hm, *_ = headroom(lx - 1e-3, ly)
    d = 1.0 if hp >= hm else -1.0
    lo, hi = 0.0, 2 * DMAX
    for _ in range(42):
        mid = (lo + hi) / 2
        _, _, D = fore_ik_raw(lx + d * mid, ly)
        if D < DMAX: lo = mid
        else: hi = mid
    edge = (lo + hi) / 2
    h, q1, q2, D = headroom(lx + d * edge, ly)
    return {'seat_local': (lx + d * edge, ly), 'headroom': h,
            'q1': q1, 'q2': q2, 'D': D, 'dir': d}

# ---------------------------------------------------------------- trace mine
dvf = re.compile(r'\[dvf\] t=(\d+) leg=(\d) mode=(\d) tgt=\(([-\d.]+),([-\d.]+)\) '
                 r'sh=\(([-\d.]+),([-\d.]+)\) D=([-\d.]+) off=([+\-\d.]+) hr=([-\d.]+) '
                 r'q1a=([-\d.]+) q1u=([-\d.]+) q2a=([-\d.]+) q2u=([-\d.]+) pins=(\d+) fol=(\d+)')
dv = re.compile(r'\[dv\] t=(\d+) ptq=([-\d.]+) ptgt=([-\d.]+) pang=([-\d.]+)')

def mine():
    lines = TRACE.read_text(encoding='utf-8', errors='replace').splitlines()
    first = min(i for i, l in enumerate(lines) if l.startswith('WALK REFUSED'))
    F, P = {}, {}
    for l in lines[:first]:
        m = dvf.match(l)
        if m:
            t, leg = int(m.group(1)), int(m.group(2))
            F.setdefault(t, {})[leg] = dict(
                mode=int(m.group(3)),
                tgtx=float(m.group(4)), tgty=float(m.group(5)),
                shx=float(m.group(6)), shy=float(m.group(7)),
                D=float(m.group(8)), hr=float(m.group(10)),
                q1u=math.radians(float(m.group(12))),   # printed deg -> rad
                q2u=math.radians(float(m.group(14))))
            continue
        m = dv.match(l)
        if m:
            P[int(m.group(1))] = math.radians(float(m.group(4))); continue
    return F, P

F, P = mine()

DMIN = abs(L1 - RHO)
# =========================================== 1. THE F-G23(b) census, reproduced
# The census's own formula on the STANCE ticks: the adopted target's
# unclamped walls margins (m1, m2) and the annulus margin (md).
print("== the F-G23(b) stance-target admissibility, reproduced vs measured (L@104, R@98) ==")
first_viol, series = {}, {}
for leg in (0, 1):
    S = (-WALL, WALL)
    for t in sorted(F):
        if t < 60: continue
        st = F[t][leg]
        if st['mode'] != 0: continue
        m1 = min(st['q1u'] - S[0], S[1] - st['q1u'])
        m2 = min(st['q2u'] - S[0], S[1] - st['q2u'])
        md = min(st['D'] - DMIN, DMAX - st['D'])
        series[(leg, t)] = (m1, m2, md)
        if (m1 < 0 or m2 < 0 or md < 0) and leg not in first_viol:
            first_viol[leg] = (t, st['shy'], m1, m2, md)
print(f"march first_viol: L@{first_viol.get(0, ('-',))[0]}  R@{first_viol.get(1, ('-',))[0]}")
print("F-G23 measured: L@104, R@98")
for leg in (0, 1):
    row = []
    for t in (92, 96, 98, 100, 102, 104):
        if (leg, t) in series:
            m1, m2, md = series[(leg, t)]
            row.append(f"t{t}: sh={F[t][leg]['shy']:.4f} m1={m1:+.3f} m2={m2:+.3f} md={md*1000:+.2f}mm")
    print('  ' + '\n  '.join(row))

# ============================== 2. h_crit: the first seat-death shoulder height
crit = max(first_viol[0][1], first_viol[1][1])
print(f"\nh_crit (the first seat-death shoulder-min height, conservative) = {crit:.6f} m "
      f"(L's crossing at {first_viol[0][1]:.6f}, R's at {first_viol[1][1]:.6f})")

# ============================================ 3. the sink rate (the trigger v)
shmin = {t: min(F[t][0]['shy'], F[t][1]['shy']) for t in F}
rates = [(t, shmin[t - 1] - shmin[t]) for t in sorted(shmin) if 61 <= t <= 104]
ksink = max(r for _, r in rates)
tmax = max(rates, key=lambda p: p[1])[0]
print(f"kSinkRateMax = {ksink:.6f} m/tick at [{tmax-1},{tmax}] ({ksink*TICK_HZ:.4f} m/s)")

# ============================== 4. the floor and the trigger replay (predict)
floor = 2 * ksink + ksink * TAU_SETTLE_TICKS
print(f"tau_settle = {TAU_SETTLE_TICKS:.2f} ticks; kHeightFloor = {floor * 1000:.2f} mm")
print("\n== the trigger replay on the reproduced baseline (the fire prediction) ==")
print("the floor is the CONSTANT worst-rate form: 2*kSinkRateMax + kSinkRateMax*tau_settle")
fire_t = None
for t in sorted(shmin):
    if t < 62: continue
    v = (shmin[t - 1] - shmin[t]) * TICK_HZ
    margin = shmin[t] - crit
    if fire_t is None and margin <= floor:
        fire_t = t
        print(f"FIRE predicted at t={t}: sh_min={shmin[t]:.6f} margin={margin*1000:.1f} mm "
              f"<= floor {floor*1000:.2f} mm (the live rate {v:.3f} m/s)")
        break
if fire_t is None:
    print("no fire in the mined life (the trigger stays inert past 105) -- INSPECT")
else:
    # the arrest's honest stop: the LIVE rate at the fire (below the worst rate
    # the floor sized itself with) through the qualified envelope
    v_fire = (shmin[fire_t - 1] - shmin[fire_t]) * TICK_HZ
    stop = v_fire * TAU_SETTLE_S
    print(f"predicted arrest: stop {stop*1000:.1f} mm; "
          f"bottom {(shmin[fire_t] - stop)*1000:.1f} mm vs h_crit {crit*1000:.1f} mm "
          f"(standing margin {(shmin[fire_t] - stop - crit)*1000:.1f} mm)")

json.dump({
    'lane': 'agent/gait-wave27-sinking-shoulder',
    'derived_by': 'derive_height_hold.py (wave 27)',
    'fore_chain': {'L1': L1, 'rho': RHO, 'beta': BETA, 'mount': list(MOUNT),
                   'wall': WALL, 'branch': BRANCH, 'dmax': DMAX},
    'h_crit_m': crit,
    'tau_settle_s': TAU_SETTLE_S, 'tau_settle_ticks': TAU_SETTLE_TICKS,
    'kSinkRateMax_m_per_tick': ksink,
    'floor_m': floor,
    'validation': {'march_first_viol': {('L' if k == 0 else 'R'): {'tick': v[0], 'sh_m': v[1],
                                                                  'm1': v[2], 'm2': v[3], 'md_m': v[4]}
                                                  for k, v in first_viol.items()},
                   'f_g23_measured': {'L': 104, 'R': 98, 'min_annulus_margin_m': -0.00177}},
    'predicted_fire_tick': fire_t,
}, open(VAL / 'derived_height_hold.json', 'w'), indent=1)
print("\nderived_height_hold.json written")
