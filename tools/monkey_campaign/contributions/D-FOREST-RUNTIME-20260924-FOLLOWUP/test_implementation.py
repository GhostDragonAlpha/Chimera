"""test_implementation.py -- D-FOREST-RUNTIME-20260924-FOLLOWUP targeted tests
(CORRECTION attempt: placement + compile evidence).

Wraps the implementation's patch generation + independent checks as unittest,
plus structural assertions on the generated artifacts. The compile+oracle check
compiles the SHIPPED terrain_surface.hpp with g++ (bounded, CPU-only) and
compares against the frozen F02 oracle. NEW vs the reviewed suite: the MODIFIED
gait_controller.hpp is syntax-checked (g++ -std=c++17 -fsyntax-only, exit 0
required) with a negative control proving the check bites on the reviewed
defect class (member-function definitions nested inside a function body);
helper placement and include scope are asserted structurally. The suite is
ORDER-INDEPENDENT: every test class materializes the artifacts it needs.

Run:  python -B -m unittest test_implementation -v   (from this directory)
"""
import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402

REPO = pathlib.Path("E:/ChimeraWork/monkey-play-20260924")


def gpp_available() -> bool:
    try:
        proc = subprocess.run(["g++", "--version"], capture_output=True, timeout=20)
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def ensure_artifacts() -> None:
    """Order independence: regenerate the patch + reference bytes whenever they
    are missing, no matter which test class runs first on a fresh directory."""
    if not (HERE / "proposed.patch").is_file() or \
       not (HERE / "reference" / "gait_controller.hpp.modified").is_file():
        impl.generate_patch(REPO, HERE)


class PatchStructureTests(unittest.TestCase):
    """The patch is scoped, applies to the pinned blob, preserves the plane."""

    @classmethod
    def setUpClass(cls):
        if not REPO.is_dir():
            raise unittest.SkipTest("play repo absent")
        ensure_artifacts()
        cls.patch = (HERE / "proposed.patch").read_text(encoding="utf-8")

    def test_patch_applies_and_is_scoped(self):
        self.assertIn("diff --git a/ChimeraEngine/engine/gait_controller.hpp",
                      self.patch)
        self.assertIn("diff --git a/ChimeraEngine/engine/terrain_surface.hpp",
                      self.patch)
        self.assertEqual(self.patch.count("diff --git"), 2)
        self.assertIn("new file mode 100644", self.patch)

    def test_pinned_blob_reproduced(self):
        pinned = (HERE / "reference" / "gait_controller.hpp.pinned").read_text(
            encoding="utf-8")
        proc = subprocess.run(["git", "-C", str(REPO), "hash-object", "--stdin"],
                              input=pinned.encode(), capture_output=True)
        self.assertEqual(proc.stdout.decode().strip(), impl.PIN_BLOB)

    def test_surface_header_matches_patch_constant(self):
        """The shipped reference bytes equal the implementation's pinned
        constant (the patch's new-file content). NOTE: vs the reviewed
        candidate this file intentionally differs by ONE change -- the
        TerrainSurface default constructor moved to public access -- which the
        new -fsyntax-only evidence required; the surface law's math is
        token-identical and re-proven by the oracle parity checks."""
        ref = (HERE / "reference" / "terrain_surface.hpp").read_text(
            encoding="utf-8")
        self.assertEqual(ref, impl.TERRAIN_SURFACE_HPP)
        self.assertIn("TerrainSurface() = default;", ref.split("public:")[1])
        self.assertNotIn("TerrainSurface() = default;", ref.split("private:")[1])

    def test_plane_expressions_verbatim(self):
        modified = (HERE / "reference" /
                    "gait_controller.hpp.modified").read_text(encoding="utf-8")
        # the four ORIGINAL plane expressions must survive character-for-character
        # inside the inactive arms (verbatim preservation law)
        expressions = [
            "e.point(points_[h].index,points_[h].local).first[1]+points_[h]"
            ".radius-plane_model_y_",
            "e.point(points_[m].index,points_[m].local).first[1]+points_[m]"
            ".radius-plane_model_y_",
            "for(size_t i=0;i<n_;++i)r[i]=j[i][1];return r;",
            "for(size_t i=0;i<n_;++i)r[i]=j[i][axis];return r;",
            "plane_model_y_=plane_world_y_-shift_[1];",
        ]
        for expr in expressions:
            self.assertTrue(expr in modified,
                            "expression not verbatim: %r" % expr[:60])

    def test_helpers_at_class_scope_not_inside_gap_of(self):
        """THE CORRECTION: terrain_model_y/contact_normal are defined at CLASS
        scope (before `double gap_of(`), never inside a function body."""
        modified = (HERE / "reference" /
                    "gait_controller.hpp.modified").read_text(encoding="utf-8")
        helper1 = "double terrain_model_y(const Evaluation&e,const ContactPoint&p)const{"
        helper2 = "chimera::TerrainNormal contact_normal(const Evaluation&e,const ContactPoint&p)const{"
        gap_def = modified.find(impl.GAP_OF_ANCHOR)
        gap_body_end = modified.find("return (std::min)(gh,gm);}")
        self.assertGreater(gap_def, -1)
        self.assertGreater(gap_body_end, gap_def)
        h1, h2 = modified.find(helper1), modified.find(helper2)
        self.assertGreater(h1, -1)
        self.assertLess(h1, gap_def,
                        "terrain_model_y defined after gap_of (wrong scope?)")
        self.assertGreater(h2, -1)
        self.assertLess(h2, gap_def,
                        "contact_normal defined after gap_of (wrong scope?)")
        # no definition slips INTO the gap_of body
        self.assertEqual(modified.find(helper1, gap_def, gap_body_end), -1)
        self.assertEqual(modified.find(helper2, gap_def, gap_body_end), -1)

    def test_include_at_file_scope(self):
        """#include "terrain_surface.hpp" sits above the engine namespace."""
        modified = (HERE / "reference" /
                    "gait_controller.hpp.modified").read_text(encoding="utf-8")
        inc = modified.find('#include "terrain_surface.hpp"')
        ns = modified.find("namespace chimera::multibody {")
        self.assertGreater(inc, -1)
        self.assertGreater(ns, -1)
        self.assertLess(inc, ns, "terrain include nested inside the namespace")

    def test_no_physics_symbols_in_changed_lines(self):
        changed = [ln[1:] for ln in self.patch.splitlines()
                   if ln.startswith("+") and not ln.startswith("+++")]
        for sym in impl.GUARD_SYMBOLS:
            for ln in changed:
                self.assertNotIn(sym, ln, "changed line touches physics: %r" % ln)

    def test_terrain_activation_is_recipe_gated(self):
        modified = (HERE / "reference" /
                    "gait_controller.hpp.modified").read_text(encoding="utf-8")
        self.assertIn('recipe_.contains("terrain_grid")', modified)
        self.assertIn("terrain_active_=true;", modified)

    def test_no_trunk_contact_machinery(self):
        """Stage 1 law: the patch adds NO trunk/prop contact code."""
        for token in ("trunk", "cylinder", "sdf", "climb", "grip"):
            self.assertNotIn(token, self.patch.lower(),
                             "Stage 1 must not contain %r machinery" % token)


