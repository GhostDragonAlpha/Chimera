"""Visible Monkey intake: the 167-structure STL set expressed AS MATTER.

Lane agent/visible-monkey-intake-20260921. Dataset (PENDING -- operator email
request, Chung et al. 2019 J Korean Med Sci 34:e70 + Kim et al. 2020
PMCID PMC7167398): adult-CONFIRMED 93-month female rhesus, segmented
167-structure STL set = skin + skeleton + merged-muscle membranes of ONE
specimen (three membrane layers arriving together as triangles). This tool
PRESTAGES the intake: everything is parameterized on a directory spec
(dir_spec.template.json) and proven NOW against synthetic closed meshes with
known analytic volumes/masses -- the real formats are never guessed; the day
the data lands, intake is filling in a spec, not writing code.

Discipline carried from matter_skeleton_import.py (branch
agent/matter-skeleton-import-20260920), parameterized further: per-structure
compartments, provenance sha256 receipts, stage=adult-CONFIRMED law,
divergence-theorem volume, t=V/A mass closure, byte determinism, the verify
battery, and NAMED refusals (never tracebacks, never silence):

    V_k = |sum_faces (1/6) * v_a . (v_b x v_c)|      (divergence theorem)
    A_k = sum_faces 0.5*|(v_b-v_a) x (v_c-v_a)|
    t_k = V_k / A_k   (equivalent shell thickness; conserves V_k)
    m_k = V_k * rho   (rho cited per tissue system; ICRP 89/23, Yamada 1970,
                       Mendez & Keys 1960, Cowin/Currey)

Stage law: adult is admitted ONLY with age evidence from the collection
record (age_months + age_source -- the real specimen: 93 months, Chung et al.
2019). One creature, one life stage; mixing is refused. Scale 1.0, identity
transform, no allometric code path (the H2 3.79-8.8x stretch factors remain
the named negative example).

Closed-mesh law: a compartment is admissible only if every undirected edge is
shared by exactly 2 triangles (the condition under which the divergence-
theorem volume is the enclosed volume). Euler characteristic is reported, not
pinned (real bones have genus).

Rule 0 receipt: tools/science_funnel/validation/visible_monkey_intake_20260921/
receipt.json (statement / prediction / falsifiers banked BEFORE this tool
existed). Runbook: RUNBOOK.md in the same directory.

Usage (repo root):
    python -B tools/science_funnel/visible_monkey_import.py build <dir_spec.json>
    python -B tools/science_funnel/visible_monkey_import.py verify <dir_spec.json>

build  validates the spec + data, regenerates the definition byte-exactly
       (in-run temp probe), validates it through the kernel's own parser
       (tools.matter_kernel.definition), re-reads it and checks every
       falsifier, then writes the derivation book and verification records.
verify reads ONLY committed artifacts: re-runs every falsifier check and
       demands byte equality with a fresh regeneration. Refuses loudly on any
       mismatch. The lead runs this in a TRUE fresh clone (worktree==blob
       pre-checked per git hash-object).
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import struct
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.matter_kernel import definition as kdef  # noqa: E402
from tools.science_funnel.common import Refusal, require  # noqa: E402

SPEC_SCHEMA = "chimera.visible_monkey.dir_spec.v1"
RECORD_SCHEMA = "chimera.visible_monkey.collection_record.v1"
BODY_SCHEMA = "chimera.matter_body.v1"

# Sourced constants (kernel law 4: no constant without a citation).
# Densities kg/mm^3; the kernel mass law (area x thickness x density) is
# unit-agnostic as long as the three agree.
RHO_BONE = 1.9e-6      # 1900 kg/m^3 cortical bone (ICRP 89; Cowin/Currey)
RHO_MUSCLE = 1.06e-6   # 1060 kg/m^3 skeletal muscle (ICRP 89; Mendez & Keys 1960)
RHO_SKIN = 1.109e-6    # 1109 kg/m^3 skin (ICRP 89)
RHO_CART = 1.06e-6     # 1060 kg/m^3 cartilage (Yamada 1970)
RHO_SOFT = 1.05e-6     # 1050 kg/m^3 organ soft tissue (ICRP 23 Reference Man)

CURE_CARTILAGE_PA = 13.0e6  # cartilage tensile failure (Yamada 1970)

MATERIALS = {
    "mat.bone_cortical": {
        "density": RHO_BONE,
        "young_modulus": 17.0e9,
        "yield": 100.0e6,
        "hardness_vickers": 40.0,
        "source": "COWIN 'Bone Mechanics Handbook'; CURREY 'Bones: Structure "
                  "and Mechanics'; ICRP Publication 89 (2002): cortical wet "
                  "density 1800-2100 kg/m^3 (1900 used); E ~15-20 GPa (17 "
                  "used); UTS ~80-150 MPa (100 used, conservative); Vickers "
                  "~30-50 HV (40 used)",
        "stage_note": "adult-confirmed specimen (93-month rhesus, Chung et al. "
                      "2019): the adult cortical range applies directly, no "
                      "infant upper-anchor caveat needed",
    },
    "mat.skeletal_muscle": {
        "density": RHO_MUSCLE,
        "young_modulus": 0.05e6,
        "yield": 0.14e6,
        "hardness_vickers": 0.05,
        "source": "ICRP Publication 89 (2002): skeletal muscle density 1060 "
                  "kg/m^3; MENDEZ & KEYS 1960 (Metabolism 9:184-188, density "
                  "and composition of mammalian muscle). Mechanics PROVISIONAL "
                  "with cited bands: passive E ~0.01-0.1 MPa (0.05 used); UTS "
                  "~0.1-0.2 MPa (0.14 used, Yamada 1970); no direct Vickers "
                  "value in literature (0.05 used -- kernel-required field, "
                  "soft-tissue order). Mass law uses DENSITY only; these "
                  "fields gate later physics lanes, not this intake. Muscles "
                  "arrive as ONE merged structure (Kim et al. 2020).",
    },
    "mat.skin": {
        "density": RHO_SKIN,
        "young_modulus": 15.0e6,
        "yield": 10.0e6,
        "hardness_vickers": 0.3,
        "source": "ICRP Publication 89 (2002): skin density 1109 kg/m^3. "
                  "Mechanics PROVISIONAL with cited bands: E ~15-40 MPa (15 "
                  "used); UTS ~7-20 MPa (10 used, Yamada 1970 'Strength of "
                  "Biological Materials'); HV 0.3 PROVISIONAL "
                  "(kernel-required field). Mass law uses DENSITY only.",
    },
    "mat.cartilage": {
        "density": RHO_CART,
        "young_modulus": 10.0e6,
        "yield": 13.0e6,
        "hardness_vickers": 0.3,
        "source": "YAMADA 1970 'Strength of Biological Materials' (Williams & "
                  "Wilkins): cartilage tensile strength ~13 MPa, Young's "
                  "modulus 7-25 MPa (10 used), density ~1.06 g/cm^3; the "
                  "articular-system material and the bond material at "
                  "measured touching edges",
    },
    "mat.soft_tissue": {
        "density": RHO_SOFT,
        "young_modulus": 1.0e6,
        "yield": 1.0e6,
        "hardness_vickers": 0.05,
        "source": "ICRP Publication 23 (1975) Reference Man soft-tissue "
                  "convention: 1050 kg/m^3; ICRP 89 solid-organ table spans "
                  "~1020-1070 kg/m^3, so ONE material for all organ systems "
                  "carries a NAMED +/-5% organ-to-organ spread (never tuned "
                  "-- itemized per structure in the derivation book). "
                  "Mechanics PROVISIONAL (kernel-required fields).",
    },
}

# Whole-animal biological bands (REAL data; collection-record body mass).
WHOLE_BODY_BAND = (0.6, 1.3)       # segmented total vs body mass
SKELETON_FRACTION_BAND = (0.08, 0.15)  # mammalian skeleton fraction of body
MUSCLE_FRACTION_BAND = (0.25, 0.50)    # mammalian muscle fraction of body

# Falsifier tolerances (pre-registered in receipt.json).
BBOX_TOL_MM = 1e-3
VOLUME_TOL_REL_DEFAULT = 0.05     # mesh vs optional stated volume
MASS_IDENTITY_TOL_REL = 1e-6      # stated mass vs V*rho
TOTAL_IDENTITY_TOL_REL = 1e-9     # book total vs sum of compartments

KNOWN_TOP_KEYS = {
    "schema", "dataset_name", "root", "stl", "labels", "collection_record",
    "adjacency", "units", "volume_tolerance_rel", "enforce_body_fraction_bands",
    "materials_by_system", "output_dir", "validation_dir",
}
KNOWN_SYSTEMS = {
    "skeletal", "articular", "muscular", "integumentary", "organ",
}
STAGE_FRACTION_SYSTEMS = {"skeletal", "muscular"}


# ------------------------------------------------------------------ helpers
def read_json(path: Path):
    require(path.is_file(), "spec_file_missing", str(path))
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise Refusal("spec_invalid_json", f"{path}: {e}") from None


def write_json(path: Path, payload) -> None:
    text = json.dumps(payload, indent=1, ensure_ascii=False,
                      allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ------------------------------------------------------------------- spec
def load_spec(spec_path: Path) -> dict:
    raw = read_json(spec_path)
    require(isinstance(raw, dict), "spec_schema", "spec is not an object")
    require(raw.get("schema") == SPEC_SCHEMA, "spec_schema",
            f"expected {SPEC_SCHEMA}, got {raw.get('schema')!r}")
    for key in raw:
        require(key in KNOWN_TOP_KEYS or key.startswith("_"),
                "spec_schema", f"unknown spec field {key!r}")
    for key in ("dataset_name", "root", "stl", "labels",
                "collection_record", "units", "materials_by_system",
                "output_dir", "validation_dir"):
        require(key in raw, "spec_missing_field", key)
    require(raw["units"] == "mm", "spec_schema",
            f"units must be 'mm' (the STL frame), got {raw['units']!r}")
    mats = raw["materials_by_system"]
    require(isinstance(mats, dict) and mats, "spec_missing_field",
            "materials_by_system")
    for system, mat in mats.items():
        if system.startswith("_"):
            continue
        require(system in KNOWN_SYSTEMS, "spec_schema",
                f"unknown tissue system {system!r}")
        require(mat in MATERIALS, "spec_schema",
                f"system {system!r} maps to unknown material {mat!r}")
    for key in ("dir", "glob", "expected_count"):
        require(key in raw["stl"], "spec_missing_field", f"stl.{key}")
    require(isinstance(raw["stl"]["expected_count"], int)
            and raw["stl"]["expected_count"] > 0, "spec_schema",
            "stl.expected_count must be a positive int")
    for key in ("file", "columns"):
        require(key in raw["labels"], "spec_missing_field", f"labels.{key}")
    for key in ("file",):
        require(key in raw["collection_record"], "spec_missing_field",
                "collection_record.file")
    tol = raw.get("volume_tolerance_rel", VOLUME_TOL_REL_DEFAULT)
    require(isinstance(tol, (int, float)) and 0 < tol < 1,
            "spec_schema", "volume_tolerance_rel must be in (0, 1)")
    raw["volume_tolerance_rel"] = float(tol)
    raw["_spec_dir"] = str(spec_path.resolve().parent)
    return raw


def load_collection_record(spec: dict) -> dict:
    path = Path(spec["root"]) / spec["collection_record"]["file"]
    rec = read_json(path)
    require(isinstance(rec, dict), "spec_schema",
            "collection_record is not an object")
    if rec.get("schema") is not None:
        require(rec["schema"] == RECORD_SCHEMA, "spec_schema",
                f"collection record schema {rec['schema']!r} != {RECORD_SCHEMA}")
    for key in ("species", "provenance"):
        require(isinstance(rec.get(key), str) and rec[key].strip(),
                "spec_missing_field", f"collection_record.{key}")
    raw_stage = rec.get("life_stage")
    require(isinstance(raw_stage, str) and raw_stage.strip(),
            "stage_unconfirmed",
            "life_stage missing/empty (unlabeled = unadmitted)")
    stage = raw_stage.strip().lower()
    require(stage in ("adult", "infant", "juvenile"), "stage_unknown",
            f"life_stage {raw_stage!r}")
    if stage == "adult":
        # THE STAGE LAW: adult must be adult-CONFIRMED from records.
        age = rec.get("age_months")
        src = rec.get("age_source")
        require(isinstance(age, (int, float)) and not isinstance(age, bool)
                and age > 0 and isinstance(src, str) and src.strip(),
                "stage_unconfirmed",
                "adult requires age_months > 0 AND age_source "
                "(collection/publication record); unlabeled = unadmitted")
    return rec


# ------------------------------------------------------------------ STL
def parse_stl(path: Path) -> list[tuple[tuple, tuple, tuple]]:
    """Parse an STL into a list of (a, b, c) float64 vertex triples.

    Binary detection is by SIZE (80-byte header + uint32 count + 50*count
    bytes); ASCII is the fallback. 'solid'-prefixed binary files are caught
    by the size law, never by the header."""
    raw = path.read_bytes()
    require(len(raw) >= 84, "mesh_unreadable", f"{path.name}: too short")
    n = struct.unpack_from("<I", raw, 80)[0]
    tris: list[tuple[tuple, tuple, tuple]] = []
    if len(raw) == 84 + 50 * n and n > 0:
        for i in range(n):
            off = 84 + 50 * i
            vals = struct.unpack_from("<12f", raw, off)
            tris.append((tuple(vals[3:6]), tuple(vals[6:9]),
                         tuple(vals[9:12])))
        require(len(tris) == n, "mesh_unreadable", path.name)
        return tris
    text = raw.decode("ascii", errors="strict")
    require("facet normal" in text and "vertex" in text, "mesh_unreadable",
            f"{path.name}: not a valid binary STL (size law) and not ASCII")
    verts: list[tuple] = []
    for line in text.splitlines():
        parts = line.split()
        if parts and parts[0] == "vertex":
            require(len(parts) == 4, "mesh_unreadable",
                    f"{path.name}: bad vertex line {line!r}")
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
    require(len(verts) % 3 == 0 and len(verts) > 0, "mesh_unreadable",
            f"{path.name}: vertex count {len(verts)} not a positive multiple "
            f"of 3")
    for i in range(0, len(verts), 3):
        tris.append((verts[i], verts[i + 1], verts[i + 2]))
    return tris


def to_f32(v: tuple) -> tuple:
    """Quantize one coordinate exactly as the triangle blob stores it."""
    return struct.unpack("<3f", struct.pack("<3f", *v))


def triangle_blob(f32_tris) -> bytes:
    """The kernel's triangle format: 36 bytes per triangle, 9 float32 LE."""
    return b"".join(struct.pack("<9f", *a, *b, *c) for a, b, c in f32_tris)


