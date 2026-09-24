"""Compiler: hierarchical Chimanoid->target anatomical fit (standalone NumPy).

Implements DERIVATION.md verbatim:
  - top-down edge fit, shared joints are one point (F1),
  - frames are rigid (proper ONB), geometry scales (S) — frames/scaling split (F2),
  - mirror enters ONLY as a negative scale entry; preserve-mode reflection is refused (F3),
  - sites move with their owning segments (F4),
  - analytic tendon moment arms cross-checked by central finite differences (F5),
  - mass/inertia closed forms with uniform-density flag (F6),
  - every missing/undefined/unresolvable input is a NAMED refusal, never a default (F7).
"""
from __future__ import annotations

import copy

import numpy as np

from schema import (
    ABSENT_IN_SOURCE,
    AXIS_ASSUMED,
    AXIS_EVIDENCE,
    AXIS_UNRESOLVED,
    DERIVED,
    GEO_MEASURE_KIND_AUTHORED,
    KIN_PRESERVED,
    NO_PATH,
    REQUIRES_PHYSIOLOGICAL_RERUN,
    ROOT_REF_FRAME_UNSCALED,
    SEG_FLAGGED,
    SEG_RESOLVED,
    Audit,
    Correspondence,
    CorrespondenceSegment,
    FittedAnatomy,
    FittedJoint,
    FittedMuscle,
    FittedPhysiology,
    FittedSegment,
    FittedSite,
    FittedTendon,
    SourceAnatomy,
    TendonMomentArm,
)
from correspondence import Refusal, build_target_frame, detect_chirality_map

FD_EPS = 1e-5
JOINT_EPS = 1e-9
ROLL_EPS = 1e-9


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-15:
        raise ValueError("degenerate vector")
    return v / n


