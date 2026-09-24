"""Schema for the anatomy compiler: SourceAnatomy and FittedAnatomy, plus a JSON emitter.

Everything is plain dataclasses + numpy. The emitter walks dataclasses/numpy and
flattens to JSON; every derived value carries an explicit status string so a reader
can always tell where a number came from (see DERIVATION.md §12).
"""
from __future__ import annotations

import dataclasses
import json
import math
import numbers
from typing import Any, Optional

import numpy as np

# --- status vocabulary -------------------------------------------------------
DERIVED = "derived"
KIN_PRESERVED = "kinematically_preserved"
INGESTED_UNCHANGED = "ingested_unchanged"
REQUIRES_DENSITY_VALIDATION = "requires_density_validation"
REQUIRES_PHYSIOLOGICAL_RERUN = "requires_physiological_rerun"
RIGID_REFERENCE_ZERO = "rigid_reference_zero"
ABSENT_IN_SOURCE = "absent_in_source"
NO_PATH = "no_path"
# v3 admission labels
ROOT_REF_FRAME_UNSCALED = "root_ref_frame_unscaled"
GEO_MEASURE_KIND_SHAPE_CALIBRATION = "skin_envelope_vs_internal_site_spread"
GEO_MEASURE_KIND_AUTHORED = "authored"

# scale-axis provenance (v2: every fitted scale axis is EVIDENCE or an ASSUMPTION)
AXIS_EVIDENCE = "evidence"
AXIS_ASSUMED = "assumption"
AXIS_UNRESOLVED = "unresolved"
# segment-level outcome
SEG_RESOLVED = "resolved"
SEG_UNRESOLVED = "unresolved"
SEG_FLAGGED = "flagged_aspect"


# --- source anatomy -----------------------------------------------------------
@dataclasses.dataclass
class SourceJoint:
    name: str
    body: str
    joint_type: str  # "hinge" | "slide"
    axis: np.ndarray  # 3, unit, in the body-local frame (== global at rest for chimanoid)
    axis_global: np.ndarray  # 3, rotated into the world frame at rest
    limited: bool
    range: list[float]  # [lo, hi] radians/meters, preserved verbatim
    pos_local: np.ndarray  # 3, joint position in body frame (0 0 0 in chimanoid)


@dataclasses.dataclass
class SourceSite:
    name: str
    body: str
    pos_local: np.ndarray  # 3
    referenced_by: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class SourceBody:
    name: str
    parent: Optional[str]
    pos_global: np.ndarray  # 3, body origin in source world (rest pose)
    quat: np.ndarray  # 4 (w, x, y, z); identity for chimanoid
    joint_names: list[str]  # DIRECT joint children only (coordinate ownership)
    site_names: list[str]
    mass: Optional[float]
    com_local: Optional[np.ndarray]  # 3, inertial pos in body frame
    inertia_local: Optional[np.ndarray]  # 3x3 about CoM in body frame


@dataclasses.dataclass
class SourceTendon:
    name: str
    site_names: list[str]


@dataclasses.dataclass
class SourceMuscle:
    name: str
    tendon: Optional[str]
    force: Optional[str]  # ingested unchanged as text (do not invent units)
    timeconst: Optional[str]
    lengthrange: Optional[str]  # "lo hi" as authored
    ctrllimited: bool
    ctrlrange: str
    # provenance per attribute: "declared" (on the actuator element) vs
    # "default_class" (resolved from the <default> muscle element, not a phantom muscle).
    attr_source: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SourceAnatomy:
    meta: dict[str, Any]
    bodies: list[SourceBody]
    joints: list[SourceJoint]  # one per distinct coordinate name
    sites: list[SourceSite]
    tendons: list[SourceTendon]
    muscles: list[SourceMuscle]

    # convenience lookups (built by index()
    body_by_name: dict[str, SourceBody] = dataclasses.field(default_factory=dict)
    joint_by_name: dict[str, SourceJoint] = dataclasses.field(default_factory=dict)
    site_by_name: dict[str, SourceSite] = dataclasses.field(default_factory=dict)

    def index(self) -> None:
        self.body_by_name = {b.name: b for b in self.bodies}
        self.joint_by_name = {j.name: j for j in self.joints}
        self.site_by_name = {s.name: s for s in self.sites}
        for t in self.tendons:
            for sn in t.site_names:
                self.site_by_name[sn].referenced_by.append(t.name)

    @property
    def root(self) -> SourceBody:
        return self.body_by_name[self.meta["root_body"]]


