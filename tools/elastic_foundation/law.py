"""law.py -- the elastic triangle: STVK membrane energy, analytic corner and vertex forces.

Implements DERIVATION.md. Per face:
    d1, d2 = current edge vectors (3,)
    F   = [d1 d2] @ B                          (3x2) in-plane deformation gradient
    C   = F^T F                                (2x2) right Cauchy-Green
    E   = (C - I)/2                            (2x2) Green-Lagrange
    Wbar= 0.5 lambda_bar tr(E)^2 + mu_bar tr(EE)   [per reference area]
    S   = lambda_bar tr(E) I + 2 mu_bar E      (2x2) PK2
    P   = F @ S                                (3x2) PK1 (nominal)
    dWbar/dd_j = P (B^T e_j)  (columns of P B^T)

Corner forces (force ON vertex = -dU/dy), U = A0 Wbar:
    f0 = +A0 (u1 + u2)      u_j = column j of P B^T
    f1 = -A0 u1
    f2 = -A0 u2
    (sums to zero per face; conservative, rotation-objective through C.)

Test-only mutation knobs exist ONLY for the negative-control battery (PREREGISTRATION.md
"mutations"). The production path always runs with defaults; a mutation must fail an independent
check, never a source assertion.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .geometry import (InvalidGeometry, Reason as GeoReason, as_positions,
                       build_vertex_corner_adjacency, DEGENERACY_FLOOR_FACTOR, EPS64)
from .materials import ElasticMaterial2D, validate_material


@dataclass(frozen=True)
class FaceState:
    F: np.ndarray      # (nF,3,2) current in-plane deformation gradient
    C: np.ndarray      # (nF,2,2)
    E: np.ndarray      # (nF,2,2)
    S: np.ndarray      # (nF,2,2) PK2 per reference area
    P: np.ndarray      # (nF,3,2) PK1 per reference area
    Wbar: np.ndarray   # (nF,) energy per reference area
    w_vol: np.ndarray  # (nF,) energy per reference volume (diagnostic)
    detF: np.ndarray   # (nF,) signed current/rest area ratio
    area_cur: np.ndarray
    inverted: np.ndarray  # detF < 0 flags
    normals_cur: np.ndarray  # (nF,3) current unsigned unit normals


@dataclass(frozen=True)
class Evaluation:
    energy: float
    per_face: FaceState
    corner_forces: np.ndarray   # (nF,3,3) per-face-corner forces (force ON the corner vertex)
    vertex_forces: np.ndarray   # (nV,3) gathered via CSR
    max_abs_vertex_force: float
    energy_scale: float         # (lambda_bar+mu_bar) * total rest area, for tolerance budgets


class InvalidDeformation(ValueError):
    """Named refusal for an invalid CURRENT pose or overflowing arithmetic."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


class DeformationReason:
    BAD_SHAPE = "bad_shape"
    NONFINITE_POSITIONS = "nonfinite_positions"
    WRONG_VERTEX_COUNT = "wrong_vertex_count"
    COLLAPSED_TRIANGLE = "collapsed_triangle"
    NEAR_DEGENERATE = "near_degenerate_triangle"
    NONFINITE_RESULT = "nonfinite_result"


