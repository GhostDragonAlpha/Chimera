"""Versioned physical CPU fixture packets; GPU ABI and tolerances remain open."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

import numpy as np

_candidate_repo = os.environ.get("CHIMERA_FIXTURE_REPO")
if _candidate_repo and _candidate_repo not in sys.path:
    sys.path.insert(0, _candidate_repo)

from tools.elastic_foundation.geometry import build_rest_geometry
from tools.elastic_foundation.units_contract import (
    SyntheticCoefficientProvenance,
    admit_surface_v1,
    admit_volumetric_v1,
    evaluate_physical_v1,
)


PACKET_VERSION = "elastic-physical-fixture/v2"
REFERENCE_VERSION = "independent-stvk-scalar/v1"
EPS64 = 2.0 ** -52
CPU_OPS = 512
CPU_GAMMA = (CPU_OPS * EPS64) / (1.0 - CPU_OPS * EPS64)
LEGACY_GEOMETRY_FIELDS = (
    "rest_pos", "cur_pos", "faces_int32", "rest_B_f32", "rest_areas0_f32",
    "csr_offsets_u32", "csr_corners_u32",
)
ARRAY_FIELDS = (
    "packet_version_u8", "fixture_id_u8", "source_json_u8", "provenance_json_u8",
    "rest_pos_original_f64", "cur_pos_original_f64", "rest_pos_upload_f32",
    "cur_pos_upload_f32", "faces_i32", "rest_B_upload_f32",
    "rest_areas0_upload_f32", "csr_offsets_upload_u32", "csr_corners_upload_u32",
    "E3d_original_f64", "h_original_f64", "E2_original_f64", "nu_original_f64",
    "E3d_upload_f32", "h_upload_f32", "E2_upload_f32", "nu_upload_f32",
    "ref_original_F_f64", "ref_original_Wbar_f64", "ref_original_wvol_f64",
    "ref_original_corner_f64", "ref_original_vertex_f64", "ref_original_energy_f64",
    "scale_original_F_f64", "scale_original_Wbar_f64", "scale_original_wvol_f64",
    "scale_original_corner_f64", "scale_original_vertex_f64", "scale_original_energy_f64",
    "ref_upload_F_f64", "ref_upload_Wbar_f64", "ref_upload_wvol_f64",
    "ref_upload_corner_f64", "ref_upload_vertex_f64", "ref_upload_energy_f64",
    "scale_upload_F_f64", "scale_upload_Wbar_f64", "scale_upload_wvol_f64",
    "scale_upload_corner_f64", "scale_upload_vertex_f64", "scale_upload_energy_f64",
)
FIELD_DTYPES = {
    **{name: "uint8" for name in
       ("packet_version_u8", "fixture_id_u8", "source_json_u8", "provenance_json_u8")},
    **{name: "float32" for name in ARRAY_FIELDS if name.endswith("_upload_f32")},
    **{name: "float64" for name in ARRAY_FIELDS
       if name.endswith("_f64") and not name.endswith("_upload_f32")},
    "faces_i32": "int32",
    "csr_offsets_upload_u32": "uint32",
    "csr_corners_upload_u32": "uint32",
}
assert set(FIELD_DTYPES) == set(ARRAY_FIELDS)
SCHEMA_DEFINITION = {
    "packet_version": PACKET_VERSION,
    "reference_version": REFERENCE_VERSION,
    "field_dtypes": FIELD_DTYPES,
    "shape_contract": (
        "positions=(nV,3); faces=(nF,3); B=(nF,2,2); areas=(nF); "
        "CSR offsets=(nV+1), corners=(3nF); references match full evaluator fields"
    ),
    "upload_rounding": "IEEE-754 binary32 round-to-nearest-ties-to-even; exact widen to binary64",
    "cpu_bound": "abs(actual-reference) <= gamma(512)*forward_absolute_path_scale",
}


class FixtureReason:
    OUTPUT_EXISTS = "output_exists"
    MISSING = "missing"
    TRUST_ANCHOR = "manifest_trust_anchor_mismatch"
    MANIFEST = "malformed_manifest"
    PACKET_HASH = "packet_hash_mismatch"
    SCHEMA = "packet_schema_mismatch"
    DTYPE = "packet_dtype_mismatch"
    SHAPE = "packet_shape_mismatch"
    NONFINITE = "packet_nonfinite"
    MATERIAL = "packet_material_inconsistent"
    GEOMETRY = "packet_geometry_inconsistent"
    CSR = "packet_csr_malformed"
    SOURCE = "packet_source_mismatch"
    PROVENANCE = "packet_provenance_mismatch"
    REFERENCE = "packet_reference_mismatch"
    LEGACY = "legacy_geometry_mismatch"
    CLI = "fixture_cli_error"


class FixtureRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


SCHEMA_SHA256 = sha256_bytes(canonical_json(SCHEMA_DEFINITION))


def _u8(value: str | dict) -> np.ndarray:
    raw = value.encode("utf-8") if isinstance(value, str) else canonical_json(value)
    return np.frombuffer(raw, dtype=np.uint8).copy()


def _decode_u8(value: np.ndarray, label: str) -> bytes:
    if value.dtype != np.uint8 or value.ndim != 1 or value.size == 0:
        raise FixtureRefusal(FixtureReason.DTYPE, f"{label} must be a nonempty uint8 vector")
    return value.tobytes()


def _exact(z, name: str, dtype, shape=None, finite=True) -> np.ndarray:
    if name not in z.files:
        raise FixtureRefusal(FixtureReason.SCHEMA, f"missing packet field {name!r}")
    value = np.asarray(z[name])
    if value.dtype != np.dtype(dtype):
        raise FixtureRefusal(
            FixtureReason.DTYPE, f"{name} must be {np.dtype(dtype)}, got {value.dtype}"
        )
    if shape is not None and value.shape != shape:
        raise FixtureRefusal(
            FixtureReason.SHAPE, f"{name} must have shape {shape}, got {value.shape}"
        )
    if finite and value.dtype.kind == "f" and not np.all(np.isfinite(value)):
        raise FixtureRefusal(FixtureReason.NONFINITE, f"{name} contains nonfinite values")
    result = value.copy()
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class MaterialStream:
    E3d_pa: float
    h_m: float
    E2_n_per_m: float
    nu: float
    stored_dtype: str


@dataclass(frozen=True)
class Reference:
    F: np.ndarray
    Wbar: np.ndarray
    wvol: np.ndarray
    corner: np.ndarray
    vertex: np.ndarray
    energy: float
    scale_F: np.ndarray
    scale_Wbar: np.ndarray
    scale_wvol: np.ndarray
    scale_corner: np.ndarray
    scale_vertex: np.ndarray
    scale_energy: float


@dataclass(frozen=True)
class PhysicalPacket:
    path: Path
    packet_sha256: str
    manifest_path: Path
    manifest_sha256: str
    fixture_id: str
    source: dict
    source_sha256: str
    provenance: dict
    provenance_sha256: str
    rest_original: np.ndarray
    current_original: np.ndarray
    rest_upload: np.ndarray
    current_upload: np.ndarray
    faces: np.ndarray
    B_upload: np.ndarray
    areas_upload: np.ndarray
    csr_offsets_upload: np.ndarray
    csr_corners_upload: np.ndarray
    original_material: MaterialStream
    upload_material: MaterialStream
    original_reference: Reference
    upload_reference: Reference


def _scalar(value, dtype, name: str) -> float:
    a = np.asarray(value)
    if a.dtype != np.dtype(dtype):
        raise FixtureRefusal(FixtureReason.DTYPE, f"{name} must be scalar {np.dtype(dtype)}")
    if a.shape != ():
        raise FixtureRefusal(FixtureReason.SHAPE, f"{name} must be scalar")
    result = float(a)
    if not math.isfinite(result):
        raise FixtureRefusal(FixtureReason.NONFINITE, f"{name} is nonfinite")
    return result


def _fraction(value) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def _reference_scalar(rest, current, faces, B, areas, offsets, corners,
                      E2, nu, h) -> Reference:
    """Independent scalar STVK reference using supplied geometry primitives."""
    n_faces, n_vertices = len(faces), len(rest)
    lam = E2 * nu / (1 - nu * nu)
    mu = E2 / (2 * (1 + nu))
    zero = E2 * 0
    Fs, Wbars, wvols, face_forces = [], [], [], []
    qFs, qWs, qWvols, qCorners = [], [], [], []
    for f, tri in enumerate(faces):
        y0, y1, y2 = (current[int(i)] for i in tri)
        N = [[y1[r] - y0[r], y2[r] - y0[r]] for r in range(3)]
        bf = B[f]
        F = [[sum(N[r][k] * bf[k][j] for k in range(2)) for j in range(2)]
             for r in range(3)]
        qF = [[sum(abs(N[r][k] * bf[k][j]) for k in range(2)) for j in range(2)]
              for r in range(3)]
        C = [[sum(F[r][i] * F[r][j] for r in range(3)) for j in range(2)]
             for i in range(2)]
        strain = [[(C[i][j] - (1 if i == j else 0)) / 2 for j in range(2)]
                  for i in range(2)]
        tr = strain[0][0] + strain[1][1]
        tr2 = strain[0][0] * strain[0][0] + 2 * strain[0][1] * strain[0][1] + \
              strain[1][1] * strain[1][1]
        term_l = lam * tr * tr / 2
        term_m = mu * tr2
        W = term_l + term_m
        qW = abs(term_l) + abs(term_m)
        S = [[zero, zero], [zero, zero]]
        qS = [[zero, zero], [zero, zero]]
        for i in range(2):
            for j in range(2):
                elastic = 2 * mu * strain[i][j]
                volumetric = lam * tr if i == j else zero
                S[i][j] = volumetric + elastic
                qS[i][j] = abs(volumetric) + abs(elastic)
        P = [[sum(F[r][k] * S[k][j] for k in range(2)) for j in range(2)]
             for r in range(3)]
        qP = [[sum(abs(F[r][k]) * qS[k][j] for k in range(2)) for j in range(2)]
              for r in range(3)]
        PBt = [[sum(P[r][k] * bf[j][k] for k in range(2)) for j in range(2)]
               for r in range(3)]
        qPBt = [[sum(qP[r][k] * abs(bf[j][k]) for k in range(2)) for j in range(2)]
                for r in range(3)]
        area = areas[f]
        ff = [
            [area * (PBt[r][0] + PBt[r][1]) for r in range(3)],
            [-area * PBt[r][0] for r in range(3)],
            [-area * PBt[r][1] for r in range(3)],
        ]
        qff = [
            [abs(area) * (qPBt[r][0] + qPBt[r][1]) for r in range(3)],
            [abs(area) * qPBt[r][0] for r in range(3)],
            [abs(area) * qPBt[r][1] for r in range(3)],
        ]
        Fs.append(F); qFs.append(qF); Wbars.append(W); qWs.append(qW)
        wvols.append(W / h); qWvols.append(qW / abs(h))
        face_forces.append(ff); qCorners.append(qff)

    vertex = [[zero, zero, zero] for _ in range(n_vertices)]
    qvertex = [[zero, zero, zero] for _ in range(n_vertices)]
    flat = [face_forces[f][k] for f in range(n_faces) for k in range(3)]
    qflat = [qCorners[f][k] for f in range(n_faces) for k in range(3)]
    for vertex_id in range(n_vertices):
        for flat_id in corners[int(offsets[vertex_id]):int(offsets[vertex_id + 1])]:
            for component in range(3):
                vertex[vertex_id][component] += flat[int(flat_id)][component]
                qvertex[vertex_id][component] += qflat[int(flat_id)][component]
    energy_terms = [areas[f] * Wbars[f] for f in range(n_faces)]
    energy = sum(energy_terms, zero)
    qenergy = sum((abs(areas[f]) * qWs[f] for f in range(n_faces)), zero)

    def f64(value):
        return np.asarray(value, dtype=np.float64)
    return Reference(
        F=f64(Fs), Wbar=f64(Wbars), wvol=f64(wvols),
        corner=f64(face_forces), vertex=f64(vertex), energy=float(energy),
        scale_F=f64(qFs), scale_Wbar=f64(qWs), scale_wvol=f64(qWvols),
        scale_corner=f64(qCorners), scale_vertex=f64(qvertex), scale_energy=float(qenergy),
    )


def _csr(faces: np.ndarray, n_vertices: int):
    flat = faces.reshape(-1)
    order = np.argsort(flat, kind="stable")
    counts = np.bincount(flat[order], minlength=n_vertices)
    offsets = np.zeros(n_vertices + 1, dtype=np.int64)
    np.cumsum(counts, out=offsets[1:])
    return offsets, order.astype(np.int64)


def _fraction_geometry(rest: np.ndarray, current: np.ndarray, faces: np.ndarray):
    r = [[Fraction(str(float(x))) for x in row] for row in rest]
    y = [[Fraction(str(float(x))) for x in row] for row in current]
    B, areas = [], []
    for tri in faces:
        p0, p1, p2 = (r[int(i)] for i in tri)
        D = [[p1[0] - p0[0], p2[0] - p0[0]],
             [p1[1] - p0[1], p2[1] - p0[1]]]
        det = D[0][0] * D[1][1] - D[0][1] * D[1][0]
        B.append([[D[1][1] / det, -D[0][1] / det],
                  [-D[1][0] / det, D[0][0] / det]])
        areas.append(abs(det) / 2)
    offsets, corners = _csr(faces, len(rest))
    return r, y, B, areas, offsets.tolist(), corners.tolist()


def canonical_geometries() -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    tri_rest = np.asarray([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
    tri_current = np.asarray([[0, 0, 0], [6 / 5, 0, 0], [0, 4 / 5, 0]], dtype=np.float64)
    tri_faces = np.asarray([[0, 1, 2]], dtype=np.int32)

    xs = [Fraction(i, 4) for i in range(9)]
    ys = [Fraction(j, 4) for j in range(5)]
    patch_rest = np.asarray([[float(x), float(y), 0.0] for y in ys for x in xs], dtype=np.float64)
    patch_current = patch_rest.copy()
    patch_current[patch_rest[:, 0] == 2.0, 1] += 0.25
    faces = []
    for j in range(4):
        for i in range(8):
            v00 = j * 9 + i; v10 = v00 + 1; v01 = v00 + 9; v11 = v01 + 1
            faces.extend(((v00, v10, v11), (v00, v11, v01)) if (i + j) % 2 == 0
                         else ((v00, v10, v01), (v10, v11, v01)))
    patch_faces = np.asarray(faces, dtype=np.int32)
    return {
        "rational_triangle": (tri_rest, tri_current, tri_faces),
        "canonical_patch_8x4": (patch_rest, patch_current, patch_faces),
    }


def _legacy_patch_source(legacy_run: Path, trusted_manifest_sha256: str,
                         canonical: tuple[np.ndarray, np.ndarray, np.ndarray]) -> dict:
    manifest_path = legacy_run / "manifest.json"
    actual_manifest_hash = sha256_file(manifest_path)
    if actual_manifest_hash != trusted_manifest_sha256.lower():
        raise FixtureRefusal(FixtureReason.TRUST_ANCHOR, "legacy manifest SHA-256 mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["fixtures"]["patch_8x4_shear"]
    packet_path = legacy_run / entry["file"]
    if sha256_file(packet_path) != entry["sha256"]:
        raise FixtureRefusal(FixtureReason.PACKET_HASH, "legacy patch NPZ hash mismatch")
    rest, current, faces = canonical
    geometry = build_rest_geometry(rest.astype(np.float32), faces)
    expected = {
        "rest_pos": rest.astype(np.float32),
        "cur_pos": current.astype(np.float32),
        "faces_int32": faces,
        "rest_B_f32": geometry.B.astype(np.float32),
        "rest_areas0_f32": geometry.areas0.astype(np.float32),
        "csr_offsets_u32": geometry.csr_offsets.astype(np.uint32),
        "csr_corners_u32": geometry.csr_corners.astype(np.uint32),
    }
    with np.load(packet_path, allow_pickle=False) as z:
        for field in LEGACY_GEOMETRY_FIELDS:
            if field not in z.files or not np.array_equal(z[field], expected[field]):
                raise FixtureRefusal(FixtureReason.LEGACY, f"legacy geometry differs at {field}")
    return {
        "kind": "canonical_geometry_with_legacy_compatibility",
        "recipe": "2m-x-1m alternating-diagonal 8x4 grid; right boundary y += 1/4m",
        "legacy_usage": "geometry compatibility only; material and expected fields unread",
        "legacy_fields_read": list(LEGACY_GEOMETRY_FIELDS),
        "legacy_manifest_sha256": actual_manifest_hash,
        "legacy_npz_sha256": entry["sha256"],
    }


def _arrays_for_fixture(fixture_id: str, geometry, source: dict) -> dict[str, np.ndarray]:
    rest, current, faces = geometry
    rest32, current32 = rest.astype(np.float32), current.astype(np.float32)
    upload_geom = build_rest_geometry(rest32, faces)
    B32 = upload_geom.B.astype(np.float32)
    areas32 = upload_geom.areas0.astype(np.float32)
    offsets32 = upload_geom.csr_offsets.astype(np.uint32)
    corners32 = upload_geom.csr_corners.astype(np.uint32)
    provenance = {
        "kind": "synthetic",
        "declaration_id": f"elastic-physical-fixture-v2:{fixture_id}",
        "purpose": "dimensionally explicit CPU fixture; no real-material or GPU claim",
    }
    E3d, h, E2, nu = 1000.0, 1.0 / 500.0, 2.0, 3.0 / 10.0
    E3d32, h32, nu32 = np.float32(E3d), np.float32(h), np.float32(nu)
    E232 = np.float32(np.float64(E3d32) * np.float64(h32))

    fr, fy, fB, fA, foffs, fcorners = _fraction_geometry(rest, current, faces)
    original_ref = _reference_scalar(fr, fy, faces.tolist(), fB, fA, foffs, fcorners,
                                     Fraction(2), Fraction(3, 10), Fraction(1, 500))
    upload_ref = _reference_scalar(
        rest32.astype(np.float64).tolist(), current32.astype(np.float64).tolist(), faces.tolist(),
        B32.astype(np.float64).tolist(), areas32.astype(np.float64).tolist(),
        offsets32.tolist(), corners32.tolist(), float(E232), float(nu32), float(h32),
    )
    arrays = {
        "packet_version_u8": _u8(PACKET_VERSION), "fixture_id_u8": _u8(fixture_id),
        "source_json_u8": _u8(source), "provenance_json_u8": _u8(provenance),
        "rest_pos_original_f64": rest, "cur_pos_original_f64": current,
        "rest_pos_upload_f32": rest32, "cur_pos_upload_f32": current32,
        "faces_i32": faces, "rest_B_upload_f32": B32,
        "rest_areas0_upload_f32": areas32, "csr_offsets_upload_u32": offsets32,
        "csr_corners_upload_u32": corners32,
        "E3d_original_f64": np.asarray(E3d, dtype=np.float64),
        "h_original_f64": np.asarray(h, dtype=np.float64),
        "E2_original_f64": np.asarray(E2, dtype=np.float64),
        "nu_original_f64": np.asarray(nu, dtype=np.float64),
        "E3d_upload_f32": np.asarray(E3d32, dtype=np.float32),
        "h_upload_f32": np.asarray(h32, dtype=np.float32),
        "E2_upload_f32": np.asarray(E232, dtype=np.float32),
        "nu_upload_f32": np.asarray(nu32, dtype=np.float32),
    }
    for prefix, ref in (("original", original_ref), ("upload", upload_ref)):
        arrays.update({
            f"ref_{prefix}_F_f64": ref.F, f"ref_{prefix}_Wbar_f64": ref.Wbar,
            f"ref_{prefix}_wvol_f64": ref.wvol, f"ref_{prefix}_corner_f64": ref.corner,
            f"ref_{prefix}_vertex_f64": ref.vertex,
            f"ref_{prefix}_energy_f64": np.asarray(ref.energy, dtype=np.float64),
            f"scale_{prefix}_F_f64": ref.scale_F,
            f"scale_{prefix}_Wbar_f64": ref.scale_Wbar,
            f"scale_{prefix}_wvol_f64": ref.scale_wvol,
            f"scale_{prefix}_corner_f64": ref.scale_corner,
            f"scale_{prefix}_vertex_f64": ref.scale_vertex,
            f"scale_{prefix}_energy_f64": np.asarray(ref.scale_energy, dtype=np.float64),
        })
    assert set(arrays) == set(ARRAY_FIELDS)
    return arrays


def generate(output: str | Path, legacy_run: str | Path,
             trusted_legacy_manifest_sha256: str) -> Path:
    output = Path(output).resolve()
    if output.exists():
        raise FixtureRefusal(FixtureReason.OUTPUT_EXISTS, f"refusing existing output {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        geometries = canonical_geometries()
        sources = {
            "rational_triangle": {
                "kind": "analytic_recipe",
                "recipe": "right unit triangle under diag(6/5,4/5)",
                "legacy_usage": "none",
            },
            "canonical_patch_8x4": _legacy_patch_source(
                Path(legacy_run).resolve(), trusted_legacy_manifest_sha256,
                geometries["canonical_patch_8x4"],
            ),
        }
        entries = {}
        for fixture_id, geometry in geometries.items():
            arrays = _arrays_for_fixture(fixture_id, geometry, sources[fixture_id])
            path = temp / f"{fixture_id}.npz"
            np.savez_compressed(path, **arrays)
            source_raw = arrays["source_json_u8"].tobytes()
            provenance_raw = arrays["provenance_json_u8"].tobytes()
            entries[fixture_id] = {
                "file": path.name, "sha256": sha256_file(path),
                "source_sha256": sha256_bytes(source_raw),
                "provenance_sha256": sha256_bytes(provenance_raw),
            }
        manifest = {
            "packet_version": PACKET_VERSION,
            "reference_version": REFERENCE_VERSION,
            "schema_sha256": SCHEMA_SHA256,
            "legacy_manifest_sha256": trusted_legacy_manifest_sha256.lower(),
            "fixtures": entries,
            "gpu_acceptance": "OPEN: no ABI execution or binary32 tolerance",
        }
        (temp / "manifest.json").write_bytes(canonical_json(manifest) + b"\n")
        temp.replace(output)
        return output
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def _material(z, prefix: str, dtype) -> MaterialStream:
    suffix = "original_f64" if prefix == "original" else "upload_f32"
    return MaterialStream(
        E3d_pa=_scalar(z[f"E3d_{suffix}"], dtype, f"E3d_{suffix}"),
        h_m=_scalar(z[f"h_{suffix}"], dtype, f"h_{suffix}"),
        E2_n_per_m=_scalar(z[f"E2_{suffix}"], dtype, f"E2_{suffix}"),
        nu=_scalar(z[f"nu_{suffix}"], dtype, f"nu_{suffix}"),
        stored_dtype=str(np.dtype(dtype)),
    )


def _reference(z, prefix: str, nf: int, nv: int) -> Reference:
    # Explicit names keep the on-disk schema auditable.
    values = {
        "F": _exact(z, f"ref_{prefix}_F_f64", np.float64, (nf, 3, 2)),
        "Wbar": _exact(z, f"ref_{prefix}_Wbar_f64", np.float64, (nf,)),
        "wvol": _exact(z, f"ref_{prefix}_wvol_f64", np.float64, (nf,)),
        "corner": _exact(z, f"ref_{prefix}_corner_f64", np.float64, (nf, 3, 3)),
        "vertex": _exact(z, f"ref_{prefix}_vertex_f64", np.float64, (nv, 3)),
        "energy": _scalar(z[f"ref_{prefix}_energy_f64"], np.float64,
                          f"ref_{prefix}_energy_f64"),
        "scale_F": _exact(z, f"scale_{prefix}_F_f64", np.float64, (nf, 3, 2)),
        "scale_Wbar": _exact(z, f"scale_{prefix}_Wbar_f64", np.float64, (nf,)),
        "scale_wvol": _exact(z, f"scale_{prefix}_wvol_f64", np.float64, (nf,)),
        "scale_corner": _exact(z, f"scale_{prefix}_corner_f64", np.float64, (nf, 3, 3)),
        "scale_vertex": _exact(z, f"scale_{prefix}_vertex_f64", np.float64, (nv, 3)),
        "scale_energy": _scalar(z[f"scale_{prefix}_energy_f64"], np.float64,
                                f"scale_{prefix}_energy_f64"),
    }
    for name in ("scale_F", "scale_Wbar", "scale_wvol", "scale_corner",
                 "scale_vertex", "scale_energy"):
        if np.any(np.asarray(values[name]) < 0):
            raise FixtureRefusal(FixtureReason.REFERENCE, f"negative forward scale {name}")
    return Reference(**values)


def _validate_csr(faces, offsets, corners, nv):
    nf = len(faces)
    if offsets.shape != (nv + 1,) or corners.shape != (3 * nf,):
        raise FixtureRefusal(FixtureReason.CSR, "CSR arrays have wrong shape")
    if int(offsets[0]) != 0 or int(offsets[-1]) != 3 * nf or np.any(offsets[1:] < offsets[:-1]):
        raise FixtureRefusal(FixtureReason.CSR, "CSR offsets are malformed")
    if not np.array_equal(np.sort(corners.astype(np.int64)), np.arange(3 * nf)):
        raise FixtureRefusal(FixtureReason.CSR, "CSR corners are not a permutation")
    flat_vertices = faces.reshape(-1)
    for vertex in range(nv):
        ids = corners[int(offsets[vertex]):int(offsets[vertex + 1])]
        if np.any(flat_vertices[ids] != vertex):
            raise FixtureRefusal(FixtureReason.CSR, f"CSR segment {vertex} owns wrong corners")


def _validate_source(source: object, fixture_id: str, manifest: dict) -> None:
    if not isinstance(source, dict):
        raise FixtureRefusal(FixtureReason.SOURCE, "source record must be an object")
    if fixture_id == "rational_triangle":
        expected = {
            "kind": "analytic_recipe",
            "recipe": "right unit triangle under diag(6/5,4/5)",
            "legacy_usage": "none",
        }
        if source != expected:
            raise FixtureRefusal(FixtureReason.SOURCE, "rational triangle source recipe changed")
        return
    if fixture_id != "canonical_patch_8x4":
        raise FixtureRefusal(FixtureReason.SOURCE, f"unknown canonical fixture {fixture_id!r}")
    required = {"kind", "recipe", "legacy_usage", "legacy_fields_read",
                "legacy_manifest_sha256", "legacy_npz_sha256"}
    if (set(source) != required or
            source.get("kind") != "canonical_geometry_with_legacy_compatibility" or
            source.get("recipe") !=
            "2m-x-1m alternating-diagonal 8x4 grid; right boundary y += 1/4m" or
            source.get("legacy_usage") !=
            "geometry compatibility only; material and expected fields unread" or
            source.get("legacy_fields_read") != list(LEGACY_GEOMETRY_FIELDS) or
            source.get("legacy_manifest_sha256") != manifest["legacy_manifest_sha256"] or
            not isinstance(source.get("legacy_npz_sha256"), str) or
            len(source["legacy_npz_sha256"]) != 64):
        raise FixtureRefusal(FixtureReason.SOURCE, "canonical patch source binding changed")


def load_packet(manifest_path: str | Path, trusted_manifest_sha256: str,
                fixture_id: str) -> PhysicalPacket:
    manifest_path = Path(manifest_path).resolve()
    if not manifest_path.is_file():
        raise FixtureRefusal(FixtureReason.MISSING, f"missing manifest {manifest_path}")
    actual_manifest_hash = sha256_file(manifest_path)
    if actual_manifest_hash != trusted_manifest_sha256.lower():
        raise FixtureRefusal(FixtureReason.TRUST_ANCHOR, "manifest SHA-256 differs from trusted anchor")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if set(manifest) != {"packet_version", "reference_version", "schema_sha256",
                            "legacy_manifest_sha256", "fixtures", "gpu_acceptance"}:
            raise ValueError("manifest keys")
        if (manifest["packet_version"] != PACKET_VERSION or
                manifest["reference_version"] != REFERENCE_VERSION or
                manifest["schema_sha256"] != SCHEMA_SHA256):
            raise ValueError("version/schema")
        entry = manifest["fixtures"][fixture_id]
        if set(entry) != {"file", "sha256", "source_sha256", "provenance_sha256"}:
            raise ValueError("fixture entry keys")
        if Path(entry["file"]).name != entry["file"]:
            raise ValueError("packet path")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FixtureRefusal(FixtureReason.MANIFEST, f"malformed manifest: {exc}") from exc
    path = manifest_path.parent / entry["file"]
    if not path.is_file() or sha256_file(path) != entry["sha256"]:
        raise FixtureRefusal(FixtureReason.PACKET_HASH, "packet SHA-256 differs from manifest")
    try:
        with np.load(path, allow_pickle=False) as z:
            if set(z.files) != set(ARRAY_FIELDS):
                raise FixtureRefusal(FixtureReason.SCHEMA, "packet fields differ from v2 schema")
            version_raw = _decode_u8(_exact(z, "packet_version_u8", np.uint8, finite=False),
                                     "packet_version_u8")
            id_raw = _decode_u8(_exact(z, "fixture_id_u8", np.uint8, finite=False), "fixture_id_u8")
            if version_raw.decode("utf-8") != PACKET_VERSION or id_raw.decode("utf-8") != fixture_id:
                raise FixtureRefusal(FixtureReason.SCHEMA, "embedded packet version/id mismatch")
            source_raw = _decode_u8(_exact(z, "source_json_u8", np.uint8, finite=False),
                                    "source_json_u8")
            provenance_raw = _decode_u8(_exact(z, "provenance_json_u8", np.uint8, finite=False),
                                        "provenance_json_u8")
            if sha256_bytes(source_raw) != entry["source_sha256"]:
                raise FixtureRefusal(FixtureReason.SOURCE, "source record hash mismatch")
            if sha256_bytes(provenance_raw) != entry["provenance_sha256"]:
                raise FixtureRefusal(FixtureReason.PROVENANCE, "provenance record hash mismatch")
            source, provenance = json.loads(source_raw), json.loads(provenance_raw)
            if source_raw != canonical_json(source) or provenance_raw != canonical_json(provenance):
                raise FixtureRefusal(FixtureReason.SCHEMA, "source/provenance JSON is not canonical")
            _validate_source(source, fixture_id, manifest)
            if (set(provenance) != {"kind", "declaration_id", "purpose"} or
                    provenance["kind"] != "synthetic" or
                    not all(isinstance(provenance[k], str) and provenance[k]
                            for k in ("declaration_id", "purpose"))):
                raise FixtureRefusal(FixtureReason.PROVENANCE, "malformed synthetic provenance")
            rest0 = _exact(z, "rest_pos_original_f64", np.float64)
            cur0 = _exact(z, "cur_pos_original_f64", np.float64)
            rest32 = _exact(z, "rest_pos_upload_f32", np.float32)
            cur32 = _exact(z, "cur_pos_upload_f32", np.float32)
            faces = _exact(z, "faces_i32", np.int32)
            if (rest0.ndim != 2 or rest0.shape[1:] != (3,) or cur0.shape != rest0.shape or
                    rest32.shape != rest0.shape or cur32.shape != rest0.shape or
                    faces.ndim != 2 or faces.shape[1:] != (3,) or len(faces) == 0):
                raise FixtureRefusal(FixtureReason.SHAPE, "position/face shapes are invalid")
            nv, nf = len(rest0), len(faces)
            if np.any(faces < 0) or np.any(faces >= nv):
                raise FixtureRefusal(FixtureReason.GEOMETRY, "face index out of range")
            expected_rest, expected_current, expected_faces = canonical_geometries()[fixture_id]
            if (not np.array_equal(rest0, expected_rest) or
                    not np.array_equal(cur0, expected_current) or
                    not np.array_equal(faces, expected_faces)):
                raise FixtureRefusal(FixtureReason.GEOMETRY,
                                     "original geometry differs from its canonical recipe")
            B = _exact(z, "rest_B_upload_f32", np.float32, (nf, 2, 2))
            areas = _exact(z, "rest_areas0_upload_f32", np.float32, (nf,))
            offsets = _exact(z, "csr_offsets_upload_u32", np.uint32, (nv + 1,), finite=False)
            corners = _exact(z, "csr_corners_upload_u32", np.uint32, (3 * nf,), finite=False)
            _validate_csr(faces, offsets, corners, nv)
            derived = build_rest_geometry(rest32, faces)
            if (not np.array_equal(B, derived.B.astype(np.float32)) or
                    not np.array_equal(areas, derived.areas0.astype(np.float32)) or
                    not np.array_equal(offsets, derived.csr_offsets.astype(np.uint32)) or
                    not np.array_equal(corners, derived.csr_corners.astype(np.uint32))):
                raise FixtureRefusal(FixtureReason.GEOMETRY, "stored upload B/area/CSR differ from geometry")
            original_material = _material(z, "original", np.float64)
            upload_material = _material(z, "upload", np.float32)
            original_reference = _reference(z, "original", nf, nv)
            upload_reference = _reference(z, "upload", nf, nv)
    except FixtureRefusal:
        raise
    except (OSError, ValueError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise FixtureRefusal(FixtureReason.SCHEMA, f"could not read packet: {exc}") from exc

    if (original_material.E3d_pa <= 0 or original_material.h_m <= 0 or
            original_material.E2_n_per_m != original_material.E3d_pa * original_material.h_m or
            not -1 < original_material.nu < 0.5):
        raise FixtureRefusal(FixtureReason.MATERIAL, "original E3d/h/E2/nu are inconsistent")
    expected_upload_E2 = float(np.float32(
        np.float64(np.float32(upload_material.E3d_pa)) *
        np.float64(np.float32(upload_material.h_m))
    ))
    if (upload_material.E3d_pa <= 0 or upload_material.h_m <= 0 or
            upload_material.E2_n_per_m != expected_upload_E2 or
            not -1 < upload_material.nu < 0.5):
        raise FixtureRefusal(FixtureReason.MATERIAL, "upload E3d/h/E2/nu recipe is inconsistent")
    if not (np.array_equal(rest32, rest0.astype(np.float32)) and
            np.array_equal(cur32, cur0.astype(np.float32))):
        raise FixtureRefusal(FixtureReason.GEOMETRY, "upload positions are not binary32 rounding of originals")
    return PhysicalPacket(
        path=path, packet_sha256=entry["sha256"], manifest_path=manifest_path,
        manifest_sha256=actual_manifest_hash, fixture_id=fixture_id,
        source=source, source_sha256=entry["source_sha256"], provenance=provenance,
        provenance_sha256=entry["provenance_sha256"], rest_original=rest0,
        current_original=cur0, rest_upload=rest32, current_upload=cur32, faces=faces,
        B_upload=B, areas_upload=areas, csr_offsets_upload=offsets,
        csr_corners_upload=corners, original_material=original_material,
        upload_material=upload_material, original_reference=original_reference,
        upload_reference=upload_reference,
    )


def _close(actual, expected, scale) -> bool:
    a, e, q = (np.asarray(x, dtype=np.float64) for x in (actual, expected, scale))
    if a.shape != e.shape or e.shape != q.shape:
        return False
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(e)) and
            np.all(np.isfinite(q)) and np.all(q >= 0)):
        return False
    bound = CPU_GAMMA * q
    return bool(np.all(np.where(q == 0, a == e, np.abs(a - e) <= bound)))


def _validate_packet_record(packet: PhysicalPacket) -> None:
    if (not packet.manifest_path.is_file() or
            sha256_file(packet.manifest_path) != packet.manifest_sha256):
        raise FixtureRefusal(FixtureReason.TRUST_ANCHOR,
                             "loaded packet's manifest no longer matches its trusted anchor")
    if not packet.path.is_file() or sha256_file(packet.path) != packet.packet_sha256:
        raise FixtureRefusal(FixtureReason.PACKET_HASH,
                             "loaded packet bytes changed after admission")
    for label, material in (("original", packet.original_material),
                            ("upload", packet.upload_material)):
        values = (material.E3d_pa, material.h_m, material.E2_n_per_m, material.nu)
        if any(isinstance(value, (bool, np.bool_)) or not math.isfinite(float(value))
               for value in values):
            raise FixtureRefusal(FixtureReason.MATERIAL,
                                 f"in-memory {label} material is nonnumeric/nonfinite")
        if material.E3d_pa <= 0 or material.h_m <= 0 or not -1 < material.nu < 0.5:
            raise FixtureRefusal(FixtureReason.MATERIAL,
                                 f"in-memory {label} material is outside its domain")
    if packet.original_material.E2_n_per_m != (
            packet.original_material.E3d_pa * packet.original_material.h_m):
        raise FixtureRefusal(FixtureReason.MATERIAL,
                             "in-memory original E2 != E3d*h")
    expected_upload_E2 = float(np.float32(
        np.float64(np.float32(packet.upload_material.E3d_pa)) *
        np.float64(np.float32(packet.upload_material.h_m))
    ))
    if packet.upload_material.E2_n_per_m != expected_upload_E2:
        raise FixtureRefusal(FixtureReason.MATERIAL,
                             "in-memory upload E2 violates its binary32 recipe")
    derived = build_rest_geometry(packet.rest_upload, packet.faces)
    if (not np.array_equal(packet.B_upload, derived.B.astype(np.float32)) or
            not np.array_equal(packet.areas_upload, derived.areas0.astype(np.float32))):
        raise FixtureRefusal(FixtureReason.GEOMETRY, "in-memory stored B/area changed")
    _validate_csr(packet.faces, packet.csr_offsets_upload, packet.csr_corners_upload,
                  len(packet.rest_upload))
    if (not np.array_equal(packet.csr_offsets_upload, derived.csr_offsets.astype(np.uint32)) or
            not np.array_equal(packet.csr_corners_upload, derived.csr_corners.astype(np.uint32))):
        raise FixtureRefusal(FixtureReason.CSR, "in-memory stored CSR changed")
    if sha256_bytes(canonical_json(packet.provenance)) != packet.provenance_sha256:
        raise FixtureRefusal(FixtureReason.PROVENANCE, "in-memory provenance changed")
    if sha256_bytes(canonical_json(packet.source)) != packet.source_sha256:
        raise FixtureRefusal(FixtureReason.SOURCE, "in-memory source changed")


def validate_evaluation(packet: PhysicalPacket, mode: str, result) -> None:
    reference = packet.original_reference if mode == "original" else packet.upload_reference
    try:
        ev = result.evaluation
        checks = {
            "F": (ev.per_face.F, reference.F, reference.scale_F),
            "Wbar": (ev.per_face.Wbar, reference.Wbar, reference.scale_Wbar),
            "wvol": (ev.per_face.w_vol, reference.wvol, reference.scale_wvol),
            "corner": (ev.corner_forces, reference.corner, reference.scale_corner),
            "vertex": (ev.vertex_forces, reference.vertex, reference.scale_vertex),
            "energy": (ev.energy, reference.energy, reference.scale_energy),
        }
    except (AttributeError, TypeError) as exc:
        raise FixtureRefusal(FixtureReason.REFERENCE, "evaluator result is malformed") from exc
    for name, values in checks.items():
        try:
            matches = _close(*values)
        except (TypeError, ValueError, OverflowError) as exc:
            raise FixtureRefusal(FixtureReason.REFERENCE,
                                 f"{mode} {name} is malformed") from exc
        if not matches:
            raise FixtureRefusal(FixtureReason.REFERENCE, f"{mode} {name} exceeds CPU reference bound")
    if not (np.any(reference.Wbar != 0) and np.any(reference.wvol != 0) and
            np.any(reference.F != 0) and reference.energy != 0 and
            np.any(reference.vertex != 0)):
        raise FixtureRefusal(FixtureReason.REFERENCE, f"{mode} required nonzero oracle is absent")
    try:
        declaration_id = result.material.provenance.declaration_id
    except (AttributeError, TypeError) as exc:
        raise FixtureRefusal(FixtureReason.PROVENANCE,
                             "evaluation omitted structured provenance") from exc
    if declaration_id != packet.provenance["declaration_id"]:
        raise FixtureRefusal(FixtureReason.PROVENANCE, "evaluation dropped packet provenance")


def _evaluate_physical(rest, material, positions):
    return evaluate_physical_v1(rest, material, positions)


def evaluate_packet(packet: PhysicalPacket, mode: str = "upload"):
    if mode not in ("original", "upload"):
        raise FixtureRefusal(FixtureReason.SCHEMA, f"unknown evaluation mode {mode!r}")
    _validate_packet_record(packet)
    provenance = SyntheticCoefficientProvenance(
        declaration_id=packet.provenance["declaration_id"],
        purpose=packet.provenance["purpose"],
    )
    if mode == "original":
        material = packet.original_material
        derived = build_rest_geometry(packet.rest_original, packet.faces)
        _, _, exact_B, exact_areas, exact_offsets, exact_corners = _fraction_geometry(
            packet.rest_original, packet.current_original, packet.faces
        )
        rest = replace(
            derived,
            B=np.asarray(exact_B, dtype=np.float64),
            areas0=np.asarray(exact_areas, dtype=np.float64),
            csr_offsets=np.asarray(exact_offsets, dtype=np.int64),
            csr_corners=np.asarray(exact_corners, dtype=np.int64),
        )
        admitted = admit_volumetric_v1(material.E3d_pa, material.h_m, material.nu,
                                       provenance=provenance)
        positions = packet.current_original
    else:
        material = packet.upload_material
        derived = build_rest_geometry(packet.rest_upload, packet.faces)
        rest = replace(
            derived,
            B=packet.B_upload.astype(np.float64),
            areas0=packet.areas_upload.astype(np.float64),
            csr_offsets=packet.csr_offsets_upload.astype(np.int64),
            csr_corners=packet.csr_corners_upload.astype(np.int64),
        )
        admitted = admit_surface_v1(material.E2_n_per_m, material.h_m, material.nu,
                                    provenance=provenance)
        positions = packet.current_upload.astype(np.float64)
    result = _evaluate_physical(rest, admitted, positions)
    validate_evaluation(packet, mode, result)
    return result


def verify_manifest(manifest_path: str | Path, trusted_manifest_sha256: str) -> dict:
    manifest_path = Path(manifest_path).resolve()
    if not manifest_path.is_file():
        raise FixtureRefusal(FixtureReason.MISSING, f"missing manifest {manifest_path}")
    if sha256_file(manifest_path) != trusted_manifest_sha256.lower():
        raise FixtureRefusal(FixtureReason.TRUST_ANCHOR,
                             "manifest SHA-256 differs from trusted anchor")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verified = []
    for fixture_id in sorted(manifest.get("fixtures", {})):
        packet = load_packet(manifest_path, trusted_manifest_sha256, fixture_id)
        for mode in ("original", "upload"):
            evaluate_packet(packet, mode)
        verified.append(fixture_id)
    if not verified:
        raise FixtureRefusal(FixtureReason.MANIFEST, "manifest contains no fixtures")
    return {
        "packet_version": PACKET_VERSION,
        "manifest_sha256": trusted_manifest_sha256.lower(),
        "fixtures": verified,
        "cpu_reference": "passed",
        "gpu_acceptance": "OPEN",
    }


def _write_json_unique(path: Path, value: dict) -> None:
    if path.exists():
        raise FixtureRefusal(FixtureReason.OUTPUT_EXISTS, f"refusing existing output {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise FixtureRefusal(FixtureReason.OUTPUT_EXISTS, f"refusing existing output {path}") from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("generate")
    make.add_argument("--output", type=Path, required=True)
    make.add_argument("--legacy-run", type=Path, required=True)
    make.add_argument("--legacy-manifest-sha256", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--manifest-sha256", required=True)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            path = generate(args.output, args.legacy_run, args.legacy_manifest_sha256)
            print(json.dumps({"ok": True, "output": str(path),
                              "manifest_sha256": sha256_file(path / "manifest.json")}, sort_keys=True))
        else:
            report = verify_manifest(args.manifest, args.manifest_sha256)
            _write_json_unique(args.output.resolve(), report)
            print(json.dumps({"ok": True, "output": str(args.output.resolve())}, sort_keys=True))
        return 0
    except Exception as exc:
        reason = exc.reason if isinstance(exc, FixtureRefusal) else FixtureReason.CLI
        print(json.dumps({"ok": False, "reason": reason, "error": str(exc)}, sort_keys=True),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

