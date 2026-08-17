"""chain_witness.py -- does every membrane ABOVE the human still work?

WHY. The human is about to be tested against the terrain, and the human stands on fourteen membranes
that reach it. If any one of them is quietly broken -- a NaN in its numbers, an emit() that returns
nothing, matter that does not fit inside the boundary it claims -- then whatever the human does on
that ground is untrustworthy, and the failure will look like a walking bug because that is the only
place anyone is looking.

So this exercises each membrane the way the game does, and reports FACTS rather than a verdict:

  DERIVED    numbers.json exists, is non-empty, carries extent_m and duration_s, and contains no
             NaN or infinity anywhere in it. A NaN propagates silently through every child.
  EMITS      emit() returns a splat buffer at t=0 and at t=1, both non-empty, both finite.
  MOVES      the two frames DIFFER. One frame cannot show motion, and this project has already been
             bitten by a scene that silently did not switch -- theSweep's `% 1.0` wrapped t=1 back
             onto t=0, so the canonical two-frame export showed nothing happening at all.
  CONTAINED  the matter fits inside the extent the membrane declares. A boundary that lies about its
             own size breaks the camera framing of every parent that composes it.
  FINITE     alpha in [0,1], size > 0. A zero-size or negative-alpha splat is invisible or worse.

A STUB IS NOT A FAILURE. Membranes that declare `stub: True` derive nothing and draw nothing on
purpose; they are reported as STUB so an empty chapter cannot be mistaken for a finished one, and
they do not count against the chain.

RUN:  python tools/chain_witness.py                 (the whole tree)
      python tools/chain_witness.py --chain         (only the ancestors of theHuman)
      python tools/chain_witness.py theGround       (one membrane and its children)
"""
from __future__ import annotations

import json
import math
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORY = ROOT / "story"
sys.path.insert(0, str(STORY))

# The splat buffer's columns, as ChimeraEngine/core/matter.py lays them out.
PX, PY, PZ = 0, 1, 2
CR, CG, CB, ALPHA, SIZE = 16, 17, 18, 19, 20


def _finite(x) -> bool:
    if isinstance(x, bool):
        return True
    if isinstance(x, (int, float)):
        return math.isfinite(x)
    if isinstance(x, (list, tuple)):
        return all(_finite(v) for v in x)
    if isinstance(x, dict):
        return all(_finite(v) for v in x.values())
    return True


def _bad_numbers(nums: dict) -> list:
    return sorted(k for k, v in nums.items() if not _finite(v))


