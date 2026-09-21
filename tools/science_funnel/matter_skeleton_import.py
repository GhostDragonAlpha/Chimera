"""Matter skeleton import: the infant skeleton expressed AS MATTER.

Lane agent/matter-skeleton-import-20260920. Specimen A (MorphoSource
000875604, Macaca mulatta USNM 497136-3, infant, 160 um CT): every
identified bone becomes ONE matter-kernel compartment whose resident
triangles ARE the bone mesh's own triangles (triangles-are-weights), and
every bond is a measured touching_edge from bone_identification_v3.json
(bonds-are-materials; the bond geometry is measured, never authored).

Rule 0 receipt: tools/science_funnel/validation/matter_skeleton_20260920/
receipt.json (statement / prediction / falsifiers banked before this tool
existed). Rule 1: every number here is DERIVED (volume -> thickness ->
mass) or CITED (material constants, literature bands); the tool authors
no parameters:

    V_k = |sum_faces (1/6) * v_a . (v_b x v_c)|      (divergence theorem)
    A_k = sum_faces 0.5*|(v_b-v_a) x (v_c-v_a)|
    t_k = V_k / A_k          (equivalent shell thickness; conserves V_k,
                              so the kernel's mass law A*t*rho == V*rho)
    m_k = V_k * rho          (rho cited, adult cortical upper anchor)

Stage-true law: the import applies NO transform to source coordinates
(scale 1.0); the creature is imported AS an infant. The H2 per-bone
allometric stretch factors (3.79-8.8x) are the named negative example.

Usage (repo root):
    python -B tools/science_funnel/matter_skeleton_import.py build
    python -B tools/science_funnel/matter_skeleton_import.py verify

build  regenerates the definition byte-exactly, validates it through the
       kernel's own parser (tools.matter_kernel.definition), re-reads it
       and checks every falsifier, then writes the derivation book and
       verification records.
verify reads ONLY committed artifacts (fresh-clone mode): regenerates
       into a temp dir, demands byte-identical output, re-runs every
       falsifier check. Refuses loudly on any mismatch.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.matter_kernel import definition as kdef  # noqa: E402
from tools.science_funnel.common import Refusal, require  # noqa: E402

DATA_DIR = REPO_ROOT / "tools/science_funnel/data/morphosource_ct"
PREVIEW_DIR = DATA_DIR / "meshes_preview"
OUT_DIR = DATA_DIR / "matter_skeleton"
VALIDATION_DIR = REPO_ROOT / "tools/science_funnel/validation/matter_skeleton_20260920"

# Sourced constants (kernel law 4: no constant without a citation).
# Densities are kg/mm^3 because the CT frame is millimetres; the kernel's
# mass law (area x thickness x density) is unit-agnostic as long as the
# three agree -- receipts record the conversion explicitly.
RHO_BONE_KG_MM3 = 1.9e-6   # 1900 kg/m^3, adult cortical wet density
RHO_CART_KG_MM3 = 1.06e-6  # 1060 kg/m^3, cartilage (Yamada 1970)
CURE_CARTILAGE_PA = 13.0e6  # cartilage tensile failure (Yamada 1970)

MATERIALS = {
    "mat.bone_cortical": {
        "density": RHO_BONE_KG_MM3,
        "young_modulus": 17.0e9,
        "yield": 100.0e6,
        "hardness_vickers": 40.0,
        "source": "COWIN 'Bone Mechanics Handbook'; CURREY 'Bones: Structure "
                  "and Mechanics': cortical wet density 1800-2100 kg/m^3 "
                  "(1900 used, = 1.9e-6 kg/mm^3); E ~15-20 GPa (17 used); "
                  "tensile failure ~80-150 MPa (100 used, conservative); "
                  "Vickers ~30-50 HV (40 used)",
        "stage_note": "PROVISIONAL for infant: adult cortical range used as "
                      "the cited UPPER ANCHOR; no infant-macaque tissue-density "
                      "citation exists and infant bone is under-mineralized "
                      "(RAUCH 2001, physiological osteoporosis of infancy), so "
                      "compartment masses bias HIGH. Receipt mass_book names "
                      "the deviation; it is never tuned away.",
    },
    "mat.cartilage": {
        "density": RHO_CART_KG_MM3,
        "young_modulus": 10.0e6,
        "yield": 13.0e6,
        "hardness_vickers": 0.3,
        "source": "YAMADA 1970 'Strength of Biological Materials' (Williams & "
                  "Wilkins): cartilage tensile strength ~13 MPa, Young's "
                  "modulus 7-25 MPa (10 used), density ~1.06 g/cm^3; the "
                  "joint bond material at the measured touching edges",
    },
}

# Literature bands for the total-mass check (receipt rule_1_derivation_plan).
BODY_MASS_BAND_KG = (0.400, 0.550)   # rhesus infant birth mass (NC3Rs)
SKELETON_FRACTION_BAND = (0.08, 0.15)  # mammalian skeleton fraction
PRANGE_A, PRANGE_B = 0.0708, 1.09    # Prange/Anderson/Rahn 1979 regression

# Falsifier tolerances (pre-registered in receipt.json).
BBOX_TOL_MM = 1e-3
MASS_TOL_FRAC = 0.05
VOXEL_TOTAL_TOL_FRAC = 0.05

SPECIMEN_ID = "000875604"


# ---------------------------------------------------------------- geometry
def parse_obj(path: Path) -> tuple[list[tuple], list[tuple]]:
    """Parse a preview OBJ: ('v x y z') vertices, ('f a b c') triangle faces."""
    verts: list[tuple] = []
    faces: list[tuple] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("f "):
                p = line.split()
                require(len(p) == 4, "obj_not_triangle", f"{path.name}: {line!r}")
                faces.append(tuple(int(q.split("/")[0]) - 1 for q in p[1:]))
    require(verts and faces, "obj_empty", str(path))
    for a, b, c in faces:
        require(0 <= a < len(verts) and 0 <= b < len(verts) and 0 <= c < len(verts),
                "obj_bad_index", path.name)
    return verts, faces


def to_f32(verts: list[tuple]) -> list[tuple]:
    """Quantize coordinates to float32 exactly as the triangle blob stores them."""
    out = []
    for x, y, z in verts:
        p = struct.pack("<3f", x, y, z)
        out.append(struct.unpack("<3f", p))
    return out


def triangle_blob(f32: list[tuple], faces: list[tuple]) -> bytes:
    """The kernel's triangle format: 36 bytes per triangle, 9 float32 LE."""
    return b"".join(struct.pack("<9f", *f32[a], *f32[b], *f32[c])
                    for a, b, c in faces)


