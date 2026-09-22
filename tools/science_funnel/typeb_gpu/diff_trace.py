"""diff_trace.py -- align two FULL-state walk traces (C++ probe / host replay /
DLL walk) and report the first bit-level divergence plus per-tick max drift.

%.17g round-trips IEEE double, so equal token strings == equal bit patterns.

Usage: python diff_trace.py <a.txt> <b.txt> [offset_b]
  offset_b: b's FULL t=N corresponds to a's FULL t=N+offset (default: auto).

Trailer Agent: GLM 5.3.
"""
import sys, re


def load(path):
    """Return {t: {name: value-string}} plus the raw line."""
    out = {}
    with open(path) as f:
        for line in f:
            if not line.startswith("FULL"):
                continue
            toks = line.split()
            t = int(toks[1].split("=")[1])
            d = {}
            for tok in toks[2:]:
                k, v = tok.split("=")
                d[k] = v
            out[t] = d
    return out


def main():
    a = load(sys.argv[1])
    b = load(sys.argv[2])
    if len(sys.argv) > 3:
        off = int(sys.argv[3])
    else:
        # auto: try offsets -2..2, pick the offset whose aligned states are
        # numerically closest (the traces are not bit-exact, so match on the
        # smallest mean state distance, not on exact string equality)
        import math

        def dist(o):
            tot, n = 0.0, 0
            for t in a:
                if t + o not in b:
                    continue
                da, db = a[t], b[t + o]
                s = 0.0
                for k in da:
                    if k in db:
                        va, vb = float(da[k]), float(db[k])
                        s += abs(va - vb) / max(abs(va), 1.0)
                tot += s
                n += 1
            return tot / max(n, 1)

        cand = {o: dist(o) for o in range(-2, 3) if o}
        off = min(cand, key=cand.get)
        print(f"auto offset = {off} (mean state dist {cand[off]:.3e}; "
              f"others {' '.join(f'{o}:{d:.1e}' for o, d in sorted(cand.items()) if o != off)})")
    common = sorted(t for t in a if t + off in b)
    first_div = None
    ndiv = 0
    for t in common:
        da, db = a[t], b[t + off]
        bad = [k for k in da if k in db and da[k] != db[k]]
        missing = [k for k in da if k not in db]
        if bad or missing:
            ndiv += 1
            if first_div is None:
                first_div = (t, bad, missing, da, db)
    print(f"compared {len(common)} aligned ticks; ticks with any token diff: {ndiv}")
    if first_div is None:
        print("BIT-EXACT on every compared component")
        return
    t, bad, missing, da, db = first_div
    print(f"FIRST divergence at aligned t={t}")
    if missing:
        print(f"  components missing in b: {missing[:8]}")
    for k in bad[:8]:
        va, vb = float(da[k]), float(db[k])
        d = abs(va - vb)
        rel = d / max(abs(va), abs(vb), 1e-300)
        print(f"  {k}: a={da[k]}  b={db[k]}  |d|={d:.3e} rel={rel:.3e}")
    # drift summary per tick after first divergence
    print("per-tick max rel drift (first 12 diverging ticks):")
    shown = 0
    for t in common:
        da, db = a[t], b[t + off]
        worst, wk = 0.0, None
        for k in da:
            if k in db and da[k] != db[k]:
                va, vb = float(da[k]), float(db[k])
                d = abs(va - vb) / max(abs(va), abs(vb), 1e-300)
                if d > worst:
                    worst, wk = d, k
        if worst > 0 and shown < 12:
            print(f"  t={t}: {worst:.3e} ({wk})")
            shown += 1


if __name__ == "__main__":
    main()
