"""walk_numbers.py -- THE WALK'S OWN NUMBERS + F-NO-WALK instrument.

(a) no freeze: consecutive captured frames must differ (jpeg byte hashes);
(b) forward progress: the skinned body's trunk centroid advance vs the
    engine walk's own mapped base dx (>= 0.5x bar);
(c) stepping: per-limb vertical oscillation (zero crossings of the limb
    group centroid's y about its mean) across the walk frames -- >= 2 limbs
    with >= 5 crossings required.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
D = HERE.parents[3] / ".tmp" / "viswalk_dump"
FRAMES = HERE / "frames"

cap = json.loads((HERE / "capture_record.json").read_text(encoding="utf-8"))
per = cap["per_frame"]

# ---- (a) freeze instrument (WALK FRAMES only: the lead-in and end-hold
# phases are declared static holds -- tick 0 and tick 301 repeats) ----
ticks_seq = [f["tick"] for f in per]
first_walk = 0
while first_walk < len(ticks_seq) - 1 and ticks_seq[first_walk + 1] == 0:
    first_walk += 1
first_walk += 1                              # first frame whose tick ADVANCES
last_walk = len(per) - 1
while last_walk > 0 and ticks_seq[last_walk] == 301:
    last_walk -= 1
last_walk += 1
hashes = []
for f in per[first_walk:last_walk]:
    p = FRAMES / ("f%05d.jpg" % f["i"])
    hashes.append(hashlib.sha256(p.read_bytes()).hexdigest()[:16])
identical = sum(1 for a, b in zip(hashes, hashes[1:]) if a == b)
run_max = best = 0
for a, b in zip(hashes, hashes[1:]):
    run_max = run_max + 1 if a == b else 0
    best = max(best, run_max)

# ---- the walk's own numbers ----
Q = np.load(D / "Q.npy")
q0 = Q[0]
dQ = Q - q0
C = np.load(D / "C.npy")
root_scale = float(C[1] / q0[4])
engine_dx = float(dQ[-1, 3])
engine_dy = float(dQ[-1, 4])
mapped_dx = -root_scale * engine_dx   # body forward is -z
mapped_dy = root_scale * engine_dy
n_ticks = len(Q)

# ---- (b) skinned advance: the ROOT PIVOT's neighborhood displacement ----
# (the trunk centroid conflates the translation with the fall rotation about
# C; the pivot neighborhood moves by the translation alone)
POS = np.load(D / "skin_pos.npy", mmap_mode="r")
pos0 = np.load(D / "rest_pos.npy").astype(np.float64)
_near_d = np.linalg.norm(pos0 - C, axis=1)
near = np.argsort(_near_d)[:500]             # the 500 verts nearest the pivot
P0 = np.asarray(POS[0])
P_end = np.asarray(POS[n_ticks - 1])
pivot_delta = P_end[near].mean(axis=0) - P0[near].mean(axis=0)
advance = float(-pivot_delta[2])      # forward = -z
advance_vert = float(pivot_delta[1])

# ---- (c) stepping: per-limb-group detrended y oscillation, stride window ----
# limb pools (fit v3): stride phase = ticks 0..180 (the certified walk's
# living strides; the last ~90 ticks are the refusal collapse)
y0v, z0v, x0v = pos0[:, 1], pos0[:, 2], pos0[:, 0]
limb = (y0v < 0.10) & (z0v >= -0.18)
limb_masks = {
    "foreL": limb & (z0v < 0.0) & (x0v > 0),
    "foreR": limb & (z0v < 0.0) & (x0v <= 0),
    "hindL": limb & (z0v >= 0.0) & (x0v > 0),
    "hindR": limb & (z0v >= 0.0) & (x0v <= 0),
}
STRIDE_END = 180
stepping = {}
for name, m in limb_masks.items():
    if m.sum() < 100:
        stepping[name] = {"verts": int(m.sum()), "note": "too few verts"}
        continue
    ys = []
    for k in range(0, STRIDE_END, 2):  # 90 samples over the stride phase
        c = np.asarray(POS[k][m]).mean(axis=0)
        ys.append(c[1])
    ys = np.array(ys)
    trend = np.convolve(ys, np.ones(15) / 15, mode="same")
    ysd = ys - trend
    crossings = int(np.sum(ysd[:-1] * ysd[1:] < 0))
    amp = float(ysd.max() - ysd.min())
    stepping[name] = {"verts": int(m.sum()), "zero_crossings": crossings,
                      "detrended_y_amplitude_m": round(amp, 4)}
osc_limbs = sum(1 for v in stepping.values()
                if v.get("zero_crossings", 0) >= 5)

out = {
    "schema": "chimera.visible_walk_20260923.walk_numbers.v1",
    "walk_ticks": n_ticks,
    "engine_base_dx_m": round(engine_dx, 4),
    "engine_base_dy_m": round(engine_dy, 4),
    "root_scale": round(root_scale, 5),
    "mapped_forward_m": round(mapped_dx, 4),
    "mapped_vertical_m": round(mapped_dy, 4),
    "skinned_pivot_advance_forward_m": round(advance, 4),
    "skinned_pivot_advance_vertical_m": round(advance_vert, 4),
    "advance_ratio_vs_engine": round(advance / abs(mapped_dx), 4) if mapped_dx else None,
    "advance_note": "pivot-neighborhood (500 nearest verts to C) world displacement over the walk",
    "freeze": {"identical_consecutive_frames": identical,
               "longest_identical_run": best,
               "frames": len(hashes)},
    "stepping": stepping,
    "limbs_oscillating_ge5_crossings": osc_limbs,
    "f_no_walk": {
        "a_no_freeze": identical == 0 and best == 0,
        "b_forward_progress": advance >= 0.5 * abs(mapped_dx),
        "c_stepping": osc_limbs >= 2,
    },
}
(HERE / "walk_numbers.json").write_text(json.dumps(out, indent=1),
                                        encoding="utf-8")
print(json.dumps(out, indent=1))
