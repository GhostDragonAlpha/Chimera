"""Assembly-handoff adapter: authored-information readiness for a dynamics trial.

THE ONE QUESTION THIS ANSWERS (and nothing else):

    "Does this assembly have the explicitly authored information needed for a
     dynamics trial, and exactly what is missing?"

It is an ASSEMBLY MANIFEST ADAPTER. It reads three upstream owners' documents —
the anatomy compiler's fitted packet + attachment-candidates packet, the
material-volume compiler's reconstructed-mass document, and an authored
mechanical-requirements document — and emits one manifest with per-field
provenance/status plus a readiness verdict and deterministically ordered gap
records. It never runs dynamics, never mutates physics state, never repairs a
mesh, and never fills a default.

WHAT IT REFUSES (hard refusal = no manifest is emitted; `AssemblyRefusal`):
  * duplicate_mass_ownership      two mass-bearing matter representations for one
                                  component (membrane + body counting the same
                                  matter twice), or an implicit binding that would
                                  have to guess which owner a region belongs to.
  * mass_status_promotion         a caller asserting a validated-tissue status that
                                  the upstream evidence does not support. Anatomy
                                  physiology is carried as transported
                                  source-effective mass and stays that way.
  * waypoint_promoted_to_attachment
                                  an attachment endpoint naming a site that is only
                                  an intermediate tendon waypoint, unless the
                                  requirements document authors that role itself.
  * unsupported_surface_mass_claim
                                  a zero-thickness overlay declared to carry mass
                                  (the v1 volume contract admits no thin-sheet mass).
  * dangling_component_reference / unknown_claim_reference / duplicate_* ids,
    nonfinite_input, bad_schema.

WHAT IT LEAVES MISSING (manifest emitted, readiness blocked, gap recorded with the
exact field path): missing patch area, areal stiffness or Kbar, material density
source, local frame bindings, unresolved anatomy mass, unqualified ports.

Upstream contracts consumed (read from their files, not assumed):
  * `.tmp/anatomy_compiler/schema.py`            FittedAnatomy / FittedPhysiology
        statuses derived|kinematically_preserved|requires_density_validation,
        mass_kind source_effective_x_det_scale | root_ref_frame_unscaled.
  * `.tmp/anatomy_compiler/attachment_candidates.py`
        port-vs-waypoint law; rev>=5 records carry `endpoint_roles` +
        `mechanical_qualification: false`; the on-disk runs/ packet is an earlier
        revision carrying `candidate_roles`. Both shapes are read, and which one
        was consumed is recorded.
  * `tools/material_volume.py`                   compile_document() -> per-region
        mass properties (mass, CoM, inertia about CoM) — delegated, never re-derived.
  * `tools/finite_area_attachment/finite_area_attachment.py`
        AttachmentSpec + assert_min_couple_stiffness() is the ONLY thing that can
        call an attachment mechanically qualified; if that dependency cannot be
        imported, nothing is ever reported as qualified.

Run:
    python tools/assembly_handoff/assembly_handoff.py --bundle <bundle.json> [--out <manifest.json>]
    python tools/assembly_handoff/run_fixtures.py            # four synthetic fixtures
    python tools/assembly_handoff/real_packet_readiness.py   # the real anatomy packet
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ADAPTER_VERSION = "v1"
TOOL_NAME = "tools/assembly_handoff/assembly_handoff.py"

BUNDLE_SCHEMA = "chimera.assembly_bundle.v1"
MANIFEST_SCHEMA = "chimera.assembly_manifest.v1"
OWNERSHIP_SCHEMA = "chimera.assembly_ownership.v1"
REQUIREMENTS_SCHEMA = "chimera.mechanical_requirements.v1"

# --- matter representations (same vocabulary as the material-volume contract) ---
REP_TET_VOLUME = "tetrahedral_volume"
REP_SURFACE_OVERLAY = "surface_mass_overlay"
REP_SOURCE_SEGMENT = "source_effective_segment"

# --- mass status vocabulary (adapter-level; upstream labels are preserved too) ---
MASS_RECONSTRUCTED = "reconstructed_tissue_volume"
MASS_TRANSPORTED = "transported_source_effective"
MASS_ROOT_REFERENCE = "root_reference_frame_only"
MASS_UNRESOLVED = "unresolved"
# A tetrahedral volume that integrated a density nobody declared a source for. It is NOT
# validated tissue mass: the geometry is real, the number behind the number is missing.
MASS_DENSITY_UNVALIDATED = "reconstructed_volume_density_unsourced"

# --- attachment status vocabulary (geometric and mechanical are SEPARATE) ---
GEO_PORT = "candidate_port"
GEO_WAYPOINT = "waypoint_not_a_port"
MECH_QUALIFIED = "mechanically_qualified"
MECH_INCOMPLETE = "incomplete_parameters_missing"

SEVERITY_BLOCKING = "blocking"
SEVERITY_NOTE = "note"

ROLE_ANATOMY = "anatomy_packet"
ROLE_CANDIDATES = "attachment_candidates"
ROLE_MATERIAL_VOLUME = "material_volume_document"
ROLE_ADMISSION_REPORT = "material_admission_report"
ROLE_FITTING_MANIFEST = "fitting_manifest"
ROLE_MATERIAL_PARTITION = "material_partition"
ROLE_OWNERSHIP = "ownership_bindings"
ROLE_REQUIREMENTS = "mechanical_requirements"
# Recognised but NOT integrated into readiness: recorded with its hash so the manifest
# says exactly which ledger was in hand, while every judgement still comes from the
# anatomy/material/attachment owners' own documents.
ROLE_ANATOMY_ADMISSION = "anatomy_admission_ledger"

# Roles whose absence is a named, blocking gap for a dynamics trial.
REQUIRED_ROLES = (ROLE_ANATOMY, ROLE_CANDIDATES, ROLE_MATERIAL_VOLUME,
                  ROLE_OWNERSHIP, ROLE_REQUIREMENTS)

_EPS_ORTHO = 1e-9


class AssemblyRefusal(Exception):
    """A hard stop: the adapter will not emit a manifest at all."""

    def __init__(self, code: str, field_path: str, detail: str):
        super().__init__(f"[{code}] at {field_path}: {detail}")
        self.code = code
        self.field_path = field_path
        self.detail = detail

    def to_record(self) -> dict[str, Any]:
        return {"code": self.code, "field_path": self.field_path, "detail": self.detail}


# --------------------------------------------------------------------------- #
# canonical serialization helpers                                              #
# --------------------------------------------------------------------------- #
def canonical_json(value: Any) -> str:
    """Sorted-key, compact, deterministic JSON. Non-finite floats are refused."""
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                      allow_nan=False)


def _plain(value: Any) -> Any:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AssemblyRefusal("nonfinite_input", "<serialization>",
                                  f"non-finite float {value!r} cannot be serialized")
        return value
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def display_path(path: Any, repo_root: Path) -> str | None:
    """A manifest path that survives being checked out somewhere else.

    The manifest digest covers every input row, so an absolute host path inside it would
    make two agents on two machines report different digests for byte-identical inputs —
    which would defeat the point of hashing them. Paths inside the repository are recorded
    relative to the repo root in POSIX form; anything outside keeps a normalised absolute
    POSIX path. Nothing is hidden, only made location-independent where that is possible.
    """
    if path is None:
        return None
    p = Path(str(path))
    try:
        resolved = p.resolve()
    except OSError:  # unresolvable (absent) paths are still reportable
        resolved = p
    root = repo_root.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def document_digest(doc: Any) -> str:
    """Digest of a parsed document's canonical form (order-independent identity)."""
    return sha256_bytes(canonical_json(doc).encode("utf-8"))


def _assert_finite(value: Any, path: str) -> None:
    """Reject NaN/Infinity anywhere in an input document, with its field path.

    Python's json accepts the bare `NaN`/`Infinity` tokens, so a packet that was
    written by a strict writer but hand-edited can still smuggle them in.
    """
    if isinstance(value, float) and not math.isfinite(value):
        raise AssemblyRefusal("nonfinite_input", path,
                              f"non-finite number {value!r} in input document")
    if isinstance(value, Mapping):
        for k, v in value.items():
            _assert_finite(v, f"{path}.{k}")
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            _assert_finite(v, f"{path}[{i}]")