def blob_area_mm2(blob: bytes) -> float:
    """Area EXACTLY as the kernel validator computes it (same accumulation)."""
    area = 0.0
    for off in range(0, len(blob), kdef.TRIANGLE_BYTES):
        ax, ay, az, bx, by, bz, cx, cy, cz = struct.unpack_from("<9f", blob, off)
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        area += 0.5 * (nx * nx + ny * ny + nz * nz) ** 0.5
    return area


def mesh_volume_mm3(verts: list[tuple], faces: list[tuple]) -> float:
    """V = |sum (1/6) v_a . (v_b x v_c)| -- divergence theorem, f64 accumulation
    over the resident (float32) coordinates."""
    vol6 = 0.0
    for a, b, c in faces:
        (xa, ya, za), (xb, yb, zb), (xc, yc, zc) = verts[a], verts[b], verts[c]
        vol6 += (xa * (yb * zc - zb * yc)
                 - ya * (xb * zc - zb * xc)
                 + za * (xb * yc - yb * xc))
    return abs(vol6) / 6.0


def vertex_records(verts_f32: list[tuple], faces: list[tuple]) -> bytes:
    """Canonical vertex serialization: the sorted unique 12-byte float32
    records actually referenced by triangles. Source and readback both
    canonicalize this way, so the sha256 comparison is order-independent."""
    seen = {struct.pack("<3f", *verts_f32[i]) for tri in faces for i in tri}
    return b"".join(sorted(seen))


def bbox(verts: list[tuple]) -> tuple[list, list]:
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return [min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]


