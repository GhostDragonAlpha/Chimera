"""Revalidate the merged ONT-A04 capture manifest against the MAT2-A04 envelope.

Prediction P5 of this attempt's frozen PREREGISTRATION.md: the merged
capture_manifest.json (byte-pinned 4447058a...) validates structurally under the
campaign validator visual_capture.validate_manifest when bound to the current-era
envelope (card_task.json, task_id "A04", scope cb5475f8...), context subject
33d3219c..., capture 878eb3de..., tick_interval [0,0].

Read-only over both contribution trees; writes only the receipt path given on the
command line. CPU-only, stdlib.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRIB = HERE.parent
ONT = CONTRIB.parent / "ONT-A04"


def load_campaign_validator():
    """Import tools/monkey_campaign/visual_capture.py.

    Default: the repo checkout this contribution lives in. --campaign-dir overrides
    (used when the sparse attempt checkout does not materialize the campaign file;
    the override must point at a directory containing visual_capture.py extracted
    read-only from the same base commit).
    """
    args = sys.argv[1:]
    campaign = None
    if "--campaign-dir" in args:
        campaign = Path(args[args.index("--campaign-dir") + 1]).resolve()
    if campaign is None:
        campaign = CONTRIB.parents[1]  # .../tools/monkey_campaign
    sys.path.insert(0, str(campaign))
    import visual_capture

    return visual_capture


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    vc = load_campaign_validator()

    manifest_path = ONT / "evidence" / "capture_manifest.json"
    envelope_path = CONTRIB / "card_task.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))

    manifest_sha = sha256(manifest_path)
    png_sha = sha256(ONT / "evidence" / "capture_a04.png")
    state_sha = sha256(ONT / "evidence" / "state_snapshot.json")

    profile = envelope["task"]["verification_profile"]
    context = {
        "task_id": envelope["task_id"],
        "subject_sha256": state_sha,
        "run_id": "ont-a04-anatomy-20260926-d9e5561a",
        "capture_sha256": png_sha,
        "tick_interval": [0, 0],
    }

    result = vc.validate_manifest(manifest, context, profile)

    receipt = {
        "schema": "mat2-a04.capture_manifest_revalidation.v1",
        "validator": "tools/monkey_campaign/visual_capture.py validate_manifest",
        "manifest": {
            "path": "tools/monkey_campaign/contributions/ONT-A04/evidence/capture_manifest.json",
            "sha256": manifest_sha,
        },
        "capture_png_sha256": png_sha,
        "state_snapshot_sha256": state_sha,
        "envelope": {
            "path": "tools/monkey_campaign/contributions/MAT2-A04/card_task.json",
            "task_id": envelope["task_id"],
            "scope_sha256": envelope["scope_sha256"],
            "profile_id": profile["id"],
            "profile_kind": profile["kind"],
        },
        "context_tick_interval": context["tick_interval"],
        "run_id": context["run_id"],
        "structurally_valid": bool(result.get("structurally_valid")),
        "fired": result.get("fired"),
        "result": result,
    }

    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
    else:
        out = HERE / "P5_manifest_revalidation.json"
    out.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("structurally_valid=%s fired=%s manifest=%s"
          % (receipt["structurally_valid"], receipt["fired"], manifest_sha[:12]))
    return 0 if receipt["structurally_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
