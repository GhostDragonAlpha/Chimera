"""attachment_candidates.py — deterministic forearm attachment-candidates packet.

Source: the fitted foreign-forearm sites (radius, radius_l) of the ACTUAL monkey
packet and their tendon membership. Every candidate derives deterministically from
the ORDERED tendon site_names:

  FIRST  site of a tendon path = first_endpoint (a role, NOT a qualification);
  LAST   site              = last_endpoint (a role, NOT a qualification);
  any INTERMEDIATE entry   = a WAYPOINT for that tendon, never an endpoint.

Session-5 corrections:
  - source_pos_local is exported EXACTLY as the intake read it from the XML
    (source SI units). The target mesh factor MESH_UNIT_TO_M applies to TARGET
    mesh coordinates only and is NEVER multiplied into source coordinates.
  - roles are first_endpoint / last_endpoint: the packet does not establish
    anatomical proximal/distal orientation, and it does NOT pretend to.
  - every site carries mechanical_qualification = false: resolved coordinates and
    tendon endpoint membership do not qualify a membrane attachment port.
  - numeric local-to-world transforms are exported (source-local SI -> fitted
    target metres): R = Bp @ diag(scale) @ B.T with t = fitted_origin, where B is
    the source ONB rebuilt from the SAME landmark resolution the fit used.
  - hashes are SEPARATE: the source XML (raw + canonical) vs the actual fitted
    packet file (sha256 of the written bytes). The XML hash is never labelled as
    the fitted-packet hash.
  - per-site skin containment status rides along from the fit measurements:
    hull sampling (session-4 diagnostic) and loop authority (session-5), each
    with verdict, distances and reason.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from compiler import onb_from_points

RUNS = Path(r"E:\PythonChimera\.tmp\anatomy_compiler\runs")
FOREARM_BODIES = ("radius", "radius_l")


def _resolve_source_landmark(real, sw, ref: str) -> np.ndarray:
    kind, name = ref.split(":", 1)
    if kind == "body_origin":
        return np.asarray(real.body_by_name[name].pos_global, dtype=np.float64)
    if kind == "site":
        return np.asarray(sw[name], dtype=np.float64)
    raise ValueError(f"unexpected source landmark kind {kind!r}")


def build_attachment_candidates(
    f,
    real,
    mt,
    corr,
    sw,
    fitted_packet_sha256: str | None = None,
) -> dict:
    """Return the attachment-candidates record for radius / radius_l.

    fitted_packet_sha256: sha256 of the WRITTEN fitted packet file bytes — a
    different object from the source XML hashes and labelled as such.
    """
    src_lm = corr.source_landmarks

    site_by_name = {s.name: s for s in f.sites}
    tendon_by_name = {t.name: t for t in f.tendons}
    seg_by_body = {s.source_body: s for s in f.segments}

    # membership: which tendons reference a site, and that site's POSITION in the
    # tendon's ordered path (0 = first_endpoint, last = last_endpoint, else waypoint).
    membership: dict[str, list[dict]] = {}
    for tname, t in sorted(tendon_by_name.items()):
        path = t.sites or []
        for idx, sn in enumerate(path):
            if sn not in site_by_name or site_by_name[sn].segment not in FOREARM_BODIES:
                continue
            role = "waypoint"
            if idx == 0:
                role = "first_endpoint"
            elif idx == len(path) - 1:
                role = "last_endpoint"
            membership.setdefault(sn, []).append(
                {"tendon": tname, "index_in_path": idx, "path_length": len(path), "role": role}
            )

    # containment status passthrough (hull diagnostic + loop authority), if the fit
    # ran the envelope machinery; absent -> "not_measured" rather than invented.
    hull_by_site: dict = {}
    loop_by_site: dict = {}
    for body in FOREARM_BODIES:
        hull_rec = (f.measurements.get("envelope_containment") or {}).get(body, {})
        loop_rec = (f.measurements.get("envelope_containment_loop") or {}).get(body, {})
        for sn, d in (hull_rec.get("per_site") or {}).items():
            hull_by_site[sn] = d
        for sn, d in (loop_rec.get("per_site") or {}).items():
            loop_by_site[sn] = d

    bodies: dict[str, dict] = {}
    for body in FOREARM_BODIES:
        seg = seg_by_body[body]
        # rebuild the source ONB from the SAME landmark resolution the fit used
        B = np.column_stack(
            onb_from_points(
                _resolve_source_landmark(real, sw, src_lm[f"{body}.prox"]),
                _resolve_source_landmark(real, sw, src_lm[f"{body}.dist"]),
                _resolve_source_landmark(real, sw, src_lm[f"{body}.roll"]),
            )
        )
        scale = np.asarray(seg.scale, dtype=np.float64)
        Bp = np.asarray(seg.frame_basis, dtype=np.float64)
        R = Bp @ np.diag(scale) @ B.T
        t = np.asarray(seg.fitted_origin, dtype=np.float64)

        sites = [s for s in f.sites if s.segment == body]
        records = []
        recon_err = 0.0
        for s in sorted(sites, key=lambda s: s.name):
            resolved = not s.unresolved
            x = np.asarray(s.source_pos_local, dtype=np.float64)  # verbatim source SI
            recon = t + R @ x
            if resolved:
                recon_err = max(recon_err, float(np.linalg.norm(recon - s.fitted_pos_global)))
            hull = hull_by_site.get(s.name)
            loop = loop_by_site.get(s.name)
            records.append({
                "site_id": s.name,
                "source_body": body,
                "source_pos_local": [float(v) for v in x],
                "source_pos_local_units": "source SI (metres), verbatim from the XML — NOT scaled by the target mesh factor",
                "mechanical_qualification": False,
                "mechanical_qualification_note": (
                    "resolved coordinates and tendon endpoint membership do NOT "
                    "qualify a membrane attachment port; qualification requires "
                    "independent anatomical evidence not present in this packet."
                ),
                "fitted": {
                    "resolved": resolved,
                    "reason": s.reason or "",
                    "units": "target metres",
                    "fitted_pos_local": [round(float(v), 9) for v in s.fitted_pos_local] if resolved else None,
                    "fitted_pos_global": [round(float(v), 9) for v in s.fitted_pos_global] if resolved else None,
                },
                "transform_application": "fitted_pos_global = fitted_origin + R @ source_pos_local",
                "tendon_membership": membership.get(s.name, []),
                "endpoint_roles": sorted(
                    {m["role"] for m in membership.get(s.name, []) if m["role"] != "waypoint"}
                ),
                "skin_containment": {
                    "authority": "local_triangle_plane_loop" if loop else None,
                    "loop": (
                        {
                            "verdict": loop["verdict"],
                            "dist_to_loop_m": loop.get("dist_to_loop_m"),
                            "n_loops": loop.get("n_loops"),
                            "reason": loop.get("reason", ""),
                        }
                        if loop
                        else {"status": "not_measured"}
                    ),
                    "hull_sampling_diagnostic": (
                        {
                            "verdict": hull["verdict"],
                            "dist_to_hull_m": hull.get("dist_to_hull_m"),
                            "section_t": hull.get("section_t"),
                        }
                        if hull
                        else {"status": "not_measured"}
                    ),
                },
            })
        bodies[body] = {
            "units": {
                "source_positions": "source SI (metres), verbatim XML values",
                "target_positions": "target metres (mesh units x authored 0.065 applied to TARGET mesh only)",
            },
            "local_to_world": {
                "R_source_local_to_target": [[round(float(v), 12) for v in row] for row in R],
                "t_fitted_origin_m": [round(float(v), 9) for v in t],
                "composition": "R = Bp @ diag(scale) @ B.T (B = source ONB from the fit's landmark resolution; Bp = fitted frame_basis)",
                "max_world_reconstruction_error_m": round(recon_err, 15),
            },
            "n_sites_total": len(sites),
            "n_resolved": sum(1 for s in sites if not s.unresolved),
            "n_unresolved": sum(1 for s in sites if s.unresolved),
            "candidates": records,
        }

    return {
        "kind": "attachment_candidates",
        "source": {"scope": "foreign-forearm muscle attachment sites (radius, radius_l)"},
        "revision": 5,
        "revision_safety": (
            "derived from the fitted packet site/tendon order + the fit's own recorded "
            "transforms and measurements; nothing re-measured or re-invented."
        ),
        "port_vs_waypoint_rule": (
            "a site is a FIRST/LAST ENDPOINT of tendon X only when it is the first/last "
            "entry of X's ordered site_names; intermediate entries are waypoints and "
            "never endpoints for that tendon. Endpoint roles are NOT mechanical "
            "qualifications: every site ships mechanical_qualification=false."
        ),
        "bodies": bodies,
        "provenance_hashes": {
            "source_xml_raw_sha256": None,
            "source_xml_canonical_sha256": None,
            "fitted_packet_sha256": fitted_packet_sha256,
            "note": (
                "source XML hashes identify the UPSTREAM anatomy file; "
                "fitted_packet_sha256 identifies the WRITTEN fitted packet bytes. "
                "They are different objects and never interchangeable."
            ),
        },
    }


if __name__ == "__main__":
    raise SystemExit("build via actual_target_fit.main(); the packet is written there")
