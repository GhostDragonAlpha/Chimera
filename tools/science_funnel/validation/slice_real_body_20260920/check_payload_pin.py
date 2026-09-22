"""check_payload_pin.py -- F-PAYLOAD-PIN: byte identity of the real body's
import payload (lane slice_real_body_20260920, falsifier named in record.md
BEFORE this run).

Two byte-identity claims, both measured here:

  1. CHECKOUT INVARIANCE: the working-tree `standing_body.obj` -- as this
     checkout holds it -- hashes to the sha256 pinned in
     meshes_body_20260922/body_manifest.json. (The CRLF lesson: under
     `* text=auto` a fresh checkout rewrote the payload's LF bytes and broke
     the pin; .gitattributes now carries `tools/playable_slice/*.obj -text`,
     and this check holds that fix to its word.)

  2. COMPOSE DETERMINISM: the payload re-derives BYTE-IDENTICALLY in process
     from the committed body bones through the SAME compose function the ghost
     runs live (scene_boot.build_standing_layer, pose.json + the pinned
     registration) and the SAME writer that produced it
     (repair_and_decimate.write_obj), written to a throwaway path -- the
     committed payload itself is never touched. Identical bytes = the compose
     is a pure function of committed files, which is what F-SLICE-RESTART's
     scene sha rides on.

Pass = both shas == pin, and the recomposed counts == the pin's counts, and
the payload is under the importer's own kMaxTris.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation"
                       / "slice_real_body_20260922"))
sys.path.insert(0, str(ROOT / "tools" / "playable_slice"))

import scene_boot as sb  # noqa: E402
import repair_and_decimate as rad  # noqa: E402

BODY_DIR = ROOT / ("tools/science_funnel/data/morphosource_ct/"
                   "meshes_body_20260922")
PAYLOAD = ROOT / "tools/playable_slice/standing_body.obj"
TMP = ROOT / ".tmp" / "realbody_pin_check"

# the exact header literal repair_and_decimate.main() wrote the payload with
HEADER = [
    b"# chimera.playable_slice REAL[physics_body] import payload",
    b"# the committed CT skeleton, repaired + decimated under the importer's",
    b"# kMaxTris (meshes_body_20260922), posed by scene_boot.build_standing_layer",
    b"# -- the SAME compose the ghost runs live (scene metres, pads' mean plane",
    b"# at y=0); sha pinned in meshes_body_20260922/body_manifest.json",
]


def main() -> int:
    man = json.loads((BODY_DIR / "body_manifest.json").read_text())
    pin = man["import_payload"]

    worktree_raw = PAYLOAD.read_bytes()
    sha_worktree = hashlib.sha256(worktree_raw).hexdigest()

    verts, tris, compose_rec = sb.build_standing_layer(
        preview_dir=BODY_DIR, obj_suffix="_body")
    TMP.mkdir(parents=True, exist_ok=True)
    recomposed_raw = rad.write_obj(TMP / "recomposed_body.obj",
                                   verts, tris, HEADER)
    sha_recomposed = hashlib.sha256(recomposed_raw).hexdigest()

    checkout_ok = sha_worktree == pin["sha256"]
    compose_ok = sha_recomposed == pin["sha256"]
    counts_ok = (int(len(verts)) == int(pin["vertices"])
                 and int(len(tris)) == int(pin["triangles"]))
    cap_ok = int(pin["triangles"]) <= rad.K_MAX_TRIS
    ok = bool(checkout_ok and compose_ok and counts_ok and cap_ok)

    out = {
        "falsifier": "F-PAYLOAD-PIN",
        "pass": ok,
        "measured": {
            "pin_sha256": pin["sha256"],
            "worktree_sha256": sha_worktree,
            "recomposed_sha256": sha_recomposed,
            "checkout_invariance": checkout_ok,
            "compose_determinism": compose_ok,
            "counts_match": counts_ok,
            "vertices": int(len(verts)), "triangles": int(len(tris)),
            "kMaxTris": rad.K_MAX_TRIS, "under_cap": cap_ok,
        },
        "compose_record": compose_rec,
        "law": "the import payload is committed bytes: a pure function of the "
               "committed body bones + pose.json + the pinned registration, "
               "checkout-invariant (-text), recomposable byte-for-byte",
    }
    (HERE / "payload_pin.json").write_text(json.dumps(out, indent=1),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "compose_record"},
                     indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
