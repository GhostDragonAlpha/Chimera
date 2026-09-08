"""dyad_topdown_capture.py -- GLM-DYAD-01: the dyad's requested ADDITIONAL views.

The round-2 dyad read asked for a near-top-down view where a raised centre
separates cleanly from the rim plane. This tool drives the ISOLATED demo
instance (the only process this task controls): it re-runs the driver for a
state (which uploads the accepted geometry and records the fixed-camera
sidecar), then immediately points the SAME instance's camera near-top-down
(phi 1.45 rad, radius 3.5 -- recorded), captures /frame, and writes a mini
sidecar binding the view to that run's upload hash (the engine's persisted
blob is corroborated against it at capture time; no other upload happens in
between). This is an explicitly-labelled DIAGNOSTIC view with its own
recorded camera -- the fixed-camera law of the demo runs is untouched.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_URL = "http://localhost:8091"
TOP_PHI = 1.45
TOP_RADIUS = 3.5
TOP_THETA = 0.0


def http_post_json(url: str, body: dict):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()


def http_get(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.status, r.read(), r.headers.get("Content-Type", "")


def blob_position_hash() -> str:
    blob = (ROOT / ".tmp/engine_demo_build/Release/session_snapshot/"
            "mesh_bin.blob").read_bytes()
    n, _ = struct.unpack_from("<II", blob, 0)
    pos = b"".join(blob[24 + i * 36: 24 + i * 36 + 12] for i in range(n))
    return hashlib.sha256(pos).hexdigest()


def main() -> int:
    stamp_base = "dyad2top"
    out = []
    for gamma, label in ((0.0, f"{stamp_base}_gamma0_bump_topdown"),
                         (1.0, f"{stamp_base}_gamma1_flat_topdown")):
        # 1. upload the state via the driver (fixed-camera capture happens too;
        #    its sidecar carries the upload hash)
        r = subprocess.run([sys.executable, str(ROOT / "tools" /
                            "membrane_window_demo.py"),
                            "--gamma", str(gamma),
                            "--engine-url", ENGINE_URL,
                            "--label", label.replace("_topdown", "")],
                           capture_output=True, text=True, cwd=ROOT)
        if r.returncode != 0:
            print(f"driver failed for gamma={gamma}:\n{r.stderr[-800:]}")
            return 1
        driver = json.loads(r.stdout[r.stdout.index("{"):])
        run_dir = Path(driver["evidence"])
        cap = json.loads((run_dir / f"{label.replace('_topdown','')}.capture.json")
                         .read_text(encoding="utf-8"))
        upload_hash = cap["state"]["upload_positions_f32le_sha256"]

        # 2. corroborate the blob still holds THIS upload, then aim top-down
        bh = blob_position_hash()
        if bh != upload_hash:
            print(f"blob mismatch for {label}: {bh} != {upload_hash}")
            return 1
        st, body = http_post_json(f"{ENGINE_URL}/camera",
                                  {"cam_radius": TOP_RADIUS,
                                   "cam_theta": TOP_THETA,
                                   "cam_phi": TOP_PHI})
        if st != 200 or b'"ok":true' not in body:
            print(f"camera post failed: {st} {body[:120]!r}")
            return 1
        st, png, ctype = http_get(f"{ENGINE_URL}/frame")
        if st != 200 or "image/png" not in ctype:
            print(f"frame failed: {st} {ctype!r}")
            return 1
        png_path = run_dir / f"{label}.png"
        png_path.write_bytes(png)
        sidecar = {
            "label": label,
            "kind": "DIAGNOSTIC extra view (dyad-requested near-top-down); "
                    "explicitly-labelled camera, not the demo's fixed camera",
            "camera": {"radius": TOP_RADIUS, "theta": TOP_THETA, "phi": TOP_PHI},
            "engine_url": ENGINE_URL,
            "png_file": str(png_path.relative_to(ROOT)),
            "png_sha256": hashlib.sha256(png).hexdigest(),
            "upload_positions_f32le_sha256": upload_hash,
            "blob_position_hash_at_capture": bh,
            "state_id": cap["state_id"],
            "state": cap["state"],
        }
        (run_dir / f"{label}.capture.json").write_text(
            json.dumps(sidecar, indent=2), encoding="utf-8")
        out.append({"label": label, "png": str(png_path.relative_to(ROOT)),
                    "sha256": sidecar["png_sha256"],
                    "upload_sha256": upload_hash})
        print(f"{label}: captured, upload corroboration MATCH")
    (ROOT / "docs/evidence/membrane_window_demo"
     / f"{stamp_base}_views.json").write_text(json.dumps(out, indent=2),
                                              encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
