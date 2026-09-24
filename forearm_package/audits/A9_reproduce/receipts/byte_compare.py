"""A9 byte-comparison: gen1 vs gen2 (determinism) and gen2 vs baseline (identity)."""
import hashlib
import json
import sys
from pathlib import Path

AUD = Path(r"E:\PythonChimera\forearm_package\audits\A9_reproduce")
REGEN1 = AUD / "regen1"
REGEN2 = AUD / "work" / "runs"
SNAP = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot") / "runs"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def first_diff(a: Path, b: Path) -> int:
    with open(a, "rb") as fa, open(b, "rb") as fb:
        i = 0
        while True:
            ca, cb = fa.read(1 << 16), fb.read(1 << 16)
            if ca != cb:
                n = min(len(ca), len(cb))
                for j in range(n):
                    if ca[j] != cb[j]:
                        return i + j
                return i + n
            if not ca:
                return -1
            i += len(ca)
    return -1


def main() -> int:
    names = sorted(p.name for p in SNAP.iterdir() if p.is_file())
    rows = []
    for n in names:
        s, r1, r2 = SNAP / n, REGEN1 / n, REGEN2 / n
        hs, h1, h2 = sha256(s), sha256(r1), sha256(r2)
        det = "IDENTICAL" if h1 == h2 else "DIFFER"
        ident = "IDENTICAL" if h2 == hs else "DIFFER"
        off = first_diff(r2, s) if h2 != hs else ""
        rows.append((n, hs, h1, h2, det, ident, off))
        print(f"{n}\n  baseline {hs}\n  gen1     {h1}\n  gen2     {h2}\n  det(gen1==gen2): {det}   vs_baseline(gen2==baseline): {ident}  first_diff_offset: {off}")
    (AUD / "receipts" / "byte_compare.json").write_text(json.dumps(
        [{"file": r[0], "baseline_sha256": r[1], "gen1_sha256": r[2], "gen2_sha256": r[3],
          "gen1_vs_gen2": r[4], "gen2_vs_baseline": r[5], "first_diff_offset": r[6]} for r in rows],
        indent=1), encoding="utf-8")
    print("\nSUMMARY:")
    print("  determinism failures (gen1!=gen2):", [r[0] for r in rows if r[4] != "IDENTICAL"])
    print("  baseline-identity failures (gen2!=baseline):", [r[0] for r in rows if r[5] != "IDENTICAL"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
