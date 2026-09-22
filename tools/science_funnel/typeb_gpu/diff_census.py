"""diff_census.py -- compare the per-substep drill dumps (SUBPRE/TAUFULL/
SUBFULL lines) between the C++ drill (csub_tick1.txt) and the kernels host
replay (ksub_tick1.txt) at token granularity; rank divergences.

Usage: python diff_census.py [csub_file] [ksub_file]
Trailer Agent: GLM 5.3.
"""
import sys

PREFIX_ORDER = {"SUBPRE": 0, "TAUFULL": 1, "SUBFULL": 2}


def load(path):
    out = []
    for line in open(path, errors="replace"):
        for p in PREFIX_ORDER:
            if line.startswith(p):
                toks = line.split()
                sub = int(toks[1].split("=")[1]) if False else int(toks[2].split("=")[1])
                out.append((p, sub, toks))
                break
    return out


def main():
    fa = sys.argv[1] if len(sys.argv) > 1 else "csub_tick1.txt"
    fb = sys.argv[2] if len(sys.argv) > 2 else "ksub_tick1.txt"
    a, b = load(fa), load(fb)
    print(f"c++ records: {len(a)}, kernels records: {len(b)}")
    for (pa, sa, ta), (pb, sb, tb) in zip(a, b):
        # keys: tokens after the sub= token; align by key name
        da = {}
        for tok in ta[3:]:
            k, v = tok.split("=", 1)
            da[k] = v
        db = {}
        for tok in tb[3:]:
            k, v = tok.split("=", 1)
            db[k] = v
        bad = []
        for k, va in da.items():
            vb = db.get(k)
            if vb is None:
                bad.append((k, va, "<missing>", -1))
            elif va != vb:
                d = abs(float(va) - float(vb))
                bad.append((k, va, vb, d))
        extra = [k for k in db if k not in da]
        tag = f"{pa} sub={sa}"
        if not bad and not extra:
            print(f"{tag}: BIT-EXACT ({len(da)} components)")
        else:
            bad.sort(key=lambda x: -x[3])
            print(f"{tag}: {len(bad)} diffs (worst first)"
                  + (f"; extra-in-b: {extra[:4]}" if extra else ""))
            for k, va, vb, d in bad[:6]:
                if d < 0:
                    print(f"   {k}: cpp={va} ker={vb}")
                    continue
                va_f, vb_f = float(va), float(vb)
                rel = d / max(abs(va_f), 1e-300)
                ulp = d * 2**52 / max(abs(va_f), 2.2e-308) if va_f else float("inf")
                print(f"   {k}: cpp={va} ker={vb} |d|={d:.3e} rel={rel:.3e} ~{ulp:.1f} ulp")


if __name__ == "__main__":
    main()