# --- correspondence ------------------------------------------------------------
@dataclasses.dataclass
class CorrespondenceSegment:
    source_body: str
    parent: str  # parent source body name (must match intake hierarchy)
    proximal_landmark: str  # landmark id == the shared joint (child origin)
    distal_landmark: str  # landmark id, far end of the bone
    roll_ref: str  # landmark id resolved by a point (the only taste axis)
    coords: list[str]  # coordinate names owned by this edge (from intake direct joints)
    scale_policy: str = "uniform"  # legacy: "uniform" | "aspect" (equivalence kept, v2 maps to axes)
    width_landmarks: list[str] = dataclasses.field(default_factory=list)  # legacy aspect radial pair
    # v2: per-axis evidence pairs + authored assumptions. Every fitted scale axis must
    # be sourced by EXACTLY ONE of: an explicit pair (AXIS_EVIDENCE) or an authored
    # value (AXIS_ASSUMED). An axis with neither is AXIS_UNRESOLVED; a segment with any
    # unresolved axis is not "repaired" by silently inheriting a neighbour's length.
    #   axial evidence defaults to (proximal_landmark, distal_landmark); override it by
    #   putting explicit ids under key "axial".
    #   transverse evidence: 8 ids per axis? no - 4: [target0, target1, source0, source1]
    #   -> s_axis = |t1-t0| / |s1-s0|.
    axis_evidence: dict[str, list[str]] = dataclasses.field(default_factory=dict)
    # keys "axial" | "b" | "c" -> {"value": float, "note": str, "provenance": str}
    axis_assumptions: dict[str, dict] = dataclasses.field(default_factory=dict)
    # WHAT a transverse axis actually measured. "skin_envelope_vs_internal_site_spread"
    # is a shape-calibration ratio (target skin width to source muscle-attachment
    # spread) — NEVER a claim about bone/tissue cross-section anatomy. "authored"
    # marks asserted axes. Every emitted axis must carry one of these.
    axis_measure_kind: dict[str, str] = dataclasses.field(default_factory=dict)
    transverse_required: bool = True  # missing b/c axis source makes the segment unresolved
    axial_unresolved: bool = False  # author-declared: NO axial evidence and NO assumption
    explicit_roll_ref: bool = False  # reserved: roll_ref ids may come from a pair (not used yet)

    @property
    def axial_pair(self) -> tuple[str, str]:
        if "axial" in self.axis_evidence and len(self.axis_evidence["axial"]) >= 2:
            return self.axis_evidence["axial"][0], self.axis_evidence["axial"][1]
        return self.proximal_landmark, self.distal_landmark

    @property
    def transverse_pair(self, axis: str) -> list[str] | None:
        return self.axis_evidence.get(axis)


@dataclasses.dataclass
class Correspondence:
    # frame: "up","anterior","right" given as target-world unit vectors
    frame_up: np.ndarray
    frame_anterior: np.ndarray
    frame_right: np.ndarray
    global_scale: float  # target length units per source length unit
    handedness: str  # "preserve" | "mirror"
    mirror_plane_normal: Optional[np.ndarray] = None
    landmarks: dict[str, np.ndarray] = dataclasses.field(default_factory=dict)  # id -> 3 target space
    source_landmarks: dict[str, str] = dataclasses.field(default_factory=dict)  # id -> "kind:name"
    root_landmark: Optional[str] = None  # default: landmarks["root"] or origin
    segments: list[CorrespondenceSegment] = dataclasses.field(default_factory=list)
    note: str = ""


# --- fitted anatomy ------------------------------------------------------------
@dataclasses.dataclass
class FittedJoint:
    name: str
    body: str
    joint_type: str
    owner_edge: str  # source body of the edge that owns the coordinate
    origin: np.ndarray  # 3 fitted world
    axis: np.ndarray  # 3 fitted unit axis = G @ axis_global
    range: list[float]
    status: str = KIN_PRESERVED
    reason: str = ""  # set when status != kinematically_preserved (e.g. unresolved_body)


@dataclasses.dataclass
class FittedSegment:
    source_body: str
    parent: str
    source_origin: np.ndarray  # 3 (A)
    fitted_origin: np.ndarray  # 3 (P)
    source_bone_axis: np.ndarray  # unit, source frame a
    dist_landmark: np.ndarray  # 3 (P_d fitted)
    frame_basis: np.ndarray  # 3x3 fitted ONB columns [a b c] = B'
    scale: np.ndarray  # 3 = diag(S)
    rotation: np.ndarray  # 3x3 = G
    roll_ref_point: np.ndarray  # 3 fitted roll-ref point
    roll_residual_deg: float  # signed angle of frame vs authored bone-axis convention
    residual: float  # scale-corrected landmark fit quality (m)
    rank: int  # depth (root = 0)
    # v2 provenance: per-axis scale source. axially: AXIS_EVIDENCE | AXIS_ASSUMED.
    scale_provenance: list[str] = dataclasses.field(default_factory=list)  # ["axial","b","c"] provenance
    axis_sources: dict[str, str] = dataclasses.field(default_factory=dict)  # axis -> provenance code
    assumption_notes: dict[str, str] = dataclasses.field(default_factory=dict)  # axis -> note when assumed
    axis_measure_kind: dict[str, str] = dataclasses.field(default_factory=dict)  # axis -> what was measured
    status: str = SEG_RESOLVED  # resolved | flagged_aspect | unresolved


