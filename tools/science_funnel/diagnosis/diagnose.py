"""diagnose.py -- the packet CLI.

  python -m tools.science_funnel.diagnosis.diagnose \
    --trace .tmp/diag_fixtures/w37comp_tr_stderr.txt \
    --stdout .tmp/diag_fixtures/w37comp_tr_stdout.txt \
    --receipt tools/science_funnel/validation/gait_zero_20260919/receipt_wave37.json \
    [--reference-trace ... --reference-stdout ...] \
    [--prior-library tools/science_funnel/diagnosis/prior_faces.json] \
    [--prior-waves-through 37] [--tick-hz 300] [--out packet.json]

Defaults for --prior-waves-through come from the receipt's own wave number, so
only STRICTLY PRIOR waves enter the match (F-DIAGNOSIS-LEAK).
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from .packet import build_packet, render_text, wave_of_receipt
from .falsifiers import Receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="machine-generated failure-analysis packet")
    ap.add_argument("--trace", required=True)
    ap.add_argument("--stdout", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--reference-trace")
    ap.add_argument("--reference-stdout")
    ap.add_argument("--prior-library", default=None)
    ap.add_argument("--prior-waves-through", type=int, default=None)
    ap.add_argument("--tick-hz", type=float, default=300.0)
    ap.add_argument("--reference-role", choices=("baseline", "parent"), default="baseline",
                    help="baseline = the accepted predecessor (launch drifts are death seeds); "
                         "parent = the amended law the run composes (its calendar changes are the "
                         "hypothesis under test, never a death seed)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    t0 = time.time()
    pkt = build_packet(args.trace, args.stdout, args.receipt,
                       reference_trace=args.reference_trace,
                       reference_stdout=args.reference_stdout,
                       prior_library=args.prior_library,
                       prior_waves_through=args.prior_waves_through,
                       tick_hz=args.tick_hz, reference_role=args.reference_role)
    pkt["generation"] = dict(seconds=round(time.time() - t0, 3),
                             pass_count=1,
                             inputs=dict(trace=args.trace, stdout=args.stdout, receipt=args.receipt,
                                         reference_trace=args.reference_trace,
                                         reference_role=args.reference_role,
                                         prior_library=args.prior_library))
    text = render_text(pkt)
    blob = json.dumps(pkt, indent=1, ensure_ascii=False, default=str)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(blob + "\n")
    print(text)
    print()
    print(f"[packet] {len(blob)} bytes, generated in {pkt['generation']['seconds']} s (one pass)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
