"""CLI: run the deterministic reference-data import.

  python run_import.py                 # fetch/verify pins + import (idempotent)
  python run_import.py --refresh       # re-download + re-pin (human decision)
  python run_import.py --force-rebuild # rebuild the store from the cache
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import import_reference  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true",
                    help="re-download artifacts and re-pin checksums")
    ap.add_argument("--force-rebuild", action="store_true",
                    help="rebuild the reference store from scratch")
    args = ap.parse_args()
    report = import_reference.import_all(refresh=args.refresh,
                                         force_rebuild=args.force_rebuild)
    print(json.dumps({k: v for k, v in report.items() if k != "metas"},
                     indent=1, ensure_ascii=False))
    for src, meta in report.get("metas", {}).items():
        print(f"[{src}] {meta}")


if __name__ == "__main__":
    main()
