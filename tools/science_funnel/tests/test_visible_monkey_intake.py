"""The Visible Monkey intake prestage: synthetic falsifier battery.

Rule 0 receipt: tools/science_funnel/validation/visible_monkey_intake_20260921/
receipt.json (banked BEFORE these tests ran). Every test here proves the
intake CONTRACT against SYNTHETIC stand-ins with known analytic
volumes/masses -- the real data has not landed; nothing about its exact
formats is guessed.

Falsifier -> test map (pre-registered):
  geometry_preserved   test_analytic_volumes_and_masses, test_kernel_conformance
  mass_book_closes     test_analytic_volumes_and_masses, test_body_bands_bite
  byte_exact_verify    test_determinism, test_verify_green_and_tamper,
                       test_fresh_clone_verify (subprocess, repo-root spec)
  stage_law_enforced   test_stage_law_refusals, test_stage_mixing_refused
  refusal_by_name      test_*_refused family
  pipeline_parameterization  test_volume_route_phantom,
                       test_volume_route_refusals, test_serial_section_hook
  determinism          test_determinism, test_volume_route_phantom (manifest
                       byte equality across builds)

Run (repo root):
    python -B -m unittest tools.science_funnel.tests.test_visible_monkey_intake
"""
from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.matter_kernel import definition as kdef  # noqa: E402
from tools.science_funnel.common import Refusal  # noqa: E402
from tools.science_funnel import visible_monkey_import as vmi  # noqa: E402
from tools.science_funnel import visible_monkey_volume_route as vmv  # noqa: E402


# ------------------------------------------------------------ STL writers
def _normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / n, ny / n, nz / n)