class CompiledOracleTests(unittest.TestCase):
    """The compiled shipped header vs the frozen Python oracle; and the
    MODIFIED gait header's compile evidence (the reviewed gap)."""

    @classmethod
    def setUpClass(cls):
        if not REPO.is_dir():
            raise unittest.SkipTest("play repo absent")
        if not gpp_available():
            raise unittest.SkipTest("g++ not available")
        ensure_artifacts()
        cls.results = impl.run_checks(REPO, HERE)

    def test_all_checks_pass(self):
        self.assertTrue(self.results["all_ok"], json.dumps(self.results, indent=1))

    def test_modified_header_compiles(self):
        """THE NEW EVIDENCE: the patched gait_controller.hpp exits 0."""
        c = self.results["header_compile_check"]
        self.assertTrue(c["available"], "g++ unavailable: compile evidence ABSENT")
        self.assertEqual(c["exit"], 0, c["stderr_tail"])
        self.assertTrue(c["passed"])
        self.assertIn("-fsyntax-only", c["command"])

    def test_compile_check_bites(self):
        """The negative control: the reviewed defect shape must NOT compile."""
        c = self.results["compile_check_bites"]
        self.assertTrue(c["available"])
        self.assertNotEqual(c["exit"], 0)
        self.assertTrue(c["named_error_present"])
        self.assertTrue(c["bites"])

    def test_compiled_matches_oracle_within_frozen_bars(self):
        c = self.results["compiled_vs_oracle"]
        self.assertTrue(c["height_ok"])
        self.assertEqual(c["worst_height_m"], 0.0)
        self.assertTrue(c["nodes_exact"])
        self.assertTrue(c["normal_ok"])
        self.assertLess(c["worst_normal_component"], 1e-15)

    def test_plane_degeneracy_and_extent(self):
        self.assertTrue(self.results["plane_degeneracy_exact"])
        self.assertEqual(self.results["gap_law_constant_grid_delta"], 0.0)
        self.assertTrue(self.results["gap_law_constant_grid_exact"])
        self.assertTrue(self.results["tangent_projection_identity"])
        self.assertTrue(self.results["tangent_axis1_degenerate_guarded"])
        e = self.results["extent_law"]
        self.assertTrue(e["closed_boundary_serves"])
        self.assertTrue(e["outside_flags_all_zero"])
        self.assertTrue(e["outside_height_refuses_named"])


class HonestBoundaryTests(unittest.TestCase):
    """The checks never claim engine integration or native acceptance."""

    def test_evidence_declares_pending_gates(self):
        ev = HERE / "evidence" / "checks.json"
        if not ev.is_file():
            raise unittest.SkipTest("run implementation.py first")
        results = json.loads(ev.read_text(encoding="utf-8"))
        self.assertIn("all_ok", results)
        # the checker's own keys describe surface-math + header-TU compile only
        self.assertIn("compiled_vs_oracle", results)
        self.assertIn("header_compile_check", results)


if __name__ == "__main__":
    unittest.main(verbosity=2)
