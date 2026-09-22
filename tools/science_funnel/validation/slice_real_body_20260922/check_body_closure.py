"""check_body_closure.py -- F-BODY-CLOSURE + F-BODY-CAP.

The closure check that refused 19/25 committed previews (the aliveness
importer's own rule, importer.cpp finish()): every output mesh this lane
produces -- repaired bones, decimated bones, the merged import payload -- must
ACCEPT: zero index-degenerate faces, zero boundary edges, zero non-manifold
edges, zero winding violations. The bone count must stay 25, each output bone
1:1 with its committed source preview. F-BODY-CAP: the merged payload's
triangle count <= kMaxTris (500,000) and its sha matches the manifest pin.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))

from repair_and_decimate import K_MAX_TRIS, edge_audit, load_obj  # noqa: E402

CT_DIR = ROOT / "tools/science_funnel/data/morphosource_ct"
PREVIEW_DIR = CT_DIR / "meshes_preview"
BODY_DIR = CT_DIR / "meshes_body_20260922"
PAYLOAD = ROOT / "tools/playable_slice/standing_body.obj"


def main() -> int:
    man = json.loads((CT_DIR / "meshes" / "manifest.json").read_text())
    body_man = json.loads((BODY_DIR / "body_manifest.json").read_text())

    bones = []
    all_closed = True
    for entry in man["bones"]:
        name = Path(entry["file"]).name
        src = PREVIEW_DIR / name.replace(".obj", "_lo.obj")
        out = BODY_DIR / name.replace(".obj", "_body.obj")
        _, T_src = load_obj(src)
        aud_src = edge_audit(T_src, 10 ** 9)          # source: the measured debt
        V_out, T_out = load_obj(out)
        aud_out = edge_audit(T_out, len(V_out))
        aud_out["vertices"] = int(len(V_out))
        bones.append({"source": src.name, "output": out.name,
                      "source_closed": aud_src["closed"],
                      "source_refusals": {k: v for k, v in aud_src.items()
                                          if k.endswith(("faces", "edges", "violations"))},
                      "output_closed": aud_out["closed"],
                      "output_audit": aud_out})
        all_closed &= aud_out["closed"]

    payload_raw = PAYLOAD.read_bytes()
    payload_sha = hashlib.sha256(payload_raw).hexdigest()
    payload_V, payload_T = load_obj(PAYLOAD)
    payload_audit = edge_audit(payload_T, len(payload_V))
    payload_audit["vertices"] = int(len(payload_V))

    cap_ok = payload_audit["faces"] <= K_MAX_TRIS
    sha_ok = payload_sha == body_man["import_payload"]["sha256"]
    bones_ok = len(bones) == 25 == body_man["bone_count"]
    src_pairs_ok = all(b["source"].replace("_lo.obj", "_body.obj") == b["output"]
                       for b in bones)
    closure_ok = all_closed and payload_audit["closed"] and bones_ok and src_pairs_ok

    refused_sources = sum(1 for b in bones if not b["source_closed"])
    out = {
        "falsifier": "F-BODY-CLOSURE + F-BODY-CAP",
        "pass": bool(closure_ok and cap_ok and sha_ok),
        "measured": {
            "source_previews_refused_by_the_same_check": refused_sources,
            "source_previews_total": len(bones),
            "output_bones_closed": sum(1 for b in bones if b["output_closed"]),
            "bone_count": len(bones),
            "one_to_one_with_sources": src_pairs_ok,
            "merged_payload_triangles": payload_audit["faces"],
            "kMaxTris": K_MAX_TRIS,
            "under_cap": cap_ok,
            "payload_sha256_matches_manifest": sha_ok,
            "payload_audit": payload_audit,
            "decimated_ratio_r": body_man["ratio_r"],
        },
        "bones": bones,
        "law": "the acceptance falsifier is the importer's own closure rule "
               "(importer.cpp finish()): degenerate / boundary / non-manifold / "
               "winding, all zero, on every output mesh; the cap is the "
               "importer's own kMaxTris",
    }
    (HERE / "body_closure.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "bones"}, indent=1))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
