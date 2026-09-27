"""child_load_probe.py -- MAT2-U04 persistence leg, CHILD side.

Runs in a SEPARATE OS process (spawned by input_settings_probe.py):
loads the saved settings file with the REAL pinned input_settings module in
this fresh interpreter, applies it to a fresh pinned InputMapper, replays the
FROZEN replay sequence (identical injected clock to the parent's), and writes
one JSON payload for the parent to compare field-exact.

    python -B child_load_probe.py <settings.json> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"

PINNED_SHA = {
    "tools/monkey_campaign/product/input_settings.py":
        "8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1",
    "tools/monkey_campaign/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "tools/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
}

TICK_MS = 50
REPLAY_MOUSE = (100, 300, 2)


def main() -> int:
    settings_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    for rel, want in PINNED_SHA.items():
        got = hashlib.sha256((REFERENCE / rel).read_bytes()).hexdigest()
        if got != want:
            raise SystemExit("PIN DRIFT (child): %s" % rel)
    sys.path.insert(0, str(REFERENCE))
    for stale in [k for k in sys.modules if k == "tools" or k.startswith("tools.")]:
        del sys.modules[stale]
    from tools.monkey_campaign.product import input_settings as IS

    lr = IS.load_settings(settings_path)
    records = []
    if lr.status == "loaded":
        mapper = IS.configured_mapper(__import__("tools.monkey_campaign.product."
                                                 "input_mapper", fromlist=["x"])
                                      .MockSink(), lr.settings)
        presses = {0: ["W"], 50: ["A"]}
        releases = {350: ["A"], 400: ["W"]}
        for now in range(0, 501, TICK_MS):
            for name in presses.get(now, []):
                mapper.press(name, now)
            if REPLAY_MOUSE[0] <= now <= REPLAY_MOUSE[1]:
                mapper.mouse(REPLAY_MOUSE[2])
            for name in releases.get(now, []):
                mapper.release(name, now)
            for rec in mapper.tick(now):
                records.append({"v_forward": rec.v_forward,
                                "yaw_rate": rec.yaw_rate,
                                "issued_tick": rec.issued_tick,
                                "source": rec.source,
                                "record_version": rec.record_version})
    payload = {
        "pid": os.getpid(),
        "python": sys.version.split()[0],
        "status": lr.status,
        "refusals": [r.code for r in lr.refusals],
        "settings_document": lr.settings.to_document(),
        "settings_file_sha256": hashlib.sha256(
            settings_path.read_bytes()).hexdigest(),
        "records": records,
    }
    out_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