# --------------------------------------------------------------- identity
def read_json(path: Path):
    # utf-8-sig: upstream captures may carry a BOM (byte-stable data law
    # keeps it); reading tolerates it without touching the committed bytes.
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_identifications() -> tuple[dict, dict]:
    """(per-rank record for all 25 bones, touching-edge book) from the
    committed identification data. Labels: v3 (authoritative); side for the
    mirror-confirmed pairs and the axial composite: v1, carried with its
    own confidence note."""
    v3 = read_json(DATA_DIR / "bone_identification_v3.json")
    v1 = read_json(DATA_DIR / "bone_identification.json")
    a3 = v3["specimens"][SPECIMEN_ID]
    a1 = v1["specimens"][SPECIMEN_ID]
    by_rank3 = {b["rank"]: b for b in a3["bones"]}
    by_rank1 = {b["rank"]: b for b in a1["bones"]}

    ranks = sorted(set(by_rank3) | set(by_rank1))
    require(ranks == list(range(1, 26)), "rank_set",
            f"expected ranks 1..25, got {ranks}")

    records = {}
    for r in ranks:
        b3 = by_rank3.get(r)
        b1 = by_rank1.get(r, {})
        rec = {
            "rank": r,
            "label": (b3 or {}).get("segment_label") or b1.get("identified_as"),
            "confidence": (b3 or b1).get("confidence"),
            "chain_kind": (b3 or {}).get("chain_kind"),
            "chain": (b3 or {}).get("chain"),
            "side": b1.get("side") if b1.get("side") not in (None, "?") else None,
            "side_source": "bone_identification.json(v1)" if b1.get("side") else None,
            "label_source": "bone_identification_v3.json" if b3
                            else "bone_identification.json(v1)",
        }
        require(rec["label"], "label_missing", f"rank {r}")
        records[r] = rec

    # The measured adjacency: chain touching_edges, cross-checked against the
    # per-bone touching_neighbors union (both live in the same v3 file).
    edges: dict[tuple, dict] = {}
    for chain in a3["chains"]:
        for e in chain["touching_edges"]:
            key = tuple(sorted(e["pair"]))
            gap = float(e["gap_mm"])
            require(key not in edges or edges[key]["gap_mm"] == gap,
                    "edge_conflict", str(key))
            edges[key] = {"gap_mm": gap, "chain_kind": chain["kind"],
                          "chain_members": chain["members"]}
    for b in a3["bones"]:
        for tn in b.get("touching_neighbors", []):
            key = tuple(sorted((b["rank"], tn["rank"])))
            require(key in edges and edges[key]["gap_mm"] == float(tn["gap_mm"]),
                    "edge_mismatch", f"per-bone {key} not in chain book")
    require(len(edges) == 21, "edge_count",
            f"expected 21 measured touching edges, got {len(edges)}")
    return records, edges


# ------------------------------------------------------------------ build
def obj_path(rank: int) -> Path:
    matches = sorted(PREVIEW_DIR.glob(f"bone_{rank:02d}_*_lo.obj"))
    require(len(matches) == 1, "obj_ambiguous", f"rank {rank}: {matches}")
    return matches[0]


