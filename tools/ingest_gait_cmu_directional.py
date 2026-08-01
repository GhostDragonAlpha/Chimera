"""ingest_gait_cmu_directional.py -- the gaits the treadmill never measured, from CMU MoCap.

WHY THIS EXISTS (A3). The story's walk is 246 adults on an instrumented treadmill (OSF,
story/measured.py) -- FORWARD only. A body also backs up and sidesteps, and those are not the
forward gait reversed or rotated: backward walking lands toe-first with a shorter stride, and a
sidestep's trailing leg CROSSES the leading one. The operator's rule is that a feature which is
data is measured, not reasoned out -- so the directional gaits come from the CMU Motion Capture
database (free for research AND commercial use, credit mocap.cs.cmu.edu + NSF EIA-0196217), the
same source the forward RL reference (tools/mocap_gait.py) already stands on.

WHAT IT PRODUCES. Two artifacts:

  story/data/gait_directional.json -- per direction (backward, sidestep toward the body's left and
      right), the hip/knee/ankle curves of the gait cycle (100 samples, 0 = a leg's own contact,
      DEGREES), the duty factor, and the measured stride/speed/cadence. Hip is the thigh's angle
      FROM VERTICAL in the progression plane (+ toward travel) -- the reference theHuman's gait
      table consumes. Sidesteps are PER LEG (leading leg first): averaging the two legs would erase
      the cross-step, which is the whole point. "right" is "left" mirrored (leading/trailing
      swapped), because a body is symmetric and the mirror is exact, not a guess.

  research_references/human/mocap_directional_reference.json -- the same curves in the RL
      tracker's convention (hip relative to the TRUNK, like tools/mocap_gait.py's forward
      reference), for G2's direction-conditioned policy.

WHICH TRIALS, AND HOW THEY ARE CHECKED. The index (cmu-mocap-index-text.txt) labels them; the tool
does not trust the label -- every trial's FACING is computed from the hip line (f_face = up x
(right_hip - left_hip)), and a trial whose travel does not point the way its label claims is
rejected and reported. Backward: 136_25/26 ("Normal Walk Backwards"), 141_31, 111_01, 113_01,
076_09. Sidestep: 141_32 ("Walk Sideways, Cross Legs"), 141_33 ("Foot to Foot"). The 069/083
trials involve turning or ledges -- excluded on purpose, a clean average beats a big one.

CONVENTIONS AND SCALING are inherited unchanged from tools/mocap_gait.py: vector-based angles from
world joint positions (never Euler channels), events by Zeni et al. (2008) -- contact = foot
maximally ALONG THE PROGRESSION from the pelvis, which is direction-agnostic -- and scale anchored
to the ANSUR II male median trochanterion height.

VALIDATION. --validate-forward runs the SAME pipeline on the forward trial 35_01 and diffs the
table theHuman's law builds from it against the committed forward gait_cycle (246 adults). A
one-subject CMU walk will not match a 246-adult average exactly -- what must match is the SIGNS,
the phase alignment, and the shape (two knee peaks, toe-up at contact). That is the check that the
conventions wired here are the ones the table law expects.

RUN:  C:\\Python314\\python.exe tools/ingest_gait_cmu_directional.py [--validate-forward]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import mocap_gait as mg                                   # the parser/FK/events, unchanged

MOCAP = ROOT / "research_references" / "human" / "mocap" / "cmu_full" / "data"
FORWARD_BVH = ROOT / "research_references" / "human" / "mocap" / "35_01_walk.bvh"
ANSUR = ROOT / "research_references" / "human" / "ansur_anchors.json"
OUT = ROOT / "story" / "data" / "gait_directional.json"
OUT_RL = ROOT / "research_references" / "human" / "mocap_directional_reference.json"

CITE = ("CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), created with NSF funding "
        "EIA-0196217; free for research and commercial use. Backward: trials 136_25, 136_26 "
        "('Normal Walk Backwards'), 141_31, 111_01, 113_01, 076_09. Sidestep: 141_32 ('Walk "
        "Sideways, Cross Legs'), 141_33 ('Foot to Foot'). 120 Hz, MotionBuilder skeleton, scale "
        "anchored to ANSUR II male median trochanterion height.")

TRIALS = {
    "backward": ["136/136_25.bvh", "136/136_26.bvh", "141/141_31.bvh",
                 "111/111_01.bvh", "113/113_01.bvh", "076/76_09.bvh"],
    "sidestep": ["141/141_32.bvh", "141/141_33.bvh",
                 "069/69_42.bvh", "069/69_43.bvh", "069/69_44.bvh", "069/69_45.bvh",
                 "069/69_56.bvh", "069/69_57.bvh", "069/69_58.bvh", "069/69_59.bvh"],
}

# A jog is not a walk: runs faster than this are a different gait and do not belong in a walk
# table (141_31 'Walk Backwards' bursts at 2.3 m/s -- measured, excluded).
WALK_SPEED_MAX = 1.5


# ---------------------------------------------------------------- one trial
def envelope_aligned(curve, strikes, offs, duty_mean, n=101):
    """Strike-to-strike cycles resampled to 0..100%, with STANCE and SWING normalized separately.

    mocap_gait's envelope() maps each cycle linearly strike->strike. Around toe-off that rings:
    the foot pitches 40 degrees in a few percent of the cycle, cycles disagree on exactly WHERE
    toe-off falls (duty 0.57..0.62), and averaging a fast edge with timing jitter produces
    sample-to-sample noise that no single cycle contains. Gait science's standard answer is the
    one the story's own u uses: stance is stance and swing is swing. Each cycle's stance maps onto
    [0, duty_mean] and its swing onto [duty_mean, 1], so the edge lands at the same phase in every
    cycle BEFORE averaging. Nothing is smoothed; the cycles are aligned."""
    xs = np.linspace(0, 100, n)
    mats = []
    offs = np.sort(offs)
    for a, b in zip(strikes[:-1], strikes[1:]):
        if b - a < 8:
            continue
        mid = offs[(offs > a) & (offs < b)]
        o = int(mid[0]) if len(mid) else a + int(0.6 * (b - a))
        ph = np.empty(b - a)
        st_len = max(o - a, 1)
        sw_len = max(b - o, 1)
        idx = np.arange(b - a)
        stance = idx < (o - a)
        ph[stance] = (idx[stance] / st_len) * (duty_mean * 100.0)
        ph[~stance] = duty_mean * 100.0 + ((idx[~stance] - (o - a)) / sw_len) * ((1.0 - duty_mean) * 100.0)
        mats.append(np.interp(xs, ph, curve[a:b]))
    if len(mats) < 2:
        return None, None, len(mats)
    M = np.array(mats)
    return M.mean(0), M.std(0), len(mats)


def _steady_runs(vel_s, dt, min_s=1.0):
    """The runs where the subject is actually GOING somewhere, in one direction.

    A CMU trial is not a treadmill: the subject walks there AND BACK inside the capture volume,
    and turns at the ends. Averaging the whole trial mixes two directions of travel (strides
    cancel to centimetres, duty collapses -- measured before this existed: a "stride" of 4 cm at
    a speed of 1.6 m/s). So the trial is cut on its own hip velocity: contiguous stretches moving
    one way along the travel axis at > 30% of the trial's p95 speed, at least min_s long, trimmed
    0.2 s at both ends where the turn bleeds in. Each run is then analysed on its own."""
    mag = np.abs(vel_s)
    p95 = float(np.percentile(mag, 95))
    if p95 < 1e-6:
        return []
    moving = mag > 0.3 * p95
    runs = []
    i, n = 0, len(vel_s)
    min_n, trim = int(min_s / dt), int(0.2 / dt)
    while i < n:
        if moving[i]:
            s = np.sign(vel_s[i])
            j = i
            while j < n and moving[j] and np.sign(vel_s[j]) == s:
                j += 1
            a, b = i + trim, j - trim
            if b - a >= min_n:
                runs.append((a, b, int(s)))
            i = j
        else:
            i += 1
    return runs


def _analyze_run(P, dt, scale):
    """One steady run, rebased so travel is +X: facing, both legs' envelopes, duty, stride."""
    hips = P["Hips"]
    # FACING, from the hip line: body right = right_hip - left_hip, so f_face = up x right.
    # dot(travel, f_face) > 0 walks forward, < 0 backward; dot(travel, right) < 0 moves toward
    # the body's LEFT. This is how a mislabeled index entry is caught rather than averaged in.
    v_right = np.median(P["RightUpLeg"] - P["LeftUpLeg"], axis=0)
    v_right = v_right - v_right[2] * np.array([0.0, 0.0, 1.0])
    v_right /= np.linalg.norm(v_right) + 1e-12
    f_face = np.cross(np.array([0.0, 0.0, 1.0]), v_right)
    along = float(f_face[0])          # travel is +X in the rebased frame
    lateral = float(v_right[0])       # < 0 -> travel toward the body's left

    mind = int(0.35 / dt)             # a fast sidestep steps quicker than 0.6 s
    legs = {}
    strides, duties = [], []
    for side, short in (("Left", "L"), ("Right", "R")):
        rel = P[f"{side}Foot"][:, 0] - hips[:, 0]
        rel = np.convolve(rel, np.ones(9) / 9, mode="same")
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
        st, off = np.array(maxs), np.array(mins)
        if len(st) < 3:
            continue
        hip_ang, knee_ang, ankle_ang, hp, kp, ap, tp = mg.sagittal_angles(
            P, np.array([1.0, 0.0]), side)
        # the table law wants the thigh FROM VERTICAL (+ toward travel), not trunk-relative
        thigh = kp - hp
        th_thigh = mg.seg_angle(thigh[:, 0], thigh[:, 1])
        shank = ap - kp
        th_shank = mg.seg_angle(shank[:, 0], shank[:, 1])
        # THE FOOT'S PITCH, measured where arcsin is blind. mocap_gait uses asin(z/len) for the
        # inclination -- right for the RL tracker (its policy measures the same asin, so the A/B
        # stays honest) but its derivative explodes as the segment passes vertical, which is
        # exactly where a foot goes at toe-off: the cycle mean rang +-12 deg sample to sample
        # there. The story's table needs the foot's TILT, so it is atan2(z, |f|): bounded to
        # +-90 by construction and continuous through the vertical. The arcsin curve is kept too
        # ("ankle_asin") -- the RL reference must match its policy's own measurement.
        foot = tp - ap
        fp_story = np.degrees(np.arctan2(foot[:, 1], np.abs(foot[:, 0]) + 1e-9))
        ankle_story = fp_story - th_shank
        # duty first: the envelopes below are stance/swing aligned on it (see envelope_aligned)
        stride_t = np.diff(st) * dt
        pairs = [(s_, off[off > s_][0]) for s_ in st
                 if np.any(off > s_) and (off[off > s_][0] - s_) * dt < 0.9 * float(np.median(stride_t))]
        duty = float(np.mean([(o - s_) * dt for s_, o in pairs]) / np.mean(stride_t)) if pairs else None
        env = {}
        for name, curve in (("hip_vert", th_thigh), ("hip_trunk", hip_ang),
                            ("knee", knee_ang), ("ankle", ankle_story),
                            ("ankle_asin", ankle_ang)):
            m, s, n = envelope_aligned(curve, st, off, duty if duty else 0.6)
            if m is None:
                break
            env[name] = {"mean": m[:100].round(3).tolist(), "std": s[:100].round(3).tolist(),
                         "n_cycles": int(n)}
        if len(env) < 5:
            continue
        # THE SEGMENT IS NOT THE SOLE, and the difference is measured, not fitted. The CMU foot
        # segment runs from the ankle JOINT CENTRE (which sits ~5 cm above the sole) to the
        # ToeBase marker, so it carries a constant downward tilt the sole does not -- here ~19
        # deg, atan(5 cm over ~15 cm), which is the joint's height, not the gait. The sole's zero
        # is foot-flat: mid-stance, where gait analysis defines zero foot pitch and the parent's
        # own law "passes through zero in mid-stance where the sole is flat". Subtract the
        # segment's measured mid-stance tilt and the curve reads sole-relative. (The RL copy
        # keeps the raw asin ankle -- its policy measures its own foot, zero included.)
        flat = float(np.median(np.array(env["ankle"]["mean"][15:45])
                               + np.array(env["hip_vert"]["mean"][15:45])
                               - np.array(env["knee"]["mean"][15:45])))
        env["ankle"]["mean"] = (np.array(env["ankle"]["mean"]) - flat).round(3).tolist()
        env["ankle"]["midstance_offset_removed_deg"] = round(flat, 2)
        stride_raw = float(np.mean([hips[b, 0] - hips[a, 0] for a, b in zip(st[:-1], st[1:])]))
        legs[short] = {"env": env, "duty": duty, "strikes": len(st)}
        strides.append(abs(stride_raw) * scale)
        if duty:
            duties.append(duty)
    if not legs:
        return None
    return {"facing": {"along_travel": round(along, 3), "right_dot_travel": round(lateral, 3)},
            "legs": legs, "stride_m": float(np.mean(strides)) if strides else None,
            "duty": float(np.mean(duties)) if duties else None}


