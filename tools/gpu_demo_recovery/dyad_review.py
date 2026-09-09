#!/usr/bin/env python
"""dyad_review.py -- GPU-DEMO-RECOVERY-01 DYAD phase (protocol-compliant).

One screenshot per watch_one call. Brief-me-first prompts carry the defect
history + physical context. Structured, non-leading questions. Records
prompts, raw responses, image hashes, and linked state identities.
Requires PYTHONIOENCODING=utf-8 (dyad emits typographic characters).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "gpu_demo_recovery"))
sys.path.insert(0, str(TOOLS / "gpu_fixtures_recovered"))
sys.path.insert(0, str(TOOLS.parent / "ChimeraEngine"))

from md_client import pack_upload, http_post, http_get, sha  # noqa: E402
from membrane_fixture_b2 import b2_mesh  # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8093
BASE = f"http://localhost:{PORT}"
EVID = Path("docs/evidence/gpu_demo_recovery")
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
OUTDIR = EVID / f"dyad_{STAMP}"
OUTDIR.mkdir(parents=True, exist_ok=True)

BRIEF = (
    "Context: isolated Vulkan engine demo of a constant-gamma surface-energy "
    "membrane (B2 fixture: hexagonal fan, 6 rim vertices pinned, centre vertex "
    "on a vertical rail, gamma=1 J/m^2). Prior review round (contrast-01): the "
    "membrane centre was locatable but its height was visually INCONCLUSIVE. "
    "Fixed camera. The membrane renders pale against a dark scene."
)

QUESTIONS = (
    "Answer with numbered items only:\n"
    "1. Describe the central object in this image (shape, extent, position).\n"
    "2. Is there a single worst visual defect (tearing, clipping, absence,\n"
    "   wrong colors, overlay text obscuring the object)? Name it or say none.\n"
    "3. Where is the brightest compact feature? "
    "(clock-face position + fraction from centre)"
)


def post_bin(blob):
    s, body, _ = http_post(f"{BASE}/membrane_demo_bin", blob,
                           "application/octet-stream", timeout=70.0)
    return s, json.loads(body.decode())


def ctl(payload):
    raw = json.dumps(payload).encode()
    s, body, _ = http_post(f"{BASE}/membrane_demo", raw, "application/json",
                           timeout=120.0)
    return s, json.loads(body.decode())


def frame(label):
    s, body, _ = http_get(f"{BASE}/frame", timeout=30.0)
    p = OUTDIR / f"{label}.png"
    if s == 200 and body[:4] == b"\x89PNG":
        p.write_bytes(body)
    return p, sha(body), len(body)


def main():
    from senses import watch_one, dyad_model, resident_model  # noqa: E402
    print("dyad model (requested):", dyad_model())
    try:
        print("resident:", resident_model())
    except Exception as e:
        print("resident probe:", e)

    _, V_up, F = b2_mesh()
    blob = pack_upload(V_up.astype(np.float32), F, 1.0, 6, 0.5)
    records = []

    # state 1: initial
    _, st = post_bin(blob)
    p1, h1, n1 = frame("dyad_initial")
    r1 = {"label": "initial", "energy": st["energy"],
          "centre": st["centre"], "accepted_id": st["accepted_state_id"],
          "render_id": st["render_state_id"], "png": str(p1),
          "png_sha": h1, "png_bytes": n1}
    # state 2: intermediate (~10 accepted steps)
    for _ in range(10):
        ctl({"op": "step"})
    _, st = post_bin(blob) if False else (None, None)
    import urllib.request as _u
    with _u.urlopen(f"{BASE}/membrane_demo", timeout=15.0) as r:
        st = json.loads(r.read().decode())
    p2, h2, n2 = frame("dyad_mid")
    r2 = {"label": "mid", "energy": st["energy"], "centre": st["centre"],
          "accepted_id": st["accepted_state_id"],
          "render_id": st["render_state_id"], "png": str(p2),
          "png_sha": h2, "png_bytes": n2}
    # state 3: final relaxed
    ctl({"op": "run", "n_steps": 5000})
    with _u.urlopen(f"{BASE}/membrane_demo", timeout=15.0) as r:
        st = json.loads(r.read().decode())
    p3, h3, n3 = frame("dyad_final")
    r3 = {"label": "final", "energy": st["energy"], "centre": st["centre"],
          "accepted_id": st["accepted_state_id"],
          "render_id": st["render_state_id"], "png": str(p3),
          "png_sha": h3, "png_bytes": n3}

    for rec in (r1, r2, r3):
        prompt = (f"{BRIEF}\nState: {rec['label']}: energy={rec['energy']:.8f} J, "
                  f"centre={rec['centre']}, accepted_id={rec['accepted_id']}, "
                  f"render_id={rec['render_id']}.\n{QUESTIONS}")
        rec["prompt"] = prompt
        print(f"--- watch_one({rec['label']}) sha={rec['png_sha'][:12]} ---")
        try:
            resp = watch_one(str(rec["png"]), prompt)
        except Exception as e:
            resp = f"WATCH_ERROR: {type(e).__name__}: {e}"
        rec["response"] = resp
        print((resp or "(none)")[:1200])
        records.append(rec)

    (OUTDIR / "dyad_records.json").write_text(
        json.dumps({"model_requested": dyad_model(), "records": records},
                   indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"evidence: {OUTDIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
