"""pair_drill.py -- closeout-8 per-section pairing of the csub/ksub drill pair.

The two sides print DIFFERENT section sets and their formats do NOT align
token-by-token (the scout's gotcha). The drill window is a SINGLE tick with a
BIT-EXACT entry state on both sides, so the legal pairing is: within each
section tag, pair the k-th printed line on the cpp side with the k-th on the
host side, then compare the fields the two formats SHARE. A count difference
between the sides for one tag is itself a finding (the sides took a different
number of branches/events inside the flipping tick).

Usage: python pair_drill.py <csub.err> <ksub.out> [--quiet]
Trailer: Agent: GLM 5.3.
"""
import sys
from collections import OrderedDict

TAGS = ["ADV", "RT", "RTFSC", "RTFRO", "RTFRI", "RTFS", "RTSC", "IMPE", "IMPF",
        "IMPP", "IMPC", "FST", "FSEND", "SEATIN", "SEATF", "SEATOUT", "SV",
        "SUBPRE", "TAUFULL", "SUBFULL"]
# host-only debug sections (STOREDBG's t= printf misses its argument; DRAIN12
# has no cpp counterpart) -- census only, never paired.


def load(path):
    out = OrderedDict((t, []) for t in TAGS)
    for ln, line in enumerate(open(path, errors="replace"), 1):
        toks = line.split()
        if not toks or toks[0] not in out:
            continue
        d = {}
        for tok in toks[1:]:
            if "=" in tok:
                k, v = tok.split("=", 1)
                d.setdefault(k, []).append(v)
        out[toks[0]].append((ln, d))
    return out


def main():
    csub, ksub = sys.argv[1], sys.argv[2]
    quiet = "--quiet" in sys.argv
    a, b = load(csub), load(ksub)
    print("section census (cpp / host):")
    for t in TAGS:
        print(f"  {t:8s} cpp={len(a[t]):5d} host={len(b[t]):5d}")

    first_bad = None  # (cpp_line, tag, occ, badfields)
    nbad = 0
    for t in TAGS:
        la, lb = a[t], b[t]
        tag_reported = 0
        for i in range(min(len(la), len(lb))):
            lna, da = la[i]
            lnb, db = lb[i]
            if t == "SUBFULL":
                # the host's sub is 1-based, the cpp's 0-based (labeling, not state)
                da = dict(da)
                db = dict(db)
                if "sub" in da:
                    da["sub"] = [str(int(da["sub"][0]) + 1)]
            common = [k for k in da if k in db]
            bad = []
            for k in common:
                if da[k] != db[k]:
                    bad.append((k, da[k], db[k]))
            if bad:
                nbad += 1
                tag_reported += 1
                if first_bad is None or lna < first_bad[0]:
                    first_bad = (lna, t, i, bad, lnb)
                if tag_reported <= 2 and not quiet:
                    print(f"DIFF {t} occ={i} (cpp line {lna}, host line {lnb}):")
                    for k, va, vb in bad[:10]:
                        print(f"    {k}: cpp={va}  host={vb}")
        if len(la) != len(lb):
            tail = la[min(len(la), len(lb))][0] if len(la) > len(lb) else None
            print(f"COUNT DIFF {t}: cpp={len(la)} host={len(lb)} "
                  f"(first unpaired cpp line: {tail})")

    print(f"\npaired line mismatches: {nbad}")
    if first_bad:
        lna, t, i, bad, lnb = first_bad
        print(f"FIRST mismatch in file order: {t} occ={i} (cpp line {lna}, host line {lnb})")
        for k, va, vb in bad[:10]:
            print(f"    {k}: cpp={va}  host={vb}")
    else:
        print("ALL PAIRED LINES BIT-IDENTICAL on shared fields")


if __name__ == "__main__":
    main()
