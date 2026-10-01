"""The matter-kernel definition format (KERNEL_SPEC.md 2), parser + validator.

A body is data: materials (sourced constants), membranes (triangle sets),
bonds (connections that are themselves materials). Meshes are clothing, not
substrate. Every material constant must cite a source; mass derives from
geometry x density and is cross-checked, never guessed.

Validation refuses loudly (named errors, no silent defaults) per the fleet's
RULE 0 culture: a definition that passes this module is a body the kernel
may load; anything else is refused with the exact reason.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

TRIANGLE_BYTES = 36  # 3 vertices x 3 floats x 4 bytes
MASS_TOLERANCE = 0.05  # 5% between stated and derived mass


class DefinitionError(Exception):
    """Named refusal: definitions never pass on silence."""


def _require(cond: bool, reason: str) -> None:
    if not cond:
        raise DefinitionError(reason)


def validate_material(name: str, mat: dict) -> None:
    _require(isinstance(mat, dict), f"material {name}: not an object")
    for key, minimum in (("density", 0.0), ("young_modulus", 0.0),
                         ("yield", 0.0), ("hardness_vickers", 0.0)):
        _require(key in mat, f"material {name}: missing {key}")
        v = mat[key]
        _require(isinstance(v, (int, float)) and v > minimum,
                 f"material {name}: {key} must be a number > {minimum}")
    src = mat.get("source", "")
    _require(isinstance(src, str) and src.strip(),
             f"material {name}: constants must cite a source (spec law 4)")


def validate_membrane(mid: str, mem: dict, materials: dict,
                      base_dir: Path) -> tuple[bytes, float]:
    """Validate one membrane; return (triangle bytes, DERIVED mass)."""
    _require(isinstance(mem, dict), f"membrane {mid}: not an object")
    _require(mem.get("material") in materials,
             f"membrane {mid}: unknown material {mem.get('material')!r}")
    ref = mem.get("triangles")
    _require(isinstance(ref, str) and ref.strip(),
             f"membrane {mid}: triangles must be a binary ref (path)")
    tri_path = (base_dir / ref).resolve()
    _require(tri_path.is_file(), f"membrane {mid}: triangle file {ref!r} not found")
    tri = tri_path.read_bytes()
    _require(len(tri) % TRIANGLE_BYTES == 0 and len(tri) > 0,
             f"membrane {mid}: triangle blob length {len(tri)} not a positive "
             f"multiple of {TRIANGLE_BYTES}")
    thickness = mem.get("thickness")
    _require(isinstance(thickness, (int, float)) and thickness > 0,
             f"membrane {mid}: thickness must be a positive number")
    # triangle area by cross product, summed (engine units)
    area = 0.0
    for off in range(0, len(tri), TRIANGLE_BYTES):
        ax, ay, az, bx, by, bz, cx, cy, cz = struct.unpack_from("<9f", tri, off)
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        area += 0.5 * (nx * nx + ny * ny + nz * nz) ** 0.5
    density = materials[mem["material"]]["density"]
    return tri, area * thickness * density


def validate_bond(bid: str, bond: dict, materials: dict,
                  membrane_ids: set) -> None:
    _require(isinstance(bond, dict), f"bond {bid}: not an object")
    _require(bond.get("material") in materials,
             f"bond {bid}: unknown material {bond.get('material')!r}")
    members = bond.get("members")
    _require(isinstance(members, list) and len(members) == 2,
             f"bond {bid}: needs exactly two members")
    for m in members:
        _require(m in membrane_ids, f"bond {bid}: member {m!r} is not a membrane")
    cure = bond.get("cure_strength")
    _require(isinstance(cure, (int, float)) and cure > 0,
             f"bond {bid}: cure_strength must be a positive number")


def parse_body(path: str | Path) -> dict:
    """Parse + fully validate a body definition file. Returns the body dict
    with each membrane's derived mass attached; refuses loudly otherwise."""
    raw = Path(path).read_text(encoding="utf-8")
    body = json.loads(raw)
    base_dir = Path(path).resolve().parent

    _require(isinstance(body, dict), "body: not an object")
    mats = body.get("materials")
    _require(isinstance(mats, dict) and mats, "body: materials required")
    for name, mat in mats.items():
        validate_material(name, mat)

    mems = body.get("membranes")
    _require(isinstance(mems, list) and mems, "body: membranes required")
    seen: set[str] = set()
    for mem in mems:
        mid = mem.get("id") if isinstance(mem, dict) else None
        _require(isinstance(mid, str) and mid, "membrane: id required")
        _require(mid not in seen, f"membrane {mid}: duplicate id")
        seen.add(mid)
        tri_bytes, derived = validate_membrane(mid, mem, mats, base_dir)
        mem["triangles_bytes"] = len(tri_bytes)
        stated = mem.get("mass")
        if stated is not None:
            _require(abs(stated - derived) / derived <= MASS_TOLERANCE,
                     f"membrane {mid}: stated mass {stated} vs derived "
                     f"{derived:.6g} beyond {MASS_TOLERANCE:.0%} tolerance")
        mem["mass_derived"] = round(derived, 9)

    bonds = body.get("bonds", [])
    _require(isinstance(bonds, list), "body: bonds must be a list")
    bseen: set[str] = set()
    for bond in bonds:
        bid = bond.get("id") if isinstance(bond, dict) else None
        _require(isinstance(bid, str) and bid, "bond: id required")
        _require(bid not in bseen, f"bond {bid}: duplicate id")
        bseen.add(bid)
        validate_bond(bid, bond, mats, seen)

    return body