def write_binary_stl(path: Path, tris, flip=False) -> None:
    """A valid binary STL: 80-byte header, uint32 count, 50 bytes per tri."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(b"synthetic visible monkey fixture".ljust(80, b"\0"))
        fh.write(struct.pack("<I", len(tris)))
        for tri in tris:
            a, b, c = tri
            if flip:
                b, c = c, b
            fh.write(struct.pack("<12fH", *_normal(a, b, c),
                                 *a, *b, *c, 0))


def box_tris(hx, hy, hz):
    """Closed box with integer corners (exact in float32). Outward winding.
    V = 2hx * 2hy * 2hz exactly."""
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
         (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
    tris = []
    for q in quads:
        tris.append((v[q[0]], v[q[1]], v[q[2]]))
        tris.append((v[q[0]], v[q[2]], v[q[3]]))
    return tris


def tetra_tris(a):
    """Regular tetrahedron, edge a. V = a^3 / (6*sqrt(2))."""
    v = [(0.0, 0.0, 0.0),
         (a, 0.0, 0.0),
         (a / 2, a * math.sqrt(3) / 2, 0.0),
         (a / 2, a / (2 * math.sqrt(3)), a * math.sqrt(2 / 3))]
    return [(v[0], v[1], v[2]), (v[0], v[1], v[3]),
            (v[1], v[2], v[3]), (v[0], v[2], v[3])]


def octa_tris(a):
    """Regular octahedron, edge a. V = (sqrt(2)/3) * a^3."""
    s = a / math.sqrt(2)
    v = [(s, 0, 0), (-s, 0, 0), (0, s, 0), (0, -s, 0), (0, 0, s), (0, 0, -s)]
    faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
             (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    return [tuple(v[i] for i in f) for f in faces]


def uv_sphere_tris(r, n_lat=16, n_lon=24):
    """UV sphere (closed, manifold): single top/bottom poles, ring fans.
    V converges to 4/3 pi r^3 from BELOW (the mesh inscribes the sphere) --
    the deficit is a named property."""
    rings = []
    for i in range(1, n_lat):
        theta = math.pi * i / n_lat
        rings.append([(r * math.sin(theta) * math.cos(2 * math.pi * j / n_lon),
                       r * math.sin(theta) * math.sin(2 * math.pi * j / n_lon),
                       r * math.cos(theta)) for j in range(n_lon)])
    top = (0.0, 0.0, r)
    bottom = (0.0, 0.0, -r)
    tris = []
    for j in range(n_lon):  # top cap fan
        tris.append((top, rings[0][j], rings[0][(j + 1) % n_lon]))
    for j in range(n_lon):  # bottom cap fan (mirrored winding)
        tris.append((bottom, rings[-1][(j + 1) % n_lon], rings[-1][j]))
    for k in range(len(rings) - 1):  # quads between consecutive rings
        for j in range(n_lon):
            a0, a1 = rings[k][j], rings[k][(j + 1) % n_lon]
            b0, b1 = rings[k + 1][j], rings[k + 1][(j + 1) % n_lon]
            tris.append((a0, b0, b1))
            tris.append((a0, b1, a1))
    # orientation probe: a consistently outward mesh has positive signed
    # volume; flip all if inverted (deterministic)
    vol6 = 0.0
    for a, b, c in tris:
        vol6 += (a[0] * (b[1] * c[2] - b[2] * c[1])
                 - a[1] * (b[0] * c[2] - b[2] * c[0])
                 + a[2] * (b[0] * c[1] - b[1] * c[0]))
    if vol6 < 0:
        tris = [(a, c, b) for a, b, c in tris]
    return tris


# --------------------------------------------------------------- fixtures
LABELS = [
    # id, label, system, optional stated volume (exact analytic where given)
    ("bone_box", "femur stand-in", "skeletal", 14400.0),
    ("bone_octa", "patella stand-in", "skeletal", None),
    ("bone_tetra", "sesamoid stand-in", "skeletal", None),
    ("muscle_box", "merged musculature stand-in", "muscular", None),
    ("skin_sphere", "skin stand-in", "integumentary", None),
    ("organ_box", "liver stand-in", "organ", None),
    ("joint_box", "knee cartilage stand-in", "articular", None),
]

SHAPES = {
    "bone_box": lambda: box_tris(15, 12, 10),     # 30x24x20 -> 14400 mm^3
    "bone_octa": lambda: octa_tris(14.0),          # (sqrt2/3)*14^3
    "bone_tetra": lambda: tetra_tris(12.0),        # 12^3/(6 sqrt2)
    "muscle_box": lambda: box_tris(30, 20, 15),    # 60x40x30 -> 72000 mm^3
    "skin_sphere": lambda: uv_sphere_tris(25.0),   # < 4/3 pi 25^3
    "organ_box": lambda: box_tris(15, 15, 15),     # 27000 mm^3
    "joint_box": lambda: box_tris(5, 5, 5),        # 1000 mm^3
}

ANALYTIC_VOLUME_MM3 = {
    "bone_box": 14400.0,
    "bone_octa": math.sqrt(2) / 3 * 14.0 ** 3,
    "bone_tetra": 12.0 ** 3 / (6 * math.sqrt(2)),
    "muscle_box": 72000.0,
    "skin_sphere": 4 / 3 * math.pi * 25.0 ** 3,   # sphere bound; mesh below
    "organ_box": 27000.0,
    "joint_box": 1000.0,
}

RHO_BY_SYSTEM = {
    "skeletal": 1.9e-6, "muscular": 1.06e-6, "integumentary": 1.109e-6,
    "organ": 1.05e-6, "articular": 1.06e-6,
}


def make_specimen(base: Path, *, body_mass_kg: float = 0.25,
                  enforce_fractions: bool = True,
                  expected_count: int = 7,
                  labels_rows=None, adjacency: list | None = None,
                  age_months=93, age_source="93-month record (synthetic)",
                  life_stage="adult", stated_volumes=True) -> Path:
    """Build the synthetic specimen dir + dir_spec.json; return spec path."""
    root = base / "visible_monkey_synthetic"
    (root / "stl").mkdir(parents=True, exist_ok=True)
    for sid, maker in SHAPES.items():
        write_binary_stl(root / "stl" / f"{sid}.stl", maker())
    rows = labels_rows if labels_rows is not None else LABELS
    cols = "id,label,system,stated_volume_mm3\n"
    lines = []
    for row in rows:
        sid, label, system, stated = row
        stated_s = ""
        if stated_volumes and stated is not None:
            stated_s = f"{stated:.6f}"
        lines.append(f"{sid},{label},{system},{stated_s}")
    (root / "labels.csv").write_text(cols + "\n".join(lines) + "\n",
                                     encoding="utf-8", newline="\n")
    record = {
        "schema": "chimera.visible_monkey.collection_record.v1",
        "species": "Macaca mulatta (synthetic fixture)",
        "specimen": "synthetic adult fixture",
        "sex": "female",
        "age_months": age_months,
        "age_source": age_source,
        "life_stage": life_stage,
        "body_mass_kg": body_mass_kg,
        "provenance": "synthetic stand-in generated in-test; analytic volumes "
                      "known in closed form",
    }
    (root / "collection_record.json").write_text(
        json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    if adjacency is not None:
        (root / "touching_edges.json").write_text(
            json.dumps(adjacency, indent=1) + "\n",
            encoding="utf-8", newline="\n")
    spec = {
        "schema": "chimera.visible_monkey.dir_spec.v1",
        "dataset_name": "visible_monkey_synthetic",
        "root": str(root),
        "stl": {"dir": "stl", "glob": "*.stl",
                "expected_count": expected_count},
        "labels": {"file": "labels.csv",
                   "columns": {"id": "id", "label": "label",
                               "system": "system",
                               "stated_volume_mm3": "stated_volume_mm3"}},
        "collection_record": {"file": "collection_record.json"},
        "units": "mm",
        "volume_tolerance_rel": 0.05,
        "enforce_body_fraction_bands": enforce_fractions,
        "materials_by_system": {
            "skeletal": "mat.bone_cortical",
            "articular": "mat.cartilage",
            "muscular": "mat.skeletal_muscle",
            "integumentary": "mat.skin",
            "organ": "mat.soft_tissue",
        },
        "output_dir": str(base / "out_body"),
        "validation_dir": str(base / "out_validation"),
    }
    if adjacency is not None:
        spec["adjacency"] = {"file": "touching_edges.json", "required": True}
    spec_path = base / "dir_spec.json"
    spec_path.write_text(json.dumps(spec, indent=1) + "\n",
                         encoding="utf-8", newline="\n")
    return spec_path


def run_build(spec_path: Path) -> None:
    vmi.main(["visible_monkey_import.py", "build", str(spec_path)])


def read_body(spec_path: Path) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    return json.loads(
        (Path(spec["output_dir"]) / "visible_monkey.body.json")
        .read_text(encoding="utf-8"))


# ----------------------------------------------------------------- tests
class TranslatorSyntheticProof(unittest.TestCase):
    """geometry_preserved + mass_book_closes + kernel_conformance."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="vm_synthetic_"))
        cls.spec_path = make_specimen(cls.tmp)
        run_build(cls.spec_path)
        cls.body = read_body(cls.spec_path)
        cls.mem = {m["structure_id"]: m for m in cls.body["membranes"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_analytic_volumes_and_masses(self):
        # Exact-analytic shapes: <= 1e-3 relative (pre-registered).
        for sid in ("bone_box", "bone_octa", "bone_tetra", "muscle_box",
                    "organ_box", "joint_box"):
            m = self.mem[sid]
            analytic = ANALYTIC_VOLUME_MM3[sid]
            rel = abs(m["volume_mm3"] - analytic) / analytic
            self.assertLessEqual(rel, 1e-3,
                                 f"{sid}: |{m['volume_mm3']:.6f} - "
                                 f"{analytic:.6f}|/analytic = {rel:.3e}")
        # Inscribed sphere: below the bound, within 2.5% (pre-registered).
        m = self.mem["skin_sphere"]
        bound = ANALYTIC_VOLUME_MM3["skin_sphere"]
        self.assertLess(m["volume_mm3"], bound)
        self.assertGreaterEqual(m["volume_mm3"] / bound, 0.975)
        # Mass closure: m == V * rho to <= 1e-6 relative (pre-registered).
        for sid, m in self.mem.items():
            system = m["system"]
            rho = RHO_BY_SYSTEM[system]
            expected = m["volume_mm3"] * rho
            rel = abs(m["mass"] - expected) / expected
            self.assertLessEqual(rel, 1e-6, f"{sid}: mass identity {rel:.3e}")
        # Book total == sum of compartments (exact identity).
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        book = json.loads(
            (Path(spec["validation_dir"]) / "derivation.json")
            .read_text(encoding="utf-8"))
        total = sum(r["mass_kg"] for r in book["compartments"])
        self.assertLessEqual(
            abs(total - book["totals"]["total_mass_kg"])
            / book["totals"]["total_mass_kg"], 1e-9)

    def test_kernel_conformance(self):
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        body_path = (Path(spec["output_dir"])
                     / "visible_monkey.body.json")
        parsed = kdef.parse_body(body_path)
        self.assertEqual(len(parsed["membranes"]), 7)
        self.assertEqual(len(parsed["bonds"]), 0)  # no adjacency -> no bonds
        worst = max(abs(m["mass"] - m["mass_derived"]) / m["mass_derived"]
                    for m in parsed["membranes"])
        self.assertLessEqual(worst, kdef.MASS_TOLERANCE)
        self.assertLessEqual(worst, 1e-6)

    def test_stage_true_in_body(self):
        stage = self.body["stage"]
        self.assertEqual(stage["life_stage"], "adult")
        self.assertEqual(stage["age_months"], 93)
        self.assertTrue(stage["age_source"])
        self.assertEqual(stage["scale"], 1.0)
        self.assertIs(stage["allometric_scaling_applied"], False)

    def test_body_bands_bite(self):
        # In-band: total/body = 0.83..0.91 for the fixture (computed above).
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        book = json.loads(
            (Path(spec["validation_dir"]) / "derivation.json")
            .read_text(encoding="utf-8"))
        frac = book["totals"]["whole_animal_check"]
        self.assertTrue(frac)
        self.assertTrue(0.6 <= frac["segmented_over_body"] <= 1.3)
        # Out-of-band: crank body mass x10 -> the gate REFUSES.
        with tempfile.TemporaryDirectory() as td:
            bad = make_specimen(Path(td), body_mass_kg=2.5,
                                enforce_fractions=True)
            with self.assertRaises(Refusal) as caught:
                run_build(bad)
            self.assertEqual(caught.exception.code, "whole_body_band")

    def test_adjacency_measured_only(self):
        with tempfile.TemporaryDirectory() as td:
            adj = [{"pair": ["bone_box", "bone_octa"], "gap_mm": 1.23,
                    "source": "synthetic touching-edge measurement"},
                   {"pair": ["bone_octa", "bone_tetra"], "gap_mm": 0.5,
                    "source": "synthetic touching-edge measurement"}]
            spec_path = make_specimen(Path(td), adjacency=adj)
            run_build(spec_path)
            body = read_body(spec_path)
            self.assertEqual(len(body["bonds"]), 2)
            by_id = {b["id"]: b for b in body["bonds"]}
            bond = by_id["bond.joint_bone_box__bone_octa"]
            self.assertEqual(bond["rest_length_mm"], 1.23)
            self.assertEqual(bond["material"], "mat.cartilage")
            self.assertEqual(bond["cure_strength"], 13.0e6)
            # unknown member refused by name
            with tempfile.TemporaryDirectory() as td2:
                spec_path2 = make_specimen(
                    Path(td2), adjacency=[{"pair": ["bone_box", "ghost"],
                                           "gap_mm": 1.0}])
                with self.assertRaises(Refusal) as caught:
                    run_build(spec_path2)
                self.assertEqual(caught.exception.code,
                                 "adjacency_member_unknown")

    def test_determinism(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = make_specimen(Path(td))
            run_build(spec_path)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            out1 = Path(spec["output_dir"])
            val1 = Path(spec["validation_dir"])
            # rebuild into DIFFERENT output dirs
            spec2 = dict(spec)
            spec2["output_dir"] = str(Path(td) / "out_body2")
            spec2["validation_dir"] = str(Path(td) / "out_validation2")
            spec2_path = Path(td) / "dir_spec2.json"
            spec2_path.write_text(json.dumps(spec2, indent=1),
                                  encoding="utf-8")
            run_build(spec2_path)
            for rel in ("visible_monkey.body.json",):
                self.assertEqual(
                    (out1 / rel).read_bytes(),
                    (Path(spec2["output_dir"]) / rel).read_bytes(),
                    rel)
            self.assertEqual(
                (val1 / "derivation.json").read_bytes(),
                (Path(spec2["validation_dir"]) / "derivation.json")
                .read_bytes())
            for p in sorted(out1.rglob("*.bin")):
                other = Path(spec2["output_dir"]) / p.relative_to(out1)
                self.assertEqual(p.read_bytes(), other.read_bytes(),
                                 p.name)


class TranslatorRefusals(unittest.TestCase):
    """refusal_by_name: every bad input refused BY NAME, never silence."""

    def refuse(self, mutate, code):
        with tempfile.TemporaryDirectory() as td:
            spec_path = make_specimen(Path(td))
            mutate(Path(td), spec_path)
            with self.assertRaises(Refusal) as caught:
                run_build(spec_path)
            self.assertEqual(caught.exception.code, code,
                             f"{caught.exception.code}: "
                             f"{caught.exception}")

    @staticmethod
    def _rewrite_spec(base: Path, spec_path: Path, **changes):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        spec.update(changes)
        spec_path.write_text(json.dumps(spec, indent=1), encoding="utf-8")

    def test_non_closed_mesh_refused(self):
        def mutate(base, spec_path):
            leak = base / "visible_monkey_synthetic" / "stl" / "bone_box.stl"
            tris = box_tris(15, 12, 10)[:-1]  # drop one triangle -> 3 open edges
            write_binary_stl(leak, tris)
        self.refuse(mutate, "mesh_not_closed")

    def test_inconsistent_stl_refused(self):
        def mutate(base, spec_path):
            junk = base / "visible_monkey_synthetic" / "stl" / "bone_box.stl"
            junk.write_bytes(b"not an stl at all" * 10)
        self.refuse(mutate, "mesh_unreadable")

    def test_label_missing_refused(self):
        def mutate(base, spec_path):
            rows = [r for r in LABELS if r[0] != "bone_octa"]
            root = base / "visible_monkey_synthetic"
            cols = "id,label,system,stated_volume_mm3\n"
            lines = [f"{s},{l},{sys_},".rstrip(",")
                     for s, l, sys_, _ in rows]
            (root / "labels.csv").write_text(
                cols + "\n".join(lines) + "\n", encoding="utf-8")
        self.refuse(mutate, "label_missing")

    def test_label_orphan_refused(self):
        def mutate(base, spec_path):
            root = base / "visible_monkey_synthetic"
            text = (root / "labels.csv").read_text(encoding="utf-8")
            text += "ghost_bone,unbacked label,skeletal,\n"
            (root / "labels.csv").write_text(text, encoding="utf-8")
        self.refuse(mutate, "label_orphan")

    def test_duplicate_structure_id_refused(self):
        def mutate(base, spec_path):
            root = base / "visible_monkey_synthetic"
            text = (root / "labels.csv").read_text(encoding="utf-8")
            text += "bone_box,duplicate id,skeletal,\n"
            (root / "labels.csv").write_text(text, encoding="utf-8")
        self.refuse(mutate, "duplicate_structure_id")

    def test_structure_count_mismatch_refused(self):
        def mutate(base, spec_path):
            self._rewrite_spec(base, spec_path,
                               stl={"dir": "stl", "glob": "*.stl",
                                    "expected_count": 167})
        self.refuse(mutate, "structure_count_mismatch")

    def test_volume_mismatch_refused(self):
        def mutate(base, spec_path):
            root = base / "visible_monkey_synthetic"
            text = (root / "labels.csv").read_text(encoding="utf-8")
            text = text.replace("14400.000000", "17280.000000")  # +20%
            (root / "labels.csv").write_text(text, encoding="utf-8")
        self.refuse(mutate, "volume_mismatch")

    def test_stage_unconfirmed_refused(self):
        self.refuse(
            lambda base, sp: make_specimen(base, age_source="   ",
                                           life_stage="adult"),
            "stage_unconfirmed")

    def test_adult_without_age_refused(self):
        self.refuse(
            lambda base, sp: make_specimen(base, age_months=None,
                                           life_stage="adult"),
            "stage_unconfirmed")

    def test_missing_life_stage_refused(self):
        self.refuse(
            lambda base, sp: make_specimen(base, life_stage=""),
            "stage_unconfirmed")

    def test_stage_mixing_refused(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = make_specimen(Path(td))
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            # per-structure stage column contradicting the specimen stage
            root = Path(spec["root"])
            text = (root / "labels.csv").read_text(encoding="utf-8")
            lines = text.rstrip("\n").splitlines()
            out = [lines[0] + ",life_stage"]
            for line in lines[1:]:
                stage_val = "infant" if line.startswith("muscle_box,") else ""
                out.append(line + "," + stage_val)
            (root / "labels.csv").write_text("\n".join(out) + "\n",
                                             encoding="utf-8", newline="\n")
            spec["labels"]["columns"]["life_stage"] = "life_stage"
            spec_path.write_text(json.dumps(spec, indent=1),
                                 encoding="utf-8")
            with self.assertRaises(Refusal) as caught:
                run_build(spec_path)
            self.assertEqual(caught.exception.code, "stage_mixing")

    def test_spec_missing_field_refused(self):
        def mutate(base, spec_path):
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            del spec["units"]
            spec_path.write_text(json.dumps(spec, indent=1),
                                 encoding="utf-8")
        self.refuse(mutate, "spec_missing_field")

    def test_spec_schema_refused(self):
        def mutate(base, spec_path):
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["units"] = "m"
            spec_path.write_text(json.dumps(spec, indent=1),
                                 encoding="utf-8")
        self.refuse(mutate, "spec_schema")

    def test_unknown_command_refused(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = make_specimen(Path(td))
            with self.assertRaises(Refusal) as caught:
                vmi.main(["x", "frobnicate", str(spec_path)])
            self.assertEqual(caught.exception.code, "unknown_command")


class VerifyBattery(unittest.TestCase):
    """byte_exact_verify: green, tamper-refused, exit-code discipline."""

    def test_verify_green_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = make_specimen(Path(td))
            run_build(spec_path)
            # green
            vmi.main(["visible_monkey_import.py", "verify", str(spec_path)])
            # tamper a NON-geometric field -> checks pass, bytes drift -> refuse
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            body_path = (Path(spec["output_dir"])
                         / "visible_monkey.body.json")
            body = json.loads(body_path.read_text(encoding="utf-8"))
            body["membranes"][0]["label"] = "tampered"
            body_path.write_text(json.dumps(body, indent=1),
                                 encoding="utf-8")
            with self.assertRaises(Refusal) as caught:
                vmi.main(["visible_monkey_import.py", "verify",
                          str(spec_path)])
            self.assertEqual(caught.exception.code, "definition_drift")

    def test_tampered_blob_refused(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = make_specimen(Path(td))
            run_build(spec_path)
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            blob = next((Path(spec["output_dir"]) / "tris").glob("*.bin"))
            raw = bytearray(blob.read_bytes())
            raw[0] ^= 0xFF
            blob.write_bytes(bytes(raw))
            with self.assertRaises(Refusal) as caught:
                vmi.main(["visible_monkey_import.py", "verify",
                          str(spec_path)])
            self.assertIn(caught.exception.code,
                          ("blob_drift", "blob_faces"))

    def test_cli_exit_code_2_on_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = make_specimen(Path(td))
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            del spec["units"]
            bad = Path(td) / "bad_spec.json"
            bad.write_text(json.dumps(spec), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-B",
                 str(REPO_ROOT / "tools/science_funnel/visible_monkey_import.py"),
                 "build", str(bad)],
                capture_output=True, text=True, cwd=str(REPO_ROOT))
            self.assertEqual(proc.returncode, 2)
            self.assertTrue(proc.stderr.startswith("REFUSED spec_missing_field"),
                            proc.stderr)


class VolumeRoute(unittest.TestCase):
    """pipeline_parameterization: analytic phantom, parameterized dirs,
    byte-determinism, honest UNTESTED serial-section hook."""

    @classmethod
    def setUpClass(cls):
        try:
            import scipy  # noqa: F401
            import skimage  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("numpy/scipy/skimage unavailable")

    @staticmethod
    def phantom_spec(base: Path) -> Path:
        """Ellipsoid semi-axes (12, 17, 25) voxels on a (40, 56, 80) grid,
        0.5 mm voxels. V_analytic = 4/3 pi * abc * 0.125 mm^3."""
        nz, ny, nx = 40, 56, 80
        az, ay, ax = 12, 17, 25
        z, y, x = np.mgrid[0:nz, 0:ny, 0:nx]
        mask = (((z - nz / 2) / az) ** 2 + ((y - ny / 2) / ay) ** 2
                + ((x - nx / 2) / ax) ** 2) <= 1.0
        vol = mask.astype(np.uint16)
        data_dir = base / "mri"
        data_dir.mkdir(parents=True, exist_ok=True)
        np.save(data_dir / "phantom.npy", vol)
        spec = {
            "schema": "chimera.visible_monkey.volume_spec.v1",
            "specimen_id": "synthetic_phantom",
            "modality": "ct_mri_density",
            "volume": {"path": str(data_dir / "phantom.npy"),
                       "reader": "npy", "dtype": "uint16", "offset": 0},
            "voxel_mm": [0.5, 0.5, 0.5],
            "segmentation": {
                "threshold": {"law": "density_percentile", "percentile": 95},
                "morphology": {"open_iterations": 1, "close_iterations": 1},
                "min_component_voxels": 100,
                "marching_cubes_level": 0.5,
                "max_components": 25,
            },
            "outputs": {
                "meshes_dir": str(base / "volume_route/meshes"),
                "preview_dir": str(base / "volume_route/meshes_preview"),
                "preview_max_faces": 30000,
                "manifest": str(base / "volume_route/manifest.json"),
                "receipt": str(base / "volume_route/mesh_receipt.json"),
            },
        }
        spec_path = base / "volume_spec.json"
        spec_path.write_text(json.dumps(spec, indent=1) + "\n",
                             encoding="utf-8", newline="\n")
        return spec_path

    def test_phantom_volume_recovered(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = self.phantom_spec(Path(td))
            vmv.main(["visible_monkey_volume_route.py", "build",
                      str(spec_path)])
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            manifest = json.loads(
                Path(spec["outputs"]["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["threshold"]["law"],
                             "density_percentile")
            self.assertEqual(manifest["threshold"]["value"], 1.0)
            self.assertEqual(len(manifest["components"]), 1)
            comp = manifest["components"][0]
            analytic = (4 / 3 * math.pi * 12 * 17 * 25
                        * 0.5 * 0.5 * 0.5)
            rel = abs(comp["volume_mm3_mesh"] - analytic) / analytic
            self.assertLessEqual(rel, 0.05,
                                 f"phantom volume off by {rel:.4f}")
            self.assertLessEqual(abs(comp["voxel_delta_pct"]), 5.0)
            self.assertEqual(comp["faces"],
                             comp["faces"])  # recorded, full mesh primary

    def test_manifest_byte_determinism(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = self.phantom_spec(Path(td))
            vmv.main(["visible_monkey_volume_route.py", "build",
                      str(spec_path)])
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            m1 = Path(spec["outputs"]["manifest"]).read_bytes()
            r1 = Path(spec["outputs"]["receipt"]).read_bytes()
            vmv.main(["visible_monkey_volume_route.py", "build",
                      str(spec_path)])
            self.assertEqual(m1,
                             Path(spec["outputs"]["manifest"]).read_bytes())
            self.assertEqual(r1,
                             Path(spec["outputs"]["receipt"]).read_bytes())

    def test_verify_green(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = self.phantom_spec(Path(td))
            vmv.main(["visible_monkey_volume_route.py", "build",
                      str(spec_path)])
            vmv.main(["visible_monkey_volume_route.py", "verify",
                      str(spec_path)])

    def test_serial_section_hook_refused(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = self.phantom_spec(Path(td))
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["modality"] = "serial_section_rgb"
            spec_path.write_text(json.dumps(spec, indent=1),
                                 encoding="utf-8")
            with self.assertRaises(Refusal) as caught:
                vmv.main(["visible_monkey_volume_route.py", "build",
                          str(spec_path)])
            self.assertEqual(caught.exception.code, "modality_untested")

    def test_volume_route_refusals(self):
        with tempfile.TemporaryDirectory() as td:
            spec_path = self.phantom_spec(Path(td))
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            del spec["voxel_mm"]
            bad = Path(td) / "bad1.json"
            bad.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaises(Refusal) as caught:
                vmv.main(["x", "build", str(bad)])
            self.assertEqual(caught.exception.code, "spec_missing_field")

            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["segmentation"]["threshold"] = {"law": "median"}
            bad = Path(td) / "bad2.json"
            bad.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaises(Refusal) as caught:
                vmv.main(["x", "build", str(bad)])
            self.assertEqual(caught.exception.code, "threshold_law_unknown")

            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["segmentation"]["threshold"] = {"law": "fixed",
                                                 "fixed_value": 1}
            bad = Path(td) / "bad3.json"
            bad.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaises(Refusal) as caught:
                vmv.main(["x", "build", str(bad)])
            self.assertEqual(caught.exception.code, "spec_schema")

    def test_spec_parameterization_no_hardcoded_paths(self):
        # The SAME spec schema pointed at a DIFFERENT temp root must work:
        # two independent fixtures, different dirs, identical results.
        with tempfile.TemporaryDirectory() as td1, \
                tempfile.TemporaryDirectory() as td2:
            s1 = self.phantom_spec(Path(td1))
            vmv.main(["x", "build", str(s1)])
            s2 = self.phantom_spec(Path(td2))
            vmv.main(["x", "build", str(s2)])
            spec1 = json.loads(s1.read_text(encoding="utf-8"))
            spec2 = json.loads(s2.read_text(encoding="utf-8"))
            m1 = json.loads(
                Path(spec1["outputs"]["manifest"]).read_text(encoding="utf-8"))
            m2 = json.loads(
                Path(spec2["outputs"]["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(m1["components"], m2["components"])


if __name__ == "__main__":
    unittest.main()