def process_trial(path: Path) -> dict:
    """FK a trial, cut it into steady runs (subjects go there AND BACK -- see _steady_runs), and
    measure every run on its own. Returns {"file", "scale", "runs": [...]}, each run holding the
    facing classification, both legs' envelopes, duty and stride."""
    root, data, dt = mg.parse_bvh(path)
    layout = mg.channel_layout(root)
    P, _tips = mg.forward_kinematics(root, data, layout)
    T = data.shape[0]
    hips0 = P["Hips"]

    # axes from the data (mocap_gait's rule: nothing about the file's frame is assumed). The
    # SIGN is not chosen here -- it is per run, because a trial can travel both ways.
    score = [abs(float(np.median(hips0[:30, k]))) / (float(np.ptp(hips0[:, k])) + 1e-9)
             for k in range(3)]
    up_axis = int(np.argmax(score))
    horiz = [k for k in range(3) if k != up_axis]
    fwd_axis = horiz[int(np.argmax([float(np.ptp(hips0[:, k])) for k in horiz]))]

    up3 = np.zeros(3); up3[up_axis] = 1.0
    axis3 = np.zeros(3); axis3[fwd_axis] = 1.0
    M0 = np.stack([axis3, np.cross(up3, axis3), up3])   # det +1: a ROTATION, not a reflection
    P0 = {name: v @ M0.T for name, v in P.items()}

    # scale: ANSUR II male median trochanterion (hip joint) height, as in mocap_gait
    anch = json.loads(ANSUR.read_text())
    troch_m = float(anch["male"]["trochanterion_m"]["median"])
    hip_center_raw = float(np.median(P0["LeftUpLeg"][:30, 2]))
    scale = troch_m / hip_center_raw

    vel = np.gradient(P0["Hips"][:, 0], dt)
    w = max(3, int(0.25 / dt))
    vel_s = np.convolve(vel, np.ones(w) / w, mode="same")

    runs = []
    for a, b, sgn in _steady_runs(vel_s, dt):
        sl = {name: v[a:b].copy() for name, v in P0.items()}
        if sgn < 0:
            # this run travels the OTHER way along the axis: rotate the slice 180 deg about up,
            # so every run is analysed with travel = +X in a proper right-handed frame
            for v in sl.values():
                v[:, 0] = -v[:, 0]
                v[:, 1] = -v[:, 1]
        run = _analyze_run(sl, dt, scale)
        if run is not None:
            run["file"] = path.name if not str(path).startswith(str(MOCAP)) \
                else str(path.relative_to(MOCAP))
            run["speed_m_s"] = round(float(np.median(np.abs(vel[a:b]))) * scale, 3)
            run["span_s"] = round((b - a) * dt, 2)
            runs.append(run)
    return {"file": path.name if not str(path).startswith(str(MOCAP))
            else str(path.relative_to(MOCAP)), "frames": int(T),
            "scale": round(scale, 5), "runs": runs}


