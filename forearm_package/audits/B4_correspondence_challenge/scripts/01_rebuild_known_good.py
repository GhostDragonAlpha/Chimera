"""01 — extract the KNOWN-GOOD (radius/radius_l) effective correspondence.

Rebuilds the authored correspondence exactly as the baseline's own builder does
(code/actual_target_fit.py::build_correspondence_envelope) against the snapshot
inputs, verifies the canonical correspondence digest equals the one recorded in the
fit packet provenance (input_files[3]), then extracts the declared landmark records
for radius + radius_l (target P/P_d/Q, source resolutions, source coordinates).

Read-only. No fitting, no moment arms, no path lengths (T6).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b4_common as C  # noqa: E402

sys.path.insert(0, str(C.B4 / "work" / "modules"))

import synthetic_fixtures as SF  # noqa: E402
from intake import global_site_positions, load_source  # noqa: E402
from mesh_target import MonkeyTarget  # noqa: E402
from actual_target_fit import _correspondence_digest, build_correspondence_envelope  # noqa: E402


def resolve_source(corr, ana) -> dict:
    """Local re-implementation of the source-landmark resolution (compiler law),
    kept dependency-light and arm-free."""
    sw = global_site_positions(ana)
    out = {}
    for lid, resolution in corr.source_landmarks.items():
        kind, _, name = resolution.partition(":")
        if kind == "body_origin":
            out[lid] = ana.body_by_name[name].pos_global.copy()
        elif kind == "site":
            out[lid] = sw[name].copy()
        else:
            raise ValueError(f"unhandled kind {kind}")
    return out


def main() -> int:
    # baseline modules must read the SNAPSHOT inputs, not the originals
    SF.REAL_XML = str(C.XML_PATH)
    real = load_source(str(C.XML_PATH))
    mt = MonkeyTarget(birth_path=str(C.MESH_PATH), pack_path=str(C.PACK_PATH))
    sw = global_site_positions(real)

    corr, notes = build_correspondence_envelope(real, mt, sw)
    digest = _correspondence_digest(corr)

    packet = C.load_packet()
    recorded = packet["meta"]["provenance"]["input_files"][3]
    ok_digest = digest == recorded["sha256"]
    C.verdict("known-good correspondence digest == packet provenance", ok_digest,
              f"rebuilt {digest[:16]}… vs recorded {recorded['sha256'][:16]}…")

    src = resolve_source(corr, real)

    records = {}
    for body in ("radius", "radius_l"):
        seg = next(s for s in corr.segments if s.source_body == body)
        lm = {
            "prox": {"id": seg.proximal_landmark,
                     "target": corr.landmarks[seg.proximal_landmark],
                     "source_resolution": corr.source_landmarks[seg.proximal_landmark],
                     "source": src[seg.proximal_landmark]},
            "dist": {"id": seg.distal_landmark,
                     "target": corr.landmarks[seg.distal_landmark],
                     "source_resolution": corr.source_landmarks[seg.distal_landmark],
                     "source": src[seg.distal_landmark]},
            "roll": {"id": seg.roll_ref,
                     "target": corr.landmarks[seg.roll_ref],
                     "source_resolution": corr.source_landmarks[seg.roll_ref],
                     "source": src[seg.roll_ref]},
        }
        records[body] = {
            "parent": seg.parent,
            "scale_policy": seg.scale_policy,
            "coords": seg.coords,
            "axial_unresolved": seg.axial_unresolved,
            "axis_assumptions": seg.axis_assumptions,
            "axis_measure_kind": seg.axis_measure_kind,
            "landmarks": lm,
            "handedness": corr.handedness,
            "mirror_plane_normal": None if corr.mirror_plane_normal is None else list(corr.mirror_plane_normal),
            "note_from_builder": notes.get(body, ""),
        }
        r = records[body]
        s_ax = float(np.linalg.norm(r["landmarks"]["dist"]["target"] - r["landmarks"]["prox"]["target"])
                     / np.linalg.norm(r["landmarks"]["dist"]["source"] - r["landmarks"]["prox"]["source"]))
        r["implied_axial_scale"] = s_ax
        print(f"{body}: parent={seg.parent} policy={seg.scale_policy} "
              f"prox_res={r['landmarks']['prox']['source_resolution']} "
              f"dist_res={r['landmarks']['dist']['source_resolution']} "
              f"roll_res={r['landmarks']['roll']['source_resolution']} "
              f"s_axial={s_ax:.12f}")

    payload = {
        "digest_rebuilt": digest,
        "digest_recorded": recorded["sha256"],
        "digest_match": ok_digest,
        "handedness": corr.handedness,
        "global_scale": float(corr.global_scale),
        "n_landmarks": len(corr.landmarks),
        "n_segments": len(corr.segments),
        "records": records,
    }
    C.save_receipt("01_known_good_records.json", payload)
    C.verdict("known-good records extracted", ok_digest,
              "radius + radius_l declared landmarks recorded")
    return 0 if ok_digest else 1


if __name__ == "__main__":
    raise SystemExit(main())