def build_body() -> tuple[dict, dict]:
    """Generate the kernel-format body definition + the derivation book."""
    manifest = read_json(DATA_DIR / "meshes/manifest.json")
    require(manifest["bones"][0]["bbox_min_mm"] and True, "manifest_shape")
    voxel_book = {b["rank"]: b for b in manifest["bones"]}
    download = read_json(DATA_DIR / "download_receipt.json")
    spec_meta = next(s for s in download["specimens"]
                     if s["media_id"] == SPECIMEN_ID)
    records, edges = load_identifications()

    membranes = []
    book_rows = []
    for rank in range(1, 26):
        src = obj_path(rank)
        verts64, faces = parse_obj(src)
        referenced = {i for tri in faces for i in tri}
        require(len(referenced) == len(verts64), "unused_vertices",
                f"{src.name}: {len(verts64) - len(referenced)} unreferenced")
        f32 = to_f32(verts64)
        blob = triangle_blob(f32, faces)

        rel = f"tris/bone_{rank:02d}.bin"
        (OUT_DIR / rel).parent.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / rel).write_bytes(blob)

        vol = mesh_volume_mm3(f32, faces)
        area = blob_area_mm2(blob)
        thickness = vol / area
        mass = area * thickness * RHO_BONE_KG_MM3  # == vol * rho by t = V/A

        rec = records[rank]
        vox = float(voxel_book[rank]["volume_mm3"])
        mem = {
            "id": f"mem.bone_{rank:02d}",
            "material": "mat.bone_cortical",
            "triangles": rel,
            "thickness": thickness,
            "mass": mass,
            "label": rec["label"],
            "side": rec["side"],
            "confidence": rec["confidence"],
            "chain_kind": rec["chain_kind"],
            "rank": rank,
            "source_obj": f"../meshes_preview/{src.name}",
            "source_obj_sha256": hashlib.sha256(
                src.read_bytes()).hexdigest(),
            "vertices": len(verts64),
            "faces": len(faces),
            "volume_mm3": vol,
            "area_mm2": area,
            "voxel_volume_mm3": vox,
            "voxel_delta_pct": round(100.0 * (vol - vox) / vox, 4),
            "vertex_sha256": hashlib.sha256(
                vertex_records(f32, faces)).hexdigest(),
            "label_source": rec["label_source"],
        }
        membranes.append(mem)
        book_rows.append({
            "rank": rank,
            "id": mem["id"],
            "label": rec["label"],
            "side": rec["side"],
            "confidence": rec["confidence"],
            "source_obj": mem["source_obj"],
            "vertices": len(verts64),
            "faces": len(faces),
            "volume_mm3_mesh": round(vol, 6),
            "area_mm2": round(area, 6),
            "thickness_mm_equivalent": round(thickness, 9),
            "mass_g": round(mass * 1000.0, 6),
            "volume_mm3_voxel_book": round(vox, 6),
            "volume_delta_pct": mem["voxel_delta_pct"],
            "vertex_sha256": mem["vertex_sha256"],
        })

    bonds = []
    bond_rows = []
    for (u, v) in sorted(edges):
        ev = edges[(u, v)]
        bid = f"bond.joint_{u:02d}_{v:02d}"
        bonds.append({
            "id": bid,
            "material": "mat.cartilage",
            "members": [f"mem.bone_{u:02d}", f"mem.bone_{v:02d}"],
            "cure_strength": CURE_CARTILAGE_PA,
            "rest_length_mm": ev["gap_mm"],
            "measured_gap_mm": ev["gap_mm"],
            "evidence": (
                f"bone_identification_v3.json chain {ev['chain_kind']} "
                f"touching_edge [{u}, {v}], gap_mm {ev['gap_mm']}"),
        })
        bond_rows.append({
            "id": bid,
            "pair": [u, v],
            "chain_kind": ev["chain_kind"],
            "rest_length_mm": ev["gap_mm"],
            "material": "mat.cartilage",
            "cure_strength_pa": CURE_CARTILAGE_PA,
        })

    body = {
        "schema": "chimera.matter_body.v1",
        "specimen": {
            "media_id": SPECIMEN_ID,
            "species": spec_meta["species"],
            "specimen": spec_meta["specimen"],
            "modality": spec_meta["modality"],
            "resolution_um": spec_meta["resolution_um"],
            "source": "MorphoSource CT 000875604; manual operator download "
                      "(download_receipt.json); meshes_preview committed with "
                      "mesh_receipt.json sha pinning",
            "coordinate_frame": "CT millimetres (voxel 0.16 mm), the committed "
                                "preview meshes' own frame, no transform applied",
        },
        "stage": {
            "life_stage": "infant",
            "scale": 1.0,
            "allometric_scaling_applied": False,
            "provenance": "MorphoSource media 000875604 metadata: Macaca "
                          "mulatta USNM 497136-3, infant, 160 um CT "
                          "(meshes/manifest.json source field + "
                          "download_receipt.json)",
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
            "layer": "bones (compartments) -- the first membrane layer",
            "successors": ["muscles: the next membrane layer over the bone "
                           "compartments", "skin eventually"],
            "doctrine": "operator 2026-09-20: mesh data with triangles is all "
                        "we need -- the triangles ARE the membranes",
        },
        "materials": MATERIALS,
        "membranes": membranes,
        "bonds": bonds,
    }

    # ---- derivation book totals
    total_mass_g = sum(r["mass_g"] for r in book_rows)
    total_mesh_mm3 = sum(r["volume_mm3_mesh"] for r in book_rows)
    total_vox_mm3 = sum(r["volume_mm3_voxel_book"] for r in book_rows)
    lo, hi = BODY_MASS_BAND_KG
    frac_lo = total_mass_g / 1000.0 / hi
    frac_hi = total_mass_g / 1000.0 / lo
    prange_lo = 1000.0 * PRANGE_A * lo ** PRANGE_B
    prange_hi = 1000.0 * PRANGE_A * hi ** PRANGE_B
    book = {
        "constants": {
            "rho_bone_kg_mm3": RHO_BONE_KG_MM3,
            "rho_bone_kg_m3": 1900.0,
            "rho_cartilage_kg_mm3": RHO_CART_KG_MM3,
            "cure_cartilage_pa": CURE_CARTILAGE_PA,
            "citations": [MATERIALS["mat.bone_cortical"]["source"],
                          MATERIALS["mat.cartilage"]["source"]],
        },
        "laws": {
            "volume": "V = |sum_faces (1/6) v_a.(v_b x v_c)| on the resident "
                      "float32 triangles",
            "area": "kernel validator accumulation over the committed blob",
            "thickness": "t = V/A (equivalent shell thickness; conserves V; "
                         "the only derived parameter)",
            "mass": "m = A*t*rho = V*rho",
        },
        "compartments": book_rows,
        "bonds": bond_rows,
        "totals": {
            "compartments": len(book_rows),
            "bonds": len(bond_rows),
            "total_mass_g": round(total_mass_g, 4),
            "total_volume_mm3_mesh": round(total_mesh_mm3, 4),
            "total_volume_mm3_voxel": round(total_vox_mm3, 4),
            "total_volume_delta_pct": round(
                100.0 * (total_mesh_mm3 - total_vox_mm3) / total_vox_mm3, 3),
            "total_mass_if_voxel_volume_g": round(
                total_vox_mm3 * RHO_BONE_KG_MM3 * 1000.0, 4),
            "body_mass_band_kg": list(BODY_MASS_BAND_KG),
            "skeleton_fraction_of_body_band_pct": [round(100.0 * frac_lo, 2),
                                                   round(100.0 * frac_hi, 2)],
            "skeleton_fraction_band_pct": [100.0 * SKELETON_FRACTION_BAND[0],
                                           100.0 * SKELETON_FRACTION_BAND[1]],
            "prange_regression_predicted_g": [round(prange_lo, 2),
                                              round(prange_hi, 2)],
            "prange_source": "Prange, Anderson & Rahn 1979 (Am Nat 113:103-122): "
                             "M_skel = 0.0708 * M_body^1.09 (adult-taxon)",
            "named_deviations": [
                "adult cortical density (1900 kg/m^3) is the cited UPPER "
                "ANCHOR: infant bone is under-mineralized (Rauch 2001), so "
                "true compartment masses sit below these numbers",
                "the CT bone threshold (118, 95th percentile) includes "
                "partially mineralized growth cartilage in this infant, so "
                "volumes include some non-bone mineralized tissue",
                "the cortical tissue density is applied to whole-bone volume "
                "(porous trabecular cores included), biasing masses HIGH; "
                "all three biases point the same direction and are named, "
                "not tuned",
            ],
        },
    }
    return body, book


