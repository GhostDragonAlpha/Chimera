"""actual_target_fit.py — defensible fit of the chimanoid.xml anatomy to the ACTUAL
monkey (birth mesh + JNT3 pack, read-only; authored 0.065 m/mesh-unit).

Membrane: a source segment is fitted ONLY where the target supplies evidence for an
axis pair, and each of its three axes (axial, b, c) must be sourced by evidence or an
authored assumption. Segments whose endpoints the pack DOES NOT declare (hands: no
finger joints; feet: no digit joints) stay UNRESOLVED - their muscle sites remain
ORDERED but unplaced, their shared measured joints remain preserved.

Measured evidence used (nothing invented):
  - axial   : pack joint pairs  (hip/knee/ankle, shoulder/elbow/wrist, spine chain)
  - b,c (limbs) : mesh cross-section extents of the proximal joint's own vertex band
               against the SOURCE body's site spread — recorded explicitly as a
               SHAPE-CALIBRATION ratio (skin width vs muscle-attachment spread), never
               as an internal (bone/tissue) anatomy measurement.
  - authored: thorax_dummy transverse = identity (it carries zero source sites).
  - FOREARM: the contaminated wrist-band extents are NOT used for the packet (they mix
    skin width and muscle-site spread and swallow the palm). Instead the forearm b/c
    are AUTHORED at the axial scale, and a NEW bounded outer-envelope estimator
    (target_envelope.py) measures interior skin cross-sections away from wrist and
    elbow, records geometry + sensitivity + uncertainty, and bounds the fit as a
    feasibility constraint only. The original wrist-band case is preserved verbatim
    as a regression (build_correspondence_band -> aspect flag).

Run:  python actual_target_fit.py   -> runs/actual_monkey_fit.json (+ tables + admission)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from compiler import FD_EPS, fit, onb_from_points
from correspondence import Refusal, build_target_frame
from intake import global_site_positions
from mesh_target import MESH_BIRTH, MESH_UNIT_TO_M, PACK_JNT3, MonkeyTarget
from schema import (
    DERIVED,
    GEO_MEASURE_KIND_AUTHORED,
    GEO_MEASURE_KIND_SHAPE_CALIBRATION,
    NO_PATH,
    AXIS_ASSUMED,
    AXIS_EVIDENCE,
    SEG_FLAGGED,
    Correspondence,
    CorrespondenceSegment,
    write_json,
)
from synthetic_fixtures import REAL_XML, chain_child, load_real, _pick_roll_site
from aspect_bounds import POLICED_FLAG, UNBOUNDED
from target_envelope import feasibility as envelope_feasibility
from target_envelope import measure_forearm_envelope
from target_envelope import containment as envelope_containment
from target_envelope import section_loop_containment

RUNS = Path(r"E:\PythonChimera\.tmp\anatomy_compiler\runs")
OUT_PACKET = RUNS / "actual_monkey_fit.json"
OUT_TABLES = RUNS / "actual_monkey_tables.txt"
OUT_ADMISSION = RUNS / "admission_actual_monkey.json"

# source body -> measured target evidence (pack joints; single central chain + R/L limbs)
# VERIFIED correspondence (pack joint heights vs source body-origin heights at ~1.0 root
# scale): spine_lower=pelvis origin, spine_mid=thorax_dummy origin, spine_upper=thorax
# origin. The source FOREARM bone is the RADIUS (its head articulates at the elbow); the
# source ULNA is a 2.3 cm elbow-head piece the pack does not declare - ulna is UNRESOLVED.
SEG_EVIDENCE = {
    "femur_r": ("hip_R", "knee_R"), "femur_l": ("hip_L", "knee_L"),
    "tibia_r": ("knee_R", "ankle_R"), "tibia_l": ("knee_L", "ankle_L"),
    "humerus": ("shoulder_R", "elbow_R"), "humerus_l": ("shoulder_L", "elbow_L"),
    "radius": ("elbow_R", "wrist_R"), "radius_l": ("elbow_L", "wrist_L"),
    "thorax_dummy": ("spine_mid", "spine_upper"),
}
# segments the pack does NOT declare endpoints for -> UNRESOLVED (no fabricated length)
UNRESOLVED = {
    "thorax", "ulna", "ulna_l", "hand_r", "hand_l",
    "talus_r", "talus_l", "toes_r", "toes_l",
}
FOREARMS = {"radius", "radius_l"}

UP = np.array([0.0, 1.0, 0.0])
ANT = np.array([0.0, 0.0, 1.0])
RGT = np.array([1.0, 0.0, 0.0])

BAND_EPS = 1e-9  # off-bone roll witness lower bound


def _band_roll(mt: MonkeyTarget, prox_joint: str, P: np.ndarray, a: np.ndarray) -> np.ndarray:
    """Measured roll witness: the proximal joint band's vertex farthest off the bone
    axis (a real skin point, reproducible)."""
    verts = mt.band_verts(prox_joint)
    if len(verts) == 0:
        raise Refusal("no_target_band", f"joint {prox_joint} has no vertices")
    rel = verts - P
    perp = rel - np.outer(rel @ a, a)
    d2 = (perp ** 2).sum(axis=1)
    return verts[int(np.argmax(d2))].copy()


def _source_transverse_pair(ana, sw, body, axis_dir) -> tuple[str, str] | None:
    """Two sites on `body` whose connecting vector mostly follows `axis_dir` in the
    source frame. Returns site names, or None when no pair spans the axis."""
    sts = [s for s in ana.sites if s.body == body]
    if len(sts) < 2:
        return None
    best = None
    for i in range(len(sts)):
        for j in range(i + 1, len(sts)):
            d = sw[sts[j].name] - sw[sts[i].name]
            span = float(abs(d @ axis_dir))
            off = float(np.linalg.norm(d - (d @ axis_dir) * axis_dir))
            if off > 0.5 * (np.linalg.norm(d) + 1e-15):
                continue  # pair does not follow the axis -> not axial-spread evidence
            if best is None or span > best[0]:
                best = (span, sts[i].name, sts[j].name)
    if best is None or best[0] < 1e-3:
        return None
    return best[1], best[2]


def build_correspondence_band(real, mt: MonkeyTarget, sw) -> tuple[Correspondence, dict]:
    """LEGACY correspondence: forearm b/c measured from the WRIST-BAND extents, which
    mix skin width against source muscle-site spread and are contaminated by the palm.
    PRESERVED VERBATIM as the regression for the forearm transverse finding (fit it
    with POLICED_FLAG: the radius MUST still be flagged; POLICED: MUST still refuse)."""
    return _build(real, mt, sw, forearm_transverse="band")


# legacy alias: band-based transverse evidence (the contaminated wrist-band finding)
build_correspondence = build_correspondence_band


def build_correspondence_envelope(real, mt: MonkeyTarget, sw) -> tuple[Correspondence, dict]:
    """The packet correspondence: the forearm's b/c are NOT skin/site evidence. They
    are AUTHORED at the axial scale, bounded by the separately-measured outer (skin)
    envelope of interior forearm cross-sections (recorded, with sensitivity)."""
    return _build(real, mt, sw, forearm_transverse="assume_envelope")


def _build(real, mt: MonkeyTarget, sw, forearm_transverse: str) -> tuple[Correspondence, dict]:
    L: dict[str, np.ndarray] = {}
    src_lm: dict[str, str] = {}
    L["root"] = mt.joint_pos("spine_lower")
    src_lm["root"] = "body_origin:pelvis"

    segments: list[CorrespondenceSegment] = []
    notes: dict[str, str] = {}

    # target frame must map source right (+z) onto monkey right (-x)
    Bt, _, det = build_target_frame(UP, ANT, RGT)
    assert det > 0.999999, det

    # coordinate anchor for segments whose origin the pack does not declare
    ANCHOR = {
        "thorax": "spine_mid",
        "ulna": "elbow_R", "ulna_l": "elbow_L",
        "hand_r": "wrist_R", "hand_l": "wrist_L",
        "talus_r": "ankle_R", "talus_l": "ankle_L",
        "toes_r": "ankle_R", "toes_l": "ankle_L",
    }

    for b in real.bodies:
        if b.parent is None:
            continue
        body = b.name
        child = chain_child(real, body)
        prox_rid, dist_rid, roll_rid = f"{body}.prox", f"{body}.dist", f"{body}.roll"
        src_lm[prox_rid] = f"body_origin:{body}"
        if child is not None:
            src_lm[dist_rid] = f"body_origin:{child}"
        else:
            own = [s for s in real.sites if s.body == body and s.referenced_by]
            if not own:
                raise Refusal("unresolvable_leaf", f"leaf {body} has no referencing sites")
            farthest = max(own, key=lambda s: np.linalg.norm(sw[s.name] - b.pos_global))
            src_lm[dist_rid] = f"site:{farthest.name}"
        roll_site = _pick_roll_site(real, b, sw)
        if roll_site is None:
            raise Refusal("unresolvable_roll", f"body {body} has no off-axis roll site")
        src_lm[roll_rid] = f"site:{roll_site}"

        if body in UNRESOLVED:
            # author-declared NO axial evidence (the pack declares no distal joint for
            # this segment; fingers/toes are not identified). The anchor is a measured
            # shank joint used ONLY to carry the coords it owns; no length is claimed.
            anch = ANCHOR[body]
            P = mt.joint_pos(anch)
            L[prox_rid] = P.copy()
            L[dist_rid] = P.copy()
            L[roll_rid] = P + np.array([0.05, 0.0, 0.05])
            segments.append(
                CorrespondenceSegment(
                    source_body=body, parent=b.parent, proximal_landmark=prox_rid,
                    distal_landmark=dist_rid, roll_ref=roll_rid,
                    coords=list(b.joint_names), axial_unresolved=True,
                )
            )
            notes[body] = f"no pack distal joint; coord anchor {anch} (not a fitted length)"
            continue

        pk = SEG_EVIDENCE[body]
        P = mt.joint_pos(pk[0])
        P_d = mt.joint_pos(pk[1])
        a = P_d - P
        a = a / np.linalg.norm(a)
        q = _band_roll(mt, pk[0], P, a)
        L[prox_rid] = P
        L[dist_rid] = P_d
        L[roll_rid] = q
        au, bu, cu = onb_from_points(P, P_d, q)

        seg_obj = CorrespondenceSegment(
            source_body=body, parent=b.parent, proximal_landmark=prox_rid,
            distal_landmark=dist_rid, roll_ref=roll_rid, coords=list(b.joint_names),
        )
        # source frame (a_s, b_s, c_s): the fixture's own conventions (A = body origin,
        # D = child origin or farthest site, Q = off-axis roll site)
        Am = b.pos_global
        if child is not None:
            Dm = real.body_by_name[child].pos_global
        else:
            own = [s for s in real.sites if s.body == body and s.referenced_by]
            Dm = max((sw[s.name] for s in own), key=lambda p: np.linalg.norm(p - Am), default=Am + np.array([0.0, -0.1, 0.0]))
        Qm = sw[roll_site]
        as_, bs, cs = onb_from_points(Am, Dm, Qm)

        for ax, (dir_t, dir_s) in (("b", (bu, bs)), ("c", (cu, cs))):
            if body == "thorax_dummy":
                # thorax_dummy carries ZERO source sites -> NO measured transverse pair.
                # Authored identity assumption (flagged), never claimed as evidence.
                seg_obj.axis_assumptions[ax] = {
                    "value": 1.0,
                    "provenance": "authored",
                    "note": "thorax_dummy has no source sites; transverse assumed identity",
                }
                seg_obj.axis_measure_kind[ax] = GEO_MEASURE_KIND_AUTHORED
                continue
            if body in FOREARMS:
                if forearm_transverse == "assume_envelope":
                    # Forearm b/c: set aside the contaminated wrist-band evidence entirely.
                    # Skin width vs source muscle-site spread are different quantities;
                    # their ratio is an outer-envelope/internal calibration at best and is
                    # NOT bone/tissue evidence. The measured axial scale is reused for the
                    # transverse axes (uniform blanket), AUTHORED, bounded by the outer
                    # skin envelope measured by target_envelope.py (recorded separately).
                    axial_val = float(np.linalg.norm(P_d - P) / np.linalg.norm(Dm - Am))
                    seg_obj.axis_assumptions[ax] = {
                        "value": axial_val,
                        "provenance": "authored_uniform_transverse_envelope_bounded",
                        "note": (
                            "uniform transverse assumed = axial for the forearm; the outer "
                            "(skin) envelope of interior cross-sections is measured by the "
                            "bounded forearm-envelope estimator (target_envelope.py) and is "
                            "an OUTER-ENVELOPE CONSTRAINT only — skin width is NOT evidence "
                            "for internal (bone/tissue) cross-section scaling"
                        ),
                    }
                    seg_obj.axis_measure_kind[ax] = GEO_MEASURE_KIND_AUTHORED
                    continue
                # else fall through to the legacy band evidence (regression path)
            ext = mt.band_extent(pk[0], dir_t)
            sp = _source_transverse_pair(real, sw, body, dir_s)
            if ext < 1e-3 or sp is None:
                raise Refusal("no_transverse_evidence", f"{body}/{ax}: band {ext:.3f} or source pair {sp} missing")
            t0, t1, s0, s1 = f"{body}.t{ax}0", f"{body}.t{ax}1", f"{body}.s{ax}0", f"{body}.s{ax}1"
            L[t0] = P + 0.5 * ext * dir_t
            L[t1] = P - 0.5 * ext * dir_t
            src_lm[s0] = f"site:{sp[0]}"
            src_lm[s1] = f"site:{sp[1]}"
            seg_obj.axis_evidence[ax] = [t0, t1, s0, s1]
            seg_obj.axis_measure_kind[ax] = GEO_MEASURE_KIND_SHAPE_CALIBRATION
        segments.append(seg_obj)
        notes[body] = f"axial {pk[0]}->{pk[1]} ; b/c measured on {pk[0]} band"

    corr = Correspondence(
        frame_up=UP, frame_anterior=ANT, frame_right=RGT, global_scale=1.0,
        handedness="preserve", landmarks=L, source_landmarks=src_lm,
        root_landmark="root", segments=segments,
        note="actual monkey target, 0.065 m/unit authored, pack-joint + mesh-band evidence",
    )
    return corr, notes


def _fitted_internal_spread(real, corr, sw, body: str, fit_scale: float) -> dict[str, float]:
    """Fitted INTERNAL (muscle-site attachment) spread of `body` along its source b,c
    axes, scaled by the fitted scale: source site offsets projected on (b_s, c_s) and
    times `fit_scale`, in target metres. Used ONLY as the feasibility argument against
    the measured outer skin envelope (the envelope is a bound, not a scale claim)."""
    sts = [s for s in real.sites if s.body == body]
    if not sts:
        return {"b": 0.0, "c": 0.0}
    Am = real.body_by_name[body].pos_global
    child = chain_child(real, body)
    if child is not None:
        Dm = real.body_by_name[child].pos_global
    else:
        own = [s for s in real.sites if s.body == body and s.referenced_by]
        Dm = max((sw[s.name] for s in own), key=lambda p: np.linalg.norm(p - Am))
    roll_rid = f"{body}.roll"
    roll_res = corr.source_landmarks[roll_rid].split(":", 1)[1]
    Qm = sw[roll_res]
    _, bs, cs = onb_from_points(Am, Dm, Qm)
    A = np.array([sw[s.name] - Am for s in sts])
    return {"b": float(fit_scale * (np.max(np.abs(A @ bs)) - np.min(np.abs(A @ bs)))),
            "c": float(fit_scale * (np.max(np.abs(A @ cs)) - np.min(np.abs(A @ cs))))}


def _fitted_sites_bc(f, real, mt, body: str, pk: tuple[str, str], sgm) -> list[dict]:
    """Project the fit's resolved sites of `body` into the envelope's (axial,b,c)
    frame around P=proximal joint, P_d=distal joint, in target metres. Only sites
    that the fit actually PLACED (resolved) participate — unresolved site positions
    are NaN and cannot be projected (they are counted as unresolved by containment)."""
    P = np.asarray(mt.joint_pos(pk[0]))
    P_d = np.asarray(mt.joint_pos(pk[1]))
    q = _band_roll(mt, pk[0], P, P_d - P)
    _, bu, cu = onb_from_points(P, P_d, q)
    a = P_d - P
    L = float(np.linalg.norm(a))
    if L < 1e-9:
        raise ValueError(f"forearm axis degenerate for {body}")
    a = a / L
    sites = []
    for s in f.sites:
        if s.segment != body or s.unresolved:
            continue
        p = np.asarray(s.fitted_pos_global, dtype=np.float64)
        rel = p - P
        sites.append({
            "name": s.name,
            "axial": float(rel @ a),
            "b": float(rel @ bu),
            "c": float(rel @ cu),
        })
    return sites


def _correspondence_digest(corr: Correspondence) -> str:
    lm = {k: [float(round(v, 9)) for v in arr] for k, arr in sorted(corr.landmarks.items())}
    segs = [
        {
            "body": s.source_body, "prox": s.proximal_landmark, "dist": s.distal_landmark,
            "roll": s.roll_ref, "coords": sorted(s.coords), "policy": s.scale_policy,
            "axial_unresolved": s.axial_unresolved,
            "ev": {k: list(v) for k, v in sorted(s.axis_evidence.items())},
            "as": {k: {"value": float(round(v["value"], 9)), "provenance": v.get("provenance", ""), "note": v.get("note", "")} for k, v in sorted(s.axis_assumptions.items())},
            "measure_kind": {k: v for k, v in sorted(s.axis_measure_kind.items())},
        }
        for s in corr.segments
    ]
    payload = {
        "frame_up": [float(round(v, 9)) for v in corr.frame_up],
        "frame_anterior": [float(round(v, 9)) for v in corr.frame_anterior],
        "frame_right": [float(round(v, 9)) for v in corr.frame_right],
        "global_scale": float(corr.global_scale),
        "handedness": corr.handedness,
        "root_landmark": corr.root_landmark,
        "landmarks": lm,
        "segments": segs,
        "note": corr.note,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _provenance(real, mt, corr) -> dict:
    canon = real.meta.get("canonicalization", {})
    return {
        "input_files": [
            {"kind": "target_mesh", "path": MESH_BIRTH, "sha256": mt.birth_sha, "bytes": mt.input_bytes["birth"]},
            {"kind": "target_binding_pack", "path": PACK_JNT3, "sha256": mt.pack_sha, "bytes": mt.input_bytes["pack"]},
            {
                "kind": "source_xml", "path": REAL_XML, "sha256": real.meta.get("sha256"),
                "canonicalization": canon,
            },
            {"kind": "correspondence", "sha256": _correspondence_digest(corr),
             "note": "canonical serialization of landmarks/segments/assumptions/frame"},
        ],
        "mesh_units_to_m": MESH_UNIT_TO_M,
        "upstream_vs_local_identity": (
            "on-disk source XML == pinned upstream bytes + a single trailing CRLF "
            "(documented, non-semantic text transform); see source_xml.canonicalization"
        ),
        "coordinate_conventions": {
            "up": [0.0, 1.0, 0.0], "anterior": [0.0, 0.0, 1.0], "right": [1.0, 0.0, 0.0],
        },
        "aspect_policy": {
            "profile": "policed_flag",
            "max_magnitude": 5.0, "min_magnitude": 0.2, "max_aspect": 6.0,
            "on_violation": "flag (never silent repair)",
        },
    }


def _report(f, notes, real, envelopes, feasi, confirm, confirm_loop) -> str:
    lines = []
    lines.append("ACTUAL-TARGET FIT (chimanoid.xml -> monkey_birth.bin + monkey_joints.bin)")
    lines.append(f"authored scale {MESH_UNIT_TO_M} m/unit")
    lines.append(f"chirality det {f.residuals['chirality_det']:+.3f} ({f.residuals['frame_handedness']})")
    lines.append(f"shared-joint max separation {f.residuals['shared_joint_max_separation_m']:.3e} m")
    lines.append(f"geometrically resolved {f.admission['counts']['geometrically_resolved']} / "
                 f"flagged {f.admission['counts']['flagged']} / "
                 f"unresolved {f.admission['counts']['unresolved']} / "
                 f"transported under assumption {f.admission['counts']['transported_under_assumption']} / "
                 f"physically admitted {f.admission['counts']['physically_admitted']}")
    lines.append("")
    lines.append("SEGMENTS (resolved)")
    for s in f.segments:
        ev = "".join(
            "E" if s.axis_sources.get(a) == AXIS_EVIDENCE else "A" if s.axis_sources.get(a) == AXIS_ASSUMED else "?"
            for a in ("axial", "b", "c")
        )
        mk = {a: s.axis_measure_kind.get(a, "")[:24] for a in ("b", "c")}
        lines.append(f"  {s.source_body:13s} scale {np.round(s.scale, 4)}  src[{ev}]  {s.status}  b:{mk['b']} c:{mk['c']}")
        for a in ("b", "c"):
            if s.axis_measure_kind.get(a) == GEO_MEASURE_KIND_AUTHORED and a in s.assumption_notes:
                lines.append(f"      {a}-assumption: {s.assumption_notes[a][:110]}")
    lines.append("")
    lines.append("SEGMENTS (unresolved - no endpoints declared by the pack; not invented)")
    for u in sorted(f.unresolved_segments, key=lambda d: d["body"]):
        lines.append(f"  {u['body']:13s} {u['reason']}  axes={u['axes']}")
    lines.append("")
    n_ordered_sites = sum(1 for s in f.sites if not s.unresolved)
    lines.append(f"sites: {n_ordered_sites} placed / {len(f.sites) - n_ordered_sites} ordered-unplaced")
    lines.append("")
    bad = [t.name for t in f.tendons if t.status != DERIVED]
    lines.append(f"tendons: {len(f.tendons) - len(bad)} {DERIVED} / {len(bad)} path_incomplete")
    lines.append("")
    lines.append("FOREARM OUTER-ENVELOPE (target_envelope.py; SKIN envelope, NOT internal anatomy)")
    for side, env in envelopes.items():
        bv = env["per_axis"]["b"]
        cv = env["per_axis"]["c"]
        s = env["sections"]
        lines.append(
            f"  {side:9s} sections t={[x['t'] for x in s]} verts={[x['n_verts'] for x in s]} "
            f"b={bv['median']*1000:.1f}mm (u={bv['uncertainty']*1000:.1f}) "
            f"c={cv['median']*1000:.1f}mm (u={cv['uncertainty']*1000:.1f})"
        )
    lines.append(
        f"  WIDTH SCREEN (coarse 1-D median screen, NOT a spatial claim): ok={feasi['ok']}"
    )
    for side, ws in ((k, v) for k, v in feasi.items() if k in ("radius", "radius_l")):
        for ax, d in sorted(ws["per_axis"].items()):
            lines.append(f"      [{side} {ax}] fitted spread {d['fitted_internal_spread_m']*1000:.1f} mm vs "
                         f"envelope median {d['envelope_median_m']*1000:.1f} mm "
                         f"(clearance {d['clearance_m']*1000:.1f} mm)")
    for side, ct in ((k, v) for k, v in confirm.items() if k in ("radius", "radius_l")):
        lines.append(
            f"  HULL SAMPLING (session-4 diagnostic, retained verbatim): "
            f"ok={ct['ok']} inside={ct['n_inside']} tight={ct.get('n_inside_insufficient_clearance', 0)} "
            f"outside={ct['n_outside']} unresolved={ct['n_unresolved']}"
        )
        if ct["outside"]:
            lines.append(f"      OUTSIDE: {', '.join(ct['outside'])}")
        if ct.get("inside_insufficient_clearance"):
            lines.append(f"      TIGHT: {', '.join(ct['inside_insufficient_clearance'])}")
        if ct["unresolved"]:
            lines.append(f"      UNRESOLVED: {', '.join(ct['unresolved'])}")
    for side, cl in ((k, v) for k, v in confirm_loop.items() if k in ("radius", "radius_l")):
        lines.append(
            f"  LOOP AUTHORITY (session-5 final; triangle-plane at exact axial): "
            f"ok={cl['ok']} inside={cl['n_inside']} tight={cl['n_inside_insufficient_clearance']} "
            f"outside={cl['n_outside']} ambiguous={cl['n_unresolved']}"
        )
        if cl["outside"]:
            lines.append(f"      OUTSIDE: {', '.join(cl['outside'])}")
        if cl["inside_insufficient_clearance"]:
            lines.append(f"      TIGHT: {', '.join(cl['inside_insufficient_clearance'])}")
        if cl["unresolved"]:
            lines.append(f"      AMBIGUOUS: {', '.join(cl['unresolved'])}")
    lines.append("")
    lines.append("PHYSIOLOGY (uniform-density affine transport; admission-aware)")
    tot_adm = 0.0
    tot_flag = 0.0
    for p in f.physiology:
        tag = "TRANSPORT" if p.admitted else ("ROOT-REF" if p.body == real.root.name else "EXCLUDED")
        if p.admitted:
            tot_adm += p.mass
        elif p.body in {b_["body"] for b_ in f.admission["bodies"]["excluded_from_physical"] if "flagged" in b_["reason"]}:
            tot_flag += p.mass
        lines.append(
            f"  {p.body:13s} {tag:8s} mass {p.mass:9.3f} kg  src {p.mass_src:7.3f}  detS {p.det_scale:8.3f}"
            f"  {p.mass_kind} {p.scale_note}"
        )
        if p.admission_note:
            lines.append(f"        {p.admission_note[:120]}")
    lines.append(f"  TRANSPORTED-under-assumption total {tot_adm:9.3f} kg  (physically admitted 0.000)"
                 f"  | flagged {tot_flag:8.3f} | "
                 f"root-ref {next((p.mass for p in f.physiology if not p.admitted and p.body == real.root.name), 0.0):8.3f}")
    lines.append(f"  (fitted mass = source effective mass ~ volume ratio at constant density; "
                 f"NOT a tissue reconstruction)")
    lines.append("")
    ssl = f.meta["source_identity"]["raw_sha256"][:16]
    csl = f.meta["source_identity"]["canonical"]["source_sha256_canonical"][:16]
    lines.append("PROVENANCE")
    for i in f.meta["provenance"]["input_files"]:
        lines.append(f"  {i['kind']:20s} {i.get('path', '')} sha256 {i['sha256'][:16]}…")
    lines.append(f"  source raw {ssl}… vs canonical(LF) {csl}… "
                 f"(difference: trailing CRLF only)")
    lines.append("  aspect policy: " + json.dumps(f.meta["provenance"]["aspect_policy"]))
    lines.append("Admission summary -> " + str(OUT_ADMISSION))
    return "\n".join(lines)


def main() -> int:
    real = load_real()
    mt = MonkeyTarget()
    sw = global_site_positions(real)
    corr, notes = build_correspondence_envelope(real, mt, sw)
    provenance = _provenance(real, mt, corr)

    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=provenance)
    f.target_inputs = provenance["input_files"]

    # --- forearm outer-envelope measurements + width screen + spatial containment ---
    envelopes: dict[str, dict] = {}
    feasi: dict[str, object] = {"ok": True}
    confirm: dict[str, object] = {"ok": True}
    confirm_loop: dict[str, object] = {"ok": True}
    seg_by_body = {s.source_body: s for s in f.segments}
    for body, pk in (("radius", ("elbow_R", "wrist_R")), ("radius_l", ("elbow_L", "wrist_L"))):
        P = mt.joint_pos(pk[0])
        P_d = mt.joint_pos(pk[1])
        q = _band_roll(mt, pk[0], P, P_d - P)
        _, bu, cu = onb_from_points(P, P_d, q)
        envelopes[body] = measure_forearm_envelope(mt, P, P_d, bu, cu)
        fit_scale = float(np.linalg.norm(P_d - P) / np.linalg.norm(
            real.body_by_name[body].pos_global - real.body_by_name[chain_child(real, body)].pos_global
        ))
        internal = _fitted_internal_spread(real, corr, sw, body, fit_scale)
        ws = envelope_feasibility(internal, envelopes[body], margin_m=0.001)  # coarse WIDTH screen
        feasi[body] = ws
        if not ws["ok"]:
            feasi["ok"] = False
            f.residuals[f"envelope_width_exceeded.{body}"] = True
            seg_ = seg_by_body.get(body)
            if seg_ is not None:
                seg_.status = SEG_FLAGGED
        sites_bc = _fitted_sites_bc(f, real, mt, body, pk, seg_by_body.get(body))
        ct = envelope_containment(sites_bc, envelopes[body], margin_m=0.001)
        confirm[body] = ct
        if not ct["ok"]:
            confirm["ok"] = False
            # Spatially-outside sites are NOT an axial-scale violation: the envelope
            # is a SKIN constraint, not a length measurement, and the admission ledger
            # was already locked by fit() — mutating seg_.status here would desync
            # them. The falsifier LOSES loudly instead: the residual + measurements +
            # admission record exactly which sites are outside / unresolved.
            if ct["n_outside"]:
                f.residuals[f"envelope_containment.outside.{body}"] = True
            if ct["n_unresolved"]:
                f.residuals[f"envelope_containment.unestablished.{body}"] = True
        # session-5 FINAL authority: local triangle-plane loops at each site's exact
        # axial position. Hull sampling above is RETAINED verbatim as a diagnostic
        # (its fired findings stay in the record); the loop verdict is authoritative.
        a_dir = (P_d - P) / np.linalg.norm(P_d - P)
        ct_loop = section_loop_containment(
            mt, P, a_dir, bu, cu, sites_bc, margin_m=0.001, owner_joint_names=pk
        )
        confirm_loop[body] = ct_loop
        if not ct_loop["ok"]:
            confirm_loop["ok"] = False
            if ct_loop["n_outside"]:
                f.residuals[f"envelope_containment_loop.outside.{body}"] = True
            if ct_loop["n_inside_insufficient_clearance"]:
                f.residuals[f"envelope_containment_loop.tight.{body}"] = True
            if ct_loop["n_unresolved"]:
                f.residuals[f"envelope_containment_loop.ambiguous_section.{body}"] = True
    f.residuals["envelope_feasibility_ok"] = feasi["ok"]
    f.residuals["envelope_containment_ok"] = confirm["ok"]
    f.residuals["envelope_containment_loop_ok"] = confirm_loop["ok"]
    f.measurements = {
        "outer_envelope": envelopes,
        "width_screen": {b: d for b, d in feasi.items() if b != "ok"},
        "envelope_containment": {b: d for b, d in confirm.items() if b != "ok"},
        "envelope_containment_loop": {b: d for b, d in confirm_loop.items() if b != "ok"},
        "containment_authority": "local_triangle_plane_loop (hull sampling retained as diagnostic)",
        "note": (
            "outer (skin) envelope of interior forearm cross-sections — an OUTER-ENVELOPE "
            "constraint only; never internal (bone/tissue) anatomy evidence. The forearm "
            "b/c scale is the AUTHORED axial scale (see radius axis_assumptions); the "
            "envelope bounds feasibility via the coarse one-dimensional WIDTH screen "
            "(a displaced narrow cluster passes it by construction), the session-4 "
            "band-vertex HULL sampling (diagnostic; retained verbatim with its fired "
            "findings), and the session-5 FINAL authority: triangle-plane section LOOPS "
            "at each site's exact axial position (ambiguous/open/multiple loops stay "
            "UNRESOLVED; no bridging, no repair). Signed-distance classes are distinct: "
            "outside (d>0) is never conflated with inside-but-below-margin."
        ),
    }

    RUNS.mkdir(parents=True, exist_ok=True)
    write_json(f, str(OUT_PACKET))
    txt = _report(f, notes, real, envelopes, feasi, confirm, confirm_loop)
    print(txt)
    OUT_TABLES.write_text(txt, encoding="utf-8")

    # machine-readable admission summary
    adm = {
        "meta": {
            "source_sha256": f.meta["source_identity"]["raw_sha256"],
            "source_canonical_sha256": f.meta["source_identity"]["canonical"]["source_sha256_canonical"],
            "target_mesh_sha256": f.meta["provenance"]["input_files"][0]["sha256"],
            "target_pack_sha256": f.meta["provenance"]["input_files"][1]["sha256"],
            "correspondence_sha256": f.meta["provenance"]["input_files"][3]["sha256"],
        },
        "admission": f.admission,
        "falsifier_flags": {
            "strict_json": True,
            "actuator_count": len(f.muscles),
            "unnamed_muscle_records": sum(1 for m in f.muscles if not m.name),
            "envelope_feasibility_ok": feasi["ok"],
            "envelope_containment_ok": confirm["ok"],
            "envelope_containment_loop_ok": confirm_loop["ok"],
            "flagged_promoted_to_admitted": any(
                p.admitted for p in f.physiology if p.body in f.admission["bodies"]["flagged"]
            ),
            "root_ref_in_transported": any(
                p.body == real.root.name and p.admitted for p in f.physiology
            ),
        },
        "envelope": {
            side: {
                "per_axis_median_b_m": env["per_axis"]["b"]["median"],
                "per_axis_median_c_m": env["per_axis"]["c"]["median"],
                "sections": [s["t"] for s in env["sections"]],
                "n_verts": [s["n_verts"] for s in env["sections"]],
                "width_screen_ok": feasi[side]["ok"],
                "containment_ok": confirm[side]["ok"],
                "containment_outside": confirm[side]["outside"],
                "containment_tight": confirm[side].get("inside_insufficient_clearance", []),
                "containment_unresolved": confirm[side]["unresolved"],
                "loop_authority_ok": confirm_loop[side]["ok"],
                "loop_outside": confirm_loop[side]["outside"],
                "loop_tight": confirm_loop[side]["inside_insufficient_clearance"],
                "loop_ambiguous": confirm_loop[side]["unresolved"],
            }
            for side, env in envelopes.items()
        },
    }
    (RUNS / "admission_actual_monkey.json").write_text(
        json.dumps(adm, indent=2, allow_nan=False), encoding="utf-8"
    )
    # --- attachment-candidates packet (Contract 4: port vs waypoint, deterministic) ---
    import hashlib as _hashlib

    from attachment_candidates import build_attachment_candidates

    packet_sha = _hashlib.sha256(OUT_PACKET.read_bytes()).hexdigest()
    cand = build_attachment_candidates(f, real, mt, corr, sw, fitted_packet_sha256=packet_sha)
    cand["provenance_hashes"]["source_xml_raw_sha256"] = f.meta["source_identity"]["raw_sha256"]
    cand["provenance_hashes"]["source_xml_canonical_sha256"] = f.meta["source_identity"]["canonical"]["source_sha256_canonical"]
    cand["provenance_hashes"]["target_mesh_sha256"] = f.meta["provenance"]["input_files"][0]["sha256"]
    cand["provenance_hashes"]["target_pack_sha256"] = f.meta["provenance"]["input_files"][1]["sha256"]
    OUT_CANDIDATES = RUNS / "attachment_candidates.json"
    (OUT_CANDIDATES).write_text(json.dumps(cand, indent=2, allow_nan=False), encoding="utf-8")
    print()
    print(f"attachment candidates -> {OUT_CANDIDATES}")
    print(f"packet -> {OUT_PACKET}")
    print(f"tables -> {OUT_TABLES}")
    print(f"admission -> {OUT_ADMISSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())