@dataclasses.dataclass
class FittedSite:
    name: str
    segment: str
    source_pos_local: np.ndarray
    fitted_pos_local: np.ndarray  # NaN when unresolved
    fitted_pos_global: np.ndarray  # NaN when unresolved
    moved_with_segment: bool = True
    unresolved: bool = False  # owning segment has no fitted scale (missing endpoints)
    reason: str = ""  # set when unresolved (why the owning segment carries no geometry)


@dataclasses.dataclass
class TendonMomentArm:
    coord: str
    analytic: float
    finite_difference: float
    fd_eps: float
    matched: bool


@dataclasses.dataclass
class FittedTendon:
    name: str
    sites: list[str]
    points: list[np.ndarray]  # fitted global points along the path
    rest_length: float
    status: str = DERIVED
    moment_arms: list[TendonMomentArm] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class FittedPhysiology:
    body: str
    mass: float
    mass_src: Optional[float]
    com_fitted: np.ndarray
    inertia_fitted: np.ndarray
    inertia_src: Optional[np.ndarray]
    det_scale: float
    status: str = REQUIRES_DENSITY_VALIDATION
    # v2: how mass was derived (never presented as an independently reconstructed tissue)
    mass_kind: str = "source_effective_x_det_scale"
    density_assumption: str = "uniform_constant_density_scale"
    scale_note: str = ""  # e.g. nonuniform 'b/c' axes present
    # v4 admission: kinematic eligibility for the TRANSPORTED-under-assumption
    # subtotal. True for a resolved, unflagged, non-root body whose mass is carried
    # at source_effective_x_det_scale under the recorded density assumption. This is
    # NOT a physical admission (no validated material/mass source); physically_admitted
    # is tracked separately in the admission ledger and stays empty unless one exists.
    admitted: bool = True
    admission_note: str = ""


@dataclasses.dataclass
class FittedMuscle:
    name: str
    tendon: Optional[str]
    rest_length: Optional[float]
    lengthrange_fitted: Optional[list[float]]
    lengthrange_src: Optional[str]
    force: Optional[str]
    timeconst: Optional[str]
    ctrlrange: str
    status: str = ""


@dataclasses.dataclass
class Audit:
    source: dict[str, Any]
    correspondence: dict[str, Any]
    assumptions: dict[str, bool]
    counts: dict[str, int]


@dataclasses.dataclass
class FittedAnatomy:
    meta: dict[str, Any]
    audit: Audit
    joints: list[FittedJoint]
    segments: list[FittedSegment]
    sites: list[FittedSite]
    tendons: list[FittedTendon]
    physiology: list[FittedPhysiology]
    muscles: list[FittedMuscle]
    unsupported: list[dict[str, str]]
    refusals: list[dict[str, str]]
    residuals: dict[str, float]
    fit_mode: str  # "synthetic" | "grounded"
    # v2: ledger of segments the fit refused to scale (missing endpoints), and any
    # linearly-dependent per-axis provenance totals.
    unresolved_segments: list[dict[str, object]] = dataclasses.field(default_factory=list)
    assumed_axes_total: int = 0
    evidence_axes_total: int = 0
    target_inputs: list[dict[str, str]] = dataclasses.field(default_factory=list)  # sha256 of read targets
    # v3: recorded measurements that are constraints, not scale claims (e.g. the
    # forearm outer-envelope estimator) + the admission ledger.
    measurements: dict[str, Any] = dataclasses.field(default_factory=dict)
    admission: dict[str, Any] = dataclasses.field(default_factory=dict)


# --- JSON emitter --------------------------------------------------------------
class PacketValidationError(Exception):
    """Raised by write_json when a non-finite number appears in a RESOLVED field.

    Mirrors correspondence.Refusal's shape (code/message) but lives in schema.py to
    avoid an import cycle. The packet contract (session 4): `null` is legal ONLY on
    fields whose owning record is explicitly unresolved WITH a status/reason. Any
    other NaN/Infinity is a bug in the fit, not a serialization concern — refuse with
    a field path instead of silently mapping it to null.
    """

    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


