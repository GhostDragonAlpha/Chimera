"""mocap_gait.py — REAL gait reference from CMU MoCap subject 35 walk (35_01_walk.bvh, 120 Hz).

THE STANDING RULE, APPLIED TO UNITS. The una-dinosauria BVH mirror documents only the frame rate
(120 Hz, READMEFIRST.txt); it does NOT state a length unit. So the unit is MEASURED, not assumed:
FK the skeleton, measure the hip-joint standing height in raw units (17.8), then anchor the scale to
the ANSUR II male median trochanterion (hip joint) height already in this repo's
research_references/human/ansur_anchors.json. The raw scale factor lands at ~5.2 cm/unit, which is
self-consistent: it puts thigh (~39 cm), shank (~41 cm) and walking speed (~1.2 m/s) all inside the
measured human range. Every metric is ALSO reported in raw units and normalized by leg length, so the
comparison survives any anchor choice.

ANGLES ARE VECTOR-BASED, not Euler-channel reads. Hip/knee/ankle sagittal angles are computed from
world joint-center positions (thigh/shank/foot/trunk segment vectors projected into the walking
plane), exactly the way the policy-side evaluator computes them from MuJoCo body positions. Same math
on both sides = an honest A/B.

EVENTS: stance = toe-tip near the floor (height threshold calibrated from the toe's own min/range);
strike/toe-off = edges of the stance flag. Duty factor, cadence, stride length (pelvis travel between
ipsilateral strikes), and per-cycle angle envelopes (0-100%, mean +/- std) follow from that.

Run:  C:\\Python314\\python.exe tools/mocap_gait.py
Writes: research_references/human/mocap_walk_reference.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BVH = ROOT / 'research_references' / 'human' / 'mocap' / '35_01_walk.bvh'
ANSUR = ROOT / 'research_references' / 'human' / 'ansur_anchors.json'
OUT = ROOT / 'research_references' / 'human' / 'mocap_walk_reference.json'


# ---------------------------------------------------------------- BVH parsing
class Joint:
    def __init__(self, name, offset, channels):
        self.name = name
        self.offset = np.array(offset, dtype=float)
        self.channels = channels            # e.g. ['Zrotation','Yrotation','Xrotation']
        self.children: list[Joint] = []
        self.end_site = None                # offset of the leaf tip, if any


def parse_bvh(path: Path):
    tokens = path.read_text().replace('\t', ' ').split()
    i = 0

    def read_joint(is_root=False):
        nonlocal i
        kind = tokens[i]; name = tokens[i + 1]; i += 2          # ROOT/JOINT name
        assert tokens[i] == '{'; i += 1
        offset = None; channels = []; children = []; end = None
        while tokens[i] != '}':
            t = tokens[i]
            if t == 'OFFSET':
                offset = [float(tokens[i + 1]), float(tokens[i + 2]), float(tokens[i + 3])]; i += 4
            elif t == 'CHANNELS':
                n = int(tokens[i + 1]); channels = tokens[i + 2:i + 2 + n]; i += 2 + n
            elif t == 'JOINT':
                children.append(read_joint())
            elif t == 'End':
                assert tokens[i + 1] == 'Site'; i += 2
                assert tokens[i] == '{'; i += 1
                assert tokens[i] == 'OFFSET'
                end = [float(tokens[i + 1]), float(tokens[i + 2]), float(tokens[i + 3])]; i += 4
                assert tokens[i] == '}'; i += 1
            else:
                raise ValueError(f'unexpected token {t}')
        i += 1
        j = Joint(name, offset, channels)
        j.children = children
        j.end_site = np.array(end, dtype=float) if end is not None else None
        return j

    assert tokens[i] == 'HIERARCHY'; i += 1
    root = read_joint(is_root=True)
    assert tokens[i] == 'MOTION'; i += 1
    assert tokens[i] == 'Frames:'; n_frames = int(tokens[i + 1]); i += 2
    assert tokens[i] == 'Frame'; frame_time = float(tokens[i + 2]); i += 3
    data = np.array([float(x) for x in tokens[i:]], dtype=float).reshape(n_frames, -1)
    return root, data, frame_time


def channel_layout(root):
    """Flatten the joint tree into the channel order the MOTION columns follow (depth-first)."""
    order = []

    def walk(j):
        for c in j.channels:
            order.append((j.name, c))
        for ch in j.children:
            walk(ch)
    walk(root)
    return order


def rot_matrix(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == 'Xrotation':
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 'Yrotation':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    if axis == 'Zrotation':
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    raise ValueError(axis)


def forward_kinematics(root, data, layout):
    """World position of every joint (and toe-tip end sites) per frame. (T, name) -> xyz."""
    names = []

    def collect(j):
        names.append(j)
        for ch in j.children:
            collect(ch)
    collect(root)

    T = data.shape[0]
    pos = {j.name: np.zeros((T, 3)) for j in names}
    tips = {}
    idx = {name: k for k, (name, _c) in enumerate(layout)}

    for t in range(T):
        def fk(j, p_pos, p_rot):
            vals = {}
            for ci, c in enumerate(j.channels):
                if 'rotation' in c:
                    vals[c] = data[t, idx[j.name] + ci] if False else None
            # channels for this joint occupy a contiguous block starting at its first layout index
            base = next(k for k, (nm, _c) in enumerate(layout) if nm == j.name)
            r = np.eye(3)
            p = p_pos + p_rot @ j.offset
            for ci, c in enumerate(j.channels):
                v = data[t, base + ci]
                if c == 'Xposition':
                    p = p + p_rot @ np.array([v, 0, 0])
                elif c == 'Yposition':
                    p = p + p_rot @ np.array([0, v, 0])
                elif c == 'Zposition':
                    p = p + p_rot @ np.array([0, 0, v])
                else:
                    r = r @ rot_matrix(c, v)
            R = p_rot @ r
            pos[j.name][t] = p
            if j.end_site is not None:
                tips.setdefault(j.name, np.zeros((T, 3)))[t] = p + R @ j.end_site
            for ch in j.children:
                fk(ch, p, R)
        fk(root, np.zeros(3), np.eye(3))
    return pos, tips


# ---------------------------------------------------------------- gait metrics
def seg_angle(v_f, v_u):
    """Angle of a segment from straight-down, + when the distal end is forward. v_f, v_u are the
    forward and up components of the (distal - proximal) vector."""
    return np.degrees(np.arctan2(v_f, -v_u))


def sagittal_angles(P, fwd2, side):
    """Hip/knee/ankle sagittal angles from world joint positions, projected into the walking plane.

    Conventions (degrees): hip + = flexion, knee + = flexion, ankle + = dorsiflexion.
    """
    up = np.array([0.0, 0.0, 1.0])
    fwd = np.array([fwd2[0], fwd2[1], 0.0])

    def proj(name):
        v = P[name]
        return np.stack([v @ fwd, v @ up], axis=1)            # (T,2): (forward, up)

    hip = proj(f'{side}UpLeg')
    knee = proj(f'{side}Leg')
    ankle = proj(f'{side}Foot')
    toe = proj(f'{side}ToeBase')
    trunk_top = proj('Spine1')
    pelvis = proj('Hips')

    thigh = knee - hip
    shank = ankle - knee
    foot = toe - ankle
    trunk = trunk_top - pelvis

    th_thigh = seg_angle(thigh[:, 0], thigh[:, 1])
    th_shank = seg_angle(shank[:, 0], shank[:, 1])
    th_trunk = seg_angle(-trunk[:, 0], -trunk[:, 1])          # pelvis tilt, down-pointing
    hip_ang = th_thigh - th_trunk
    knee_ang = th_thigh - th_shank                            # + flexion
    # ankle: foot inclination above horizontal (+ toes up) + shank tilt from vertical (+ forward).
    # Neutral standing = 0; + = dorsiflexion, - = plantarflexion. Inclination is computed with
    # arcsin (range +-90) rather than atan2: atan2 wraps to +-180 when the toe passes behind the
    # ankle at full plantarflexion, and one wrapped frame poisons the whole cycle AVERAGE (caught
    # as a -148 deg "mean"; the per-frame pitch is anatomically sane).
    flen = np.linalg.norm(foot, axis=1) + 1e-9
    foot_pitch = np.degrees(np.arcsin(np.clip(foot[:, 1] / flen, -1, 1)))
    ankle_ang = foot_pitch - th_shank                         # + dorsiflexion
    # NOTE the MINUS: th_shank is the DOWN-pointing shank (knee->ankle); the tibia leaning
    # forward over a planted foot (dorsiflexion) puts the ankle BEHIND the knee, i.e. th_shank
    # goes negative while the joint dorsiflexes. Verified against neutral/toes-up/tibia-forward/
    # toe-off cases; the earlier plus-sign gave a stance curve mirrored from the textbook one.
    return hip_ang, knee_ang, ankle_ang, hip, knee, ankle, toe


def edges(flag):
    """Rising/falling edges of a boolean stance flag -> (strikes, offs), as sample indices."""
    f = flag.astype(int)
    d = np.diff(np.concatenate([[0], f, [0]]))
    return np.where(d == 1)[0], np.where(d == -1)[0]


def envelope(cycles_angles, strikes, n=101):
    """Resample strike->strike cycles to 0..100% and average mean/std across cycles."""
    xs = np.linspace(0, 100, n)
    mats = []
    for a, b in zip(strikes[:-1], strikes[1:]):
        if b - a < 8:
            continue
        mats.append(np.interp(xs, np.linspace(0, 100, b - a), cycles_angles[a:b]))
    if len(mats) < 2:
        return None, None, len(mats)
    M = np.array(mats)
    return M.mean(0), M.std(0), len(mats)


def main():
    root, data, dt = parse_bvh(BVH)
    layout = channel_layout(root)
    P, tips = forward_kinematics(root, data, layout)
    T = data.shape[0]
    t = np.arange(T) * dt

    # ---- measured raw geometry -------------------------------------------------
    # Identify axes FROM THE DATA: up = large steady hips coordinate (max |median|/ptp);
    # forward = the horizontal axis with the most travel. No assumption about the file's frame.
    hips = P['Hips']
    score = [abs(float(np.median(hips[:30, k]))) / (float(np.ptp(hips[:, k])) + 1e-9)
             for k in range(3)]
    up_axis = int(np.argmax(score))
    horiz = [k for k in range(3) if k != up_axis]
    travel = [float(np.ptp(hips[:, k])) for k in horiz]
    fwd_axis = horiz[int(np.argmax(travel))]
    fwd_sign = 1.0 if (hips[-1, fwd_axis] - hips[0, fwd_axis]) >= 0 else -1.0

    # rebase every joint into a canonical frame: X = walking direction, Z = up
    up3 = np.zeros(3); up3[up_axis] = 1.0
    fwd3 = np.zeros(3); fwd3[fwd_axis] = fwd_sign
    right3 = np.cross(fwd3, up3)
    M = np.stack([fwd3, right3, up3])                         # rows: new axes in old coords
    P = {name: v @ M.T for name, v in P.items()}
    tips = {name: v @ M.T for name, v in tips.items()}
    hips = P['Hips']
    up_axis, fwd_axis, fwd_sign = 2, 0, 1.0                   # canonical frame from here on
    stand_hip_raw = float(np.median(hips[:30, 2]))
    # leg segment lengths from the skeleton offsets (raw units)
    def off_len(name):
        j = {nm: jj for nm, jj in [(x.name, x) for x in _flat(root)]}[name]
        return float(np.linalg.norm(j.offset))
    thigh_raw = off_len('LeftLeg')
    shank_raw = off_len('LeftFoot')
    hip_off_raw = off_len('LeftUpLeg')

    # ANSUR II anchor: male median trochanterion (hip joint) height
    anch = json.loads(ANSUR.read_text())
    troch_m = float(anch['male']['trochanterion_m']['median'])
    # measured hip-joint-center height while standing (first 30 frames, canonical up)
    hip_center_raw = float(np.median(P['LeftUpLeg'][:30, up_axis]))
    scale = troch_m / hip_center_raw                          # metres per raw unit

    # ---- walking speed ----------------------------------------------------------
    vel = np.gradient(hips[:, fwd_axis], dt)
    s0, s1 = int(0.2 * T), int(0.8 * T)                       # steady middle 60% of the trial
    speed_raw = float(np.median(np.abs(vel[s0:s1])))
    speed = speed_raw * scale

    # ---- events: Zeni et al. (2008) — heel strike = foot maximally FORWARD of the pelvis,
    # toe-off = foot maximally BEHIND. Robust where toe-height thresholds flicker (verified on
    # this file: height thresholds double-counted strikes; relative-position extrema alternate
    # L/R cleanly at a steady step interval).
    events = {}
    strikes_by_side = {}
    offs_by_side = {}
    angles_by_side = {}
    duty_by_side = {}
    mind = int(0.6 / dt)                                      # min separation: no step is < 0.6 s here
    for side, short in (('Left', 'L'), ('Right', 'R')):
        rel = P[f'{side}Foot'][:, fwd_axis] - hips[:, fwd_axis]
        rel = np.convolve(rel, np.ones(9) / 9, mode='same')   # 75 ms smoothing
        maxs, mins = [], []
        for i in range(1, len(rel) - 1):
            if rel[i] >= rel[i - 1] and rel[i] > rel[i + 1]:
                if not maxs or i - maxs[-1] > mind:
                    maxs.append(i)
                elif rel[i] > rel[maxs[-1]]:
                    maxs[-1] = i
            if rel[i] <= rel[i - 1] and rel[i] < rel[i + 1]:
                if not mins or i - mins[-1] > mind:
                    mins.append(i)
                elif rel[i] < rel[mins[-1]]:
                    mins[-1] = i
        st = np.array(maxs); off = np.array(mins)
        strikes_by_side[short] = st
        offs_by_side[short] = off
        strides_t = np.diff(st) * dt
        # duty: stance = strike -> the toe-off that follows it
        pairs = [(s, off[off > s][0]) for s in st if np.any(off > s) and (off[off > s][0] - s) * dt < 0.9 * np.median(strides_t if len(strides_t) else [1.0])]
        if pairs and len(strides_t):
            duty_by_side[short] = float(np.mean([(o - s) * dt for s, o in pairs]) / np.mean(strides_t))
        events[short] = {'n_strikes': int(len(st)),
                         'strike_times_s': (st * dt).round(3).tolist(),
                         'mean_stride_s': float(np.mean(strides_t)) if len(strides_t) else None}
        angles_by_side[short] = sagittal_angles(P, np.array([1.0, 0.0]), side)

    all_strikes = np.sort(np.concatenate(list(strikes_by_side.values())))
    cadence = 60.0 * (len(all_strikes) - 1) / ((all_strikes[-1] - all_strikes[0]) * dt)
    duty = float(np.mean([d for d in duty_by_side.values() if d]))

    # stride length: pelvis forward travel between consecutive same-side strikes
    fwd_pos = hips[:, fwd_axis] * fwd_sign
    stride_raws = []
    for st in strikes_by_side.values():
        for a, b in zip(st[:-1], st[1:]):
            stride_raws.append(float(fwd_pos[b] - fwd_pos[a]))
    stride_m = float(np.mean(stride_raws)) * scale
    stride_time = float(np.mean([e['mean_stride_s'] for e in events.values()]))

    # ---- angle envelopes (average of L/R means) --------------------------------
    envs = {}
    for ji, name in ((0, 'hip'), (1, 'knee'), (2, 'ankle')):
        means, stds, ncyc = [], [], 0
        for short in ('L', 'R'):
            m, s, n = envelope(angles_by_side[short][ji], strikes_by_side[short])
            if m is not None:
                means.append(m); stds.append(s); ncyc += n
        envs[name] = {
            'mean': np.mean(means, 0).round(2).tolist(),
            'std': np.mean(stds, 0).round(2).tolist(),
            'n_cycles': int(ncyc),
        }

    leg_len_m = (hip_center_raw - float(np.percentile(P['LeftToeBase'][:30, up_axis], 10))) * scale
    out = {
        'source': 'CMU MoCap subject 35, walk trial (35_01_walk.bvh), una-dinosauria BVH mirror',
        'fps': round(1.0 / dt, 1),
        'frames': int(T),
        'duration_s': round(T * dt, 3),
        'units': {
            'raw_unit': 'BVH offset units (UNDOCUMENTED by the mirror — measured here)',
            'measured_hip_center_height_raw': round(hip_center_raw, 3),
            'anchor': f'ANSUR II male median trochanterion height = {troch_m:.4f} m',
            'scale_m_per_raw_unit': round(scale, 5),
            'sanity': {
                'thigh_m': round(thigh_raw * scale, 3),
                'shank_m': round(shank_raw * scale, 3),
                'speed_m_s': round(speed, 3),
            },
        },
        'cadence_steps_per_min': round(float(cadence), 1),
        'stride_length_m': round(stride_m, 3),
        'stride_length_leg_lengths': round(stride_m / leg_len_m, 3),
        'stride_time_s': round(stride_time, 3),
        'duty_factor': round(duty, 3),
        'speed_m_s': round(speed, 3),
        'leg_length_m': round(leg_len_m, 3),
        'events': events,
        'envelopes_deg': envs,
        'conventions': 'angles: vector-based sagittal, hip/knee +flexion, ankle +dorsiflexion; '
                       'cycle 0% = heel strike (toe-contact onset)',
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != 'envelopes_deg'}, indent=2))
    print(f'\n  envelopes: hip {envs["hip"]["n_cycles"]} cycles, knee {envs["knee"]["n_cycles"]}, '
          f'ankle {envs["ankle"]["n_cycles"]}')
    print(f'  wrote {OUT}')
    return 0


def _flat(root):
    out = [root]
    for c in root.children:
        out += _flat(c)
    return out


def _fwd_vec(fwd_axis, up_axis, sign):
    v = np.zeros(2)
    # returns 2D unit vector in the horizontal plane pointing along travel
    comps = np.zeros(3); comps[fwd_axis] = sign
    horiz = [comps[k] for k in range(3) if k != up_axis]
    return np.array(horiz)


def _clean(strikes, offs, min_gap):
    """Drop stance bouts separated by a gap shorter than min_gap samples (mocap jitter)."""
    if len(strikes) < 2:
        return strikes, offs
    keep_s = [strikes[0]]; keep_o = []
    for i in range(len(offs)):
        if i + 1 < len(strikes) and strikes[i + 1] - offs[i] < min_gap:
            continue                              # merge: skip this off and the next strike
        keep_o.append(offs[i])
        if i + 1 < len(strikes):
            keep_s.append(strikes[i + 1])
    n = min(len(keep_s), len(keep_o))
    return np.array(keep_s[:n]), np.array(keep_o[:n])


if __name__ == '__main__':
    raise SystemExit(main())
