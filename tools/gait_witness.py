"""gait_witness.py -- does the story's body WALK, or does it just arrive?

WHY A SEPARATE INSTRUMENT. A membrane's own `measure()` reads the numbers it just produced, which
makes it a good check on arithmetic and a poor check on physics: it cannot notice that the thing it
computed correctly is not a walk. This reads only the PUBLISHED gait table out of numbers.json and
rebuilds the body's geometry from scratch, so a table that is internally consistent but physically
wrong -- feet through the floor, both feet airborne, no overlap -- has nowhere to hide.

WHAT IT CHECKS, and why each one is the failure it is named after:

  SOLE PENETRATION      a planted foot's sole must sit exactly on the ground. If it does not, the
                        hip height and the leg geometry disagree, and the body is standing on air
                        or buried in rock. This is the check that convicts a table outright.
  CONTACT-PLANE TRAVEL  the ground the body walks on must not move. A bobbing contact plane is the
                        signature of THE SLED -- a body that translates without ever pushing off.
  DUTY FACTOR           the fraction of the cycle each foot is down. ~1.0 is a sled, ~0 is cargo,
                        0.55-0.65 is a walk, below 0.5 is a run.
  DOUBLE SUPPORT        the overlap where both feet are down. Without it there is no leg pushing
                        off while the other reaches, and a walk becomes two abutting hops.
                        ~20% of the cycle in human walking; EXACTLY ZERO for any sine-driven gait,
                        which is how the earlier model was caught.
  SWING CLEARANCE       the swinging foot must leave the floor, or it drags.
  VAULT                 how far the hip rises and falls. A human walks flat -- about 2.5% of
                        stature -- because a knee flexes and a foot rolls. A compass gait with a
                        straight leg and a point foot vaults far more, and that difference is what
                        the ankle and the knee are worth.
  SYMMETRY              left and right must agree. A real body is asymmetric by ~3%; a table that
                        is asymmetric by more than that has an indexing bug, not a limp.

Every threshold below is a MEASUREMENT with a source, not a preference. Where the membrane also
publishes the measured counterpart (it does now, from the OSF normative dataset), the witness
compares against THAT rather than against a constant typed here.

RUN:  python tools/gait_witness.py                     (every membrane that publishes a gait)
      python tools/gait_witness.py theHuman aHuman     (named ones)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORY = ROOT / "story"

# Human level walking, from the literature the membranes already cite. Used only where a membrane
# does not publish its own measured counterpart.
HUMAN = {
    "duty": (0.55, 0.65),          # stance / stride, comfortable walking
    "double_support": (0.15, 0.25),
    "clearance_frac": (0.005, 0.15),   # swing foot above the floor, as a fraction of stature
    "vault_frac": (0.010, 0.040),      # hip vertical excursion / stature
    "asymmetry": 0.05,                 # measured step-time asymmetry is ~3%
}


def _find(name: str):
    hits = [p for p in STORY.rglob("numbers.json") if p.parent.name == name]
    return hits[0] if hits else None


def _rows(nums):
    """The published table, as (hip, [(hip_a, knee_a, pitch, u, planted) x 2]) per sample."""
    tab = nums.get("gait_cycle")
    if not tab:
        return None
    out = []
    for r in tab:
        legs = [(float(r[1 + 5 * i]), float(r[2 + 5 * i]), float(r[3 + 5 * i]),
                 float(r[4 + 5 * i]), r[5 + 5 * i] > 0.5) for i in (0, 1)]
        out.append((float(r[0]), legs))
    return out


def _sole_z(hip_z, hip_a, knee_a, pitch, thigh, shank, heel, toe, drop):
    """THE LOWEST POINT OF THE SOLE, rebuilt from the pose rather than read from the table.

    Walk the chain: hip down the thigh to the knee, knee down the shank to the ankle, then the foot
    hung off the ankle and pitched. The sole's ends are the heel behind and the toe in front, both
    `drop` below the ankle before rotation. Whichever ends up lower is the contact."""
    ankle_z = hip_z - thigh * math.cos(hip_a) - shank * math.cos(hip_a - knee_a)
    hz = ankle_z - heel * math.sin(pitch) - drop * math.cos(pitch)
    tz = ankle_z + toe * math.sin(pitch) - drop * math.cos(pitch)
    return min(hz, tz)


def witness(name: str) -> dict:
    p = _find(name)
    if p is None:
        return {"name": name, "error": "no numbers.json"}
    nums = json.loads(p.read_text(encoding="utf8"))
    rows = _rows(nums)
    if rows is None:
        return {"name": name, "error": "publishes no gait_cycle"}

    # geometry, in units of stature, as the membrane itself uses them
    h = float(nums.get("height_m", 1.0))
    leg = float(nums.get("leg_length_m", 0.53 * h)) / h
    thigh, shank = 0.245, 0.246          # theHuman's own fractions
    heel = 0.050
    # THE PIVOT THE MEMBRANE ACTUALLY USES, read from what it published. Grading a foot against a
    # lever it does not use would test this file's opinion rather than the body's geometry -- and
    # since the pivot moved from the toe tip to the ball, a witness holding the old value would
    # report a penetration that is entirely its own.
    toe = float(nums.get("forefoot_lever_frac", 0.152))
    drop = leg - (thigh + shank)

    N = len(rows)
    duty = [0, 0]
    both = 0
    hips = [r[0] for r in rows]
    # SINGLE AND DOUBLE SUPPORT ARE JUDGED SEPARATELY, and that separation is the point.
    #
    # In single support one leg carries everything, so its sole's height is FULLY DETERMINED and the
    # check is exact -- zero or a bug, no interpretation. In double support two legs each demand a
    # pelvis height from their own joint angles, and the two demands only agree if the segment
    # lengths are the ones the measured angles were recorded on. They are not: theHuman's segment
    # fractions are still Dempster's typed values (`segment_lengths_are_sourced: False`), so a
    # residual there is EXPECTED and its size is the measurement of that gap.
    #
    # Averaging the two into one number would hide an exact result behind a known-approximate one.
    single, dbl, clear = [], [], [[], []]
    for hip_z, legs in rows:
        planted = [i for i, lg in enumerate(legs) if lg[4]]
        for i, (ha, ka, pi_, u, pl) in enumerate(legs):
            z = _sole_z(hip_z, ha, ka, pi_, thigh, shank, heel, toe, drop)
            if pl:
                duty[i] += 1
                (single if len(planted) == 1 else dbl).append(z)
            else:
                clear[i].append(z)
        if len(planted) == 2:
            both += 1

    duty_f = [d / N for d in duty]
    ds = both / N
    plane_travel = (max(single) - min(single)) if single else float("nan")
    sole_err = max(abs(z) for z in single) if single else float("nan")
    dbl_err = max(abs(z) for z in dbl) if dbl else 0.0
    # peak clearance and the lowest the swinging foot gets while off the ground -- two different
    # things, and the dataset's "foot clearance" is the second one, so they must not be compared.
    clr = [max(c) if c else 0.0 for c in clear]
    clr_min = [min(c) if c else 0.0 for c in clear]
    vault = max(hips) - min(hips)
    asym = abs(duty_f[0] - duty_f[1]) / max(sum(duty_f) / 2, 1e-9)

    # peak of the hip path, as a percentage of the cycle -- a real hip peaks at mid-stance (~30%)
    peak_at = hips.index(max(hips)) / N

    out = {"name": name, "samples": N, "height_m": h,
           "duty": duty_f, "double_support": ds,
           "sole_error_frac": sole_err, "sole_error_double_support_frac": dbl_err,
           "contact_plane_travel_frac": plane_travel,
           "clearance_frac": clr, "clearance_min_frac": clr_min,
           "vault_frac": vault, "vault_m": vault * h,
           "hip_peak_at_cycle": peak_at, "asymmetry": asym,
           "measured": {k: nums[k] for k in
                        ("duty_factor", "double_support_frac", "measured_foot_clearance_m",
                         "gait_source", "gait_group", "gait_speed_condition", "gait_is_measured")
                        if k in nums}}

    fails = []
    ref_duty = nums.get("duty_factor")
    for i, d in enumerate(duty_f):
        if ref_duty is not None:
            if abs(d - ref_duty) > 0.05:
                fails.append(f"duty[{i}] {d:.3f} is {abs(d-ref_duty):.3f} off its own measured "
                             f"{ref_duty:.3f}")
        elif not (HUMAN["duty"][0] <= d <= HUMAN["duty"][1]):
            fails.append(f"duty[{i}] {d:.3f} outside human {HUMAN['duty']}")
    ref_ds = nums.get("double_support_frac")
    if ref_ds is not None:
        if abs(ds - ref_ds) > 0.06:
            fails.append(f"double support {ds:.3f} vs its own measured {ref_ds:.3f}")
    elif not (HUMAN["double_support"][0] <= ds <= HUMAN["double_support"][1]):
        fails.append(f"double support {ds:.3f} outside human {HUMAN['double_support']}")
    if sole_err > 0.002:
        fails.append(f"SOLE PENETRATION {sole_err*100:.2f}% of stature IN SINGLE SUPPORT -- one leg "
                     f"carries everything there, so this is fully determined and must be zero")
    if plane_travel > 0.002:
        fails.append(f"CONTACT PLANE TRAVELS {plane_travel*100:.2f}% of stature in single support "
                     f"-- a sled")
    for i, c in enumerate(clr):
        if c < HUMAN["clearance_frac"][0]:
            fails.append(f"swing foot {i} clears only {c*100:.2f}% of stature -- it drags")
    if min(clr_min) < -0.002:
        fails.append(f"swing foot goes {abs(min(clr_min))*100:.2f}% of stature BELOW the floor")
    if not (HUMAN["vault_frac"][0] <= vault <= HUMAN["vault_frac"][1]):
        fails.append(f"vault {vault*100:.2f}% of stature outside human "
                     f"{HUMAN['vault_frac'][0]*100:.1f}-{HUMAN['vault_frac'][1]*100:.1f}%")
    if asym > HUMAN["asymmetry"]:
        fails.append(f"left/right differ by {asym*100:.1f}% -- an indexing bug, not a limp")
    out["fails"] = fails
    out["verdict"] = "WALKS" if not fails else "REFUSED"
    return out


def main(argv) -> int:
    names = argv[1:] or [p.parent.name for p in STORY.rglob("numbers.json")
                         if "gait_cycle" in p.read_text(encoding="utf8")]
    bad = 0
    for n in dict.fromkeys(names):
        r = witness(n)
        if "error" in r:
            print(f"{n:<12} -- {r['error']}")
            continue
        print(f"\n{'='*88}\n{r['name']}   {r['verdict']}\n{'='*88}")
        m = r["measured"]
        if m.get("gait_is_measured"):
            print(f"  gait read from   {m.get('gait_group')} at the "
                  f"{m.get('gait_speed_condition')} condition")
        print(f"  duty factor      {r['duty'][0]:.3f} / {r['duty'][1]:.3f}"
              + (f"      measured {m['duty_factor']:.3f}" if "duty_factor" in m else ""))
        print(f"  double support   {r['double_support']:.3f}"
              + (f"              measured {m['double_support_frac']:.3f}"
                 if "double_support_frac" in m else ""))
        print(f"  sole error       {r['sole_error_frac']*100:.3f}% of stature IN SINGLE SUPPORT   "
              f"(fully determined -- must be zero)")
        print(f"                   {r['sole_error_double_support_frac']*100:.3f}% in DOUBLE support "
              f"  (two legs, one pelvis: the residual is the unsourced segment lengths)")
        print(f"  contact plane    {r['contact_plane_travel_frac']*100:.3f}% of stature   "
              f"(must not move)")
        print(f"  swing clearance  peak {r['clearance_frac'][0]*100:.2f}% / "
              f"{r['clearance_frac'][1]*100:.2f}%, lowest {min(r['clearance_min_frac'])*100:.2f}% "
              f"of stature"
              + (f"   measured MTC {m['measured_foot_clearance_m']/r['height_m']*100:.2f}%"
                 if "measured_foot_clearance_m" in m else ""))
        print(f"  vault            {r['vault_frac']*100:.2f}% of stature "
              f"({r['vault_m']*100:.1f} cm)   human ~2.5%")
        print(f"  hip peaks at     {r['hip_peak_at_cycle']*100:.0f}% of the cycle   "
              f"(a real hip peaks at mid-stance, ~30%)")
        print(f"  left/right       {r['asymmetry']*100:.2f}% apart   (human ~3%)")
        for f in r["fails"]:
            print(f"  REFUSED: {f}")
        bad += bool(r["fails"])
    print()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
