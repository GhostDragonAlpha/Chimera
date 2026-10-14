"""CLI for fast, deterministic wave-2 proof bundles.

Use from the repository root:
  python -m tools.science_funnel.parallel_visual_proof --out tools/science_funnel/validation/visual_proof_wave2_20260918 --workers 8

The main guard is required on Windows because workers use spawn semantics.
"""
import argparse
import multiprocessing
import time
from pathlib import Path

from .visual_proof_wave2 import build_wave2_renders, verify_wave2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--workers', default='auto',
                        help='bounded worker processes, integer or auto; small bundles stay serial')
    parser.add_argument('--profile', action='store_true',
                        help='print elapsed seconds and throughput')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args(argv)
    multiprocessing.freeze_support()
    if args.verify:
        for rid in verify_wave2(args.out):
            print(f'VERIFIED {rid}')
        return 0
    started = time.perf_counter()
    manifest = build_wave2_renders(args.out, workers=args.workers)
    elapsed = time.perf_counter() - started
    print(f"RENDERED {len(manifest['renders'])} wave-2 proofs with {manifest['workers']} workers")
    if args.profile:
        print(f"PROFILE seconds={elapsed:.3f} proofs_per_second={len(manifest['renders']) / max(elapsed, 1e-9):.3f}")
    for render in manifest['renders']:
        print(f"  {render['id']} {render['png_sha256'][:16]}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
