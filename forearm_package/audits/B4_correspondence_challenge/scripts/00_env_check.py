"""00 — environment check: snapshot integrity vs MANIFEST, constant citations.

Verifies the snapshot inputs are byte-identical to the MANIFEST's recorded hashes
before anything is run, and cites the measured tolerance constants from the baseline.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b4_common import B4, MANIFEST_PATH, SNAP, XML_PATH, save_receipt, verdict  # noqa: E402

import re  # noqa: E402


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    checks = []
    for rel, meta in manifest["files"].items():
        p = SNAP / rel
        h = sha256_of(p)
        checks.append({"file": rel, "sha256_ok": h == meta["sha256"],
                       "bytes_ok": p.stat().st_size == meta["bytes"]})
    bad = [c for c in checks if not (c["sha256_ok"] and c["bytes_ok"])]
    verdict("snapshot integrity vs MANIFEST", not bad,
            f"{len(checks)} files checked, {len(bad)} mismatched" + (f": {bad}" if bad else ""))

    # constant citations: grep the measured values + line numbers out of the baseline
    comp = (SNAP / "code" / "compiler.py").read_text(encoding="utf-8").splitlines()
    hits = {}
    for i, line in enumerate(comp, start=1):
        m = re.search(r"^(FD_EPS|JOINT_EPS|ROLL_EPS)\s*=\s*([0-9.eE+-]+)", line)
        if m:
            hits[m.group(1)] = {"value": float(m.group(2)), "line": i}
    corr = (SNAP / "code" / "correspondence.py").read_text(encoding="utf-8")
    hits["frame_orthogonality_1e-6_in_correspondence"] = "1e-6" in corr
    verdict("constants present", hits.get("JOINT_EPS", {}).get("value") == 1e-9
            and hits.get("ROLL_EPS", {}).get("value") == 1e-9,
            str(hits))

    save_receipt("00_env_check.json", {
        "snapshot_files_checked": len(checks),
        "mismatches": bad,
        "constants": hits,
        "xml_path": str(XML_PATH),
    })
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