def mesh_volume_mm3(f32_tris) -> float:
    """V = |sum (1/6) v_a . (v_b x v_c)| -- divergence theorem, f64
    accumulation over the resident (float32) coordinates."""
    vol6 = 0.0
    for a, b, c in f32_tris:
        (xa, ya, za), (xb, yb, zb), (xc, yc, zc) = a, b, c
        vol6 += (xa * (yb * zc - zb * yc)
                 - ya * (xb * zc - zb * xc)
                 + za * (xb * yc - yb * xc))
    return abs(vol6) / 6.0


def mesh_area_mm2(f32_tris) -> float:
    """Area EXACTLY as the kernel validator accumulates it."""
    area = 0.0
    for a, b, c in f32_tris:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        area += 0.5 * (nx * nx + ny * ny + nz * nz) ** 0.5
    return area


def vertex_records(f32_tris) -> bytes:
    """Canonical vertex serialization: the sorted unique 12-byte float32
    records referenced by triangles. Order-independent by construction."""
    seen = {struct.pack("<3f", *v) for tri in f32_tris for v in tri}
    return b"".join(sorted(seen))


def mesh_topology(f32_tris):
    """(is_closed, open_edge_count, euler_characteristic, unique_vertex_count).

    Edges are keyed by vertex COORDINATE bytes (STL is unindexed; identical
    coordinates unify). Closed = every undirected edge shared by exactly 2
    triangles."""
    from collections import Counter
    edge_count: Counter = Counter()
    verts = {struct.pack("<3f", *tri[0]) for tri in f32_tris}
    verts |= {struct.pack("<3f", *tri[1]) for tri in f32_tris}
    verts |= {struct.pack("<3f", *tri[2]) for tri in f32_tris}
    for tri in f32_tris:
        keys = [struct.pack("<3f", *v) for v in tri]
        for i in range(3):
            u, w = sorted((keys[i], keys[(i + 1) % 3]))
            edge_count[(u, w)] += 1
    open_edges = sum(1 for c in edge_count.values() if c != 2)
    closed = all(c == 2 for c in edge_count.values())
    chi = len(verts) - len(edge_count) + len(f32_tris)
    return closed, open_edges, chi, len(verts)


