#!/usr/bin/env python3
"""MAT2-X04: the two-stage capture-gate stage (the standing capture-gate
template, capture_card/; the resumed dispatch's capture acceptance gate).

Consumes the sealed run's OWN committed capture artifacts from
CHIMERA_OUTPUT_DIR (frames.npy + frames_meta.json — the frozen 39-frame
plan's actual frames, already video-bound by the capture stage) and runs
every declared case (3 production + 4 defect) through the template pipeline
(prereg -> sidecar capture -> stage-0 palette + stage-1 mask co-location ->
receipts -> verification). The gate call is part of the flow: the summary is
GREEN only if every production case is GREEN and every defect case is
REJECTED with its expected dominant code. The frozen prereg's own capture
law (FFV1 + decode probes + the pinned visual_capture validator) ran UNCHANGED
in the preceding capture stage; this stage is IN ADDITION, and the gap
between the frozen prereg text and this standing gate is disclosed in
capture_card/card/card_prereg.json for the chain-stop ruling.

No subprocess; the template pipeline runs in-process (the card's only
subprocess remains run_capture_x04.py's declared ffmpeg calls).

Run:  python -B run_capture_gate_x04.py   (exit 0 green / 1 rejected / 2 refused)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CARD = HERE / "capture_card" / "card"
sys.path.insert(0, str(CARD))
sys.path.insert(0, str(HERE / "capture_card"))

OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def main() -> int:
    frames_path = OUT / "frames.npy"
    meta_path = OUT / "frames_meta.json"
    if not frames_path.exists() or not meta_path.exists():
        print("REFUSAL:capture_gate_frames_missing", file=sys.stderr)
        return 2
    frames = np.load(str(frames_path))
    meta = json.loads(meta_path.read_bytes())
    metas = meta["metas"]
    frames_by_id = {m["frame_id"]: frames[m["render_index"]]
                    for m in metas}
    manifest_path = HERE / "capture_card" / "TEMPLATE_MANIFEST.json"
    template_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    import run_all as card_run_all
    summary = card_run_all.run_cases(str(OUT / "capture_gate"), {
        "frames_by_id": frames_by_id, "metas": metas,
        "template_manifest_sha256": template_sha})

    summary["preregistration_sha256"] = json.loads(
        (OUT / "presentation_receipt.json").read_bytes()
    )["preregistration_sha256"]
    summary["case_count"] = len(summary.get("cases", {}))
    (OUT / "capture_gate_summary.json").write_bytes(canonical(summary) + b"\n")
    print("capture gate: %s (production %d frames green=%s; defects "
          "rejected=%s)" % (summary["verdict"],
                            summary.get("production_frames_total", 0),
                            summary.get("all_production_green"),
                            summary.get("all_defects_rejected")))
    return int(summary.get("exit_code", 2))


if __name__ == "__main__":
    sys.exit(main())