def write_json(path: Path, payload) -> None:
    text = json.dumps(payload, indent=1, ensure_ascii=False,
                      allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ------------------------------------------------------- falsifier checks
def components(body: dict) -> list[set[int]]:
    parent = {r: r for r in range(1, 26)}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for bond in body["bonds"]:
        u = int(bond["members"][0].split("_")[1])
        v = int(bond["members"][1].split("_")[1])
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
    groups: dict[int, set[int]] = {}
    for r in range(1, 26):
        groups.setdefault(find(r), set()).add(r)
    return sorted(groups.values(), key=lambda s: min(s))


def run_checks(body: dict, book: dict) -> dict:
    """Every pre-registered falsifier, measured. Returns the verify record."""
    results: dict = {}

    # -- kernel_conformance: the kernel's OWN parser validates the definition
    body_path = OUT_DIR / "infant_skeleton.body.json"
    parsed = kdef.parse_body(body_path)
    require(len(parsed["membranes"]) == 25, "kernel_membranes", "expected 25")
    require(len(parsed["bonds"]) == 21, "kernel_bonds", "expected 21")
    results["kernel_conformance"] = {
        "pass": True,
        "measured": {
            "parser": "tools.matter_kernel.definition.parse_body",
            "membranes": len(parsed["membranes"]),
            "bonds": len(parsed["bonds"]),
            "stated_vs_kernel_derived_mass_max_rel": max(
                abs(m["mass"] - m["mass_derived"]) / m["mass_derived"]
                for m in parsed["membranes"]),
        },
    }

    # -- geometry_preserved: read the definition back, compare to source OBJs
    geo = []
    worst_bbox = 0.0
    for mem in parsed["membranes"]:
        rank = mem["rank"]
        src = obj_path(rank)
        verts64, faces = parse_obj(src)
        f32 = to_f32(verts64)

        blob = (OUT_DIR / mem["triangles"]).read_bytes()
        require(len(blob) == 36 * len(faces), "blob_size", mem["id"])
        readback = []
        for off in range(0, len(blob), kdef.TRIANGLE_BYTES):
            vals = struct.unpack_from("<9f", blob, off)
            readback.append((tuple(vals[0:3]), tuple(vals[3:6]),
                             tuple(vals[6:9])))
        expected = [(f32[a], f32[b], f32[c]) for a, b, c in faces]
        require(readback == expected, "blob_faces", mem["id"])

        rb_verts = [v for tri in readback for v in tri]
        rb_min, rb_max = bbox(rb_verts)
        s_min, s_max = bbox(verts64)
        dev = max(max(abs(a - b) for a, b in zip(rb_min, s_min)),
                  max(abs(a - b) for a, b in zip(rb_max, s_max)))
        worst_bbox = max(worst_bbox, dev)
        src_hash = hashlib.sha256(vertex_records(f32, faces)).hexdigest()
        geo.append({
            "id": mem["id"], "vertices": len(verts64), "faces": len(faces),
            "bbox_max_dev_mm": dev, "vertex_sha256_match":
                src_hash == mem["vertex_sha256"],
        })
        require(geo[-1]["vertex_sha256_match"], "vertex_hash", mem["id"])
        require(dev <= BBOX_TOL_MM, "bbox_tol", f"{mem['id']}: {dev}")
    results["geometry_preserved"] = {
        "pass": True,
        "measured": {
            "compartments": len(geo),
            "face_count_equal": True,
            "vertex_count_equal": True,
            "per_face_float32_equal": True,
            "worst_bbox_dev_mm": worst_bbox,
            "bbox_tolerance_mm": BBOX_TOL_MM,
            "vertex_sha256_all_match": True,
            "losses": "none itemized; all 25 compartments byte-canonical",
        },
    }

    # -- adjacency_reproduced: the bond graph IS the measured graph
    _, edges = load_identifications()
    def_edges = {}
    for bond in parsed["bonds"]:
        u = int(bond["members"][0].split("_")[1])
        v = int(bond["members"][1].split("_")[1])
        def_edges[tuple(sorted((u, v)))] = bond["rest_length_mm"]
    require(set(def_edges) == set(edges), "edge_set",
            f"invented={set(def_edges) - set(edges)} "
            f"dropped={set(edges) - set(def_edges)}")
    gap_dev = max(abs(def_edges[k] - edges[k]["gap_mm"]) for k in edges)
    require(gap_dev <= 0.005, "gap_tol", str(gap_dev))
    comps = components(parsed)
    results["adjacency_reproduced"] = {
        "pass": True,
        "measured": {
            "edges": len(def_edges),
            "invented_joints": 0,
            "dropped_joints": 0,
            "max_rest_length_dev_mm": gap_dev,
            "components": [sorted(c) for c in comps],
            "components_note": "8 honest components: 4 measured chains + the "
                               "axial composite + 3 singletons with NO measured "
                               "adjacency; cross-component joints are successor "
                               "measurement work, never invented here",
        },
    }

    # -- mass_book
    tot = book["totals"]
    require(abs(tot["total_volume_delta_pct"]) / 100.0
            <= VOXEL_TOTAL_TOL_FRAC, "voxel_total_tol",
            str(tot["total_volume_delta_pct"]))
    frac = tot["skeleton_fraction_of_body_band_pct"]
    in_band = (frac[1] >= tot["skeleton_fraction_band_pct"][0]
               and frac[0] <= tot["skeleton_fraction_band_pct"][1])
    mass_g = tot["total_mass_g"]
    in_window = 30.0 <= mass_g <= 65.0
    require(in_window, "mass_window", str(mass_g))
    results["mass_book"] = {
        "pass": True,
        "measured": {
            "total_mass_g": mass_g,
            "mass_window_g": [30.0, 65.0],
            "in_window": in_window,
            "total_volume_mesh_mm3": tot["total_volume_mm3_mesh"],
            "total_volume_voxel_mm3": tot["total_volume_mm3_voxel"],
            "total_volume_delta_pct": tot["total_volume_delta_pct"],
            "worst_compartment_delta_pct": min(
                r["volume_delta_pct"] for r in book["compartments"]),
            "worst_compartment": min(
                book["compartments"],
                key=lambda r: r["volume_delta_pct"])["id"],
            "fraction_of_body_band_pct": frac,
            "skeleton_fraction_band_pct": tot["skeleton_fraction_band_pct"],
            "lands_in_band": in_band,
            "prange_predicted_g": tot["prange_regression_predicted_g"],
            "deviation_vs_regression": "named, not tuned: " + "; ".join(
                tot["named_deviations"]),
        },
    }

    # -- stage_true
    stage = parsed["stage"]
    require(stage["life_stage"] == "infant" and stage["scale"] == 1.0
            and stage["allometric_scaling_applied"] is False, "stage_law",
            json.dumps(stage))
    results["stage_true"] = {
        "pass": True,
        "measured": {
            "life_stage": stage["life_stage"],
            "scale": stage["scale"],
            "allometric_scaling_applied": False,
            "transform": "identity -- writer packs source coordinates through "
                         "float32 only; proven by geometry_preserved hashes",
            "provenance": stage["provenance"],
        },
    }
    return results


# ------------------------------------------------------------------- cli
def regenerate(tmp: Path) -> None:
    """Generate the definition into tmp (byte-determinism probe)."""
    global OUT_DIR
    saved = OUT_DIR
    OUT_DIR = tmp
    try:
        body, _book = build_body()
        write_json(OUT_DIR / "infant_skeleton.body.json", body)
    finally:
        OUT_DIR = saved


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "build"
    if cmd == "build":
        body, book = build_body()
        write_json(OUT_DIR / "infant_skeleton.body.json", body)
        # byte-determinism: regenerate into a temp dir and demand equality
        with tempfile.TemporaryDirectory() as td:
            regen = Path(td) / "regen"
            regen.mkdir()
            regenerate(regen)
            for p in sorted((OUT_DIR).rglob("*")):
                if p.is_file():
                    rel = p.relative_to(OUT_DIR)
                    other = regen / rel
                    require(other.is_file() and
                            other.read_bytes() == p.read_bytes(),
                            "nondeterministic_output", str(rel))
        checks = run_checks(body, book)
        write_json(VALIDATION_DIR / "derivation.json", book)
        write_json(VALIDATION_DIR / "verify.json", checks)
        print(f"matter_skeleton_import build OK: 25 compartments, 21 bonds, "
              f"total {book['totals']['total_mass_g']} g; "
              f"all falsifiers green")
        return 0
    if cmd == "verify":
        require(OUT_DIR.is_dir(), "missing_definition", str(OUT_DIR))
        body = read_json(OUT_DIR / "infant_skeleton.body.json")
        book = read_json(VALIDATION_DIR / "derivation.json")
        checks = run_checks(body, book)
        with tempfile.TemporaryDirectory() as td:
            regen = Path(td) / "regen"
            regen.mkdir()
            regenerate(regen)
            committed = (OUT_DIR / "infant_skeleton.body.json").read_bytes()
            require((regen / "infant_skeleton.body.json").read_bytes()
                    == committed, "definition_drift",
                    "committed body.json != fresh regeneration")
            for p in sorted(OUT_DIR.rglob("*.bin")):
                rel = p.relative_to(OUT_DIR)
                require((regen / rel).read_bytes() == p.read_bytes(),
                        "blob_drift", str(rel))
        print("matter_skeleton_import verify OK: committed definition is "
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
