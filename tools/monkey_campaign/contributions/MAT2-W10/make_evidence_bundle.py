#!/usr/bin/env python3
"""MAT2-W10: deterministic evidence bundle (runner --keep single artifact).

Packs every produced evidence file of the card (receipts, capture set,
checks receipt, REPORT.md) into ONE deterministically-ordered zip with fixed
timestamps so the runner's declared-output preservation keeps the whole set.
The canonical bytes remain the individual files; the bundle is transport.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "evidence_bundle.zip"

PATTERNS = [
    "receipts/*.json",
    "capture/*.json",
    "capture/*.mkv",
    "capture/*.bmp",
    "checks_receipt.json",
    "REPORT.md",
    "DEV_RUN_REFUSALS.md",
]


def main() -> int:
    files = []
    for pattern in PATTERNS:
        files.extend(sorted(p for p in HERE.glob(pattern) if p.is_file()))
    seen = set()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_STORED) as zf:
        for path in sorted(files):
            rel = path.relative_to(HERE).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    print("bundle:", OUT.name, "files:", len(seen),
          "bytes:", OUT.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