def _require_mapping(value: Any, path: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AssemblyRefusal("bad_schema", path, f"{label} must be a JSON object")
    return value


def _require_list(value: Any, path: str, label: str) -> list[Any]:
    # Tuples are accepted as well as lists: the material-volume compiler returns
    # `dataclasses.asdict()` rows whose vector fields are tuples, not JSON arrays.
    if isinstance(value, (list, tuple)):
        return list(value)
    raise AssemblyRefusal("bad_schema", path, f"{label} must be a JSON array")


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _vec3(value: Any, path: str, *, allow_nonfinite: bool = False) -> list[float] | None:
    """A 3-vector of finite numbers, or None when absent (never guessed).

    `allow_nonfinite` is for upstream records that carry an explicit unresolved
    marker: the upstream packet contract allows null/NaN there. Such a value is
    reported as ABSENT (None) — never coerced to zero and never placed.
    """
    if value is None:
        return None
    items = _require_list(value, path, "vector")
    if len(items) != 3 or any(not isinstance(v, (int, float)) for v in items):
        raise AssemblyRefusal("bad_schema", path, "expected exactly 3 numbers")
    out = [float(v) for v in items]
    if not all(math.isfinite(v) for v in out):
        if allow_nonfinite:
            return None
        raise AssemblyRefusal("nonfinite_input", path,
                              f"non-finite vector {out!r} on a record that is not "
                              f"declared unresolved")
    return out


def _mat3(value: Any, path: str, *, allow_nonfinite: bool = False) -> list[list[float]] | None:
    if value is None:
        return None
    rows = _require_list(value, path, "matrix")
    if len(rows) != 3:
        raise AssemblyRefusal("bad_schema", path, "expected a 3x3 matrix")
    out = [_vec3(row, f"{path}[{i}]", allow_nonfinite=allow_nonfinite) for i, row in enumerate(rows)]
    if any(row is None for row in out):
        if allow_nonfinite:
            return None
        raise AssemblyRefusal("nonfinite_input", path, "non-finite matrix entry")
    return out


# --------------------------------------------------------------------------- #
# gap recorder                                                                 #
# --------------------------------------------------------------------------- #
class GapRecorder:
    """Collects unresolved/conflict records; emits them in one deterministic order.

    Order key is (severity, code, field_path, subject_id) — no insertion-order
    dependence anywhere in the manifest.
    """

    _SEV_RANK = {SEVERITY_BLOCKING: 0, SEVERITY_NOTE: 1}

    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str], dict[str, Any]] = {}

    def add(self, code: str, field_path: str, message: str, *,
            severity: str = SEVERITY_BLOCKING, subject_id: str | None = None,
            evidence: Mapping[str, Any] | None = None) -> None:
        key = (severity, code, field_path)
        rec = self._records.get(key)
        if rec is not None:  # idempotent merge, never a duplicate row
            if subject_id and subject_id not in rec["subject_ids"]:
                rec["subject_ids"].append(subject_id)
                rec["subject_ids"].sort()
            return
        self._records[key] = {
            "code": code,
            "severity": severity,
            "field_path": field_path,
            "subject_id": subject_id,
            "subject_ids": sorted({subject_id}) if subject_id else [],
            "message": message,
            "evidence": dict(evidence) if evidence else {},
        }

    def records(self) -> list[dict[str, Any]]:
        return [self._records[k] for k in sorted(
            self._records, key=lambda k: (self._SEV_RANK.get(k[0], 9), k[1], k[2]))]

    def blocking_codes(self) -> list[str]:
        return sorted({r["code"] for r in self.records()
                       if r["severity"] == SEVERITY_BLOCKING})


# --------------------------------------------------------------------------- #
# upstream dependency loading (delegation, never re-implementation)            #
# --------------------------------------------------------------------------- #
def _load_upstream(repo_root: Path) -> dict[str, Any]:
    """Import the material-volume compiler and the finite-area attachment gate.

    A missing dependency is reported as an absent artifact; it can never make a
    claim stronger (nothing is ever qualified without the real gate).
    """
    out: dict[str, Any] = {"material_volume": None, "finite_area_attachment": None,
                           "absent": []}
    for key, sub in (("material_volume", repo_root / "tools"),
                     ("finite_area_attachment", repo_root / "tools" / "finite_area_attachment")):
        if not sub.is_dir():
            out["absent"].append({"dependency": key,
                                  "expected_path": display_path(sub, repo_root)})
            continue
        text = str(sub)
        if text not in sys.path:
            sys.path.insert(0, text)
        try:
            module = __import__(key)
            out[key] = module
        except Exception as ex:  # pragma: no cover - environment dependent
            out["absent"].append({"dependency": key,
                                  "expected_path": display_path(sub, repo_root),
                                  "error": f"{type(ex).__name__}: {ex}"})
    return out


# --------------------------------------------------------------------------- #
# input resolution                                                             #
# --------------------------------------------------------------------------- #
def _detect_role(doc: Any) -> tuple[str | None, str]:
    """Return (role, schema_detected) from the document's own markers."""
    if not isinstance(doc, Mapping):
        return None, "not_an_object"
    sv = doc.get("schema_version")
    if isinstance(sv, str):
        if sv == "chimera.material_volume.v1":
            return ROLE_MATERIAL_VOLUME, sv
        if sv == "chimera.fitting_manifest.v1":
            return ROLE_FITTING_MANIFEST, sv
        if sv == "chimera.material_partition.v1":
            return ROLE_MATERIAL_PARTITION, sv
        if sv == "chimera.material_volume_admission_report.v1":
            return ROLE_ADMISSION_REPORT, sv
    if doc.get("kind") == "attachment_candidates":
        rev = doc.get("revision")
        shape = f"attachment_candidates.revision_{rev}" if isinstance(rev, int) \
            else "attachment_candidates.pre_revision"
        return ROLE_CANDIDATES, shape
    meta = doc.get("meta")
    if isinstance(meta, Mapping) and meta.get("compiler") == "anatomy_compiler":
        return ROLE_ANATOMY, f"anatomy_compiler/{meta.get('version', 'unknown')}"
    if sv == OWNERSHIP_SCHEMA:
        return ROLE_OWNERSHIP, sv
    if sv == REQUIREMENTS_SCHEMA:
        return ROLE_REQUIREMENTS, sv
    return None, "unrecognised_schema"


class ResolvedInput:
    def __init__(self, label: str, role: str | None, admitted_as: str, source_kind: str,
                 path: str | None, schema_detected: str, document: Any,
                 presence: str, note: str):
        self.label = label
        self.role = role
        self.admitted_as = admitted_as
        self.source_kind = source_kind
        self.path = path
        self.schema_detected = schema_detected
        self.document = document
        self.presence = presence
        self.note = note
        self.sha256: str | None = None
        self.bytes: int | None = None

    def to_row(self) -> dict[str, Any]:
        return {"label": self.label, "role": self.role, "presence": self.presence,
                "source_kind": self.source_kind, "admitted_as": self.admitted_as,
                "path": self.path, "sha256": self.sha256, "bytes": self.bytes,
                "schema_detected": self.schema_detected, "note": self.note}


def _resolve_inputs(bundle: Mapping[str, Any], bundle_dir: Path,
                    repo_root: Path) -> list[ResolvedInput]:
    rows = _require_list(bundle.get("inputs"), "inputs", "bundle inputs")
    resolved: list[ResolvedInput] = []
    seen_labels: set[str] = set()
    for i, raw in enumerate(rows):
        path_prefix = f"inputs[{i}]"
        entry = _require_mapping(raw, path_prefix, "bundle input")
        label = entry.get("label")
        if not isinstance(label, str) or not label.strip():
            raise AssemblyRefusal("bad_schema", f"{path_prefix}.label",
                                  "every input needs a non-empty stable label")
        if label in seen_labels:
            raise AssemblyRefusal("duplicate_input_label", f"{path_prefix}.label",
                                  f"input label {label!r} is used more than once")
        seen_labels.add(label)
        admitted_as = entry.get("admitted_as")
        if admitted_as not in ("synthetic", "real"):
            raise AssemblyRefusal("bad_schema", f"{path_prefix}.admitted_as",
                                  "admitted_as must be 'synthetic' or 'real': provenance "
                                  "is authored, never inferred")

        if entry.get("absent") is True:
            resolved.append(ResolvedInput(
                label, entry.get("role"), admitted_as, "declared_absent",
                display_path(entry.get("expected_path"), repo_root), "absent", None,
                "absent", str(entry.get("reason", ""))))
            continue

        document = entry.get("document")
        if document is not None:
            file_path = None
            source_kind = "inline_document"
            raw_bytes = canonical_json(document).encode("utf-8")
        else:
            rel = entry.get("path")
            if not isinstance(rel, str) or not rel.strip():
                raise AssemblyRefusal("bad_schema", f"{path_prefix}",
                                      "input needs either 'document' or 'path' (or absent=true)")
            p = Path(rel)
            if not p.is_absolute():
                p = bundle_dir / p
            if not p.is_file():
                resolved.append(ResolvedInput(
                    label, entry.get("role"), admitted_as, "file",
                    display_path(p, repo_root), "missing_file", None, "absent",
                    "declared as a file input but the file is not present"))
                continue
            raw_bytes = p.read_bytes()
            document = json.loads(raw_bytes.decode("utf-8"))
            source_kind = "file"
            file_path = display_path(p, repo_root)

        _assert_finite(document, f"{path_prefix}.document")
        declared_role = entry.get("role")
        detected_role, schema_detected = _detect_role(document)
        if declared_role is not None and detected_role is not None \
                and declared_role != detected_role:
            raise AssemblyRefusal("input_role_mismatch", f"{path_prefix}.role",
                                  f"declared role {declared_role!r} but the document "
                                  f"identifies itself as {detected_role!r}")
        resolved.append(ResolvedInput(label, declared_role or detected_role, admitted_as,
                                      source_kind, file_path, schema_detected, document,
                                      "present", str(entry.get("note", ""))))
        r = resolved[-1]
        r.sha256 = sha256_bytes(raw_bytes)
        r.bytes = len(raw_bytes)
    return resolved