# Record types + fields that MAY hold non-finite values, but only when the owning
# record is EXPLICITLY unresolved (marker checked next to each entry).
_NONFINITE_ALLOWED = {
    "FittedSite": ("fitted_pos_local", "fitted_pos_global"),
    "FittedJoint": ("axis", "origin"),
    "FittedTendon": ("points", "rest_length"),
    "TendonMomentArm": ("analytic", "finite_difference"),
}


def _record_unresolved(owner: Any) -> bool:
    """True when `owner` carries an explicit unmeasured marker + reason.

    None -> not a fit record -> the non-finite value is a bug, not an intent.
    """
    if owner is None:
        return False
    if hasattr(owner, "unresolved") and owner.unresolved:
        return bool(getattr(owner, "reason", ""))
    if hasattr(owner, "status"):
        st = owner.status or ""
        if str(st).startswith("path_incomplete"):
            return True
        if str(st) == "unresolved_body":
            return bool(getattr(owner, "reason", ""))
        if str(st) in ("no_path", "requires_density_validation"):
            return False
    if hasattr(owner, "matched") and getattr(owner, "matched") is False:
        return True
    return False


def _field_is_optional(field) -> bool:
    t = (field.type or "").replace(" ", "")
    return "Optional[" in t or "|None" in t or t == "None"


def validate_finite(root: Any, path: str = "") -> list[str]:
    """Walk a FittedAnatomy and return field paths of non-finite numbers in
    RESOLVED records (i.e. null-intent not declared). Empty list == writable."""
    problems: list[str] = []

    def walk(obj: Any, p: str, owner: Any) -> None:
        if obj is None:
            return
        if dataclasses.is_dataclass(obj):
            for field in dataclasses.fields(obj):
                v = getattr(obj, field.name)
                if v is not None:
                    walk(v, f"{p}.{field.name}" if p else field.name, obj)
                elif not _field_is_optional(field):
                    problems.append(f"{p}.{field.name}=None (field not declared Optional)")
            return
        if isinstance(obj, np.ndarray):
            walk(obj.tolist(), p, owner)
            return
        if isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                walk(item, f"{p}[{i}]", owner)
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{p}.{k}", None)
            return
        if isinstance(obj, numbers.Real):
            if not math.isfinite(float(obj)):
                allowed = None
                if owner is not None:
                    fname = p.rsplit(".", 1)[-1]
                    fname = fname.split("[", 1)[0]
                    recname = type(owner).__name__
                    if recname in _NONFINITE_ALLOWED and fname in _NONFINITE_ALLOWED[recname]:
                        if _record_unresolved(owner):
                            allowed = True
                if allowed is not True:
                    problems.append(f"{p}={obj} (non-finite in a resolved record; "
                                    f"null is only legal with an explicit status/reason)")
            return

    walk(root, path, None)
    return problems


def _is_nan_token(o: Any) -> bool:
    return (o is None) or (isinstance(o, numbers.Real) and not math.isfinite(float(o)))


def _jsonable(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj):
        out = {}
        for f in dataclasses.fields(obj):
            v = getattr(obj, f.name)
            # required nullable fields (e.g. rest_length when unmeasured) must
            # SURVIVE as an explicit null — a reader must be able to distinguish
            # "declared unmeasured" from "field not present".
            out[f.name] = _jsonable(v)
        return out
    if isinstance(obj, np.ndarray):
        if obj.dtype.kind == "f" and obj.size and np.isnan(obj).all():
            return None  # an all-NaN vector IS "unmeasured": export a single null
        return _jsonable(obj.tolist())
    if isinstance(obj, (list, tuple)):
        if len(obj) and all(_is_nan_token(o) for o in obj):
            return None  # e.g. [None, None, None] already null-ed upstream
        return [_jsonable(o) for o in obj]
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    # non-finite numbers are NULL in the export (never "NaN"/"Infinity" tokens) —
    # the surrounding record always carries an explicit status/reason for them.
    if isinstance(obj, numbers.Real):
        v = float(obj)
        if not math.isfinite(v):
            return None
        return obj
    if obj is None or isinstance(obj, (str, bool)):
        return obj
    return str(obj)


def write_json(fitted: FittedAnatomy, path: str) -> str:
    problems = validate_finite(fitted)
    if problems:
        raise PacketValidationError(
            "nonfinite_resolved_field",
            "refusing to serialize non-finite values in resolved fields: "
            f"{len(problems)} problem(s); first={problems[0]!r}",
        )
    text = json.dumps(_jsonable(fitted), indent=2, allow_nan=False)
    # strict round-trip: a packet that cannot be re-parsed as strict JSON is a bug.
    parsed = json.loads(text)
    if not isinstance(parsed, dict) or "NaN" in text or "Infinity" in text or "-Infinity" in text:
        raise ValueError("write_json: packet contains nonstandard JSON tokens")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path