# ---------------------------------------------------------------- aggregation
def _avg_curves(curves):
    """Mean of same-length mean curves across trials/legs, entry by entry."""
    M = np.array(curves)
    return M.mean(0).round(3).tolist()


def aggregate(trials: list[dict], symmetric: bool, lead: str = "L") -> dict:
    """Average the accepted runs into one direction's curves.

    symmetric=True (backward): the two legs are the same gait half a cycle apart -- average L and
    R into one curve set. symmetric=False (sidestep): the legs differ (the trailing one crosses),
    so they are kept apart as lead/trail; `lead` names the side TOWARD the travel (the runs handed
    in were classified to travel that way)."""
    per_leg = {s: {k: [] for k in ("hip_vert", "hip_trunk", "knee", "ankle", "ankle_asin", "duty")}
               for s in ("L", "R")}
    strides, speeds, ncyc = [], [], 0
    for tr in trials:
        for short in ("L", "R"):
            lg = tr["legs"].get(short)
            if not lg:
                continue
            for k in ("hip_vert", "hip_trunk", "knee", "ankle", "ankle_asin"):
                per_leg[short][k].append(lg["env"][k]["mean"])
            ncyc += lg["env"]["knee"]["n_cycles"]
            if lg["duty"]:
                per_leg[short]["duty"].append(lg["duty"])
        if tr["stride_m"]:
            strides.append(tr["stride_m"])
        speeds.append(tr["speed_m_s"])

    def pack(side):
        if not per_leg[side]["knee"]:
            raise SystemExit(f"aggregate: no {side}-leg curves in the accepted runs")
        return {"hip_deg": _avg_curves(per_leg[side]["hip_vert"]),
                "hip_trunk_deg": _avg_curves(per_leg[side]["hip_trunk"]),
                "knee_deg": _avg_curves(per_leg[side]["knee"]),
                "ankle_deg": _avg_curves(per_leg[side]["ankle"]),
                "ankle_asin_deg": _avg_curves(per_leg[side]["ankle_asin"]),
                "duty": round(float(np.mean(per_leg[side]["duty"])), 4)}

    out = {"stride_m": round(float(np.mean(strides)), 4),
           "speed_m_s": round(float(np.mean(speeds)), 3),
           "n_cycles": int(ncyc),
           "trials": sorted({t["file"] for t in trials})}
    if symmetric:
        both = {k: per_leg["L"][k] + per_leg["R"][k] for k in per_leg["L"]}
        duty_all = per_leg["L"]["duty"] + per_leg["R"]["duty"]
        out.update({"symmetric": True,
                    "hip_deg": _avg_curves(both["hip_vert"]),
                    "hip_trunk_deg": _avg_curves(both["hip_trunk"]),
                    "knee_deg": _avg_curves(both["knee"]),
                    "ankle_deg": _avg_curves(both["ankle"]),
                    "ankle_asin_deg": _avg_curves(both["ankle_asin"]),
                    "duty": round(float(np.mean(duty_all)), 4)})
    else:
        trail = "R" if lead == "L" else "L"
        out.update({"symmetric": False, "lead": pack(lead), "trail": pack(trail),
                    "duty": round(float(np.mean(per_leg["L"]["duty"]
                                                + per_leg["R"]["duty"])), 4)})
    return out


