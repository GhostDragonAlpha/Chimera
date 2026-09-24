"""A9 quarantine integrity checks — verifies MANIFEST against snapshot files and
the live absolute-path inputs against the snapshot copies. Read-only elsewhere."""
import hashlib
import json
import sys
from pathlib import Path

SNAP = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
AUD = Path(r"E:\PythonChimera\forearm_package\audits\A9_reproduce")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    man = json.loads((SNAP / "MANIFEST.json").read_text(encoding="utf-8"))
    bad = []
    n = 0
    for rel, rec in man["files"].items():
        p = SNAP / rel
        if not p.is_file():
            bad.append((rel, "MISSING"))
            continue
        b = p.stat().st_size
        h = sha256(p)
        n += 1
        if b != rec["bytes"] or h != rec["sha256"]:
            bad.append((rel, f"size {b} vs {rec['bytes']}, sha {h} vs {rec['sha256']}"))
    print(f"MANIFEST verification: {n} files checked, {len(bad)} mismatches")
    for r in bad:
        print("  MISMATCH:", r)

    print("\n-- live absolute-path inputs vs snapshot copies --")
    pairs = [
        (r"E:\PythonChimera\.tmp\chimanoid.xml", SNAP / "source_xml/chimanoid.xml"),
        (r"E:\PythonChimera\Saved\meshes\monkey_birth.bin", SNAP / "inputs/monkey_birth.bin"),
        (r"E:\PythonChimera\Saved\meshes\monkey_joints.bin", SNAP / "inputs/monkey_joints.bin"),
    ]
    for live, snap in pairs:
        if not Path(live).is_file():
            print(f"  {live}: MISSING (CRITICAL for regeneration)")
            continue
        lh, sh = sha256(Path(live)), sha256(snap)
        print(f"  {live}\n    live {lh}\n    snap {sh}  {'MATCH' if lh == sh else 'DIFFER'}")

    print("\n-- live .tmp/anatomy_compiler vs snapshot (code + runs) --")
    live_root = Path(r"E:\PythonChimera\.tmp\anatomy_compiler")
    for sub in ("code", "runs"):
        live_d, snap_d = live_root / sub, SNAP / sub
        live_files = sorted(p for p in live_d.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        snap_files = sorted(p for p in snap_d.rglob("*") if p.is_file())
        live_h = {p.relative_path if False else p.name: sha256(p) for p in live_files}
        snap_h = {p.name: sha256(p) for p in snap_files}
        same = {k for k in live_h if k in snap_h and live_h[k] == snap_h[k]}
        only_live = sorted(set(live_h) - set(snap_h))
        only_snap = sorted(set(snap_h) - set(live_h))
        diff = sorted(k for k in live_h if k in snap_h and live_h[k] != snap_h[k])
        print(f"  {sub}: live={len(live_files)} snap={len(snap_files)} identical={len(same)} "
              f"only_live={only_live} only_snap={only_snap} differing={diff}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