def bbox(f32_tris):
    xs = [v[0] for tri in f32_tris for v in tri]
    ys = [v[1] for tri in f32_tris for v in tri]
    zs = [v[2] for tri in f32_tris for v in tri]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


# ----------------------------------------------------------------- labels
def load_labels(spec: dict, stage: str | None = None) -> dict:
    path = Path(spec["root"]) / spec["labels"]["file"]
    cols = spec["labels"]["columns"]
    stage_col = cols.get("life_stage", "")
    require(path.is_file(), "spec_file_missing", str(path))
    rows: dict[str, dict] = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        for key in ("id", "label", "system"):
            require(cols[key] in header, "spec_missing_field",
                    f"labels CSV missing column {cols[key]!r}")
        for row in reader:
            sid = (row.get(cols["id"]) or "").strip()
            if not sid:
                continue  # blank row
            require(sid not in rows, "duplicate_structure_id", sid)
            label = (row.get(cols["label"]) or "").strip()
            system = (row.get(cols["system"]) or "").strip()
            require(label, "label_missing",
                    f"{sid}: empty label (unlabeled = unadmitted)")
            require(system in KNOWN_SYSTEMS, "spec_schema",
                    f"{sid}: unknown tissue system {system!r}")
            if stage and stage_col and stage_col in header:
                row_stage = (row.get(stage_col) or "").strip().lower()
                require(not row_stage or row_stage == stage,
                        "stage_mixing",
                        f"{sid}: per-structure life_stage {row_stage!r} "
                        f"contradicts the specimen's one stage {stage!r} "
                        f"(one creature, one life stage)")
            stated = (row.get(cols.get("stated_volume_mm3", "")) or "").strip()
            rows[sid] = {
                "label": label,
                "system": system,
                "stated_volume_mm3": float(stated) if stated else None,
            }
    require(rows, "label_missing", f"{path}: no labeled structures")
    return rows


