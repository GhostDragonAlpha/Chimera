"""Versioned CPU physical fixture packets for the future GPU membrane input.

This module reads the immutable v1 fixture format and evaluates its float32 input
stream through the admitted physical units contract. It never certifies a GPU.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

import numpy as np

from .geometry import build_rest_geometry
from .units_contract import (
    SyntheticCoefficientProvenance, admit_volumetric_v1, evaluate_physical_v1,
)

PACKET_VERSION = "elastic-physical-fixtures/v1"


class FixtureRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason, self.message = reason, message


@dataclass(frozen=True)
class PhysicalFixture:
    path: Path
    source_sha256: str
    name: str
    rest_pos_f32: np.ndarray
    cur_pos_f32: np.ndarray
    faces_i32: np.ndarray
    E_pa: float
    nu: float
    thickness_m: float
    expected_energy_j: float
    expected_corner_forces_n: np.ndarray
    expected_vertex_forces_n: np.ndarray
    rest_B_f32: np.ndarray
    rest_areas0_f32: np.ndarray
    csr_offsets_u32: np.ndarray | None
    csr_corners_u32: np.ndarray | None


def _finite_array(value: Any, name: str, dtype: Any) -> np.ndarray:
    a = np.asarray(value)
    if not np.issubdtype(a.dtype, np.number):
        raise FixtureRefusal("non_numeric", f"{name} is not numeric")
    a = a.astype(dtype, copy=True)
    if not np.all(np.isfinite(a)):
        raise FixtureRefusal("nonfinite", f"{name} contains nonfinite values")
    return a


def load_fixture(path: str | Path) -> PhysicalFixture:
    """Load and validate a frozen v1 fixture without modifying it."""
    p = Path(path).resolve()
    if p.suffix.lower() != ".npz" or not p.is_file():
        raise FixtureRefusal("missing_fixture", f"fixture must be an existing .npz: {p}")
    try:
        with np.load(p, allow_pickle=False) as z:
            required = ("rest_pos", "cur_pos", "faces_int32", "E_f64", "nu_f64", "h_f64",
                        "rest_B_f32", "rest_areas0_f32", "exp_energy_f64",
                        "exp_corner_f64", "exp_vertex_f64")
            missing = [k for k in required if k not in z.files]
            if missing:
                raise FixtureRefusal("missing_field", f"missing fixture fields: {missing}")
            rest = _finite_array(z["rest_pos"], "rest_pos", np.float32)
            cur = _finite_array(z["cur_pos"], "cur_pos", np.float32)
            faces = np.asarray(z["faces_int32"])
            if faces.dtype != np.int32 or faces.ndim != 2 or faces.shape[1] != 3:
                raise FixtureRefusal("bad_faces", "faces_int32 must be an int32 (n,3) array")
            faces = faces.copy()
            E, nu, h = (float(z[k]) for k in ("E_f64", "nu_f64", "h_f64"))
            if not all(np.isfinite(v) for v in (E, nu, h)):
                raise FixtureRefusal("nonfinite_material", "material scalars must be finite")
            B = _finite_array(z["rest_B_f32"], "rest_B_f32", np.float32)
            areas = _finite_array(z["rest_areas0_f32"], "rest_areas0_f32", np.float32)
            corner = _finite_array(z["exp_corner_f64"], "exp_corner_f64", np.float64)
            vertex = _finite_array(z["exp_vertex_f64"], "exp_vertex_f64", np.float64)
            energy = float(z["exp_energy_f64"])
            if not np.isfinite(energy):
                raise FixtureRefusal("nonfinite_expected", "expected energy is nonfinite")
            offsets = corners = None
            if "csr_offsets_u32" in z.files or "csr_corners_u32" in z.files:
                if "csr_offsets_u32" not in z.files or "csr_corners_u32" not in z.files:
                    raise FixtureRefusal("missing_csr", "CSR offsets and corners are paired")
                offsets = np.asarray(z["csr_offsets_u32"])
                corners = np.asarray(z["csr_corners_u32"])
                if offsets.dtype != np.uint32 or corners.dtype != np.uint32:
                    raise FixtureRefusal("bad_csr", "CSR arrays must retain uint32 dtype")
                offsets, corners = offsets.copy(), corners.copy()
    except FixtureRefusal:
        raise
    except (TypeError, ValueError, OSError) as exc:
        raise FixtureRefusal("malformed_fixture", f"could not read fixture: {exc}") from exc
    if rest.ndim != 2 or rest.shape[1] != 3 or cur.shape != rest.shape:
        raise FixtureRefusal("bad_positions", "rest/current positions must have equal (n,3) shape")
    if faces.shape[0] == 0 or np.any(faces < 0) or np.any(faces >= rest.shape[0]):
        raise FixtureRefusal("bad_faces", "face indices are outside the position array")
    if corner.shape != (faces.shape[0], 3, 3) or vertex.shape != (rest.shape[0], 3):
        raise FixtureRefusal("bad_expected_shape", "expected full force arrays have wrong shape")
    if B.shape != (faces.shape[0], 2, 2) or areas.shape != (faces.shape[0],):
        raise FixtureRefusal("bad_rest_shape", "rest frame arrays have wrong shape")
    return PhysicalFixture(p, hashlib.sha256(p.read_bytes()).hexdigest(), p.stem,
                           rest, cur, faces, E, nu, h, energy, corner, vertex,
                           B, areas, offsets, corners)


def evaluate_fixture(fixture: PhysicalFixture):
    """Evaluate the frozen float32 input stream in float64 arithmetic."""
    rest = build_rest_geometry(fixture.rest_pos_f32, fixture.faces_i32)
    provenance = SyntheticCoefficientProvenance(
        declaration_id="elastic-physical-fixtures-v1-frozen-input",
        purpose="CPU reference for explicitly synthetic fixture coefficients",
    )
    material = admit_volumetric_v1(fixture.E_pa, fixture.thickness_m, fixture.nu,
                                   provenance=provenance)
    return evaluate_physical_v1(rest, material, fixture.cur_pos_f32)


def _json_array(a):
    return np.asarray(a).tolist()


def reference_record(fixture: PhysicalFixture) -> dict[str, Any]:
    result = evaluate_fixture(fixture)
    ev = result.evaluation
    return {
        "packet_version": PACKET_VERSION, "fixture": fixture.name,
        "source_npz_sha256": fixture.source_sha256,
        "input_dtype": "float32", "evaluation_dtype": "float64",
        "material": {"E_pa": fixture.E_pa, "nu": fixture.nu, "thickness_m": fixture.thickness_m,
                     "provenance_kind": result.material.provenance.kind,
                     "provenance_declaration": result.material.provenance.declaration_id},
        "energy_j": ev.energy, "surface_energy_j_per_m2": _json_array(ev.per_face.Wbar),
        "volume_energy_j_per_m3": _json_array(ev.per_face.w_vol),
        "corner_forces_n": _json_array(ev.corner_forces),
        "vertex_forces_n": _json_array(ev.vertex_forces),
        "reference_expected_energy_j": fixture.expected_energy_j,
        "reference_expected_corner_forces_n": _json_array(fixture.expected_corner_forces_n),
        "reference_expected_vertex_forces_n": _json_array(fixture.expected_vertex_forces_n),
        "gpu_certification": "open; CPU reference only",
    }


def write_reference(fixture: PhysicalFixture, output: str | Path) -> Path:
    """Write one complete JSON reference; refuse overwrite and partial output."""
    out = Path(output).resolve()
    if out.exists():
        raise FixtureRefusal("output_exists", f"refusing to overwrite existing output: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    record = reference_record(fixture)
    try:
        with out.open("x", encoding="utf8", newline="\n") as fh:
            json.dump(record, fh, indent=2, sort_keys=True)
            fh.write("\n")
    except FileExistsError as exc:
        raise FixtureRefusal("output_exists", f"refusing to overwrite existing output: {out}") from exc
    return out


def validate_result(fixture: PhysicalFixture, result) -> dict[str, Any]:
    """Compare every reference component; scalar-only matches are insufficient."""
    ev = result.evaluation
    def exact(a, b): return np.array_equal(np.asarray(a), np.asarray(b))
    finite = bool(np.isfinite(ev.energy) and np.all(np.isfinite(ev.corner_forces))
                  and np.all(np.isfinite(ev.vertex_forces)) and
                  np.all(np.isfinite(ev.per_face.w_vol)))
    return {"fixture": fixture.name, "source_npz_sha256": fixture.source_sha256,
            "finite": finite,
            "full_energy_equal": bool(finite and ev.energy == fixture.expected_energy_j),
            "full_corner_equal": bool(finite and exact(ev.corner_forces, fixture.expected_corner_forces_n)),
            "full_vertex_equal": bool(finite and exact(ev.vertex_forces, fixture.expected_vertex_forces_n)),
            "all_ok": bool(finite and ev.energy == fixture.expected_energy_j and
                           exact(ev.corner_forces, fixture.expected_corner_forces_n) and
                           exact(ev.vertex_forces, fixture.expected_vertex_forces_n))}


def verify_frozen_fixture(path: str | Path) -> dict[str, Any]:
    fixture = load_fixture(path)
    return validate_result(fixture, evaluate_fixture(fixture))


__all__ = ["PACKET_VERSION", "FixtureRefusal", "PhysicalFixture", "load_fixture",
           "evaluate_fixture", "reference_record", "write_reference", "validate_result", "verify_frozen_fixture"]