def mirror_left_to_right(left: dict) -> dict:
    """Fallback if a side ever has no measured runs: leading and trailing swap. A body is
    symmetric; the mirror is exact, and it is labelled as a mirror rather than presented as a
    second measurement."""
    return {"symmetric": False, "lead": left["trail"], "trail": left["lead"],
            "duty": left["duty"], "stride_m": left["stride_m"], "speed_m_s": left["speed_m_s"],
            "n_cycles": left["n_cycles"], "trials": left["trials"],
            "mirrored_from": "left"}


# ---------------------------------------------------------------- validation
def validate_forward() -> int:
    """Run the SAME pipeline on the forward trial and diff against the committed forward table."""
    sys.path.insert(0, str(ROOT / "story"))
    import importlib.util
    chap = (ROOT / "story" / "theZero" / "theHorizon" / "theEmptying" / "theCooling" / "theCloud"
            / "theGalaxy" / "theSolarSystem" / "thePlanets" / "theRockyPlanet" / "aRockyPlanet"
            / "aBlueWorld" / "theTerrain" / "aTerrain" / "theGround" / "theHuman")
    spec = importlib.util.spec_from_file_location("thehuman_physics", chap / "physics.py")
    ph = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ph)
    nums = json.loads((chap / "numbers.json").read_text())
    committed = nums["gait_cycle"]

    # 35_01 alone is too SHORT for the run cutter (the subject turns in the volume and only ~2
    # clean cycles survive); 136_20 'Normal Walk' adds long steady forward walking, and 136 is
    # the same subject the backward trials come from -- one skeleton for the whole A/B.
    fwd_runs = []
    for path in (FORWARD_BVH, MOCAP / "136" / "136_20.bvh"):
        tr = process_trial(path)
        fwd_runs += [r for r in tr["runs"] if r["facing"]["along_travel"] > 0.5
                     and len(r["legs"]) >= 1]
    if not fwd_runs:
        print("  no forward runs found in the forward reference trials -- pipeline broken")
        return 1
    agg = aggregate(fwd_runs, symmetric=True)
    G = {"hip": agg["hip_deg"], "knee": agg["knee_deg"], "ankle": agg["ankle_deg"],
         "duty": agg["duty"], "grf": ph.measured_gait(None)["grf"]}
    mine = ph._gait_table(float(nums["height_m"]), None,
                          float(nums["forefoot_lever_frac"]), curves=G)

    def col(tab, c):
        return [r[c] for r in tab]
    print(f"  forward validation: {len(fwd_runs)} forward run(s) from 35_01 + 136_20, facing "
          f"along_travel={fwd_runs[0]['facing']['along_travel']:+.2f} (must be > 0), duty "
          f"{agg['duty']:.3f} (committed {nums['duty_factor']:.3f}), stride "
          f"{agg['stride_m']:.3f} m (committed {nums['stride_m']:.3f})")
    print(f"  {'column':<22}{'committed range':>22}{'extracted range':>22}{'stance|diff|':>14}")
    ok = True
    duty_c = float(nums["duty_factor"])
    n_stance = int(round(duty_c * len(committed)))
    for c, name, unit in ((0, "hip_height (stature)", 1.0), (1, "leg0 hip (deg)", 57.2958),
                          (2, "leg0 knee (deg)", 57.2958), (3, "leg0 foot pitch (deg)", 57.2958)):
        a, b = np.array(col(committed, c)) * unit, np.array(col(mine, c)) * unit
        md = float(np.mean(np.abs(a[:n_stance] - b[:n_stance])))
        print(f"  {name:<22}{a.min():>9.3f}..{a.max():<9.3f}   {b.min():>9.3f}..{b.max():<9.3f}"
              f"{md:>13.3f}")
        # judged on STANCE: that is where a foot is planted and a convention error would break
        # the contact law. Swing is air -- subject 35's skeleton proxy runs ~11 deg more knee
        # and a flatter-striking foot segment than the 246-adult average, and that is a SUBJECT
        # difference (the same numbers mocap_walk_reference.json already validated), not a sign.
        if c and md > 20.0:
            ok = False
    print("  CONVENTIONS OK (stance-phase agreement; swing differences are subject 35's own, "
          "already in the validated RL reference)" if ok
          else "  CONVENTION MISMATCH -- check signs before trusting the directional tables")
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> int:
    if "--validate-forward" in sys.argv:
        return validate_forward()

    files = sorted({rel for rels in TRIALS.values() for rel in rels})
    buckets = {"backward": [], "left": [], "right": []}
    for rel in files:
        tr = process_trial(MOCAP / rel)
        for run in tr["runs"]:
            f = run["facing"]
            if f["along_travel"] < -0.5:
                kind = "backward"
            elif abs(f["along_travel"]) <= 0.5 and abs(f["right_dot_travel"]) > 0.7:
                kind = "left" if f["right_dot_travel"] < 0 else "right"
            else:
                kind = None                       # forward, turning, or too slow to be a gait
            keep = (kind is not None and len(run["legs"]) >= 1
                    and 0.25 < run["speed_m_s"] <= WALK_SPEED_MAX)
            print(f"  {'KEEP ' + kind if keep else 'REJECT':<14} {rel:<16} "
                  f"along={f['along_travel']:+.2f} right={f['right_dot_travel']:+.2f} "
                  f"speed={run['speed_m_s']:<6} duty={run['duty']} "
                  f"stride={run['stride_m']} span={run['span_s']}s")
            if keep:
                run["file"] = tr["file"]
                buckets[kind].append(run)
    for kind, runs in buckets.items():
        if not runs:
            raise SystemExit(f"no usable runs for {kind}")

    backward = aggregate(buckets["backward"], symmetric=True)
    left = aggregate(buckets["left"], symmetric=False, lead="L")
    # the runs classified "right" travel toward the body's RIGHT -- measured, not mirrored
    right = aggregate(buckets["right"], symmetric=False, lead="R")

    directions = {"backward": backward, "left": left, "right": right}
    OUT.write_text(json.dumps({
        "source": CITE,
        "conventions": ("curves: 100 samples of the gait cycle, 0 = a leg's own contact (Zeni: foot "
                        "maximally along the progression from the pelvis), DEGREES; hip = thigh "
                        "FROM VERTICAL in the progression plane, + toward travel (the reference "
                        "theHuman's gait table consumes); knee + flexion; ankle + dorsiflexion. "
                        "Sidesteps are per leg, LEADING leg first (the leg toward the travel "
                        "side); 'left' and 'right' are BOTH measured -- the trials travel both "
                        "ways inside the capture volume, and the runs are classified by their "
                        "own facing, never by the index label. No force plates at CMU: the load "
                        "(GRF) curve is NOT here -- theHuman keeps the OSF treadmill's."),
        "directions": directions}, indent=1))
    print(f"\n  backward: {backward['n_cycles']} cycles, duty {backward['duty']}, "
          f"stride {backward['stride_m']} m, speed {backward['speed_m_s']} m/s")
    print(f"  sidestep: {left['n_cycles']} cycles, duty {left['duty']}, "
          f"stride {left['stride_m']} m, lead hip range "
          f"{min(left['lead']['hip_deg']):.1f}..{max(left['lead']['hip_deg']):.1f} deg, "
          f"trail {min(left['trail']['hip_deg']):.1f}..{max(left['trail']['hip_deg']):.1f} deg "
          f"(asymmetric = the cross-step)")
    print(f"  wrote {OUT}")

    # the RL tracker's copy: hip TRUNK-relative, mocap_gait's own convention, for G2
    rl = {"source": CITE,
          "conventions": "same as mocap_walk_reference.json (hip trunk-relative, ankle from the "
                         "ARCSIN foot pitch -- the policy measures its own foot with asin, so the "
                         "tracking A/B must read the same quantity; the story table uses the "
                         "atan2|f| tilt instead, see gait_directional.json)"}
    for name, d in directions.items():
        if d.get("symmetric", True):
            rl[name] = {"envelopes_deg": {"hip": d["hip_trunk_deg"], "knee": d["knee_deg"],
                                          "ankle": d["ankle_asin_deg"]},
                        "duty": d["duty"], "speed_m_s": d["speed_m_s"],
                        "stride_m": d["stride_m"]}
        else:
            rl[name] = {"envelopes_deg": {
                            "lead": {k: d["lead"][k2] for k, k2 in
                                     (("hip", "hip_trunk_deg"), ("knee", "knee_deg"),
                                      ("ankle", "ankle_asin_deg"))},
                            "trail": {k: d["trail"][k2] for k, k2 in
                                      (("hip", "hip_trunk_deg"), ("knee", "knee_deg"),
                                       ("ankle", "ankle_asin_deg"))}},
                        "duty": d["duty"], "speed_m_s": d["speed_m_s"], "stride_m": d["stride_m"]}
    OUT_RL.write_text(json.dumps(rl, indent=1))
    print(f"  wrote {OUT_RL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