def evaluate_elastic(rest, material, positions, _mutations=None) -> Evaluation:
    """Evaluate the STVK membrane energy + forces. Returns Evaluation or raises a named refusal.

    rest : RestGeometry (frozen, built by geometry.build_rest_geometry)
    material : ElasticMaterial2D (frozen, admissible)
    positions : (nV,3) float64 current positions (may differ from rest arbitrarily)
    """
    validate_material(material)
    mut = dict(_mutations) if _mutations else {}
    pos = as_positions(positions)
    tri = rest.faces
    if pos.shape[0] != rest.n_vertices:
        raise InvalidDeformation(DeformationReason.WRONG_VERTEX_COUNT,
                                 f"current has {pos.shape[0]} vertices, rest has "
                                 f"{rest.n_vertices}")

    lam = material.lambda_bar
    mu = material.mu_bar

    d1 = pos[tri[:, 1]] - pos[tri[:, 0]]
    d2 = pos[tri[:, 2]] - pos[tri[:, 0]]
    cross = np.cross(d1, d2)
    cross_mag = np.linalg.norm(cross, axis=1)
    e1len = np.linalg.norm(d1, axis=1)
    e2len = np.linalg.norm(d2, axis=1)
    e3len = np.linalg.norm(pos[tri[:, 2]] - pos[tri[:, 1]], axis=1)
    max_edge = np.maximum(e1len, np.maximum(e2len, e3len))
    if not (np.all(np.isfinite(cross_mag)) and np.all(np.isfinite(max_edge))):
        raise InvalidDeformation(DeformationReason.NONFINITE_RESULT,
                                 "current edge/cross magnitudes overflow float64 -- refusing")
    floor = DEGENERACY_FLOOR_FACTOR * EPS64 * max_edge * max_edge
    if np.any(cross_mag <= floor):
        i = int(np.argmax(cross_mag <= floor))
        if cross_mag[i] <= 0.0:
            raise InvalidDeformation(DeformationReason.COLLAPSED_TRIANGLE,
                                     f"face {i} collapsed: |cross| = {cross_mag[i]:.3e} <= floor")
        raise InvalidDeformation(
            DeformationReason.NEAR_DEGENERATE,
            f"face {i} near-degenerate: |cross| = {cross_mag[i]:.3e} <= floor {floor[i]:.3e}")
    area_cur = 0.5 * cross_mag
    normals_cur = cross / cross_mag[:, None]
    # SIGNED oriented area: detF<0 iff the current triangle is inverted (normal flipped
    # vs the rest face). Folds (same-material, flipped orientation) are resolvable: the STVK
    # functional is still finite, so they are reported with the inverted flag, not refused.
    signed_area = 0.5 * np.sum(cross * rest.n, axis=1)
    detF = signed_area / rest.areas0

    N = np.stack([d1, d2], axis=2)              # (nF,3,2)
    F = N @ rest.B                              # (nF,3,2)
    if mut.get("eulerian_frame", False):
        FFt = F @ F.transpose(0, 2, 1)          # (nF,3,3) spatial frame -- NOT objective
        C = FFt[:, :2, :2]
    else:
        C = np.einsum("fji,fjk->fik", F, F)     # F^T F  (objective)

    if mut.get("linear_strain", False):
        Fin = F[:, :2, :]                       # in-plane 2x2 (planar fixtures)
        E = 0.5 * (Fin + Fin.transpose(0, 2, 1)) - np.eye(2)
    else:
        E = 0.5 * (C - np.eye(2))

    trE = E[:, 0, 0] + E[:, 1, 1]
    trE2 = E[:, 0, 0] ** 2 + 2.0 * E[:, 0, 1] ** 2 + E[:, 1, 1] ** 2
    Wbar = 0.5 * lam * trE ** 2 + mu * trE2

    S = np.empty_like(E)
    S[:, 0, 0] = lam * trE + 2.0 * mu * E[:, 0, 0]
    S[:, 1, 1] = lam * trE + 2.0 * mu * E[:, 1, 1]
    S[:, 0, 1] = 2.0 * mu * E[:, 0, 1]
    S[:, 1, 0] = S[:, 0, 1]
    P = F @ S                                   # (nF,3,2) PK1 per reference area

    PBt = P @ rest.B.transpose(0, 2, 1)         # (nF,3,2); columns u1,u2 = dWbar/dd_j
    u1 = PBt[:, :, 0]
    u2 = PBt[:, :, 1]

    # U = A0 Wbar; force on corner vertex = -dU/dy
    A0 = rest.areas0
    force_v0 = A0[:, None] * (u1 + u2)
    force_v1 = A0[:, None] * (-u1)
    force_v2 = A0[:, None] * (-u2)
    corner_forces = np.stack([force_v0, force_v1, force_v2], axis=1)   # (nF,3,3)

    if mut.get("current_area_source", False):
        # Bug: energy/forces scaled by CURRENT area instead of rest reference area.
        Wbar = Wbar * (area_cur / A0)
        corner_forces = corner_forces * (area_cur / A0)[:, None, None]

    if mut.get("sign", False):
        corner_forces = -corner_forces
    if mut.get("swap_corners", False):
        corner_forces = corner_forces[:, [0, 2, 1], :]

    # Deterministic CSR gather of corner forces into vertex forces.
    flat = corner_forces.reshape(-1, 3)                    # face-major 3f+k
    if mut.get("gather_drop", False):
        keep = np.ones(flat.shape[0], dtype=bool)
        keep[::2] = False
        red_flat = flat[keep]
        # re-segment: count per vertex over kept corners only
        counts = np.bincount(rest.csr_corners[keep], minlength=rest.n_vertices)
        if int(counts.sum()) != red_flat.shape[0]:
            raise InvalidDeformation(DeformationReason.NONFINITE_RESULT,
                                     "mutation gather accounting broken")
        offs = np.zeros(rest.n_vertices + 1, dtype=np.int64)
        np.cumsum(counts, out=offs[1:])
        vertex_forces = np.zeros((rest.n_vertices, 3))
        if offs[-1] == red_flat.shape[0] and np.all(np.diff(offs) > 0):
            np.add.reduceat(red_flat, offs[:-1], axis=0, out=vertex_forces)
        else:
            corner_of = np.repeat(np.arange(rest.n_vertices), np.diff(offs))
            np.add.at(vertex_forces, corner_of, red_flat)
    else:
        offsets = rest.csr_offsets
        corner_idx = rest.csr_corners
        vertex_forces = np.zeros_like(pos)
        if offsets[-1] == flat.shape[0] and np.all(np.diff(offsets) > 0):
            np.add.reduceat(flat[corner_idx], offsets[:-1], axis=0, out=vertex_forces)
        else:
            corner_of = np.repeat(np.arange(rest.n_vertices), np.diff(offsets))
            np.add.at(vertex_forces, corner_of, flat[corner_idx])

    energy = float(np.sum(Wbar * A0))
    w_vol = Wbar / material.h
    state = FaceState(F=F, C=C, E=E, S=S, P=P, Wbar=Wbar, w_vol=w_vol,
                      detF=detF, area_cur=area_cur, inverted=detF < 0.0,
                      normals_cur=normals_cur)

    # A valid Evaluation is entirely finite -- finite input, finite output, or refusal.
    if not (math.isfinite(energy)
            and np.all(np.isfinite(Wbar)) and np.all(np.isfinite(corner_forces))
            and np.all(np.isfinite(vertex_forces)) and np.all(np.isfinite(F))
            and np.all(np.isfinite(np.max(np.abs(vertex_forces), axis=1)))):
        raise InvalidDeformation(DeformationReason.NONFINITE_RESULT,
                                 "evaluation produced non-finite energy/forces from finite "
                                 "input -- refusing")

    scale = float((lam + mu) * np.sum(A0))
    return Evaluation(energy=energy, per_face=state, corner_forces=corner_forces,
                      vertex_forces=vertex_forces,
                      max_abs_vertex_force=float(np.max(np.abs(vertex_forces))),
                      energy_scale=scale)