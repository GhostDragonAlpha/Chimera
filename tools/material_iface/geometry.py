"""geometry.py -- Geometry: surface / volume / particle representation binding.

A Geometry binds owned physical points (with stable IDs and masses) to a
law-specific rest reference. The record type distinguishes the three
representations; an actual binding exists only where an existing repo law
supplies one (surface: the STVK rest geometry). Volume binding is refused by
name rather than inventing data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math


SURFACE = "surface"
VOLUME = "volume"
PARTICLE = "particle"


class GeometryRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class GeometryReason:
    VOLUME_UNSUPPORTED = "volume_binding_unsupported"
    BAD_POINTS = "bad_point_cloud"
    BAD_FACES = "bad_face_list"
    BAD_MASSES = "bad_masses"
    REPRESENTATION_MISMATCH = "representation_mismatch"


def _check_positions(positions, what) -> tuple[tuple[float, float, float], ...]:
    out = []
    for i, p in enumerate(positions):
        if len(p) != 3:
            raise GeometryRefusal(GeometryReason.BAD_POINTS,
                                  f"{what}[{i}] must be an (x, y, z) triple")
        x, y, z = (float(c) for c in p)
        if not all(math.isfinite(c) for c in (x, y, z)):
            raise GeometryRefusal(GeometryReason.BAD_POINTS,
                                  f"{what}[{i}] non-finite")
        out.append((x, y, z))
    if not out:
        raise GeometryRefusal(GeometryReason.BAD_POINTS, f"{what}: empty")
    return tuple(out)


def _check_masses(masses, n: int) -> tuple[float, ...]:
    if masses is None or len(masses) != n:
        raise GeometryRefusal(GeometryReason.BAD_MASSES,
                              f"masses must supply exactly {n} positive values")
    out = []
    for i, m in enumerate(masses):
        m = float(m)
        if not math.isfinite(m) or m <= 0.0:
            raise GeometryRefusal(GeometryReason.BAD_MASSES,
                                  f"mass[{i}] must be finite and > 0; got {m!r}")
        out.append(m)
    return tuple(out)


@dataclass(frozen=True)
class Geometry:
    """Owned point set + law-specific rest reference. No material values live here."""
    geometry_id: str
    representation: str            # SURFACE | VOLUME | PARTICLE
    point_ids: tuple[str, ...]     # stable point keys, e.g. ("v0", ...)
    masses: tuple[float, ...]      # kg per point (integrator inertia owner input)
    binding: dict = field(default_factory=dict)  # opaque to the interface

    @property
    def n_points(self) -> int:
        return len(self.point_ids)

    @classmethod
    def surface(cls, geometry_id: str, positions, faces,
                masses) -> "Geometry":
        pts = _check_positions(positions, "positions")
        n = len(pts)
        clean_faces = []
        for i, f in enumerate(faces):
            if len(f) != 3:
                raise GeometryRefusal(GeometryReason.BAD_FACES,
                                      f"faces[{i}] must be a triangle")
            idx = tuple(int(k) for k in f)
            if any(k < 0 or k >= n for k in idx):
                raise GeometryRefusal(GeometryReason.BAD_FACES,
                                      f"faces[{i}] indexes outside 0..{n - 1}")
            clean_faces.append(idx)
        if not clean_faces:
            raise GeometryRefusal(GeometryReason.BAD_FACES, "faces: empty")
        ms = _check_masses(masses, n)
        return cls(geometry_id=geometry_id, representation=SURFACE,
                   point_ids=tuple(f"v{i}" for i in range(n)),
                   masses=ms,
                   binding={"rest_positions": pts, "faces": tuple(clean_faces)})

    @classmethod
    def particle(cls, geometry_id: str, positions, masses) -> "Geometry":
        pts = _check_positions(positions, "positions")
        ms = _check_masses(masses, len(pts))
        return cls(geometry_id=geometry_id, representation=PARTICLE,
                   point_ids=tuple(f"p{i}" for i in range(len(pts))),
                   masses=ms, binding={"rest_positions": pts})

    @classmethod
    def volume(cls, geometry_id: str) -> "Geometry":
        raise GeometryRefusal(
            GeometryReason.VOLUME_UNSUPPORTED,
            "the volume representation is a declared record type, but no "
            "existing repo law supplies a volumetric rest reference this lane "
            "may bind; refusing rather than inventing tet data")
