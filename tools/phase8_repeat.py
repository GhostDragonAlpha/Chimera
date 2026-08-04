"""phase8_repeat.py -- PHASE 8's MIXED ARM IS A COIN TOSS. This turns it into a measurement.

WHY. `docs/THE_LIVING_MATTER.md` closes Phase 8 PASS at 800 sweeps and calls it "the last named
debt of this ledger, paid". Re-running the documented command against the frozen code
(`Chimera/core/matter_gpu.py` last moved at 8ec593e, BEFORE both verdicts) does not reproduce it.
Twice, the same command, the same seed:

    swap-only   18.4 / 18.9 / 20.8, drift {0,0,0}, H 26459470 -> 21554082    run 1
    swap-only   18.4 / 18.9 / 20.8, drift {0,0,0}, H 26459472 -> 21554080    run 2   IDENTICAL
    mixed       33.2 / 27.6 / 32.3, drift {  63, -78,  -38},  H ->  42.9M    run 1
    mixed       32.5 / 28.7 / 36.2, drift {-362, -65, +432},  H -> 344.0M    run 2   8x APART

THE SWAP ARM IS BIT-DETERMINISTIC AND THE MIXED ARM IS NOT, and the reason is in the kernels:
`_potts_swap_pass` takes no area array at all -- a swap is volume-neutral, so it never touches
the population counters -- while `_potts_color_pass` does an ATOMIC read-modify-write on the
shared per-type area accumulator. Every copy thread's dH therefore depends on the order the other
threads' atomics land, and the order is the GPU's to choose.

    A SINGLE RUN OF THE MIXED ARM IS ONE DRAW FROM A DISTRIBUTION.

That is this project's oldest measured rule -- ONE ROLLOUT IS A COIN TOSS, the one that convicted
a 13.52-body-length walker with periodicity 0.25 -- applied to the shaker instead of to a gait.
Phase 8's 200-sweep FIRED and its 800-sweep PASS are two draws, and neither settles anything on
its own. The cold-monotone gate that earned the swap kernel its keep was run on SWAP-ONLY; the
interleaved path it certifies was never gated.

So: run the mixed arm N times, at N seeds, and report the DISTRIBUTION and the WORST case. If it
sorts every time, the recorded PASS was right and my two draws were unlucky. If it sorts sometimes,
the honest verdict is a rate, not a verdict. If it never sorts, the debt is open.

    python tools/phase8_repeat.py --runs 5 --sweeps 800
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Chimera"))

import numpy as np  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--sweeps", type=int, default=800)
    ap.add_argument("--n", type=int, default=96)
    a = ap.parse_args(argv)

    from core.matter import metrics_3d
    from core.matter_gpu import step_swaps, step_mixed, open_lattice, close
    from core.matter_derive import (_scramble, derive_J, SIGMA_GEO_MN_M, ELL_M, TEMP,
                                    BONE, MUSCLE, SKIN, NAMES)

    K_PA = {BONE: 13.9e9, MUSCLE: 2.3e9, SKIN: 2.3e9}
    E0 = SIGMA_GEO_MN_M * 1e-3 * ELL_M ** 2 / TEMP
    grid, shape, targets = _scramble(a.n)
    lam = {t: K_PA[t] * ELL_M ** 3 / (2.0 * targets[t] * E0) for t in (BONE, MUSCLE, SKIN)}
    J4 = derive_J(anchor="liquidity")[np.ix_([0, 1, 2, 3], [0, 1, 2, 3])]

    print("=" * 100)
    print(f"  PHASE 8 REPEAT -- the mixed arm as a DISTRIBUTION, not a draw")
    print(f"  n={a.n}, {a.sweeps} sweeps, {a.runs} seeds, derived lambda "
          + ", ".join(f"{NAMES[t]} {lam[t]:.0f}" for t in (BONE, MUSCLE, SKIN)))
    print("=" * 100)

    rows = {"swap-only": [], "mixed": []}
    for arm in ("swap-only", "mixed"):
        for s in range(a.runs):
            h = open_lattice(grid.copy(), shape, targets, J4, temp=TEMP, lam=lam, seed=s)
            tr = (step_swaps(h, a.sweeps, trace=True) if arm == "swap-only"
                  else step_mixed(h, a.sweeps, trace=True))
            final = close(h)
            npass = 12 if arm == "swap-only" else 20
            sw = tr.reshape(a.sweeps, npass).mean(axis=1)
            r = metrics_3d(final, shape)["radius"]
            drift = {t: int((final == t).sum()) - targets[t] for t in (BONE, MUSCLE, SKIN)}
            ok = bool(r[BONE] < r[MUSCLE] < r[SKIN])
            within = all(abs(v) <= 0.01 * targets[t] for t, v in drift.items())
            rows[arm].append(dict(seed=s, sorted=ok, within=within, H0=float(sw[0]),
                                  H1=float(sw[-1]), r=[float(r[t]) for t in (BONE, MUSCLE, SKIN)],
                                  drift=[drift[t] for t in (BONE, MUSCLE, SKIN)]))
            print(f"  {arm:<9} seed {s}: bone {r[BONE]:5.1f} muscle {r[MUSCLE]:5.1f} "
                  f"skin {r[SKIN]:5.1f} -> sorted {str(ok):<5} drift "
                  f"{[drift[t] for t in (BONE, MUSCLE, SKIN)]}  H {sw[0]/1e6:.2f}M -> "
                  f"{sw[-1]/1e6:.2f}M")

    print("-" * 100)
    for arm in ("swap-only", "mixed"):
        rs = rows[arm]
        nsort = sum(r["sorted"] for r in rs)
        H1 = [r["H1"] for r in rs]
        spread = max(H1) / max(min(H1), 1e-9)
        print(f"  {arm:<9} sorted {nsort}/{len(rs)}  |  final H {min(H1)/1e6:.2f}M .. "
              f"{max(H1)/1e6:.2f}M  (spread {spread:.2f}x)  |  counts within 1%: "
              f"{sum(r['within'] for r in rs)}/{len(rs)}")
    so, mx = rows["swap-only"], rows["mixed"]
    print("-" * 100)
    print(f"  FALSIFIER 3 (swap-only sorts -> swaps carry the dynamics): "
          f"{'PASS' if all(r['sorted'] for r in so) else 'FIRED'} "
          f"at {sum(r['sorted'] for r in so)}/{len(so)}")
    print(f"  FALSIFIER 2 (counts within 1%): "
          f"{'PASS' if all(r['within'] for r in mx) else 'FIRED'} "
          f"at {sum(r['within'] for r in mx)}/{len(mx)}")
    rate = sum(r["sorted"] for r in mx) / max(len(mx), 1)
    print(f"  FALSIFIER 1 (mixed sorts): {'PASS' if rate == 1.0 else 'FIRED'} -- "
          f"sort RATE {100*rate:.0f}%. A rate is what a nondeterministic arm can report; "
          f"a single run cannot.")
    print(f"\n  WORST CASE (the number this project scores on): mixed sorted "
          f"{sum(r['sorted'] for r in mx)}/{len(mx)}; the worst final H is "
          f"{max(r['H1'] for r in mx)/1e6:.2f}M against swap-only's "
          f"{max(r['H1'] for r in so)/1e6:.2f}M.")
    return 0 if rate == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