# --------------------------------------------------------------------------- #
# the assembler                                                                #
# --------------------------------------------------------------------------- #
class HandoffAssembler:
    def __init__(self, bundle: Mapping[str, Any], *, repo_root: Path | None = None,
                 bundle_dir: Path | None = None):
        self.bundle = _require_mapping(bundle, "<bundle>", "assembly bundle")
        if self.bundle.get("schema_version") != BUNDLE_SCHEMA:
            raise AssemblyRefusal("bad_schema", "schema_version",
                                  f"expected {BUNDLE_SCHEMA!r}")
        assembly_id = self.bundle.get("assembly_id")
        if not isinstance(assembly_id, str) or not assembly_id.strip():
            raise AssemblyRefusal("bad_schema", "assembly_id", "required non-empty string")
        self.assembly_id = assembly_id
        self.bundle_dir = bundle_dir or Path.cwd()
        self.repo_root = repo_root or self._find_repo_root()
        self.gaps = GapRecorder()
        self.upstream = _load_upstream(self.repo_root)
        for dep in self.upstream["absent"]:
            self.gaps.add("upstream_dependency_absent", f"upstream[{dep['dependency']}]",
                          f"cannot delegate to {dep['dependency']}: "
                          f"{dep.get('error', 'directory not present')}",
                          subject_id=dep["dependency"], evidence=dict(dep))

    @staticmethod
    def _find_repo_root() -> Path:
        p = Path(__file__).resolve()
        for parent in [p.parent, *p.parents]:
            if (parent / "AGENTS.md").is_file():
                return parent
        return p.parent.parent.parent

    # -- public --------------------------------------------------------------
    def build(self) -> dict[str, Any]:
        self.inputs = _resolve_inputs(self.bundle, self.bundle_dir, self.repo_root)
        by_role: dict[str, list[ResolvedInput]] = {}
        for r in self.inputs:
            if r.presence != "present" or r.role is None:
                continue
            by_role.setdefault(r.role, []).append(r)

        # One document per role. Silently keeping the first of several would quietly decide
        # which authored information wins — exactly the kind of unstated choice this adapter
        # exists to refuse.
        for role in sorted(by_role):
            if len(by_role[role]) > 1:
                raise AssemblyRefusal(
                    "duplicate_role_input", f"inputs[role={role}]",
                    f"{len(by_role[role])} present inputs claim role {role!r} "
                    f"({sorted(r.label for r in by_role[role])}); merge them into one document "
                    f"or drop the extra — this adapter does not pick a winner")

        for role in REQUIRED_ROLES:
            present = [r for r in self.inputs if r.role == role and r.presence == "present"]
            if not present:
                absent = [r for r in self.inputs if r.role == role]
                detail = ("declared absent" if absent else "not supplied in the bundle")
                self.gaps.add("required_input_absent", f"inputs[role={role}]",
                              f"no {role} input is present ({detail}); its information "
                              f"cannot be substituted by this adapter",
                              subject_id=role)

        self.anatomy = by_role.get(ROLE_ANATOMY, [None])[0] if ROLE_ANATOMY in by_role else None
        self.candidates = by_role.get(ROLE_CANDIDATES, [None])[0] if ROLE_CANDIDATES in by_role else None
        self.material = by_role.get(ROLE_MATERIAL_VOLUME, [None])[0] if ROLE_MATERIAL_VOLUME in by_role else None
        self.ownership = by_role.get(ROLE_OWNERSHIP, [None])[0] if ROLE_OWNERSHIP in by_role else None
        self.requirements = by_role.get(ROLE_REQUIREMENTS, [None])[0] if ROLE_REQUIREMENTS in by_role else None

        units = self._units()
        frames = self._frame_records()
        # Only AUTHORED frames are required to bind. A frame merely observed inside an
        # upstream packet is recorded as `observed_unbound` (a note) by _frame_records;
        # demanding it bind would be this adapter inventing a transform nobody authored.
        for frame in self._frames_output(frames):
            if frame["authored"] and frame["status"] != "bound":
                self.gaps.add("frame_not_bound", f"frames[{frame['frame_id']}].status",
                              f"authored frame {frame['frame_id']!r} is {frame['status']} "
                              f"relative to the assembly root", subject_id=frame["frame_id"])
        self.frames = frames
        components, mass_ledger = self._components_and_mass()
        attachments = self._attachments(frames)
        readiness = self._readiness(components, attachments, units)

        manifest: dict[str, Any] = {
            "schema_version": MANIFEST_SCHEMA,
            "assembly_id": self.assembly_id,
            "generated_by": {"tool": TOOL_NAME, "adapter_version": ADAPTER_VERSION},
            "scope_declaration": {
                "question_answered": ("does this assembly have the explicitly authored "
                                      "information needed for a dynamics trial"),
                "dynamics_executed": False,
                "physics_state_mutated": False,
                "production_wired": False,
                "meshes_repaired": False,
                "silent_defaults_used": False,
            },
            "inputs": [r.to_row() for r in sorted(self.inputs, key=lambda r: r.label)],
            "units": units,
            "frames": self._frames_output(frames),
            "components": components,
            "mass_ownership_ledger": mass_ledger,
            "attachments": attachments,
            "readiness": readiness,
            "unresolved": self.gaps.records(),
        }
        manifest["digest"] = document_digest(
            {k: v for k, v in manifest.items() if k != "digest"})
        return manifest

    # -- units ---------------------------------------------------------------
    def _units(self) -> dict[str, Any]:
        """Collect every units declaration the inputs actually make.

        Nothing is converted and nothing is assumed: a declaration that does not name
        metres, kilograms and seconds is a conflict, and an absent declaration is a
        gap. The canonical block states what the manifest's numbers are in.
        """
        declared: list[dict[str, Any]] = []
        conflicts: list[str] = []

        def record(label: str, field_path: str, value: Any, ok: bool) -> None:
            declared.append({"input_label": label, "field_path": field_path,
                             "declared": value, "names_si_m_kg_s": ok})
            if not str(value or "").strip():
                conflicts.append(f"{label}: no units declaration at {field_path}")
            elif not ok:
                conflicts.append(
                    f"{label}: declared units {value!r} at {field_path} do not name m, kg "
                    f"and s — this adapter applies no conversion")

        if self.anatomy is not None:
            meta = self.anatomy.document.get("meta", {}) or {}
            record(self.anatomy.label, "meta.units", meta.get("units"),
                   _declares_si(meta.get("units")))
        if self.material is not None:
            doc = self.material.document
            # material_volume.compile_document accepts coordinate_unit='m' and
            # density_unit='kg/m^3' only; check each field against that contract.
            record(self.material.label, "coordinate_unit", doc.get("coordinate_unit"),
                  doc.get("coordinate_unit") == "m")
            record(self.material.label, "density_unit", doc.get("density_unit"),
                  doc.get("density_unit") == "kg/m^3")
        if self.requirements is not None:
            req = self.requirements.document
            record(self.requirements.label, "units", req.get("units"),
                   _declares_si(req.get("units")))
        resolved = {"length_unit": "m", "mass_unit": "kg", "time_unit": "s",
                    "angle_unit": "rad"}
        return {"canonical": resolved, "declared_in": sorted(
            declared, key=lambda r: (r["input_label"], r["field_path"])),
            "conflicts": sorted(conflicts)}

    # -- frames --------------------------------------------------------------
    def _frame_records(self) -> dict[str, dict[str, Any]]:
        frames: dict[str, dict[str, Any]] = {}

        def register(frame_id: str, row: Mapping[str, Any], origin: list[float] | None,
                     basis: list[list[float]] | None, source: str, path: str) -> None:
            if frame_id in frames:
                raise AssemblyRefusal("duplicate_frame_id", f"{path}.frame_id",
                                      f"frame {frame_id!r} is declared more than once")
            authored = source.startswith("authored:")
            handedness = row.get("handedness")
            unit = row.get("coordinate_unit")
            scale = row.get("scale_to_m")
            if not isinstance(scale, (int, float)) or scale <= 0:
                self.gaps.add("frame_scale_to_m_missing", f"{path}.scale_to_m",
                              f"frame {frame_id!r} declares no positive scale_to_m; "
                              f"positions in it cannot be placed in metres",
                              severity=SEVERITY_BLOCKING if authored else SEVERITY_NOTE,
                              subject_id=frame_id)
            frames[frame_id] = {"frame_id": frame_id,
                                 "parent_frame_id": row.get("parent_frame_id"),
                                 "handedness": handedness,
                                 "coordinate_unit": unit,
                                 "scale_to_m": scale if isinstance(scale, (int, float)) else None,
                                 "origin_m": origin, "basis_rows": basis,
                                 "declared_by": source, "declaration_path": path,
                                 "authored": authored, "status": "declared"}

        if self.requirements is not None:
            for i, raw in enumerate(self.requirements.document.get("frames") or []):
                path = f"requirements[{self.requirements.label}].frames[{i}]"
                row = _require_mapping(raw, path, "frame declaration")
                fid = row.get("frame_id")
                if not isinstance(fid, str) or not fid.strip():
                    raise AssemblyRefusal("bad_schema", f"{path}.frame_id",
                                          "frame_id is required")
                register(fid, row, _vec3(row.get("origin_m"), f"{path}.origin_m"),
                         _mat3(row.get("basis_rows"), f"{path}.basis_rows"),
                         f"authored:{self.requirements.label}", path)

        if self.anatomy is not None:
            meta = self.anatomy.document.get("meta", {}) or {}
            conv = meta.get("coordinate_conventions")
            if isinstance(conv, Mapping):
                fid = f"anatomy:{self.anatomy.label}:target"
                register(fid, {"frame_id": fid, "parent_frame_id": None,
                                "handedness": conv.get("handedness"),
                                "coordinate_unit": meta.get("units"),
                                "scale_to_m": 1.0 if str(meta.get("units", "")).lower().startswith("si") else None},
                         [0.0, 0.0, 0.0], None, f"observed:{self.anatomy.label}",
                         f"inputs[label={self.anatomy.label}].meta.coordinate_conventions")

        if self.candidates is not None:
            bodies = self.candidates.document.get("bodies") or {}
            for body in sorted(bodies):
                body_row = bodies[body] or {}
                ltw = body_row.get("local_to_world")
                if not isinstance(ltw, Mapping):
                    continue
                fid = f"candidates:{self.candidates.label}:{body}"
                register(fid, {"frame_id": fid, "parent_frame_id": None,
                                "handedness": None, "coordinate_unit": body_row.get("units"),
                                "scale_to_m": 1.0},
                         _vec3(ltw.get("t_fitted_origin_m") or ltw.get("t_fitted_origin"),
                               f"{fid}.origin"),
                         _mat3(ltw.get("R_source_local_to_target"), f"{fid}.basis"),
                         f"observed:{self.candidates.label}",
                         f"inputs[label={self.candidates.label}].bodies.{body}.local_to_world")

        # Only AUTHORED frames (the requirements document's own declarations) form
        # the assembly frame tree. Frames merely OBSERVED inside an upstream packet
        # are recorded as what they are — a declared convention with no authored tie
        # to the assembly root — and never silently adopted as the root.
        for frame in frames.values():
            if not frame["authored"]:
                frame["status"] = "observed_unbound"
                self.gaps.add(
                    "frame_observed_not_bound", f"frames[{frame['frame_id']}].status",
                    f"frame {frame['frame_id']!r} is declared by "
                    f"{frame['declared_by']!r} but no authored transform ties it to the "
                    f"assembly root; geometry expressed in it stays unplaced. This adapter "
                    f"will not invent that transform.",
                    severity=SEVERITY_NOTE, subject_id=frame["frame_id"])
        roots = [f for f in frames.values() if f["authored"] and f["parent_frame_id"] is None]
        if frames and not roots:
            self.gaps.add("root_frame_ambiguous", "frames",
                          "no authored frame declares parent_frame_id null, so no assembly "
                          "root frame exists to bind anything to")
            return frames
        if len(roots) > 1:
            raise AssemblyRefusal(
                "root_frame_ambiguous", "requirements.frames",
                f"{len(roots)} authored frames declare parent_frame_id null "
                f"({sorted(f['frame_id'] for f in roots)}); exactly one assembly root is allowed")

        def bind(fid: str, seen: tuple[str, ...]) -> bool:
            frame = frames[fid]
            if frame["status"] == "bound":
                return True
            if frame["status"] in ("unbound", "conflict"):
                return False
            # An OBSERVED frame is never adopted as bound, even with a null parent:
            # being the packet's own rest frame is not an authored tie to this assembly.
            if not frame["authored"]:
                return False
            parent = frame["parent_frame_id"]
            if parent is None:
                if frame["origin_m"] is None or frame["basis_rows"] is None:
                    frame["status"] = "unbound"
                    self.gaps.add("root_frame_pose_missing", f"frames[{fid}]",
                                  f"the authored root frame {fid!r} declares no origin/basis; "
                                  f"nothing can be placed relative to it",
                                  subject_id=fid)
                    return False
                if not self._orthonormal(frame["basis_rows"]):
                    frame["status"] = "conflict"
                    self.gaps.add("frame_basis_not_orthonormal", f"frames[{fid}].basis_rows",
                                  f"root frame {fid!r} declares a non-orthonormal basis; no "
                                  f"re-orthogonalisation is performed", subject_id=fid)
                    return False
                frame["status"] = "bound"
                return True
            if fid in seen:
                frame["status"] = "unbound"
                self.gaps.add("frame_cycle", f"frames[{fid}].parent_frame_id",
                              f"frame {fid!r} is its own ancestor")
                return False
            if parent not in frames:
                frame["status"] = "unbound"
                self.gaps.add("frame_parent_unknown", f"frames[{fid}].parent_frame_id",
                              f"frame {fid!r} names unknown parent {parent!r}",
                              subject_id=fid)
                return False
            if frame["origin_m"] is None or frame["basis_rows"] is None:
                frame["status"] = "unbound"
                self.gaps.add("frame_unbound", f"frames[{fid}]",
                              f"frame {fid!r} has no authored origin/basis relative to "
                              f"{parent!r}; nothing in it can be placed in the assembly frame",
                              subject_id=fid)
                return False
            if not self._orthonormal(frame["basis_rows"]):
                frame["status"] = "conflict"
                self.gaps.add("frame_basis_not_orthonormal", f"frames[{fid}].basis_rows",
                              f"frame {fid!r} declares a non-orthonormal basis; no "
                              f"re-orthogonalisation is performed", subject_id=fid)
                return False
            if not bind(parent, seen + (fid,)):
                frame["status"] = "unbound"
                return False
            frame["status"] = "bound"
            return True

        for fid in sorted(frames):
            bind(fid, ())
        return frames

    @staticmethod
    def _orthonormal(basis: list[list[float]]) -> bool:
        try:
            rows = [[float(v) for v in row] for row in basis]
        except (TypeError, ValueError):
            return False
        for i in range(3):
            for j in range(3):
                dot = sum(rows[k][i] * rows[k][j] for k in range(3))
                if abs(dot - (1.0 if i == j else 0.0)) > _EPS_ORTHO:
                    return False
        return True

    def _frames_output(self, frames: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
        return [frames[k] for k in sorted(frames)]

    # -- components and mass --------------------------------------------------
    def _components_and_mass(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Build the component list and the explicit matter ledger."""
        claims: dict[str, dict[str, Any]] = {}
        counting_bindings: dict[str, list[str]] = {}
        self._component_index: dict[str, dict[str, Any]] = {}
        self._anatomy_claims(claims)
        self._material_claims(claims)

        components: dict[str, dict[str, Any]] = {}
        bound_claim_refs: set[str] = set()

        ownership_components: list[Mapping[str, Any]] = []
        if self.ownership is not None:
            for i, raw in enumerate(self.ownership.document.get("components") or []):
                path = f"ownership[{self.ownership.label}].components[{i}]"
                row = _require_mapping(raw, path, "component declaration")
                cid = row.get("component_id")
                if not isinstance(cid, str) or not cid.strip():
                    raise AssemblyRefusal("bad_schema", f"{path}.component_id",
                                          "component_id is required and must be non-empty")
                if cid in components:
                    raise AssemblyRefusal("duplicate_component_id", f"{path}.component_id",
                                          f"component id {cid!r} is declared more than once")
                kind = row.get("kind")
                if kind not in ("rigid_body", "membrane_patch", "tissue_volume"):
                    raise AssemblyRefusal("bad_schema", f"{path}.kind",
                                          f"component {cid!r}: kind must be rigid_body, "
                                          f"membrane_patch or tissue_volume")
                mass_mode = row.get("mass")
                if isinstance(mass_mode, Mapping) and mass_mode.get("declared") != "none":
                    raise AssemblyRefusal("bad_schema", f"{path}.mass",
                                          'the only inline mass declaration is {"declared": "none"}')
                local_frame = row.get("local_frame_id")
                frame = self.frames.get(local_frame) if isinstance(local_frame, str) else None
                if frame is None:
                    self.gaps.add("component_frame_missing", f"{path}.local_frame_id",
                                  f"component {cid!r} declares no local frame that exists in "
                                  f"the authored frame tree; its pose is unplaced",
                                  subject_id=cid)
                elif frame["status"] != "bound":
                    self.gaps.add("component_frame_unbound", f"{path}.local_frame_id",
                                  f"component {cid!r} local frame {local_frame!r} is "
                                  f"{frame['status']}", subject_id=cid)
                components[cid] = {"component_id": cid, "kind": kind,
                                   "local_frame_id": local_frame,
                                   "local_frame_status": (frame or {}).get("status", "absent"),
                                   "source_refs": [],
                                   "mass_declared_none": bool(mass_mode),
                                   "counting_claims": [], "claims": []}
                self._component_index[cid] = components[cid]
                ownership_components.append(row)

        for i, raw in enumerate((self.ownership.document.get("mass_claims") or [])
                                if self.ownership is not None else []):
            path = f"ownership[{self.ownership.label}].mass_claims[{i}]"
            row = _require_mapping(raw, path, "mass claim binding")
            ref = row.get("claim_ref")
            cid = row.get("component_id")
            if not isinstance(ref, str) or ref not in claims:
                raise AssemblyRefusal("unknown_claim_reference", f"{path}.claim_ref",
                                      f"binds unknown matter claim {ref!r}; known refs are "
                                      f"listed under mass_ownership_ledger.claims")
            if not isinstance(cid, str) or cid not in components:
                raise AssemblyRefusal("dangling_component_reference", f"{path}.component_id",
                                      f"claim {ref!r} binds to undeclared component {cid!r}")
            claim = claims[ref]
            counts = row.get("counts_toward_component_mass")
            if not isinstance(counts, bool):
                raise AssemblyRefusal("bad_schema", f"{path}.counts_toward_component_mass",
                                      "mass ownership must be authored explicitly as true/false")
            asserted = row.get("assert_mass_status")
            if asserted is not None and asserted != claim["mass_status"]:
                raise AssemblyRefusal(
                    "mass_status_promotion", f"{path}.assert_mass_status",
                    f"claim {ref!r} is supported as {claim['mass_status']!r} by its source; "
                    f"asserting {asserted!r} would promote provenance to a claim")
            if counts and (claim["representation"] == REP_SURFACE_OVERLAY
                           or components[cid]["kind"] == "membrane_patch"):
                raise AssemblyRefusal(
                    "unsupported_surface_mass_claim", f"{path}.counts_toward_component_mass",
                    f"component {cid!r} is a zero-thickness membrane patch and claim {ref!r} "
                    f"({claim['representation']}) is declared to count toward its mass; the v1 "
                    f"volume contract admits no thin-sheet mass, so a membrane that must carry "
                    f"mass has to own exclusive volume cells instead")
            claim["component_id"] = cid
            claim["counts_toward_component_mass"] = (bool(counts)
                                                     or bool(claim.get("counts_toward_component_mass")))
            claim["ownership_note"] = str(row.get("reason", ""))
            bound_claim_refs.add(ref)
            counting_bindings.setdefault(ref, []).append(cid)
            components[cid]["claims"].append(ref)
            if counts:
                components[cid]["counting_claims"].append(ref)

        # Any upstream matter that nobody owns is a gap, never a silent drop and
        # never an implicit assignment (implicit identity would be a guess).
        for ref in sorted(claims):
            claim = claims[ref]
            if ref in bound_claim_refs:
                continue
            self.gaps.add("unbound_matter_claim", f"mass_ownership_ledger.claims[{ref}]",
                          f"matter {ref!r} ({claim['representation']}) is not bound to any "
                          f"component by an ownership document; it is counted nowhere and "
                          f"dropped by nobody", subject_id=ref)

        # duplicate mass ownership, direction 1: one piece of matter counted by more
        # than one binding (whether or not the bindings name the same component).
        for ref in sorted(counting_bindings):
            if len(counting_bindings[ref]) > 1:
                raise AssemblyRefusal(
                    "duplicate_mass_ownership", f"mass_ownership_ledger.claims[{ref}]",
                    f"matter {ref!r} is declared to count toward the mass of "
                    f"{len(counting_bindings[ref])} bindings {sorted(counting_bindings[ref])}; "
                    f"the same matter may be counted once and only once")

        # duplicate mass ownership, direction 2: two counting claims for one component.
        for cid in sorted(components):
            counting = components[cid]["counting_claims"]
            if len(counting) > 1:
                raise AssemblyRefusal(
                    "duplicate_mass_ownership", f"components[{cid}].mass_claims",
                    f"component {cid!r} has {len(counting)} mass-bearing matter claims "
                    f"{sorted(counting)}; membrane and body representations may not both "
                    f"count the same matter")
            if counting and components[cid]["mass_declared_none"]:
                raise AssemblyRefusal(
                    "contradictory_mass_declaration", f"components[{cid}].mass",
                    f"component {cid!r} declares zero mass AND owns mass-bearing claim(s) "
                    f"{sorted(counting)}; the contradiction is authored, so it is refused "
                    f"rather than resolved by picking one")

        component_rows: list[dict[str, Any]] = []
        for cid in sorted(components):
            comp = components[cid]
            counting = comp["counting_claims"]
            if len(counting) == 1:
                claim = claims[counting[0]]
                mass = {"status": claim["mass_status"],
                        "authority_claim_ref": counting[0],
                        "representation": claim["representation"],
                        "mass_kg": claim["mass_kg"],
                        "center_of_mass_m": claim["center_of_mass_m"],
                        "inertia_com_kg_m2": claim["inertia_com_kg_m2"],
                        "validated_tissue_mass": claim["mass_status"] == MASS_RECONSTRUCTED,
                        "requires_density_validation": claim["requires_density_validation"],
                        "assumptions": claim["assumptions"],
                        "source": claim["source"]}
                if claim["mass_status"] != MASS_RECONSTRUCTED:
                    self.gaps.add(
                        "component_mass_not_validated", f"components[{cid}].mass.status",
                        f"component {cid!r} mass is {claim['mass_status']!r}; a dynamics "
                        f"trial needs reconstructed tissue mass with a declared density "
                        f"source", subject_id=cid,
                        evidence={"assumptions": list(claim["assumptions"])})
            elif comp["mass_declared_none"]:
                mass = {"status": "declared_massless", "authority_claim_ref": None,
                        "representation": None, "mass_kg": 0.0,
                        "center_of_mass_m": None, "inertia_com_kg_m2": None,
                        "validated_tissue_mass": False,
                        "requires_density_validation": False, "assumptions": [
                            "authored zero-mass declaration; contributes no matter"],
                        "source": {"input_label": self.ownership.label if self.ownership else None,
                                   "field_path": f"components[{cid}].mass"}}
            elif counting:  # unreachable (guarded above) but explicit for safety
                mass = {"status": MASS_UNRESOLVED, "authority_claim_ref": None,
                        "representation": None, "mass_kg": None, "center_of_mass_m": None,
                        "inertia_com_kg_m2": None, "validated_tissue_mass": False,
                        "requires_density_validation": True, "assumptions": [], "source": {}}
            else:
                mass = {"status": MASS_UNRESOLVED, "authority_claim_ref": None,
                        "representation": None, "mass_kg": None, "center_of_mass_m": None,
                        "inertia_com_kg_m2": None, "validated_tissue_mass": False,
                        "requires_density_validation": True, "assumptions": [
                            "no mass-bearing claim bound and no authored zero-mass declaration"],
                        "source": {}}
                self.gaps.add("component_mass_undecided", f"components[{cid}].mass.status",
                              f"component {cid!r} has neither a single mass-bearing matter "
                              f"claim nor an explicit zero-mass declaration", subject_id=cid)
            component_rows.append({
                "component_id": cid, "kind": comp["kind"],
                "local_frame_id": comp["local_frame_id"],
                "local_frame_status": comp["local_frame_status"],
                "source_refs": sorted(set(comp["claims"])), "mass": mass})

        self.claim_index = claims
        ledger = {
            "claims": [dict(claims[ref], claim_ref=ref) for ref in sorted(claims)],
            "counted_mass_kg": self._summed([c["mass"]["mass_kg"] for c in component_rows
                                            if c["mass"]["authority_claim_ref"]]),
            "uncounted_mass_kg": self._summed([claims[ref]["mass_kg"] for ref in sorted(claims)
                                               if not claims[ref].get("counts_toward_component_mass",
                                                                            False)]),
            "double_counting_check": ("one mass-bearing representation per component; "
                                      "enforced by refusal duplicate_mass_ownership"),
        }
        return component_rows, ledger

    @staticmethod
    def _summed(values: Sequence[float | None]) -> dict[str, Any]:
        """Sum the masses that exist; `incomplete` says loudly that some did not."""
        vals = [float(v) for v in values if v is not None]
        return {"value": float(sum(vals)), "incomplete": len(vals) != len(values)}

    def _anatomy_claims(self, claims: dict[str, dict[str, Any]]) -> None:
        if self.anatomy is None:
            return
        label = self.anatomy.label
        phys = self.anatomy.document.get("physiology") or []
        for i, raw in enumerate(phys):
            path = f"inputs[label={label}].physiology[{i}]"
            row = _require_mapping(raw, f"{path}", "physiology record")
            body = row.get("body")
            if not isinstance(body, str) or not body.strip():
                raise AssemblyRefusal("bad_schema", f"{path}.body",
                                      "physiology record needs a body name")
            ref = f"anatomy:{label}:physiology:{body}"
            if ref in claims:
                raise AssemblyRefusal("duplicate_claim_reference", f"{path}.body",
                                      f"two physiology records for body {body!r}")
            # A transported record may legitimately carry null/NaN inertial fields when
            # the upstream fit declared it unresolved; that is reported as ABSENT mass
            # property, never coerced and never placed.
            com = _vec3(row.get("com_fitted"), f"{path}.com_fitted", allow_nonfinite=True)
            inertia = _mat3(row.get("inertia_fitted"), f"{path}.inertia_fitted",
                            allow_nonfinite=True)
            mass_kind = row.get("mass_kind")
            status = row.get("status")
            if mass_kind == "root_ref_frame_unscaled":
                mass_status = MASS_ROOT_REFERENCE
            elif mass_kind == "source_effective_x_det_scale" or \
                    status == "requires_density_validation":
                mass_status = MASS_TRANSPORTED
            else:
                mass_status = MASS_UNRESOLVED
            assumptions = [a for a in (mass_kind, row.get("density_assumption")) if a]
            claims[ref] = {
                "matter_id": ref, "representation": REP_SOURCE_SEGMENT,
                "mass_kg": row.get("mass") if _is_finite_number(row.get("mass")) else None,
                "center_of_mass_m": com,
                "inertia_com_kg_m2": inertia,
                "mass_status": mass_status,
                "requires_density_validation": bool(
                    row.get("status") == "requires_density_validation" or not row.get("admitted")),
                "assumptions": assumptions,
                "source": {"input_label": label, "field_path": path,
                           "upstream_status": status, "upstream_mass_kind": mass_kind,
                           "upstream_admitted_kinematic": row.get("admitted"),
                           "admitted_as": self.anatomy.admitted_as},
                "component_id": None, "counts_toward_component_mass": None,
                "ownership_note": ""}
            if com is None or inertia is None:
                self.gaps.add("mass_property_absent", f"{path}.com_fitted",
                              f"physiology record for body {body!r} carries no finite centre "
                              f"of mass / inertia; it stays absent (no value is inferred)",
                              severity=SEVERITY_NOTE, subject_id=ref)

    def _material_claims(self, claims: dict[str, dict[str, Any]]) -> None:
        if self.material is None:
            return
        label = self.material.label
        mv = self.upstream["material_volume"]
        if mv is None:
            self.gaps.add("upstream_dependency_absent", f"inputs[label={label}]",
                          "material_volume compiler unavailable; reconstructed mass cannot "
                          "be integrated and stays unresolved")
            return
        try:
            result = mv.compile_document(self.material.document)
        except Exception as ex:  # upstream refusal is surfaced verbatim, never repaired
            self.gaps.add("material_volume_compile_refused", f"inputs[label={label}]",
                          f"{type(ex).__name__}: {ex}", subject_id=label)
            return
        doc = self.material.document
        densities = {m.get("material_id"): m for m in (doc.get("materials") or [])}
        regions = {r.get("region_id"): r for r in (doc.get("regions") or [])}
        subtotals = result.get("resolved_region_subtotals") or {}
        for region_id in sorted(subtotals):
            props = subtotals[region_id]
            region = regions.get(region_id, {})
            material = densities.get(region.get("material_id"), {})
            density_source = material.get("density_source")
            # Whitespace is not a source. Upstream already refuses an empty one, so this is
            # defence in depth: if that ever loosens, unsourced mass still cannot validate.
            if isinstance(density_source, str) and not density_source.strip():
                density_source = None
            ref = f"material_volume:{label}:region:{region_id}"
            com_path = f"inputs[label={label}].resolved_region_subtotals[{region_id}]"
            com = _vec3(props.get("center_of_mass_m"), f"{com_path}.center_of_mass_m",
                        allow_nonfinite=True)
            inertia = _mat3(props.get("inertia_com_kg_m2"),
                            f"{com_path}.inertia_com_kg_m2", allow_nonfinite=True)
            mass_kg = props.get("mass_kg") if _is_finite_number(props.get("mass_kg")) else None
            claims[ref] = {
                "matter_id": ref, "representation": REP_TET_VOLUME,
                "mass_kg": mass_kg,
                "center_of_mass_m": com,
                "inertia_com_kg_m2": inertia,
                # The volume is reconstructed, but a density with no declared source is an
                # assumption, not a measurement: it can never validate tissue mass.
                "mass_status": (MASS_RECONSTRUCTED if density_source
                                else MASS_DENSITY_UNVALIDATED),
                "requires_density_validation": not bool(density_source),
                "assumptions": ["piecewise-constant density integrated over tetrahedral volume",
                                f"density_source={density_source!r}"],
                "source": {"input_label": label,
                           "field_path": f"resolved_region_subtotals[{region_id}]",
                           "upstream_status": "compiled_by_material_volume",
                           "volume_m3": props.get("volume_m3"),
                           "cell_count": props.get("cell_count"),
                           "mass_owner_id": region.get("mass_owner_id"),
                           "admitted_as": self.material.admitted_as},
                "component_id": None, "counts_toward_component_mass": None,
                "ownership_note": ""}
            if mass_kg is None or com is None or inertia is None:
                self.gaps.add("mass_property_absent",
                              f"inputs[label={label}].resolved_region_subtotals[{region_id}]",
                              f"the material-volume compiler returned no finite mass property "
                              f"for region {region_id!r}; it is reported absent, not zeroed",
                              subject_id=region_id)
            if not density_source:
                self.gaps.add("density_source_missing",
                              f"inputs[label={label}].materials[{region.get('material_id')}].density_source",
                              f"region {region_id!r} integrates a density with no declared "
                              f"source; the mass is reported but never validated",
                              subject_id=region_id)
        if not result.get("complete"):
            self.gaps.add("material_volume_incomplete", f"inputs[label={label}]",
                          "the tetrahedral partition has unresolved or conflicted cells, so "
                          "no body total mass exists (resolved-only subtotals are partial)",
                          subject_id=label)

    # -- attachments ----------------------------------------------------------
    def _attachments(self, frames: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        geometric = self._geometric_candidates()
        self._candidate_index = {c["candidate_id"]: c for c in geometric}
        mechanical = self._mechanical_attachments(frames)

        qualified_ids = {a["attachment_id"] for a in mechanical if a["status"] == MECH_QUALIFIED}
        for cand in geometric:
            refs = sorted({a["attachment_id"] for a in mechanical
                           if cand["candidate_id"] in a.get("port_refs", [])})
            cand["referenced_by_attachments"] = refs
            cand["covered_by_qualified_attachment"] = bool(set(refs) & qualified_ids)
            if cand["status"] == GEO_PORT and not cand["covered_by_qualified_attachment"]:
                self.gaps.add("attachment_port_unqualified",
                              f"attachments.geometric_candidates[{cand['candidate_id']}]",
                              f"anatomical port {cand['site_id']!r} on body "
                              f"{cand['source_body']!r} has no mechanically qualified "
                              f"attachment", subject_id=cand["candidate_id"])
        return {"geometric_candidates": geometric, "mechanical_attachments": mechanical,
                "status_separation_note": (
                    "geometric candidate status answers 'is this a port or a waypoint'; "
                    "mechanical attachment status answers 'does an authored patch at these "
                    "ports pass the finite-area couple-stiffness gate'. Neither is derived "
                    "from the other.")}

    def _geometric_candidates(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if self.candidates is None:
            return out
        label = self.candidates.label
        doc = self.candidates.document
        bodies = doc.get("bodies") or {}
        for body in sorted(bodies):
            body_row = bodies[body] or {}
            for i, raw in enumerate(body_row.get("candidates") or []):
                path = f"inputs[label={label}].bodies.{body}.candidates[{i}]"
                row = _require_mapping(raw, path, "attachment candidate")
                site_id = row.get("site_id")
                if not isinstance(site_id, str) or not site_id.strip():
                    raise AssemblyRefusal("bad_schema", f"{path}.site_id",
                                          "candidate needs a site_id")
                roles = row.get("endpoint_roles")
                legacy = row.get("candidate_roles")
                role_source = ("endpoint_roles" if roles is not None and legacy is None else
                               "candidate_roles(legacy)" if legacy is not None and roles is None
                               else "both" if roles is not None and legacy is not None
                               else "tendon_membership_only")
                merged = sorted({str(r) for r in (roles or [])} | {str(r) for r in (legacy or [])})
                membership = row.get("tendon_membership") or []
                if not merged:
                    merged = [f"{m.get('role')}:{m.get('tendon')}" for m in membership
                              if isinstance(m, Mapping)]
                    merged = sorted({r for r in merged if not r.startswith("waypoint:")})
                is_port = bool(merged)
                fitted = row.get("fitted") or {}
                pos = fitted.get("fitted_pos_global", fitted.get("fitted_pos_global_m"))
                resolved_flag = bool(fitted.get("resolved", pos is not None))
                cand_id = f"cand:{label}:{body}:{site_id}"
                mech_qual = row.get("mechanical_qualification", False)
                out.append({
                    "candidate_id": cand_id, "site_id": site_id, "source_body": body,
                    "status": GEO_PORT if is_port else GEO_WAYPOINT,
                    "endpoint_roles": merged,
                    "role_field_source": role_source,
                    "tendon_membership": sorted(
                        [f"{m.get('tendon')}[{m.get('index_in_path')}/{m.get('path_length')}]="
                         f"{m.get('role')}" for m in membership if isinstance(m, Mapping)]),
                    "position_m": _vec3(pos, f"{path}.fitted.fitted_pos_global",
                                        allow_nonfinite=not resolved_flag),
                    "resolved": resolved_flag,
                    "source_mechanical_qualification": bool(mech_qual),
                    "referenced_by_attachments": [],
                    "covered_by_qualified_attachment": False})
                if not fitted.get("resolved", True):
                    self.gaps.add("candidate_position_unresolved", f"{path}.fitted.resolved",
                                  f"site {site_id!r} carries no fitted position "
                                  f"({fitted.get('reason', 'no reason given')})", subject_id=cand_id,
                                  severity=SEVERITY_NOTE)
                if mech_qual:  # never trust it; qualification is the gate's to grant
                    self.gaps.add("upstream_mechanical_claim_overridden", f"{path}.mechanical_qualification",
                                  f"candidate {site_id!r} arrived with mechanical_qualification "
                                  f"true; this adapter re-derives qualification only from the "
                                  f"finite-area gate", subject_id=cand_id)
        return sorted(out, key=lambda c: c["candidate_id"])

    def _mechanical_attachments(self, frames: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
        if self.requirements is None:
            return []
        label = self.requirements.label
        faa = self.upstream["finite_area_attachment"]
        out: list[dict[str, Any]] = []
        for i, raw in enumerate(self.requirements.document.get("attachments") or []):
            path = f"requirements[{label}].attachments[{i}]"
            row = _require_mapping(raw, path, "mechanical attachment requirement")
            aid = row.get("attachment_id")
            if not isinstance(aid, str) or not aid.strip():
                raise AssemblyRefusal("bad_schema", f"{path}.attachment_id",
                                      "attachment_id is required")
            missing: list[str] = []

            def need(field: str, value: Any) -> Any:
                if value is None:
                    missing.append(f"{path}.{field}")
                return value

            membrane = need("membrane_component_id", row.get("membrane_component_id"))
            body = need("body_component_id", row.get("body_component_id"))
            for field, value in (("membrane_component_id", membrane),
                                 ("body_component_id", body)):
                if isinstance(value, str) and value not in self._component_index:
                    raise AssemblyRefusal(
                        "dangling_component_reference", f"{path}.{field}",
                        f"attachment {aid!r} references component {value!r}, which no ownership "
                        f"document declares")
            anchor_frame = need("anchor_frame_id", row.get("anchor_frame_id"))
            anchors = _mat3_list(row.get("anchors_local_m"), f"{path}.anchors_local_m")
            if anchors is None or len(anchors) < 3:
                missing.append(f"{path}.anchors_local_m")
            weights = row.get("weights")
            if weights is None:
                missing.append(f"{path}.weights")
            patch_area = need("patch_area_m2", row.get("patch_area_m2"))
            kappa = need("kappa_areal_n_m3", row.get("kappa_areal_n_m3"))
            k_couple_min = need("k_couple_min_n_m_per_rad", row.get("k_couple_min_n_m_per_rad"))

            # The patch stiffness Kbar must be authored, or derived by the attachment
            # owner's own provenance law Kbar = kappa_areal * A_patch. It is NEVER left
            # to AttachmentSpec's internal default of 1 N/m — that would be a silent
            # default smuggled in through a dependency. Every route is recorded.
            stiffness_kbar = row.get("stiffness_kbar")
            if stiffness_kbar is None:
                if _is_finite_number(patch_area) and _is_finite_number(kappa):
                    stiffness_kbar = float(patch_area) * float(kappa)
                    stiffness_source = "derived:kappa_areal_n_m3*patch_area_m2"
                    self.gaps.add(
                        "attachment_stiffness_derived", f"{path}.stiffness_kbar",
                        f"attachment {aid!r} authors no explicit stiffness_kbar; the gate is "
                        f"run with Kbar = kappa_areal*patch_area = {stiffness_kbar:.6e} N/m, "
                        f"the attachment owner's own provenance relation (recorded, not silent)",
                        severity=SEVERITY_NOTE, subject_id=aid)
                else:
                    stiffness_source = None
                    missing.append(f"{path}.stiffness_kbar")
            else:
                stiffness_source = "authored"

            endpoints: list[dict[str, Any]] = []
            ep_path_root = f"{path}.endpoints"
            for j, raw_ep in enumerate(row.get("endpoints") or []):
                ep_path = f"{ep_path_root}[{j}]"
                ep = _require_mapping(raw_ep, ep_path, "attachment endpoint")
                comp = ep.get("component_id")
                if not isinstance(comp, str) or not comp:
                    raise AssemblyRefusal("dangling_component_reference",
                                          f"{ep_path}.component_id",
                                          f"endpoint of attachment {aid!r} names no component")
                if comp not in self._component_index:
                    raise AssemblyRefusal(
                        "dangling_component_reference", f"{ep_path}.component_id",
                        f"attachment {aid!r} endpoint references component {comp!r}, which no "
                        f"ownership document declares; the reference is not created implicitly")
                port_ref = ep.get("port_candidate_id")
                frame_id = ep.get("local_frame_id")
                endpoints.append({"endpoint_id": str(ep.get("endpoint_id") or f"{aid}-ep{j}"),
                                  "component_id": comp,
                                  "local_frame_id": frame_id,
                                  "position_m": _vec3(ep.get("position_m"), f"{ep_path}.position_m"),
                                  "port_candidate_id": port_ref,
                                  "authored_role": ep.get("authored_role")})

            # --- the waypoint law: a waypoint is never an attachment by geometry ---
            for ep in endpoints:
                ref = ep["port_candidate_id"]
                if not isinstance(ref, str):
                    continue
                cand = self._candidate_by_id(ref)
                if cand is None:
                    raise AssemblyRefusal("unknown_port_reference", f"{path}.endpoints",
                                          f"attachment {aid!r} references unknown candidate "
                                          f"{ref!r}")
                if cand["status"] == GEO_WAYPOINT and ep["authored_role"] in (
                        "first_endpoint", "last_endpoint"):
                    # Allowed, but never silent: the ROLE comes from the requirements
                    # document, not from this adapter deciding the waypoint is a port.
                    self.gaps.add(
                        "waypoint_authored_as_port",
                        f"{path}.endpoints[{j}].authored_role",
                        f"site {cand['site_id']!r} is an intermediate tendon waypoint in the "
                        f"candidates packet; attachment {aid!r} authors it as a "
                        f"{ep['authored_role']!r}. The geometric status stays "
                        f"{GEO_WAYPOINT}; only the authored role makes it usable here",
                        severity=SEVERITY_NOTE, subject_id=cand["candidate_id"])
                elif cand["status"] == GEO_WAYPOINT:
                    raise AssemblyRefusal(
                        "waypoint_promoted_to_attachment", f"{path}.endpoints",
                        f"site {cand['site_id']!r} is an intermediate tendon waypoint on "
                        f"{cand['source_body']!r}; a waypoint does not become a membrane "
                        f"attachment patch automatically. Author endpoint_role explicitly "
                        f"if this port is intended.")

            record: dict[str, Any] = {
                "attachment_id": aid, "membrane_component_id": membrane,
                "body_component_id": body, "anchor_frame_id": anchor_frame,
                "endpoints": sorted(endpoints, key=lambda e: e["endpoint_id"]),
                "port_refs": sorted({e["port_candidate_id"] for e in endpoints
                                     if isinstance(e["port_candidate_id"], str)}),
                "anchors_local_m": anchors, "weights": (
                    [float(w) for w in weights] if isinstance(weights, list) else None),
                "patch_area_m2": patch_area, "kappa_areal_n_m3": kappa,
                "stiffness_kbar": stiffness_kbar, "stiffness_kbar_source": stiffness_source,
                "k_couple_min_n_m_per_rad": k_couple_min,
                "missing_fields": sorted(set(missing)),
                "gate_result": None, "status": MECH_INCOMPLETE}

            if anchor_frame is not None:
                frame = frames.get(anchor_frame)
                if frame is None:
                    self.gaps.add("anchor_frame_unknown", f"{path}.anchor_frame_id",
                                  f"attachment {aid!r} names frame {anchor_frame!r}, which no "
                                  f"authored frame declaration provides", subject_id=aid)
                elif frame["status"] != "bound":
                    self.gaps.add("frame_unbound", f"{path}.anchor_frame_id",
                                  f"attachment {aid!r} anchors live in unbound frame "
                                  f"{anchor_frame!r}", subject_id=aid)
            for j, ep in enumerate(endpoints):
                ep_frame = ep["local_frame_id"]
                if not isinstance(ep_frame, str) or not ep_frame:
                    self.gaps.add("attachment_endpoint_frame_missing",
                                  f"{ep_path_root}[{j}].local_frame_id",
                                  f"endpoint of attachment {aid!r} declares no local frame; "
                                  f"its pose is unplaced", subject_id=aid)
                elif ep_frame not in frames or frames[ep_frame]["status"] != "bound":
                    self.gaps.add("frame_unbound", f"{ep_path_root}[{j}].local_frame_id",
                                  f"endpoint of attachment {aid!r} names frame "
                                  f"{ep_frame!r}, which is not bound to the assembly root",
                                  subject_id=aid)

            record["missing_fields"] = sorted(set(record["missing_fields"]))
            if record["missing_fields"]:
                for field_path in record["missing_fields"]:
                    self.gaps.add("attachment_parameter_missing", field_path,
                                  f"attachment {aid!r} cannot be mechanically qualified: "
                                  f"this authored value is absent and no default is supplied",
                                  subject_id=aid)
            elif faa is None:
                record["gate_result"] = {"error": "finite_area_attachment dependency absent"}
                self.gaps.add("attachment_gate_dependency_absent", f"{path}",
                              f"attachment {aid!r} cannot be qualified without the "
                              f"finite-area attachment gate", subject_id=aid)
            else:
                record = self._qualify(record, faa, path)

            if record["status"] != MECH_QUALIFIED:
                self.gaps.add("attachment_not_qualified", f"{path}.status",
                              f"attachment {aid!r} is not mechanically qualified "
                              f"(missing: {record['missing_fields'] or 'gate refused'})",
                              subject_id=aid)
            out.append(record)
        return sorted(out, key=lambda a: a["attachment_id"])

    def _candidate_by_id(self, candidate_id: str) -> dict[str, Any] | None:
        return getattr(self, "_candidate_index", {}).get(candidate_id)

    def _qualify(self, record: dict[str, Any], faa: Any, path: str) -> dict[str, Any]:
        """Delegate qualification to the finite-area attachment owner's gate."""
        try:
            spec = faa.AttachmentSpec(record["anchors_local_m"], weights=record["weights"],
                                      stiffness=record["stiffness_kbar"])
        except Exception as ex:
            record["gate_result"] = {"refusal": f"AttachmentSpec: {ex}"}
            return record
        try:
            quality = spec.quality()
            eigen = spec.assert_min_couple_stiffness(
                record["k_couple_min_n_m_per_rad"], kappa_areal=record["kappa_areal_n_m3"],
                patch_area=record["patch_area_m2"])
        except Exception as ex:
            record["gate_result"] = {"refusal": f"assert_min_couple_stiffness: {ex}",
                                     "numerical_verdict": quality.verdict}
            return record
        record["gate_result"] = {
            "delegated_to": "tools/finite_area_attachment/finite_area_attachment.py",
            "numerical_verdict": quality.verdict,
            "constrains_all_six": bool(quality.constrains_all_six),
            "kappa_rot": float(quality.kappa_rot) if math.isfinite(quality.kappa_rot) else None,
            "spread_radius_m": float(quality.spread_radius),
            "couple_stiffness_eigenvalues_n_m_per_rad": [float(v) for v in eigen]}
        record["status"] = MECH_QUALIFIED
        return record

    # -- readiness ------------------------------------------------------------
    def _readiness(self, components: list[dict[str, Any]], attachments: dict[str, Any],
                  units: dict[str, Any]) -> dict[str, Any]:
        mechanical = attachments["mechanical_attachments"]
        geometric = attachments["geometric_candidates"]
        ports = [c for c in geometric if c["status"] == GEO_PORT]
        checks = {
            "all_required_inputs_present": not any(
                r["code"] == "required_input_absent" for r in self.gaps.records()),
            "units_consistent": not units["conflicts"],
            "every_component_has_validated_tissue_mass": bool(components) and all(
                c["mass"]["validated_tissue_mass"] or c["mass"]["status"] == "declared_massless"
                for c in components),
            "every_authored_frame_bound": all(
                f["status"] == "bound" for f in self._frames_output(self.frames)
                if f["authored"]),
            "no_unbound_frame_is_referenced": not any(
                r["code"] in ("component_frame_missing", "component_frame_unbound",
                              "frame_unbound", "anchor_frame_unknown",
                              "attachment_endpoint_frame_missing")
                for r in self.gaps.records()),
            "no_matter_unowned": not any(r["code"] == "unbound_matter_claim"
                                         for r in self.gaps.records()),
            "every_attachment_qualified": bool(mechanical) and all(
                a["status"] == MECH_QUALIFIED for a in mechanical),
            "every_anatomical_port_covered": all(c["covered_by_qualified_attachment"]
                                                 for c in ports),
        }
        blocking = self.gaps.blocking_codes()
        return {"dynamics_trial_ready": (not blocking) and all(checks.values()),
                "checks": {k: bool(v) for k, v in sorted(checks.items())},
                "blocking_codes": blocking,
                "counts": {
                    "inputs_present": sum(1 for r in self.inputs if r.presence == "present"),
                    "inputs_absent": sum(1 for r in self.inputs if r.presence != "present"),
                    "components": len(components),
                    "matter_claims": len(self.claim_index),
                    "geometric_candidates": len(geometric),
                    "anatomical_ports": len(ports),
                    "mechanical_attachments": len(mechanical),
                    "mechanically_qualified": sum(1 for a in mechanical
                                                  if a["status"] == MECH_QUALIFIED),
                    "unresolved_records": len(self.gaps.records()),
                }}


def _mat3_list(value: Any, path: str) -> list[list[float]] | None:
    """An (N,3) list of finite 3-vectors, or None when absent."""
    if value is None:
        return None
    rows = _require_list(value, path, "anchor list")
    out = [_vec3(row, f"{path}[{i}]") for i, row in enumerate(rows)]
    if any(row is None for row in out):  # unreachable: allow_nonfinite defaults False
        raise AssemblyRefusal("nonfinite_input", path, "non-finite anchor coordinate")
    return out


_SI_TOKENS = ("m", "kg", "s", "rad")


def _si_tokens(text: str) -> set[str]:
    import re
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if t}


def _declares_si(text: Any) -> bool:
    """True only when the declared unit string names metres, kilograms and seconds.

    A crude substring test would accept `"cm"` (contains 'm'); tokenising does not.
    """
    if not isinstance(text, str) or not text.strip():
        return False
    tokens = _si_tokens(text)
    return {"m", "kg", "s"} <= tokens


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def build_from_bundle_file(path: Path) -> dict[str, Any]:
    bundle = json.loads(Path(path).read_text(encoding="utf-8"))
    return HandoffAssembler(bundle, bundle_dir=Path(path).resolve().parent).build()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", required=True, help="assembly bundle JSON")
    parser.add_argument("--out", default=None, help="write the manifest here")
    args = parser.parse_args(argv)
    try:
        manifest = build_from_bundle_file(Path(args.bundle))
    except AssemblyRefusal as ex:
        print(json.dumps({"refused": ex.to_record()}, sort_keys=True, indent=2))
        return 2
    text = canonical_json(manifest) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(json.dumps({"assembly_id": manifest["assembly_id"],
                      "dynamics_trial_ready": manifest["readiness"]["dynamics_trial_ready"],
                      "blocking_codes": manifest["readiness"]["blocking_codes"],
                      "unresolved_records": len(manifest["unresolved"]),
                      "out": args.out}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