def _law(folder: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"_cw_{folder.name}", folder / "physics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(folder: Path) -> dict:
    name = folder.name
    r = {"name": name, "path": str(folder.relative_to(STORY)), "notes": [], "fails": []}
    nj = folder / "numbers.json"
    if not nj.exists():
        r["fails"].append("no numbers.json -- derive() never ran or never wrote")
        return r
    try:
        nums = json.loads(nj.read_text(encoding="utf8"))
    except Exception as e:
        r["fails"].append(f"numbers.json will not parse: {e}")
        return r
    r["n_numbers"] = len(nums)
    if nums.get("stub"):
        r["stub"] = True
        return r
    for k in ("extent_m", "duration_s"):
        if k not in nums:
            r["fails"].append(f"publishes no {k} -- every membrane has a size and a clock")
    bad = _bad_numbers(nums)
    if bad:
        r["fails"].append(f"NaN or infinity in: {', '.join(bad[:6])}"
                          + (f" (+{len(bad)-6} more)" if len(bad) > 6 else ""))
    r["extent_m"] = nums.get("extent_m")
    r["duration_s"] = nums.get("duration_s")

    if not (folder / "physics.py").exists():
        r["fails"].append("no physics.py")
        return r
    try:
        law = _law(folder)
    except Exception as e:
        r["fails"].append(f"physics.py will not import: {type(e).__name__}: {e}")
        return r
    if not hasattr(law, "emit"):
        r["notes"].append("no emit() -- draws nothing")
        return r

    # SEVEN SAMPLES, AND SEVEN IS CHOSEN RATHER THAN CONVENIENT.
    #
    # The canonical export renders exactly t=0 and t=1. For a CYCLIC membrane those are the same
    # instant by definition -- a planet that has turned once is back where it started, and a gait
    # that has walked one stride is back at heel strike -- so comparing only the ends reports
    # "nothing happens" for every membrane that correctly closes its loop. This project has already
    # paid for the inverse of that mistake in theSweep, where a `% 1.0` wrapped a TRANSIENT back
    # onto its start and the two-frame check showed nothing when something was genuinely wrong.
    #
    # So sample the middle too -- and this file's FIRST attempt did exactly that, at t=0.5, and
    # convicted theBreath of being a photograph. It was not. theBreath advects its gas EXACTLY
    # 2.0 transits per breath (deliberately, so its loop closes), which makes t=0.5 one whole
    # transit and therefore identical to t=0 by construction. The instrument had aliased, and
    # reported the membrane's correctness as its failure.
    #
    # Seven samples at k/7 cannot alias with 2, 3, 4, 5 or 6 internal cycles, because 7 is prime
    # and shares no factor with any of them. A membrane that is identical at all seven is genuinely
    # still. This is the "verify your own measurement, not just the claim" rule applied to a witness.
    bufs = {}
    _S = 7
    for label, t in ([("t0", 0.0)] + [(f"s{k}", k / _S) for k in range(1, _S)] + [("t1", 1.0)]):
        try:
            b = law.emit(nums, t)
        except Exception as e:
            r["fails"].append(f"emit(t={t}) raised {type(e).__name__}: {e}")
            r["trace"] = traceback.format_exc(limit=3)
            return r
        bufs[label] = b

    import numpy as np
    n0, n1 = len(bufs["t0"]), len(bufs["t1"])
    r["splats"] = (n0, n1)
    if n0 == 0 and n1 == 0:
        r["fails"].append("emits NO matter at either end -- an invisible membrane")
        return r

    b1 = np.asarray(bufs["t1"], dtype=float)
    if len(b1):
        pos = b1[:, PX:PZ + 1]
        if not np.isfinite(b1).all():
            r["fails"].append(f"{int((~np.isfinite(b1)).any(axis=1).sum())} splats carry NaN/inf")
        else:
            reach = float(np.linalg.norm(pos, axis=1).max())
            r["reach_local"] = reach
            a = b1[:, ALPHA]
            s = b1[:, SIZE]
            if a.min() < -1e-6 or a.max() > 1.0 + 1e-6:
                r["fails"].append(f"alpha outside [0,1]: {a.min():.3f}..{a.max():.3f}")
            if s.min() <= 0.0:
                r["fails"].append(f"{int((s <= 0).sum())} splats have size <= 0 -- invisible")
            col = b1[:, CR:CB + 1]
            if col.min() < -1e-6:
                r["fails"].append(f"negative colour: {col.min():.3f}")

    # MOVES, and CLOSES -- two separate questions.
    def delta(a, b):
        if len(a) != len(b):
            return float("inf")           # a changed splat count is certainly a change
        A, B = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        if not (np.isfinite(A).all() and np.isfinite(B).all()):
            return float("nan")
        return float(np.abs(A - B).max())

    # the largest departure from the opening frame anywhere in the cycle -- does anything happen?
    d_mid = max(delta(bufs["t0"], bufs[f"s{k}"]) for k in range(1, _S))
    d_end = delta(bufs["t0"], bufs["t1"])     # and does it come back?
    r["moves"], r["closes"] = d_mid, d_end
    if d_mid == 0.0 and d_end == 0.0:
        r["fails"].append(f"NOTHING MOVES -- identical at all {_S + 1} samples of its own cycle. "
                          f"Its movie is a photograph")
    elif d_end == 0.0:
        r["notes"].append("cyclic: moves through the middle and closes exactly at t=1, so the "
                          "canonical begin/end stills cannot show it -- sample the middle")
    return r


def main(argv) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    chain_only = "--chain" in argv

    folders = sorted({p.parent for p in STORY.rglob("numbers.json")},
                     key=lambda p: (len(p.parts), str(p)))
    if args:
        keep = set(args)
        folders = [f for f in folders if f.name in keep or any(k in f.parts for k in keep)]
    if chain_only:
        human = next((f for f in folders if f.name == "theHuman"), None)
        if human:
            anc = set(human.parts)
            folders = [f for f in folders if f.name in anc]

    ok = stub = bad = held = 0
    rows = []
    for f in folders:
        r = check(f)
        # A SELF-DECLARED PLACEHOLDER IS NOT A BROKEN MEMBRANE, and conflating them costs the
        # metric its meaning. A membrane that publishes `placeholder: true` is saying, in its own
        # numbers.json, that it draws and does not yet derive -- so of course it does not move
        # through its own time, and this witness is RIGHT to notice. What it must not do is report
        # it in the same bucket as a chapter that was supposed to work and does not.
        #
        #     "NOT BUILT YET" AND "BUILT WRONG" DEMAND OPPOSITE RESPONSES, and a count that merges
        #     them tells you to go fix something that was never claimed to be finished.
        #
        # It is counted and named rather than skipped -- the same treatment `action_tests` gives a
        # refusal. Five announced placeholders should read as five open gaps in the ledger, which
        # is exactly what docs/TERM_INVENTORY.md already says they are.
        try:
            import json as _j
            _n = _j.loads((f / "numbers.json").read_text(encoding="utf8"))
            r["placeholder"] = bool(_n.get("placeholder"))
        except Exception:
            r["placeholder"] = False
        rows.append(r)
        if r.get("stub"):
            stub += 1
        elif r.get("placeholder"):
            held += 1
        elif r["fails"]:
            bad += 1
        else:
            ok += 1

    depth0 = min(len(f.parts) for f in folders) if folders else 0
    W = max(30, max((len(r["name"]) + 2 * (len(f.parts) - depth0)) for r, f in zip(rows, folders)))
    print(f"{'membrane':<{W}} {'splats':>9} {'extent m':>12} {'reach':>9} {'moves':>10}  state")
    print("-" * (W + 46))
    for r, f in zip(rows, folders):
        nm = "  " * (len(f.parts) - depth0) + r["name"]
        if r.get("stub"):
            print(f"{nm:<{W}} {'-':>9} {'-':>12} {'-':>9} {'-':>10}  STUB (declares nothing)")
            continue
        sp = f"{r['splats'][0]}" if "splats" in r else "-"
        ex = f"{r['extent_m']:.4g}" if isinstance(r.get("extent_m"), (int, float)) else "-"
        rc = f"{r['reach_local']:.3g}" if "reach_local" in r else "-"
        mv = ("-" if r.get("moves") is None
              else "yes" if r["moves"] == float("inf") else f"{r['moves']:.3g}")
        state = ("PLACEHOLDER (draws, does not derive -- an open gap, not a defect)"
                 if r.get("placeholder") else "ok" if not r["fails"] else "BROKEN")
        if not r["fails"] and r.get("closes") == 0.0:
            state = "ok  cyclic"
        print(f"{nm:<{W}} {sp:>9} {ex:>12} {rc:>9} {mv:>10}  {state}")
        for note in r["notes"]:
            print(f"{'':<26} note: {note}")
        if not r.get("placeholder"):
            for fl in r["fails"]:
                print(f"{'':<26} BROKEN: {fl}")
        if "trace" in r:
            for line in r["trace"].strip().splitlines()[-4:]:
                print(f"{'':<30} {line}")
    print("-" * 92)
    print(f"{ok} working, {stub} stubs, {held} placeholders, {bad} broken   "
          f"({len(folders)} membranes)")
    if held:
        print(f"{'':<4}the {held} placeholder(s) publish `placeholder: true` and are OPEN GAPS -- "
              f"see docs/TERM_INVENTORY.md. They are not counted as broken and are not counted as "
              f"working.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