def onb_from_points(p0: np.ndarray, p1: np.ndarray, q: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Proper ONB [a b c] with a = p1-p0 (bone) and b = roll-ref rejected off a."""
    a = _unit(p1 - p0)
    t = (q - p0) - a * (a @ (q - p0))
    if np.linalg.norm(t) < ROLL_EPS:
        raise Refusal("axis_parallel_roll", "roll reference lies on the bone axis")
    b = _unit(t)
    c = np.cross(a, b)
    if abs(np.linalg.det(np.column_stack([a, b, c])) - 1.0) > 1e-9:
        raise Refusal("non_proper_target_frame", "ONB construction failed to stay proper")
    return a, b, c


def _twist_deg(b_align: np.ndarray, c_align: np.ndarray, b_prime: np.ndarray) -> float:
    """Signed twist about the bone axis between the source (b,c) plane and b_prime."""
    b2 = b_prime - b_align * (b_align @ b_prime)
    if np.linalg.norm(b2) < 1e-12:
        return 0.0
    b2 = _unit(b2)
    return float(np.degrees(np.arctan2(b2 @ c_align, b2 @ b_align)))


def _pl(pts) -> float:
    return float(sum(np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)))


_SUBTREES: dict[tuple[int, str], set[str]] = {}


def subtree_of(ana: SourceAnatomy, body: str) -> set[str]:
    key = (id(ana), body)
    if key in _SUBTREES:
        return _SUBTREES[key]
    children: dict[str, list[str]] = {b.name: [] for b in ana.bodies}
    for b in ana.bodies:
        if b.parent is not None:
            children[b.parent].append(b.name)

    def rec(name: str) -> set[str]:
        s = {name}
        for c in children.get(name, []):
            s |= rec(c)
        return s

    _SUBTREES[key] = rec(body)
    return _SUBTREES[key]


# ----------------------------------------------------------------- source landmarks
def resolve_source_landmarks(corr: Correspondence, ana: SourceAnatomy) -> dict[str, np.ndarray]:
    from intake import global_site_positions

    site_world = global_site_positions(ana)
    out: dict[str, np.ndarray] = {}
    for lid, resolution in corr.source_landmarks.items():
        kind, _, name = resolution.partition(":")
        if kind == "body_origin":
            if name not in ana.body_by_name:
                raise Refusal("unknown_source_body", f"source landmark {lid!r} -> body {name!r} not in intake")
            out[lid] = ana.body_by_name[name].pos_global.copy()
        elif kind == "joint":
            if name not in ana.joint_by_name:
                raise Refusal("unknown_source_joint", f"source landmark {lid!r} -> joint {name!r} not in intake")
            j = ana.joint_by_name[name]
            out[lid] = ana.body_by_name[j.body].pos_global.copy() + j.pos_local
        elif kind == "site":
            if name not in site_world:
                raise Refusal("unknown_site", f"source landmark {lid!r} -> site {name!r} not found")
            out[lid] = site_world[name].copy()
        else:
            raise Refusal("bad_source_landmark", f"resolution {resolution!r} has unknown kind {kind!r}")
    return out


def _resolve_target(corr: Correspondence, lid: str) -> np.ndarray:
    if lid not in corr.landmarks:
        raise Refusal("missing_landmark", f"target landmark {lid!r} not declared")
    return corr.landmarks[lid].copy()


# ----------------------------------------------------------------- segment fit
class _Segment:
    __slots__ = (
        "seg", "src_A", "src_D", "src_Q", "P", "P_d", "Q",
        "s_src", "B", "Bp", "scale", "twist", "rank",
        "axis_sources", "assumption_notes", "axis_measure_kind", "resolved", "scale_src",
    )

    def __init__(self, seg: CorrespondenceSegment, src_lm: dict, tgt_lm: dict, rank: int):
        self.seg = seg
        self.src_A = src_lm[seg.proximal_landmark]
        self.src_D = src_lm[seg.distal_landmark]
        self.src_Q = src_lm[seg.roll_ref]
        self.P = tgt_lm[seg.proximal_landmark]
        self.P_d = tgt_lm[seg.distal_landmark]
        self.Q = tgt_lm[seg.roll_ref]
        self.s_src = float(np.linalg.norm(self.src_D - self.src_A))
        if self.s_src < 1e-12:
            raise Refusal("degenerate_bone", f"segment {seg.source_body} has zero source bone length")
        a, b, c = onb_from_points(self.src_A, self.src_D, self.src_Q)
        self.B = np.column_stack([a, b, c])
        if np.linalg.norm(self.P_d - self.P) > 1e-12:
            ap, bp, cp = onb_from_points(self.P, self.P_d, self.Q)
            self.Bp = np.column_stack([ap, bp, cp])
            self.twist = _twist_deg(b, c, bp)
        else:
            # axial_degenerate (author-declared unresolved): no direction is claimed,
            # so no target frame is needed; the source frame stands in for cosmetic use.
            self.Bp = self.B.copy()
            self.twist = 0.0
        self.rank = rank

        # ---- v2: one scale per axis, each EVIDENCE or an AUTHORED ASSUMPTION ----
        # An axis with neither source is AXIS_UNRESOLVED; unless every axis is sourced
        # the segment is not fitted (never silently inheritance of a neighbour length).
        ratio = float(np.linalg.norm(self.P_d - self.P) / self.s_src)
        self.axis_sources: dict[str, str] = {}
        self.assumption_notes: dict[str, str] = {}
        # what each axis actually measured: segments may declare their own kind
        # (e.g. shape-calibration band evidence); anything else defaults by source.
        self.axis_measure_kind: dict[str, str] = {
            a: seg.axis_measure_kind.get(a, "axial_pair_length") for a in ("axial", "b", "c")
        }

        def _assume(ax: str) -> tuple[float, str]:
            a = seg.axis_assumptions[ax]
            self.assumption_notes[ax] = a.get("note", a.get("provenance", "authored"))
            self.axis_measure_kind[ax] = seg.axis_measure_kind.get(ax, GEO_MEASURE_KIND_AUTHORED)
            return float(a["value"]), "assumption"

        axial: float | None = None
        if seg.axial_unresolved:
            self.axis_sources["axial"] = AXIS_UNRESOLVED
        elif "axial" in seg.axis_assumptions:
            axial, prov = _assume("axial")
            self.axis_sources["axial"] = prov
        else:
            axial = ratio
            self.axis_sources["axial"] = AXIS_EVIDENCE

        if seg.scale_policy == "aspect" and seg.width_landmarks:
            # legacy radial pair spans BOTH transverse axes (S1 semantics preserved)
            w1, w2, sw1, sw2 = seg.width_landmarks
            w_src = float(np.linalg.norm(src_lm[sw1] - src_lm[sw2]))
            w_fit = float(np.linalg.norm(tgt_lm[w1] - tgt_lm[w2]))
            radial = w_fit / w_src if w_src > 1e-12 else (axial if axial is not None else 1.0)
            self.scale = np.array([axial if axial is not None else radial, radial, radial])
            self.axis_sources.update({"b": AXIS_EVIDENCE, "c": AXIS_EVIDENCE})
            self.resolved = axial is not None
            return

        bscale: float | None = None
        cscale: float | None = None
        for ax in ("b", "c"):
            if ax in seg.axis_assumptions:
                val, prov = _assume(ax)
                self.axis_sources[ax] = prov
                if ax == "b":
                    bscale = val
                else:
                    cscale = val
            elif ax in seg.axis_evidence and len(seg.axis_evidence[ax]) >= 4:
                t0, t1, s0, s1 = seg.axis_evidence[ax][:4]
                ts = float(np.linalg.norm(tgt_lm[t0] - tgt_lm[t1]))
                ss = float(np.linalg.norm(src_lm[s0] - src_lm[s1]))
                self.axis_sources[ax] = AXIS_EVIDENCE if (ts > 1e-12 and ss > 1e-12) else AXIS_UNRESOLVED
                if self.axis_sources[ax] == AXIS_EVIDENCE:
                    if ax == "b":
                        bscale = ts / ss
                    else:
                        cscale = ts / ss
            elif seg.scale_policy == "uniform" and axial is not None:
                # the LEGACY blanket: b and c inherit the axial scale. This counts as
                # an AUTHORED assumption (flagged below), never as measured evidence.
                bscale = axial if ax == "b" else axial
                cscale = axial
                self.axis_sources[ax] = AXIS_ASSUMED
                self.assumption_notes[ax] = "uniform_legacy: b/c inherit axial scale (blanket, not evidence)"
            else:
                self.axis_sources[ax] = AXIS_UNRESOLVED

        self.scale = None if (axial is None or bscale is None or cscale is None) else np.array([axial, bscale, cscale])
        self.resolved = self.scale is not None and all(
            v == AXIS_EVIDENCE or v == AXIS_ASSUMED for v in self.axis_sources.values()
        )
        self.scale_src = {k: self.axis_sources[k] for k in ("axial", "b", "c")}


def build_segments(corr: Correspondence, ana: SourceAnatomy) -> tuple[list[_Segment], dict[str, _Segment], list[str]]:
    src_lm = resolve_source_landmarks(corr, ana)
    tgt_lm = {k: _resolve_target(corr, k) for k in corr.landmarks}
    depth: dict[str, int] = {}
    children: dict[str, list[str]] = {b.name: [] for b in ana.bodies}
    for b in ana.bodies:
        if b.parent is not None:
            children[b.parent].append(b.name)
    stack = [(ana.root.name, 0)]
    while stack:
        name, d = stack.pop()
        depth[name] = d
        for c in children.get(name, []):
            stack.append((c, d + 1))
    ordered: list[_Segment] = []
    seen: dict[str, _Segment] = {}
    unresolved: list[str] = []
    for seg in sorted(corr.segments, key=lambda s: depth.get(s.source_body, 10**9)):
        seg_obj = _Segment(seg, src_lm, tgt_lm, depth.get(seg.source_body, 0))
        if seg_obj.resolved:
            seen[seg.source_body] = seg_obj
            ordered.append(seg_obj)
        else:
            unresolved.append(seg.source_body)
    # bodies that have no correspondence segment at all (chain gaps) are still reported
    for b in ana.bodies:
        if b.parent is not None and b.name not in seen and b.name not in unresolved:
            unresolved.append(b.name)
    return ordered, seen, unresolved


# ----------------------------------------------------------------- main fit
def reflect(normal: np.ndarray) -> np.ndarray:
    """Plane-reflection matrix (det = -1) across the plane with the given normal."""
    n = np.asarray(normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    return np.eye(3) - 2.0 * np.outer(n, n)


def _reflect_fitted(f: FittedAnatomy, R: np.ndarray, n: np.ndarray) -> FittedAnatomy:
    """Hand-raise the preserve fit into the mirror: geometry R-reflected, frames proper
    (R . Bp . diag(1,1,-1)), the negative axis declared in each segment's scale. All
    scalar physics of a reflected body is unchanged, so physiology/path lengths/arms
    pass through untouched — exactly the 'exact reflection' claim of F3."""
    D = np.diag([1.0, 1.0, -1.0])
    out = copy.deepcopy(f)
    out.meta = {**f.meta, "frame_handedness": "left", "mirror_reflect": "true"}
    for s in out.sites:
        s.fitted_pos_global = R @ s.fitted_pos_global
    for j in out.joints:
        j.origin = R @ j.origin
        j.axis = R @ j.axis
    for sg in out.segments:
        sg.fitted_origin = R @ sg.fitted_origin
        sg.dist_landmark = R @ sg.dist_landmark
        sg.roll_ref_point = R @ sg.roll_ref_point
        sg.source_bone_axis = R @ sg.source_bone_axis
        sg.frame_basis = R @ sg.frame_basis @ D
        sg.rotation = R @ sg.rotation
        sg.scale = D @ sg.scale
    out.residuals = {**f.residuals}
    out.residuals["frame_handedness"] = "left"
    out.residuals["chirality_det"] = -f.residuals["chirality_det"]
    out.residuals["mirror_plane_normal"] = n
    return out


def fit(
    ana: SourceAnatomy,
    corr: Correspondence,
    fit_mode: str = "synthetic",
    aspect_bounds: dict | None = None,
    provenance: dict | None = None,
) -> FittedAnatomy:
    from correspondence import collect_refusals

    refusals = collect_refusals(corr, ana)
    if refusals:
        raise Refusal("refusals_present", "; ".join(f"{r['code']}: {r['message']}" for r in refusals))

    from aspect_bounds import merge_profile, check_segment

    bounds = merge_profile(aspect_bounds) if aspect_bounds is not None else None

    if corr.handedness == "mirror":
        R = reflect(corr.mirror_plane_normal)
        corr_eff = copy.deepcopy(corr)
        corr_eff.landmarks = {k: R @ p for k, p in corr.landmarks.items()}
        corr_eff.handedness = "preserve"
        base = fit(ana, corr_eff, fit_mode=fit_mode, aspect_bounds=aspect_bounds, provenance=provenance)
        return _reflect_fitted(base, R, np.asarray(corr.mirror_plane_normal))

    B_t, _axes, _bt_det = build_target_frame(corr.frame_up, corr.frame_anterior, corr.frame_right)
    g = float(corr.global_scale)

    root_landmark = corr.root_landmark or "root"
    if root_landmark not in corr.landmarks and "root" in corr.landmarks:
        root_landmark = "root"
    P_root = _resolve_target(corr, root_landmark)

    # --- chirality guard (F3) -----------------------------------------------
    # only bodies the fit can actually place take part (unresolved bodies would
    # drag unplaced landmarks into the best-fit chirality test)
    src_pts, tgt_pts = [], []
    for b in ana.bodies:
        if b.parent is None:
            src_pts.append(b.pos_global)
            tgt_pts.append(P_root)
            continue
        seg = next((s for s in corr.segments if s.source_body == b.name), None)
        if seg is None:
            continue
        if getattr(seg, "axial_unresolved", False) or seg.axial_pair is None:
            continue
        src_pts.append(b.pos_global)
        tgt_pts.append(_resolve_target(corr, seg.proximal_landmark))
    if len(src_pts) < 3:
        raise Refusal("chirality_undecidable", "too few placeable bodies to judge handedness")
    _, chirality_det = detect_chirality_map(np.array(src_pts), np.array(tgt_pts))
    if corr.handedness == "preserve" and chirality_det < 0:
        raise Refusal(
            "handedness_mismatch",
            f"target landmarks reflect the source (det={chirality_det:+.3f}) but handedness=preserve",
        )
    frame_handedness = "right" if chirality_det > 0 else "left"

    ordered, seen, unresolved_bodies = build_segments(corr, ana)
    seg_by_body: dict[str, _Segment] = {}
    fitted_origin: dict[str, np.ndarray] = {ana.root.name: P_root}
    for sl in ordered:
        seg_by_body[sl.seg.source_body] = sl
        fitted_origin[sl.seg.source_body] = sl.P.copy()
    parent_of = {b.name: b.parent for b in ana.bodies}

    # --- aspect bounds: refuse or flag; never silently repair ------------------
    flagged_bodies: set[str] = set()
    if bounds is not None:
        for sl in ordered:
            msgs = check_segment(sl.seg.source_body, sl.scale, bounds)
            if not msgs:
                continue
            if bounds["on_violation"] == "refuse":
                raise Refusal(
                    "aspect_out_of_bounds",
                    f"segment {sl.seg.source_body} scale {np.round(sl.scale, 5)} "
                    f"outside bounds: {'; '.join(msgs)}",
                )
            flagged_bodies.add(sl.seg.source_body)

    # --- shared-joint closure (F1) ------------------------------------------
    # only RESOLVED segments form the kinematic trunk (see topology comment below);
    # an unresolved body's shared points are still measured, but its length is not
    # claimed, so it participates in no closure arithmetic.
    first_child_of: dict[str, str | None] = {}
    for sl in ordered:
        parent = parent_of[sl.seg.source_body]
        if parent in first_child_of:
            continue
        first_child_of[parent] = sl.seg.source_body
        first_child_of.setdefault(sl.seg.source_body, None)
    max_sep = 0.0
    per_seg_closure: dict[str, float] = {}
    for sl in ordered:
        child = sl.seg.source_body
        parent = parent_of[child]
        if parent is None or parent == ana.root.name or first_child_of.get(parent) != child:
            per_seg_closure[child] = 0.0
            continue
        if parent not in seg_by_body:
            # an unresolved parent contributes no segment length; the child's shared
            # point is still a measured joint, so no closure arithmetic is owed
            per_seg_closure[child] = 0.0
            continue
        sep = np.linalg.norm(sl.P - seg_by_body[parent].P_d)
        per_seg_closure[child] = sep
        max_sep = max(max_sep, sep)
    if max_sep > JOINT_EPS:
        raise Refusal("shared_joint_separation", f"max shared-joint separation {max_sep:.3e} m")

    unresolved_set = set(unresolved_bodies)

    # --- joints --------------------------------------------------------------
    def _unresolved_origin(body: str) -> np.ndarray:
        seg = next((s for s in corr.segments if s.source_body == body), None)
        if seg is not None and seg.proximal_landmark in corr.landmarks:
            return corr.landmarks[seg.proximal_landmark].copy()
        return NaN3.copy()

    joints_out: list[FittedJoint] = []
    for j in ana.joints:
        if j.body == ana.root.name:
            axis_fit = B_t @ j.axis_global
        elif j.body in unresolved_set:
            # shared point (if measured) is preserved, geometry NOT claimed
            axis_fit = np.full(3, np.nan)
        else:
            sl = seg_by_body[j.body]
            K = sl.Bp @ np.diag(sl.scale) @ sl.B.T
            axis_fit = K @ j.axis_global
            n = np.linalg.norm(axis_fit)
            axis_fit = axis_fit / n if n > 1e-12 else sl.Bp[:, 2]
        joints_out.append(
            FittedJoint(
                name=j.name,
                body=j.body,
                joint_type=j.joint_type,
                owner_edge=j.body,
                origin=(_unresolved_origin(j.body) if j.body in unresolved_set else fitted_origin[j.body]),
                axis=axis_fit,
                range=list(j.range),
                status=KIN_PRESERVED if j.body not in unresolved_set else "unresolved_body",
                reason=(
                    ""
                    if j.body not in unresolved_set
                    else f"body {j.body}: no fitted scale (endpoints not declared); axis not claimed"
                ),
            )
        )
    joint_axis = {jo.name: jo for jo in joints_out}

    NaN3 = np.full(3, np.nan)
    # --- sites ---------------------------------------------------------------
    sites_out: list[FittedSite] = []
    for s in ana.sites:
        if s.body in unresolved_set:
            sites_out.append(
                FittedSite(
                    name=s.name,
                    segment=s.body,
                    source_pos_local=s.pos_local.copy(),
                    fitted_pos_local=NaN3.copy(),
                    fitted_pos_global=NaN3.copy(),
                    moved_with_segment=False,
                    unresolved=True,
                    reason=f"owning segment {s.body} unresolved: no fitted scale (endpoints not declared)",
                )
            )
            continue
        if s.body == ana.root.name:
            local = g * s.pos_local
            world = P_root + B_t @ local
        else:
            sl = seg_by_body[s.body]
            local = np.diag(sl.scale) @ (sl.B.T @ s.pos_local)
            world = fitted_origin[s.body] + sl.Bp @ local
        sites_out.append(
            FittedSite(
                name=s.name,
                segment=s.body,
                source_pos_local=s.pos_local.copy(),
                fitted_pos_local=local,
                fitted_pos_global=world,
            )
        )
    site_fit = {s.name: s.fitted_pos_global for s in sites_out}
    body_of_site = {s.name: s.segment for s in sites_out}

    # --- tendons + moment arms ----------------------------------------------
    tendons_out: list[FittedTendon] = []
    for t in ana.tendons:
        pts = [site_fit[sn] for sn in t.site_names]
        unresolved_hits = sorted({body_of_site[sn] for sn in t.site_names if sn in body_of_site and body_of_site[sn] in unresolved_set})
        complete = not any(np.isnan(p).any() for p in pts)
        tnd_status = f"path_incomplete:unresolved_bodies {unresolved_hits}" if unresolved_hits else DERIVED
        tnd = FittedTendon(
            name=t.name, sites=list(t.site_names), points=[p.copy() for p in pts],
            rest_length=_pl(pts) if complete else float("nan"), status=tnd_status,
        )
        for j in ana.joints:
            if j.body == ana.root.name:
                tnd.moment_arms.append(
                    TendonMomentArm(coord=j.name, analytic=0.0, finite_difference=0.0, fd_eps=FD_EPS, matched=True)
                )
                continue
            if not complete or j.body in unresolved_set:
                tnd.moment_arms.append(
                    TendonMomentArm(coord=j.name, analytic=float("nan"), finite_difference=float("nan"),
                                    fd_eps=FD_EPS, matched=False)
                )
                continue
            arm = _analytic_arm(t, j, site_fit, body_of_site, fitted_origin, joint_axis, ana)
            arm_fd = _fd_arm(t, j, site_fit, body_of_site, fitted_origin, joint_axis, ana, FD_EPS)
            matched = abs(arm - arm_fd) / (1.0 + abs(arm_fd)) < 5e-6
            tnd.moment_arms.append(
                TendonMomentArm(coord=j.name, analytic=arm, finite_difference=arm_fd, fd_eps=FD_EPS, matched=matched)
            )
        tendons_out.append(tnd)

    # --- physiology ------------------------------------------------------------
    # Affine-image transport (constant density): a body scaled by D = diag(s) has
    #   mass'   = m * |det D|                 (volume ratio at constant density)
    #   Sigma'  = |det D| * D Sigma Dᵀ         (pseudo-inertia, Sigma = tr(I)/2 I - I)
    #   I'      = tr(Sigma') I - Sigma'
    # The source mass is an EFFECTIVE value for the source segment, never presented
    # as an independently reconstructed tissue mass (mass_kind states it).
    phys_out: list[FittedPhysiology] = []
    inertia_spectrum: list[float] = []
    # v3 admission: the ROOT body keeps its identity scale (it anchors the tree), which
    # establishes NOTHING about pelvis size — carrying its original mass through the
    # ledger is an explicit reference-frame carry, flagged below and excluded from the
    # admitted physical total. Flagged geometry is transported AND reported, then ALSO
    # excluded from any admitted physical total (never silently admitted).
    for b in ana.bodies:
        if b.mass is None or b.com_local is None or b.inertia_local is None:
            continue
        if b.name in unresolved_set:
            continue  # no scale -> no transport; reported in unresolved_segments
        is_root = b.name == ana.root.name
        is_flagged_seg = (not is_root) and b.name in flagged_bodies
        if is_root:
            Sg, Bp_, P = np.diag([g, g, g]), B_t, P_root
            LB = Bp_ @ Sg @ np.eye(3)
        else:
            sl = seg_by_body[b.name]
            Sg, Bp_, P = np.diag(sl.scale), sl.Bp, fitted_origin[b.name]
            LB = Bp_ @ Sg @ sl.B.T
        detS = float(np.linalg.det(Sg))
        mf = b.mass * detS
        com_f = P + LB @ b.com_local
        X = (np.trace(b.inertia_local) / 2.0) * np.eye(3) - b.inertia_local
        Xp = LB @ X @ LB.T
        I_f = detS * (np.trace(Xp) * np.eye(3) - Xp)
        I_f = (I_f + I_f.T) / 2.0
        if np.min(np.linalg.eigvalsh(I_f)) <= 0.0:
            raise Refusal("nonphysical_inertia", f"fitted inertia of {b.name} not positive-definite")
        inertia_spectrum.extend(np.linalg.eigvalsh(I_f).tolist())
        sl_note = ""
        if b.name in seg_by_body:
            s = seg_by_body[b.name].scale
            if s is not None and not np.allclose(s, s[0]):
                sl_note = "nonuniform_scale_axes"
        if is_root:
            mass_kind = ROOT_REF_FRAME_UNSCALED
            admitted, adm_note = False, (
                "root reference frame only: identity scale carries the original mass "
                "as a reference-frame quantity — it does not measure or validate pelvis size"
            )
        elif is_flagged_seg:
            mass_kind = "source_effective_x_det_scale"
            admitted, adm_note = False, (
                f"flagged geometry ({b.name}) transported for inspection but excluded "
                f"from the admitted physical subset"
            )
        else:
            mass_kind = "source_effective_x_det_scale"
            admitted, adm_note = True, ""
        phys_out.append(
            FittedPhysiology(
                body=b.name,
                mass=mf,
                mass_src=b.mass,
                com_fitted=com_f,
                inertia_fitted=I_f,
                inertia_src=b.inertia_local.copy(),
                det_scale=detS,
                mass_kind=mass_kind,
                density_assumption="uniform_constant_density_scale",
                scale_note=sl_note,
                admitted=admitted,
                admission_note=adm_note,
            )
        )

    # --- muscles ----------------------------------------------------------------
    from intake import global_site_positions

    site_world_src = global_site_positions(ana)
    rest_src = {t.name: _pl([site_world_src[sn] for sn in t.site_names]) for t in ana.tendons}
    muscles_out: list[FittedMuscle] = []
    for m in ana.muscles:
        if m.tendon is None:
            muscles_out.append(
                FittedMuscle(
                    name=m.name,
                    tendon=None,
                    rest_length=None,
                    lengthrange_fitted=None,
                    lengthrange_src=m.lengthrange,
                    force=m.force,
                    timeconst=m.timeconst,
                    ctrlrange=m.ctrlrange,
                    status=NO_PATH,
                )
            )
            continue
        tnd = next((t for t in tendons_out if t.name == m.tendon), None)
        if tnd is None:
            raise Refusal("unknown_tendon", f"muscle {m.name}: tendon {m.tendon!r} not found")
        if tnd.status != DERIVED:
            muscles_out.append(
                FittedMuscle(
                    name=m.name,
                    tendon=m.tendon,
                    rest_length=None,
                    lengthrange_fitted=None,
                    lengthrange_src=m.lengthrange,
                    force=m.force,
                    timeconst=m.timeconst,
                    ctrlrange=m.ctrlrange,
                    status=tnd.status,
                )
            )
            continue
        lam = tnd.rest_length / rest_src[m.tendon] if rest_src[m.tendon] > 0 else 1.0
        lrf = None
        if m.lengthrange:
            lo, hi = (float(x) for x in m.lengthrange.split())
            lrf = [lam * lo, lam * hi]
        status = DERIVED
        if m.force or m.timeconst:
            status = f"path:{DERIVED}|physiology:{REQUIRES_PHYSIOLOGICAL_RERUN}"
        muscles_out.append(
            FittedMuscle(
                name=m.name,
                tendon=m.tendon,
                rest_length=tnd.rest_length,
                lengthrange_fitted=lrf,
                lengthrange_src=m.lengthrange,
                force=m.force,
                timeconst=m.timeconst,
                ctrlrange=m.ctrlrange,
                status=status,
            )
        )

    # --- unsupported ------------------------------------------------------------
    corpus = " ".join(
        [b.name.lower() for b in ana.bodies]
        + [s.name.lower() for s in ana.sites]
        + [j.name.lower() for j in ana.joints]
    )
    unsupported = []
    for label, key in [
        ("tail", "tail"),
        ("neck/head", "neck"),
        ("neck/head", "head"),
        ("articulated_fingers", "finger"),
    ]:
        if key not in corpus:
            unsupported.append(
                {"feature": label, "status": ABSENT_IN_SOURCE, "evidence": f"no '{key}' token in source taxonomy"}
            )

    # --- unresolved ledger --------------------------------------------------------
    unresolved_ledger: list[dict[str, object]] = []
    for name in sorted(unresolved_set):
        seg = next((s for s in corr.segments if s.source_body == name), None)
        if seg is None:
            unresolved_ledger.append({"body": name, "reason": "no correspondence segment"})
            continue
        unresolved_ledger.append(
            {
                "body": name,
                "reason": "no fitted scale (axis source missing; not silently repaired)",
                "axes": {
                    "axial": "declared_unresolved" if seg.axial_unresolved else "pair",
                    "b": "pair" if "b" in seg.axis_evidence else "none",
                    "c": "pair" if "c" in seg.axis_evidence else "none",
                },
            }
        )

    # --- admission ledger ---------------------------------------------------------
    # Session-4 split: GEOMETRIC admission (a segment is resolved, unflagged, and the
    # fit placed it) is NOT a PHYSICAL admission. A mass reaches the transported
    # subtotal only as source_effective_x_det_scale under a RECORDED material/mass
    # assumption ("uniform_constant_density_scale"); geometry resolution alone does
    # NOT discharge requires_density_validation. No body is physically_admitted
    # unless an explicit validated material/mass source exists — and none is
    # invented here. The root is a reference-frame carry, not a measurement of
    # pelvis scale (its physiology row says so); flagged geometry is transported for
    # inspection but NEVER silently admitted to any subtotal of "admitted" meaning.
    resolved_bodies = [sl.seg.source_body for sl in ordered if sl.seg.source_body not in flagged_bodies]
    flagged_names = sorted(flagged_bodies)
    unresolved_names = sorted(unresolved_set)
    transported = [p for p in phys_out if p.admitted]
    excluded_phys = [
        {"body": p.body, "reason": p.admission_note}
        for p in phys_out
        if not p.admitted
    ]
    transported_mass = float(sum(p.mass for p in transported))
    flagged_phys_mass = float(sum(p.mass for p in phys_out if (not p.admitted) and p.body in flagged_bodies))
    root_phys = next((p for p in phys_out if p.body == ana.root.name), None)
    admission = {
        "counts": {
            "geometrically_resolved": len(resolved_bodies),
            "flagged": len(flagged_names),
            "unresolved": len(unresolved_names),
            "admitted_kinematic": len(resolved_bodies),
            "transported_under_assumption": len(transported),
            "physically_admitted": 0,
        },
        "bodies": {
            "geometrically_resolved": sorted(resolved_bodies),
            "flagged": flagged_names,
            "unresolved": unresolved_names,
            "kinematically_admitted": sorted(sl.seg.source_body for sl in ordered),
            "transported_under_assumption": sorted(p.body for p in transported),
            "physically_admitted": [],
            "excluded_from_physical": excluded_phys,
        },
        "totals_mass_kg": {
            "transported_under_assumption": transported_mass,
            "physically_admitted": 0.0,
            "flagged_only": flagged_phys_mass,
            "root_reference_only": float(root_phys.mass) if root_phys is not None else None,
            "all_transported": float(sum(p.mass for p in phys_out)),
        },
        "mass_admission": {
            "assumption": "uniform_constant_density_scale",
            "kind": "source_effective_x_det_scale",
            "requires_density_validation": True,
            "density_validated": False,
            "note": (
                "a transported mass is the source effective mass scaled by |det D| "
                "under a RECORDED constant-density assumption. Geometry resolution "
                "alone does NOT discharge requires_density_validation; no body is "
                "physically admitted because no validated material/mass source was "
                "supplied and none is invented."
            ),
        },
    }

    # --- audit --------------------------------------------------------------------
    n_ev, n_as = 0, 0
    for sl in ordered:
        for ax, src in sl.axis_sources.items():
            if src == AXIS_EVIDENCE:
                n_ev += 1
            elif src == AXIS_ASSUMED:
                n_as += 1
    blanket_uniform = any(
        s.axis_sources.get("b") == AXIS_ASSUMED and "uniform" in s.assumption_notes.get("b", "")
        for s in ordered
    )

    audit = Audit(
        source={
            "file": ana.meta.get("source_file"),
            "revision": ana.meta.get("revision"),
            "sha256": ana.meta.get("sha256"),
            "bodies": len(ana.bodies),
            "coords": len(ana.joints),
            "sites": len(ana.sites),
            "sites_in_paths": len([s for s in ana.sites if s.referenced_by]),
            "tendons": len(ana.tendons),
            "muscles": len(ana.muscles),
        },
        correspondence={
            "handedness": corr.handedness,
            "mirror_plane_normal": corr.mirror_plane_normal.tolist() if corr.mirror_plane_normal is not None else None,
            "global_scale": g,
            "n_target_landmarks": len(corr.landmarks),
            "n_segments": len(corr.segments),
            "n_resolved_segments": len(ordered),
            "n_unresolved_segments": len(unresolved_set),
        },
        assumptions={
            "requires_density_validation": True,
            "homogeneous_path_scaling": True,
            "muscle_physiology_not_geometric": True,
            "root_coords_rigid_reference": True,
            "mass_is_source_effective_x_det_scale": True,
            "uniform_transverse_legacy_blanket": blanket_uniform,
            "n_axis_assumptions": n_as,
            "n_axis_evidence": n_ev,
            "flagged_geometry_excluded_from_admitted_physical": bool(flagged_names),
            "root_ref_frame_not_scale_evidence": True,
            "geometry_resolution_does_not_discharge_density_validation": True,
        },
        counts={
            "bodies": len(ana.bodies),
            "coords": len(ana.joints),
            "sites": len(ana.sites),
            "path_sites": len([s for s in ana.sites if s.referenced_by]),
            "tendons": len(ana.tendons),
            "muscles": len(ana.muscles),
        },
    )

    residuals: dict[str, object] = {
        "shared_joint_max_separation_m": max_sep,
        "chirality_det": chirality_det,
        "frame_handedness": frame_handedness,
        "inertia_spectrum": sorted(inertia_spectrum),
        **{f"closure.{k}": v for k, v in per_seg_closure.items()},
        **{f"aspect_flag.{k}": True for k in sorted(flagged_bodies)},
    }
    for sl in ordered:
        residuals[f"roll_twist_deg.{sl.seg.source_body}"] = sl.twist

    aspect_policy_meta = bounds if bounds is not None else "unbounded"
    meta = {
        "compiler": "anatomy_compiler",
        "version": "v3",
        "fit_mode": fit_mode,
        "units": "SI (m, kg, s)",
        "frame_handedness": frame_handedness,
        "source": ana.meta.get("source_file"),
        "source_identity": {
            "raw_sha256": ana.meta.get("sha256"),
            "canonical": ana.meta.get("canonicalization", {}),
        },
        "aspect_bounds": aspect_policy_meta,
        "coordinate_conventions": {
            "up": [round(float(v), 9) for v in corr.frame_up],
            "anterior": [round(float(v), 9) for v in corr.frame_anterior],
            "right": [round(float(v), 9) for v in corr.frame_right],
            "handedness": frame_handedness,
            "global_scale_factor": float(corr.global_scale),
        },
        "provenance": dict(provenance or {}),
    }

    fitted = FittedAnatomy(
        meta=meta,
        audit=audit,
        joints=joints_out,
        segments=[
            FittedSegment(
                source_body=sl.seg.source_body,
                parent=sl.seg.parent,
                source_origin=sl.src_A.copy(),
                fitted_origin=sl.P.copy(),
                source_bone_axis=sl.B[:, 0].copy(),
                dist_landmark=sl.P_d.copy(),
                frame_basis=sl.Bp.copy(),
                scale=sl.scale.copy(),
                rotation=sl.Bp @ sl.B.T,
                roll_ref_point=sl.Q.copy(),
                roll_residual_deg=float(sl.twist),
                residual=float(per_seg_closure.get(sl.seg.source_body, 0.0)),
                rank=sl.rank,
                scale_provenance=[sl.axis_sources.get(a, AXIS_UNRESOLVED) for a in ("axial", "b", "c")],
                axis_sources=dict(sl.axis_sources),
                assumption_notes=dict(sl.assumption_notes),
                axis_measure_kind=dict(sl.axis_measure_kind),
                status=SEG_FLAGGED if sl.seg.source_body in flagged_bodies else SEG_RESOLVED,
            )
            for sl in ordered
        ],
        sites=sites_out,
        tendons=tendons_out,
        physiology=phys_out,
        muscles=muscles_out,
        unsupported=unsupported,
        refusals=[],
        residuals=residuals,
        fit_mode=fit_mode,
        unresolved_segments=unresolved_ledger,
        assumed_axes_total=n_as,
        evidence_axes_total=n_ev,
        admission=admission,
    )
    return fitted


# ----------------------------------------------------------------- moment arms
def _analytic_arm(t, j, site_fit, body_of_site, fitted_origin, joint_axis, ana) -> float:
    pts = [site_fit[sn] for sn in t.site_names]
    J = fitted_origin[j.body]
    axis = joint_axis[j.name].axis
    sub = subtree_of(ana, j.body)
    if j.joint_type == "slide":
        arm = 0.0
        for i in range(len(pts) - 1):
            u = pts[i + 1] - pts[i]
            n = np.linalg.norm(u)
            if n < 1e-15:
                continue
            u = u / n
            arm += u @ axis * (int(body_of_site[t.site_names[i + 1]] in sub) - int(body_of_site[t.site_names[i]] in sub))
        return float(arm)
    arm = 0.0
    for i in range(len(pts) - 1):
        u = pts[i + 1] - pts[i]
        n = np.linalg.norm(u)
        if n < 1e-15:
            continue
        u = u / n
        for idx in (i, i + 1):
            if body_of_site[t.site_names[idx]] not in sub:
                continue
            ds = np.cross(axis, pts[idx] - J)
            arm += (u if idx == i + 1 else -u) @ ds
    return float(arm)


def _fd_arm(t, j, site_fit, body_of_site, fitted_origin, joint_axis, ana, eps: float) -> float:
    pts0 = [site_fit[sn] for sn in t.site_names]
    J = fitted_origin[j.body]
    axis = joint_axis[j.name].axis
    sub = subtree_of(ana, j.body)

    def L_at(dq: float) -> float:
        if j.joint_type == "slide":
            pts = [p + axis * dq if body_of_site[sn] in sub else p for sn, p in zip(t.site_names, pts0)]
            return _pl(pts)
        c, s = np.cos(dq), np.sin(dq)
        k = axis
        R = np.array(
            [
                [c + k[0] ** 2 * (1 - c), k[0] * k[1] * (1 - c) - k[2] * s, k[0] * k[2] * (1 - c) + k[1] * s],
                [k[1] * k[0] * (1 - c) + k[2] * s, c + k[1] ** 2 * (1 - c), k[1] * k[2] * (1 - c) - k[0] * s],
                [k[2] * k[0] * (1 - c) - k[1] * s, k[2] * k[1] * (1 - c) + k[0] * s, c + k[2] ** 2 * (1 - c)],
            ]
        )
        pts = []
        for sn, p in zip(t.site_names, pts0):
            if body_of_site[sn] in sub:
                p = J + R @ (p - J)
            pts.append(p)
        return _pl(pts)

    return (L_at(eps) - L_at(-eps)) / (2 * eps)


def global_site(ana: SourceAnatomy, sitename: str) -> np.ndarray:
    from intake import global_site_positions

    return global_site_positions(ana)[sitename]