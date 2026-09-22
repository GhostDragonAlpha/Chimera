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
    # align by (prefix, t, sub): the C++ driver's tick index and the kernels'
    # a_ticks differ by the trace offset; SUBPRE sub k of tick T pairs with
    # the record printed for the same (T, k). Build dicts keyed for lookup.
    def key(rec):
        pfx, sub, toks = rec
        t = 0
        for tok in toks[1:]:
            if tok.startswith("t="):
                t = int(tok.split("=")[1])
                break
        return (pfx, t, sub)
    bmap = {}
    for rec in b:
        bmap.setdefault(key(rec), []).append(rec)
    matched = 0
    for rec in a:
        k = key(rec)
        # c++ ticks_==ticks after ++; the kernels print BEFORE increment:
        # c++ tick T (ticks_=T during step T+1's print? we printed with the
        # live ticks_ value) -- try both offsets.
        cands = [(k[0], k[1], k[2]), (k[0], k[1] + 1, k[2]), (k[0], k[1] - 1, k[2])]
        hit = None
        for cc in cands:
            if cc in bmap and bmap[cc]:
                hit = cc
                break
        if hit is None:
            print(f"{rec[0]} t={k[1]} sub={k[2]}: no kernels counterpart")
            continue
        pb, sb, tb = bmap[hit].pop(0)
        matched += 1
        da = {}
        for tok in rec[2][3:]:
            kk, v = tok.split("=", 1)
            da[kk] = v
        db = {}
        for tok in tb[3:]:
            kk, v = tok.split("=", 1)
            db[kk] = v
        bad = []
        for kk, va in da.items():
            vb = db.get(kk)
            if vb is None:
                bad.append((kk, va, "<missing>", -1))
            elif va != vb:
                d = abs(float(va) - float(vb))
                bad.append((kk, va, vb, d))
        tag = f"{rec[0]} t={k[1]} sub={rec[1]}"
        if not bad:
            print(f"{tag}: BIT-EXACT ({len(da)} components)")
        else:
            bad.sort(key=lambda x: -x[3])
            print(f"{tag}: {len(bad)} diffs (worst first)")
            for kk, va, vb, d in bad[:4]:
                if d < 0:
                    print(f"   {kk}: cpp={va} ker={vb}")
                    continue
                va_f, vb_f = float(va), float(vb)
                rel = d / max(abs(va_f), 1e-300)
                print(f"   {kk}: cpp={va} ker={vb} |d|={d:.3e} rel={rel:.3e}")
    print(f"matched {matched} record pairs")
if __name__ == "__main__":
    main()