def load_adjacency(spec: dict) -> list[dict]:
    adj = spec.get("adjacency") or {}
    if not adj.get("file"):
        return []
    path = Path(spec["root"]) / adj["file"]
    if not path.is_file():
        require(not adj.get("required", False), "spec_file_missing", str(path))
        return []
    data = read_json(path)
    require(isinstance(data, list), "spec_schema",
            "adjacency file must be a list of edges")
    edges: list[dict] = []
    seen: set = set()
    for e in data:
        pair = e.get("pair")
        gap = e.get("gap_mm")
        require(isinstance(pair, list) and len(pair) == 2
                and all(isinstance(p, str) for p in pair),
                "spec_schema", f"bad adjacency pair {pair!r}")
        key = tuple(sorted(pair))
        require(key not in seen, "adjacency_duplicate", str(key))
        seen.add(key)
        require(isinstance(gap, (int, float)) and gap > 0,
                "adjacency_gap", f"{key}: gap_mm {gap!r}")
        edges.append({"pair": key, "gap_mm": float(gap),
                      "source": e.get("source", "touching_edges.json")})
    return edges


# ------------------------------------------------------------------ build
def stl_dir(spec: dict) -> Path:
    return Path(spec["root"]) / spec["stl"]["dir"]


def discover_stls(spec: dict) -> dict[str, Path]:
    d = stl_dir(spec)
    require(d.is_dir(), "spec_file_missing", str(d))
    files = sorted(d.glob(spec["stl"]["glob"]))
    by_id = {f.stem: f for f in files}
    require(len(by_id) == len(files), "duplicate_structure_id",
            "glob collision in stl dir")
    expected = spec["stl"]["expected_count"]
    require(len(by_id) == expected, "structure_count_mismatch",
            f"expected {expected} structures, found {len(by_id)} in {d}")
    return by_id


