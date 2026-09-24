"""Correspondence: the author-facing bridge between source anatomy and target landmarks.

This is the ONLY place taste is legal. It declares:
  - the output frame (up/anterior/right unit vectors in output space),
  - handedness policy (preserve | mirror) and the mirror-plane normal,
  - global_scale (output length units per source meter; landmarks live in output space),
  - named target landmarks,
  - per-segment roll references and scale policy.

Validation produces NAMED refusals (never silent defaults) — DERIVATION.md §11.
"""
from __future__ import annotations

import numpy as np

from schema import Correspondence, CorrespondenceSegment, SourceAnatomy


class Refusal(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


SOURCE_UP = np.array([0.0, 1.0, 0.0])       # chimanoid spine grows +y
SOURCE_ANTERIOR = np.array([1.0, 0.0, 0.0])  # +x
SOURCE_RIGHT = np.array([0.0, 0.0, 1.0])     # right limbs at +z

# proper source world ONB: columns [up, anterior, right]
SOURCE_WORLD = np.column_stack([SOURCE_UP, SOURCE_ANTERIOR, SOURCE_RIGHT])


def build_target_frame(up, anterior, right) -> tuple[np.ndarray, dict, float]:
    """Return the authored target ONB B_t = [up', anterior', right'] for the output space.

    The triple (up, anterior, right) in column order carries the SAME handedness as the
    source anatomy's own axes (for chimanoid: y-up / x-anterior / z-right in that order
    is a det = -1 triple, which is the correct authoring basis). The basis must be an
    orthonormal frame (det = ±1); authoring an OPPOSITE-handed triple for the same
    skeleton is caught downstream by the chirality guard as a mirror. Segment frames
    downstream are always proper (det +1) by construction.
    """
    u = np.asarray(up, dtype=np.float64)
    f = np.asarray(anterior, dtype=np.float64)
    r = np.asarray(right, dtype=np.float64)
    if not (np.isfinite(u).all() and np.isfinite(f).all() and np.isfinite(r).all()):
        raise Refusal("non_proper_target_frame", "frame vectors must be finite")
    un, fn, rn = np.linalg.norm(u), np.linalg.norm(f), np.linalg.norm(r)
    if min(un, fn, rn) < 1e-9:
        raise Refusal("non_proper_target_frame", "frame vectors must be nonzero")
    u, f, r = u / un, f / fn, r / rn
    if abs(u @ f) > 1e-6 or abs(u @ r) > 1e-6 or abs(f @ r) > 1e-6:
        raise Refusal(
            "non_proper_target_frame",
            f"frame vectors not orthogonal: u.f={u @ f:.3e} u.r={u @ r:.3e} f.r={f @ r:.3e}",
        )
    B = np.column_stack([u, f, r])
    d = np.linalg.det(B)
    if abs(abs(d) - 1.0) > 1e-9:
        raise Refusal("non_proper_target_frame", f"|det(B_t)| = {abs(d):.6f} != 1 (frame collapse)")
    return B, {"up": u, "anterior": f, "right": r}, d


def detect_chirality_map(source_pts: np.ndarray, target_pts: np.ndarray) -> tuple[np.ndarray, float]:
    """BEST-fit rigid alignment source->target; the fitted map's determininant IS
    the chirality: +1 when the target is a proper image of the source, -1 when it
    is reflected. det(UVᵀ) of the SVD of the covariance carries that sign directly
    (a proper rotation map has det +1, a plane reflection det -1)."""
    cs = source_pts.mean(axis=0)
    ct = target_pts.mean(axis=0)
    xs = source_pts - cs
    xt = target_pts - ct
    H = xt.T @ xs
    U, S, Vt = np.linalg.svd(H)
    R = U @ Vt
    return R, float(np.linalg.det(R))


def collect_refusals(corr: Correspondence, ana: SourceAnatomy) -> list[dict[str, str]]:
    r: list[dict[str, str]] = []
    add = lambda code, msg: r.append({"code": code, "message": msg})

    if not np.isfinite(corr.global_scale) or corr.global_scale <= 0:
        add("bad_global_scale", f"global_scale = {corr.global_scale!r} must be finite > 0")
    if corr.handedness not in ("preserve", "mirror"):
        add("bad_handedness", f"handedness {corr.handedness!r} not in preserve|mirror")
    if corr.handedness == "mirror" and corr.mirror_plane_normal is None:
        add("missing_mirror_normal", "mirror mode requires mirror_plane_normal")
    if corr.mirror_plane_normal is not None:
        n = np.asarray(corr.mirror_plane_normal, dtype=np.float64)
        if not np.isfinite(n).all() or abs(np.linalg.norm(n) - 1.0) > 1e-9:
            add("bad_mirror_normal", "mirror_plane_normal must be a unit vector")

    try:
        build_target_frame(corr.frame_up, corr.frame_anterior, corr.frame_right)
    except Refusal as e:
        add(e.code, e.message)

    known_bodies = set(ana.body_by_name)
    known_joints = set(ana.joint_by_name)
    parents = {b.name: b.parent for b in ana.bodies}

    seen_coords: set[str] = set()
    seen_bodies: set[str] = set()
    for seg in corr.segments:
        if seg.source_body not in known_bodies:
            add("unknown_source_body", f"segment {seg.source_body!r} not in intake")
            continue
        if seg.parent not in known_bodies:
            add("unknown_source_body", f"parent {seg.parent!r} of {seg.source_body} not in intake")
            continue
        if parents.get(seg.source_body) != seg.parent:
            add(
                "chain_conflict",
                f"{seg.source_body!r}: intake parent {parents.get(seg.source_body)!r} != correspondence {seg.parent!r}",
            )
        if seg.source_body in seen_bodies:
            add("duplicate_segment", f"segment {seg.source_body!r} declared twice")
        seen_bodies.add(seg.source_body)
        if seg.proximal_landmark not in corr.landmarks:
            add("missing_landmark", f"segment {seg.source_body}: proximal {seg.proximal_landmark!r} not in landmarks")
        if seg.distal_landmark not in corr.landmarks:
            add("missing_landmark", f"segment {seg.source_body}: distal {seg.distal_landmark!r} not in landmarks")
        if seg.roll_ref not in corr.landmarks:
            add("missing_landmark", f"segment {seg.source_body}: roll_ref {seg.roll_ref!r} not in landmarks")
        if seg.scale_policy not in ("uniform", "aspect"):
            add("bad_scale_policy", f"segment {seg.source_body}: policy {seg.scale_policy!r}")
        if seg.scale_policy == "aspect" and not seg.width_landmarks:
            add("bad_scale_policy", f"segment {seg.source_body}: aspect policy needs width_landmarks")
        for wl in seg.width_landmarks:
            if wl not in corr.landmarks:
                add("missing_landmark", f"segment {seg.source_body}: width landmark {wl!r} not in landmarks")
        for ax in ("axial", "b", "c"):
            ev = seg.axis_evidence.get(ax)
            if not ev:
                continue
            if ax == "axial":
                for lid in ("axial" in seg.axis_evidence and seg.axis_evidence["axial"][:2] or []):
                    if lid not in corr.landmarks:
                        add("missing_landmark", f"segment {seg.source_body}: axial evidence id {lid!r} not in landmarks")
                    if lid not in corr.source_landmarks:
                        add("missing_source_landmark", f"segment {seg.source_body}: axial evidence id {lid!r} unresolved")
            else:
                if len(ev) < 4:
                    add("bad_axis_evidence", f"segment {seg.source_body}: {ax} evidence needs 4 ids [t0 t1 s0 s1]")
                    continue
                for lid in ev[:2]:
                    if lid not in corr.landmarks:
                        add("missing_landmark", f"segment {seg.source_body}: {ax} target id {lid!r} not in landmarks")
                for lid in ev[2:4]:
                    if lid not in corr.source_landmarks:
                        add("missing_source_landmark", f"segment {seg.source_body}: {ax} source id {lid!r} unresolved")
        for ax, a in seg.axis_assumptions.items():
            if ax not in ("axial", "b", "c"):
                add("bad_axis_assumption", f"segment {seg.source_body}: unknown assumed axis {ax!r}")
                continue
            v = a.get("value")
            if not (isinstance(v, (int, float)) and np.isfinite(v) and v > 0):
                add("bad_axis_assumption", f"segment {seg.source_body}: {ax} assumption value must be finite > 0")
        if seg.axial_unresolved and "axial" in seg.axis_assumptions:
            add("bad_axis_assumption", f"segment {seg.source_body}: axial_unresolved conflicts with axial assumption")
        if seg.axial_unresolved and ("axial" in seg.axis_evidence):
            add("bad_axis_evidence", f"segment {seg.source_body}: axial_unresolved conflicts with axial evidence")
        for c in seg.coords:
            if c not in known_joints:
                add("unknown_source_joint", f"segment {seg.source_body}: coord {c!r} not in intake")
            if c in seen_coords:
                add("duplicate_coord", f"coord {c!r} assigned to two segments")
            seen_coords.add(c)

    root_coords = {j.name for j in ana.joints if j.body == ana.root.name}
    missing_coords = known_joints - seen_coords - root_coords
    if missing_coords:
        add("unassigned_coords", f"coords not covered by correspondence: {sorted(missing_coords)}")

    for name, p in corr.landmarks.items():
        if not np.isfinite(p).all() or len(p) != 3:
            add("bad_landmark", f"landmark {name!r} must be a finite 3-vector")

    if corr.root_landmark is not None and corr.root_landmark not in corr.landmarks:
        add("missing_landmark", f"root_landmark {corr.root_landmark!r} not in landmarks")

    return r


def ensure_clean(corr: Correspondence, ana: SourceAnatomy) -> None:
    refusals = collect_refusals(corr, ana)
    if refusals:
        raise Refusal("refusals_present", "; ".join(f"{r['code']}: {r['message']}" for r in refusals))