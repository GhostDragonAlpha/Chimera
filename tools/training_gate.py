"""training_gate.py -- refuse a training run whose targets were not derived for THIS world.

WHY THIS EXISTS, and it is the second time the same correction has been needed.

CLAUDE.md has said since 2026-07-28, in the operator's own words: *"You have to know it works
because it's proven mathematically first before you start training."* On 2026-08-02 a walker that
would not walk was met with a FOUR-VARIANT PARAMETER SWEEP -- alive bonus, stagnation floor,
penalty weight, effort cost -- run in parallel on the theory that measuring four guesses beats
making one.

    A PARAMETER SWEEP IS AN ADMISSION THAT THE DERIVATION WAS NOT DONE.
    Every variant in that sweep was asking the body for a speed it physically cannot walk at.
    Four flavours of the same impossible demand, ranked against each other.

WHAT THE DERIVATION FOUND IN FIVE MINUTES, once someone did it instead of sweeping:

    this world     g = 7.076 m/s2 (0.722 Earth),  leg 0.9201 m
    the body derives its own comfortable speed:   0.9924 m/s
    the trainer was targeting:                    1.285  m/s   <- MEASURED ON EARTH
                                                  = 1.29x what this body can walk at

Froude is the whole of it: Fr = v^2/(gL), and equal Fr means dynamically similar gait. Earth
walking at 1.285 m/s is Fr = 0.183. Demanding 1.285 m/s at 7.076 m/s^2 is Fr = 0.254 -- 39%
higher, heading toward the walk-run transition. So the velocity term demanded a running-ward gait
while the tracking term simultaneously demanded Earth WALKING envelopes. The two terms pulled
against each other and the body's best available answer was to satisfy neither and collect the
alive bonus. THE CROUCH WAS THE ONLY STABLE POINT IN A CONTRADICTORY REWARD.

No sweep finds that. Four variants all asking for an impossible speed rank four failures.

WHAT THIS GATE CHECKS, before a single GPU-hour is spent:

  1. EVERY TARGET SPEED IS FROUDE-CONSISTENT with the world the body stands in. A speed measured
     on Earth must be scaled by sqrt(g_here/g_earth) or it is asking for a different gait.
  2. EVERY STRIDE TIME AGREES WITH THE ONE THE BODY DERIVES FOR ITSELF (2 x its published
     step_time_s). NOT with a Froude transport of an Earth stride -- that is second-best, and
     for one day this gate demanded it and refused the correct answer. See the note at the
     stride check for the full account; it is the same defect this file exists to catch,
     committed by this file.
  3. THE TARGET AGREES WITH WHAT THE BODY PUBLISHES. theHuman derives comfortable_speed_ms for
     itself. A trainer that ignores it is training against a body other than the one it has.

It does not check whether the reward is well designed -- nothing can. It checks that the numbers
in it belong to this planet, which is the failure that actually happened.

    python tools/training_gate.py --target-speed 1.285 --stride-s 1.127
    python tools/training_gate.py --trainer tools/train_myobody_directional.py
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G_EARTH = 9.80665
TOL = 0.06          # 6% -- tighter than the difference any of these errors produce


def body():
    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == "theHuman"]
    if not hits:
        return None
    return json.loads(hits[0].read_text(encoding="utf8"))


def check(target_speed=None, stride_s=None, verbose=True):
    b = body()
    if b is None:
        print("REFUSED: no theHuman numbers.json -- nothing to derive against")
        return 1
    g, L = float(b["g"]), float(b["leg_length_m"])
    own = float(b.get("comfortable_speed_ms", 0.0))
    scale = math.sqrt(g / G_EARTH)
    fails = []

    if verbose:
        print(f"THIS WORLD   g = {g:.4f} m/s2  ({g/G_EARTH:.3f} of Earth)   leg = {L:.4f} m")
        print(f"             Froude scale for speed  sqrt(g/g_E) = {scale:.4f}")
        print(f"             stride scale            sqrt(g_E/g) = {1/scale:.4f}")
        print(f"             the body derives its own comfortable speed: {own:.4f} m/s\n")

    if target_speed is not None:
        fr_here = target_speed ** 2 / (g * L)
        fr_earth = target_speed ** 2 / (G_EARTH * L)
        want = target_speed * scale
        if own > 0 and abs(target_speed - own) / own > TOL:
            fails.append(
                f"TARGET SPEED {target_speed:.4f} m/s is {target_speed/own:.2f}x the speed this "
                f"body derives for itself ({own:.4f}). If it came from an Earth dataset, Froude "
                f"says it becomes {want:.4f} m/s here.")
        if verbose:
            print(f"  target {target_speed:.4f} m/s -> Fr = {fr_here:.4f} here, "
                  f"{fr_earth:.4f} if this were Earth")

    if stride_s is not None:
        # WHAT THIS USED TO DO, AND WHY IT WAS THE SAME BUG IT HUNTS. It computed
        #     want_T = stride_s / scale        and then compared stride_s against want_T
        # -- the input against a transform of ITSELF. That comparison can only pass when
        # scale == 1, which is to say ON EARTH: the gate written to refuse Earth numbers was
        # unpassable on every world except Earth, and it REFUSED theHuman's own correctly
        # derived 1.1730 s while demanding a 1.3809 s that no membrane publishes.
        #
        # The root assumption was that whatever it was handed must be an Earth measurement in
        # need of transport. That is the instrument keeping its own private copy of the body --
        # rule 20 -- and it drifts the instant the body derives something better. A transported
        # Earth number is second-best by construction: the membrane already did the derivation,
        # from a compound pendulum with a measured swing drive, and the honest check is against
        # what it PUBLISHED.
        if "step_time_s" not in b:
            fails.append(
                "STRIDE TIME cannot be checked: theHuman publishes no step_time_s, so there is "
                "nothing to compare against. A fallback here would be this gate inventing the "
                "cadence it exists to police. Fix the membrane, not the gate.")
        else:
            own_T = 2.0 * float(b["step_time_s"])   # the membrane's own rule: a stride is two steps
            if abs(stride_s - own_T) / own_T > TOL:
                fails.append(
                    f"STRIDE TIME {stride_s:.4f} s disagrees with the {own_T:.4f} s this body "
                    f"derives for itself (2 x step_time_s, from the leg as a compound pendulum "
                    f"at {g:.3f} m/s2). It is being clocked "
                    f"{(own_T/stride_s - 1)*100:+.0f}% wrong. If {stride_s:.4f} came from an "
                    f"Earth dataset, Froude transport gives {stride_s/scale:.4f} s -- which is "
                    f"still second-best, because the membrane already derived the real one.")

    print()
    if fails:
        print("REFUSED -- these targets were not derived for this world:\n")
        for f in fails:
            print(f"  * {f}\n")
        print("  Derive before you train. A parameter sweep over a reward whose targets belong to")
        print("  another planet ranks four flavours of the same impossible demand.")
        return 1
    print("PASS -- every target is Froude-consistent with the world this body stands in.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target-speed", type=float, default=None)
    ap.add_argument("--stride-s", type=float, default=None)
    ap.add_argument("--trainer", default=None,
                    help="scan a trainer for hard-coded m/s and stride constants")
    a = ap.parse_args()

    if a.trainer:
        src = Path(a.trainer).read_text(encoding="utf8", errors="replace")
        sp = [float(x) for x in re.findall(r"(\d\.\d{2,4})\s*m/s", src)]
        if sp:
            print(f"found hard-coded speeds in {a.trainer}: {sorted(set(sp))}\n")
            worst = max(sp)
            return check(target_speed=worst, stride_s=a.stride_s)
        print(f"no literal m/s speeds found in {a.trainer}; pass --target-speed explicitly")
        return 0
    return check(a.target_speed, a.stride_s)


if __name__ == "__main__":
    sys.exit(main())
