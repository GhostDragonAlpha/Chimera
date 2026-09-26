"""One-shot: write reference/EXTRACTION.json with pinned provenance hashes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ref = HERE / "reference"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


PINS = {
    "chimanoid.xml": "43b599a7:forearm_package/baseline_snapshot/source_xml/chimanoid.xml",
    "mesh_target_o1.py": "c3255f74:forearm_package/audits/O1_ulna_orientation/work/mesh_target_o1.py",
    "o1_source_split.py": "c3255f74:forearm_package/audits/O1_ulna_orientation/scripts/o1_source_split.py",
}
entries = {}
for p in sorted(ref.rglob("*")):
    if p.is_file() and p.name != "EXTRACTION.json":
        rel = p.relative_to(ref).as_posix()
        pin = PINS.get(p.name)
        if pin is None:
            pin = ("c3255f74:forearm_package/audits/O1_ulna_orientation/receipts/"
                   + p.name)
        entries[rel] = {"sha256": sha(p), "bytes": p.stat().st_size, "pin": pin}
out = {
    "schema": "chimera.ota01_extraction.v1",
    "rule": "read-only extraction from git pins in E:/ChimeraWork/monkey-play-20260924; "
            "bytes preserved (hashes below); no writes to any source checkout",
    "files": entries,
}
(ref / "EXTRACTION.json").write_text(json.dumps(out, indent=2, sort_keys=True),
                                     encoding="utf-8")
print(json.dumps({k: v["sha256"][:12] for k, v in entries.items()}, indent=1))