def build_body(spec: dict) -> tuple[dict, dict]:
    """Generate the kernel-format body definition + the derivation book."""
    record = load_collection_record(spec)
    stage = record["life_stage"].strip().lower()
    labels = load_labels(spec, stage)
    stls = discover_stls(spec)

    for sid in stls:
        require(sid in labels, "label_missing",
                f"STL {sid!r} has no labels row (unlabeled = unadmitted)")
    for sid in labels:
        require(sid in stls, "label_orphan",
                f"labels row {sid!r} has no STL file")

    out_dir = Path(spec["output_dir"])

    # Optional stated volumes / tolerance / band flag.
    vol_tol = spec["volume_tolerance_rel"]
    enforce_fractions = bool(spec.get("enforce_body_fraction_bands", False))

    membranes = []
    book_rows = []
    for sid in sorted(stls):
        path = stls[sid]
        tris = parse_stl(path)
        f32_tris = [(to_f32(a), to_f32(b), to_f32(c)) for a, b, c in tris]
        closed, open_edges, chi, n_verts = mesh_topology(f32_tris)
        require(closed, "mesh_not_closed",
                f"{sid}: {open_edges} edge(s) not shared by exactly 2 "
                f"triangles; a non-closed mesh has no defined enclosed "
                f"volume and is refused")
        info = labels[sid]
        system = info["system"]
        material = spec["materials_by_system"][system]

        blob = triangle_blob(f32_tris)
        rel = f"tris/{sid}.bin"
        (out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (out_dir / rel).write_bytes(blob)

        vol = mesh_volume_mm3(f32_tris)
        area = mesh_area_mm2(f32_tris)
        require(vol > 0.0, "mesh_zero_volume", sid)
        thickness = vol / area
        mass = area * thickness * MATERIALS[material]["density"]  # == V*rho

        stated = info["stated_volume_mm3"]
        stated_delta = None
        if stated is not None:
            stated_delta = round(100.0 * (vol - stated) / stated, 4)
            require(abs(vol - stated) / stated <= vol_tol, "volume_mismatch",
                    f"{sid}: mesh volume {vol:.4f} vs stated {stated:.4f} "
                    f"mm^3 ({stated_delta}%) beyond "
                    f"{100 * vol_tol:.0f}% tolerance")

        mem = {
            "id": f"mem.{sid}",
            "material": material,
            "triangles": rel,
            "thickness": thickness,
            "mass": mass,
            "label": info["label"],
            "structure_id": sid,
            "system": system,
            "source_stl": f"{spec['stl']['dir']}/{path.name}",
            "source_stl_sha256": sha256_file(path),
            "unique_vertices": n_verts,
            "faces": len(f32_tris),
            "volume_mm3": vol,
            "area_mm2": area,
            "stated_volume_mm3": stated,
            "stated_volume_delta_pct": stated_delta,
            "euler_characteristic": chi,
            "edge_degree_two_closed": True,
            "vertex_sha256": hashlib.sha256(vertex_records(f32_tris)).hexdigest(),
        }
        membranes.append(mem)
        book_rows.append({
            "structure_id": sid,
            "id": mem["id"],
            "label": info["label"],
            "system": system,
            "material": material,
            "source_stl": mem["source_stl"],
            "faces": len(f32_tris),
            "unique_vertices": n_verts,
            "volume_mm3_mesh": round(vol, 6),
            "area_mm2": round(area, 6),
            "thickness_mm_equivalent": round(thickness, 9),
            "mass_g": round(mass * 1000.0, 6),
            "mass_kg": mass,
            "euler_characteristic": chi,
            "vertex_sha256": mem["vertex_sha256"],
        })

    # Bonds: MEASURED adjacency only, or none (zero invented joints).
    edges = load_adjacency(spec)
    known_ids = set(stls)
    bonds = []
    bond_rows = []
    for e in edges:
        u, v = e["pair"]
        require(u in known_ids and v in known_ids, "adjacency_member_unknown",
                f"{u}, {v}")
        bid = f"bond.joint_{u}__{v}"
        bonds.append({
            "id": bid,
            "material": "mat.cartilage",
            "members": [f"mem.{u}", f"mem.{v}"],
            "cure_strength": CURE_CARTILAGE_PA,
            "rest_length_mm": e["gap_mm"],
            "measured_gap_mm": e["gap_mm"],
            "evidence": f"measured touching edge [{u}, {v}] "
                        f"gap_mm {e['gap_mm']} ({e['source']})",
        })
        bond_rows.append({"id": bid, "pair": list(e["pair"]),
                          "rest_length_mm": e["gap_mm"],
                          "material": "mat.cartilage",
                          "cure_strength_pa": CURE_CARTILAGE_PA})

    by_system: dict[str, float] = {}
    for r in book_rows:
        by_system[r["system"]] = by_system.get(r["system"], 0.0) + r["mass_kg"]
    total_mass_kg = sum(r["mass_kg"] for r in book_rows)
    total_mass_g = total_mass_kg * 1000.0

    body_mass_kg = record.get("body_mass_kg")
    fraction_book = None
    if isinstance(body_mass_kg, (int, float)) and body_mass_kg > 0:
        fraction_book = {
            "body_mass_kg": body_mass_kg,
            "segmented_total_kg": round(total_mass_kg, 6),
            "segmented_over_body": round(total_mass_kg / body_mass_kg, 4),
            "whole_body_band": list(WHOLE_BODY_BAND),
            "system_fractions_of_body": {
                s: round(m / body_mass_kg, 4)
                for s, m in sorted(by_system.items())
            },
            "fraction_bands_enforced": enforce_fractions,
            "bands_source": "mammalian skeleton fraction 8-15% of body mass; "
                            "muscle 25-50%; segmented excludes blood + GI "
                            "contents so the whole-body band is wide and "
                            "deviations are NAMED, never tuned",
        }

    body = {
        "schema": BODY_SCHEMA,
        "dataset": {
            "name": spec["dataset_name"],
            "source": "Chung et al. 2019 (J Korean Med Sci 34:e70) + Kim et "
                      "al. 2020 (PMCID PMC7167398): segmented 167-structure "
                      "STL set, Mimics 17.01; acquired by operator "
                      "request/certification",
            "spec_dir": str(Path(spec["_spec_dir"])),
        },
        "specimen": {
            "species": record["species"],
            "sex": record.get("sex"),
            "provenance": record["provenance"],
            "coordinate_frame": "mm, the STL set's own export frame, no "
                                "transform applied",
        },
        "stage": {
            "life_stage": stage,
            "age_months": record.get("age_months"),
            "age_source": record.get("age_source"),
            "scale": 1.0,
            "allometric_scaling_applied": False,
            "negative_example": "the H2 per-bone 3.79-8.8x stretch factors "
                                "(adjudicated FANTASY) -- this import shows "
                                "scale 1.0 and an identity transform",
        },
        "units": {
            "coordinates": "mm",
            "thickness": "mm",
            "density": "kg/mm^3",
            "mass": "kg",
            "cure_strength": "Pa (kernel convention)",
            "note": "the kernel mass law (area x thickness x density) is "
                    "unit-agnostic; these three agree, so mass is kg",
        },
        "membrane_layer": {
            "layer": "the Visible Monkey set as THREE membrane layers of one "
                     "adult-confirmed specimen: skeletal compartments, merged "
                     "muscular layer, integumentary layer (+ organ systems as "
                     "soft-tissue compartments)",
            "successors": ["measured adjacency -> bonds (never invented)",
                           "individual-muscle resolution (Guimaraes pairing)",
                           "the volume route (paired MRI/CT) for interior "
                           "structures the surface set cannot see"],
            "doctrine": "operator: mesh data with triangles is all we need -- "
                        "the triangles ARE the membranes",
        },
        "materials": MATERIALS,
        "membranes": membranes,
        "bonds": bonds,
    }

    book = {
        "constants": {
            "densities_kg_mm3": {name: mat["density"]
                                 for name, mat in sorted(MATERIALS.items())},
            "cure_cartilage_pa": CURE_CARTILAGE_PA,
            "citations": [mat["source"] for mat in MATERIALS.values()],
        },
        "laws": {
            "volume": "V = |sum_faces (1/6) v_a.(v_b x v_c)| on the resident "
                      "float32 triangles",
            "area": "kernel validator accumulation",
            "thickness": "t = V/A (equivalent shell thickness; conserves V; "
                         "the only derived parameter)",
            "mass": "m = A*t*rho = V*rho",
            "closed_mesh": "every undirected edge shared by exactly 2 "
                           "triangles; Euler characteristic reported, not "
                           "pinned (genus allowed)",
            "stage": "adult admitted only with age evidence "
                     "(age_months + age_source); one creature, one stage",
        },
        "compartments": book_rows,
        "bonds": bond_rows,
        "totals": {
            "compartments": len(book_rows),
            "bonds": len(bond_rows),
            "expected_structures": spec["stl"]["expected_count"],
            "total_mass_g": round(total_mass_g, 4),
            "total_mass_kg": total_mass_kg,
            "mass_by_system_kg": {s: round(m, 6)
                                  for s, m in sorted(by_system.items())},
            "whole_animal_check": fraction_book,
            "named_deviations": [
                "muscles are ONE merged structure (Kim et al. 2020): "
                "individual-muscle bookkeeping is successor work",
                "organ systems share one soft-tissue density (ICRP 23 "
                "convention): +/-5% organ-to-organ spread named, not tuned",
                "the segmented set excludes blood and GI contents: the "
                "segmented total is expected BELOW the 4.3 kg body mass, "
                "inside the wide [0.6, 1.3] band",
            ],
        },
    }
    return body, book


# ------------------------------------------------------- falsifier checks
def connected_components(body: dict, structure_ids) -> list[list[str]]:
    parent = {s: s for s in structure_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for bond in body["bonds"]:
        u = bond["members"][0][len("mem."):]
        v = bond["members"][1][len("mem."):]
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
    groups: dict[str, set] = {}
    for s in structure_ids:
        groups.setdefault(find(s), set()).add(s)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: g[0])


def run_checks(spec: dict, out_dir: Path, val_dir: Path) -> dict:
    """Every pre-registered falsifier, measured. Returns the verify record."""
    record = load_collection_record(spec)
    labels = load_labels(spec, record["life_stage"].strip().lower())
    stls = discover_stls(spec)
    body_path = out_dir / "visible_monkey.body.json"
    book = read_json(val_dir / "derivation.json")
    body = read_json(body_path)
    results: dict = {}

    # -- kernel_conformance: the kernel's OWN parser validates the definition
    parsed = kdef.parse_body(body_path)
    expected = spec["stl"]["expected_count"]
    require(len(parsed["membranes"]) == expected, "structure_count_mismatch",
            f"kernel sees {len(parsed['membranes'])}, spec expects {expected}")
    worst_mass_rel = max(
        abs(m["mass"] - m["mass_derived"]) / m["mass_derived"]
        for m in parsed["membranes"])
    require(worst_mass_rel <= kdef.MASS_TOLERANCE, "kernel_mass_tol",
            str(worst_mass_rel))
    results["kernel_conformance"] = {
        "pass": True,
        "measured": {
            "parser": "tools.matter_kernel.definition.parse_body",
            "membranes": len(parsed["membranes"]),
            "bonds": len(parsed["bonds"]),
            "stated_vs_kernel_derived_mass_max_rel": worst_mass_rel,
            "kernel_mass_tolerance": kdef.MASS_TOLERANCE,
        },
    }

    # -- geometry_preserved: read the definition back, compare to source STLs
    geo = []
    worst_bbox = 0.0
    worst_volume_rel = 0.0
    for mem in parsed["membranes"]:
        sid = mem["structure_id"]
        src = stls[sid]
        tris = parse_stl(src)
        f32_tris = [(to_f32(a), to_f32(b), to_f32(c)) for a, b, c in tris]

        blob = (out_dir / mem["triangles"]).read_bytes()
        require(len(blob) == kdef.TRIANGLE_BYTES * len(f32_tris),
                "blob_size", mem["id"])
        readback = []
        for off in range(0, len(blob), kdef.TRIANGLE_BYTES):
            vals = struct.unpack_from("<9f", blob, off)
            readback.append((tuple(vals[0:3]), tuple(vals[3:6]),
                             tuple(vals[6:9])))
        require(readback == f32_tris, "blob_faces", mem["id"])

        rb_min, rb_max = bbox(readback)
        s_min, s_max = bbox(f32_tris)
        dev = max(max(abs(a - b) for a, b in zip(rb_min, s_min)),
                  max(abs(a - b) for a, b in zip(rb_max, s_max)))
        worst_bbox = max(worst_bbox, dev)
        src_hash = hashlib.sha256(vertex_records(f32_tris)).hexdigest()
        require(src_hash == mem["vertex_sha256"], "vertex_hash", mem["id"])

        vol = mesh_volume_mm3(f32_tris)
        vol_rel = abs(vol - mem["volume_mm3"]) / vol
        worst_volume_rel = max(worst_volume_rel, vol_rel)
        require(vol_rel <= 1e-9, "volume_readback", f"{mem['id']}: {vol_rel}")
        require(mem["edge_degree_two_closed"] is True, "mesh_not_closed",
                mem["id"])
        geo.append({"id": mem["id"], "faces": len(f32_tris),
                    "bbox_max_dev_mm": dev, "vertex_sha256_match": True})
    results["geometry_preserved"] = {
        "pass": True,
        "measured": {
            "compartments": len(geo),
            "face_count_equal": True,
            "per_triangle_float32_equal": True,
            "worst_bbox_dev_mm": worst_bbox,
            "bbox_tolerance_mm": BBOX_TOL_MM,
            "worst_volume_readback_rel": worst_volume_rel,
            "vertex_sha256_all_match": True,
            "losses": "none itemized; all compartments byte-canonical",
        },
    }

    # -- closed_manifold: recheck topology from the READBACK blob
    open_total = 0
    chi_min, chi_max = None, None
    for mem in parsed["membranes"]:
        blob = (out_dir / mem["triangles"]).read_bytes()
        tris = []
        for off in range(0, len(blob), kdef.TRIANGLE_BYTES):
            v = struct.unpack_from("<9f", blob, off)
            tris.append((tuple(v[0:3]), tuple(v[3:6]), tuple(v[6:9])))
        closed, open_edges, chi, _ = mesh_topology(tris)
        require(closed, "mesh_not_closed", f"{mem['id']}: {open_edges}")
        open_total += open_edges
        chi_min = chi if chi_min is None else min(chi_min, chi)
        chi_max = chi if chi_max is None else max(chi_max, chi)
    results["closed_manifold"] = {
        "pass": True,
        "measured": {
            "open_edges_total": open_total,
            "euler_characteristic_range": [chi_min, chi_max],
            "note": "chi = 2 - 2g reported per compartment in the book; "
                    "genus allowed, open edges refused",
        },
    }

    # -- mass_book: identities close, totals close, biology bands (real data)
    total_kg = 0.0
    worst_mass_identity = 0.0
    stated_worst = None
    vol_tol = spec["volume_tolerance_rel"]
    for r in book["compartments"]:
        total_kg += r["mass_kg"]
        rho = MATERIALS[r["material"]]["density"]
        ident = abs(r["mass_kg"] - r["volume_mm3_mesh"] * rho) / (
            r["volume_mm3_mesh"] * rho)
        worst_mass_identity = max(worst_mass_identity, ident)
        require(ident <= MASS_IDENTITY_TOL_REL, "mass_identity",
                f"{r['id']}: {ident}")
        info = labels[r["structure_id"]]
        if info["stated_volume_mm3"] is not None:
            d = abs(r["volume_mm3_mesh"] - info["stated_volume_mm3"]) / (
                info["stated_volume_mm3"])
            require(d <= vol_tol, "volume_mismatch", f"{r['id']}: {d}")
            stated_worst = d if stated_worst is None else max(stated_worst, d)
    book_total_kg = book["totals"]["total_mass_kg"]  # unrounded in the book
    require(abs(total_kg - book_total_kg) / book_total_kg
            <= TOTAL_IDENTITY_TOL_REL,
            "total_identity", f"{total_kg} vs {book_total_kg}")
    frac = book["totals"]["whole_animal_check"]
    if frac is not None:
        blo, bhi = WHOLE_BODY_BAND
        require(blo <= frac["segmented_over_body"] <= bhi,
                "whole_body_band",
                f"segmented/body {frac['segmented_over_body']} outside "
                f"{list(WHOLE_BODY_BAND)} -- name the deviation, never tune "
                f"it (recompute body_mass_kg from the collection record)")
        if frac["fraction_bands_enforced"]:
            sysfrac = frac["system_fractions_of_body"]
            for system, band in (("skeletal", SKELETON_FRACTION_BAND),
                                 ("muscular", MUSCLE_FRACTION_BAND)):
                if system in sysfrac:
                    require(band[0] <= sysfrac[system] <= band[1],
                            "system_fraction_band",
                            f"{system} fraction {sysfrac[system]} outside "
                            f"{list(band)} -- name the deviation, never tune")
    results["mass_book"] = {
        "pass": True,
        "measured": {
            "total_mass_g": book["totals"]["total_mass_g"],
            "worst_mass_identity_rel_vs_Vrho": worst_mass_identity,
            "mass_identity_tolerance_rel": MASS_IDENTITY_TOL_REL,
            "stated_volume_worst_rel": stated_worst,
            "mass_by_system_kg": book["totals"]["mass_by_system_kg"],
            "whole_animal_check": book["totals"]["whole_animal_check"],
        },
    }

    # -- stage_true: the stage law, enforced and measured
    stage = parsed["stage"]
    require(stage["life_stage"] == record["life_stage"].strip().lower(),
            "stage_mixing", "body stage != collection record stage")
    require(stage["scale"] == 1.0
            and stage["allometric_scaling_applied"] is False, "stage_law",
            json.dumps(stage))
    if stage["life_stage"] == "adult":
        require(stage.get("age_months") and stage.get("age_source"),
                "stage_unconfirmed",
                "adult without age evidence (collection-record law)")
    results["stage_true"] = {
        "pass": True,
        "measured": {
            "life_stage": stage["life_stage"],
            "age_months": stage.get("age_months"),
            "age_evidence": bool(stage.get("age_source")),
            "scale": stage["scale"],
            "allometric_scaling_applied": False,
            "transform": "identity -- the writer packs source float32 "
                         "coordinates only; proven by the geometry hashes",
        },
    }

    # -- structure_set: the count identity + honest components
    comps = connected_components(parsed, sorted(stls))
    results["structure_set"] = {
        "pass": True,
        "measured": {
            "structures": len(parsed["membranes"]),
            "expected": spec["stl"]["expected_count"],
            "connected_components": len(comps),
            "components_note": "bonds exist ONLY at measured touching edges; "
                               "with no adjacency file the honest reading is "
                               "one component per structure, zero invented "
                               "joints",
        },
    }
    return results


# ------------------------------------------------------------------- cli
def regenerate(tmp: Path, spec: dict) -> None:
    """Generate the definition into tmp (byte-determinism probe)."""
    spec = dict(spec)
    spec["output_dir"] = str(tmp / "body")
    body, _book = build_body(spec)
    write_json(Path(spec["output_dir"]) / "visible_monkey.body.json", body)


def main(argv: list[str]) -> int:
    require(len(argv) >= 3, "unknown_command",
            "usage: visible_monkey_import.py {build|verify} <dir_spec.json>")
    cmd = argv[1]
    require(cmd in ("build", "verify"), "unknown_command", cmd)
    spec = load_spec(Path(argv[2]))
    out_dir = Path(spec["output_dir"])
    val_dir = Path(spec["validation_dir"])

    if cmd == "build":
        body, book = build_body(spec)
        write_json(out_dir / "visible_monkey.body.json", body)
        write_json(val_dir / "derivation.json", book)
        # byte-determinism: regenerate into a temp dir and demand equality
        with tempfile.TemporaryDirectory() as td:
            regen = Path(td) / "regen"
            regenerate(regen, spec)  # writes regen/body/...
            regen_body = regen / "body"
            for p in sorted(out_dir.rglob("*")):
                if p.is_file():
                    rel = p.relative_to(out_dir)
                    other = regen_body / rel
                    require(other.is_file()
                            and other.read_bytes() == p.read_bytes(),
                            "nondeterministic_output", str(rel))
        checks = run_checks(spec, out_dir, val_dir)
        write_json(val_dir / "verify.json", checks)
        print(f"visible_monkey_import build OK: {len(body['membranes'])} "
              f"compartments, {len(body['bonds'])} bonds, total "
              f"{book['totals']['total_mass_g']} g; all falsifiers green")
        return 0

    if cmd == "verify":
        require(out_dir.is_dir(), "missing_definition", str(out_dir))
        require((val_dir / "derivation.json").is_file(), "missing_definition",
                str(val_dir / "derivation.json"))
        run_checks(spec, out_dir, val_dir)
        with tempfile.TemporaryDirectory() as td:
            regen = Path(td) / "regen"
            regenerate(regen, spec)  # writes regen/body/...
            regen_body = regen / "body"
            committed = (out_dir / "visible_monkey.body.json").read_bytes()
            require((regen_body / "visible_monkey.body.json").read_bytes()
                    == committed, "definition_drift",
                    "committed body.json != fresh regeneration")
            for p in sorted(out_dir.rglob("*.bin")):
                rel = p.relative_to(out_dir)
                require((regen_body / rel).read_bytes() == p.read_bytes(),
                        "blob_drift", str(rel))
        print("visible_monkey_import verify OK: committed definition is "
              "byte-exact reproducible; all falsifiers green")
        return 0
    raise Refusal("unknown_command", cmd)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Refusal as ref:
        print(f"REFUSED {ref.code}: {ref.detail}", file=sys.stderr)
        sys.exit(2)
    except kdef.DefinitionError as de:
        print(f"KERNEL REFUSED: {de}", file=sys.stderr)
        sys.exit(3)
