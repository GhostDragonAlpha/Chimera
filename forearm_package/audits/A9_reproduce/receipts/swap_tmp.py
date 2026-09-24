"""A9 swap: rename live .tmp/anatomy_compiler aside, junction it to the quarantine
work/ dir. Also writes a restoration manifest of the live tree first."""
import hashlib
import json
import os
import sys
from pathlib import Path

LIVE = Path(r"E:\PythonChimera\.tmp\anatomy_compiler")
HOLD = Path(r"E:\PythonChimera\.tmp\anatomy_compiler_A9_hold")
WORK = Path(r"E:\PythonChimera\forearm_package\audits\A9_reproduce\work")
REC = Path(r"E:\PythonChimera\forearm_package\audits\A9_reproduce\receipts")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_manifest(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root)).replace("\\", "/")] = [p.stat().st_size, sha256(p)]
    return out


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "swap"
    if action == "manifest":
        man = {"live": tree_manifest(LIVE), "hold": None, "work_after": None}
        (REC / "restore_manifest_live.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
        print(f"manifest: {len(man['live'])} files recorded from live tree")
        return 0
    if action == "swap":
        (REC / "restore_manifest_live.json").write_text(
            json.dumps({"live": tree_manifest(LIVE)}, indent=1), encoding="utf-8")
        if HOLD.exists():
            print("HOLD dir already exists - aborting to avoid clobber", file=sys.stderr)
            return 2
        os.rename(LIVE, HOLD)
        print(f"renamed {LIVE} -> {HOLD}")
        import _winapi
        _winapi.CreateJunction(str(WORK), str(LIVE))
        print(f"junction {LIVE} -> {WORK}")
        return 0
    if action == "restore":
        # verify work/ (via junction) then remove junction, rename hold back
        assert LIVE.is_symlink() or os.path.islink(str(LIVE)) or (
            Path(os.path.realpath(str(LIVE))) == WORK), "LIVE is not a junction anymore?"
        os.remove(str(LIVE))  # removes the junction reparse point, not the target
        print("junction removed")
        os.rename(HOLD, LIVE)
        print(f"restored {LIVE} from hold")
        orig = json.loads((REC / "restore_manifest_live.json").read_text())["live"]
        now = tree_manifest(LIVE)
        if orig == now:
            print(f"RESTORE VERIFIED: {len(now)} files byte-identical to pre-audit state")
        else:
            only_orig = sorted(set(orig) - set(now))
            only_now = sorted(set(now) - set(orig))
            diff = sorted(k for k in orig if k in now and orig[k] != now[k])
            print(f"RESTORE MISMATCH: only_orig={only_orig} only_now={only_now} diff={diff}")
            return 1
        return 0
    print("unknown action", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
