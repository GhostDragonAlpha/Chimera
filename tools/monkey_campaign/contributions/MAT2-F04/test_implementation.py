"""MAT2-F04 frozen regression suite (offline, CPU-only, stdlib).

Runs against the committed implementation on the exact candidate revision.
The full build is exercised separately (`python -B implementation.py build`,
then `verify` for determinism); these tests pin the frozen identities,
refusals and falsifier forms without re-rendering the capture.
"""
from __future__ import annotations

import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import implementation as impl  # noqa: E402


def _assets():
    pins = impl.load_pins()
    tb, tq, lc = impl.load_modules(pins)
    bundle = tb.loads(
        (impl.CONTRIB / impl.PINS["terrain_bundle_json"]["rel"]).read_bytes())
    tb.validate_bundle(bundle)
    surface = tq.TerrainSurface(bundle, validate=False)
    trunk = json.loads(
        (impl.CONTRIB / impl.PINS["trunk_declaration_json"]["rel"]).read_bytes())
    groups, _ = impl.trunk_partition(trunk)
    tverts = [impl.to_contact(v[0:3])
              for v in trunk["render_mesh"]["vertices"]]
    impl.TRUNK_VERTS_CACHE = [tuple(v[0:3])
                              for v in trunk["render_mesh"]["vertices"]]
    ta = {"groups": groups, "vertices": tverts,
          "base": impl.to_contact(trunk["site"]["base_centre_m"]),
          "radius": trunk["geometry"]["radius_m"],
          "height": trunk["geometry"]["height_m"],
          "base_clearing": tuple(trunk["site"]["base_centre_m"]),
          "declaration": trunk}
    impl.BASE_APPROACH = ta["base"]
    return pins, tb, tq, lc, bundle, surface, trunk, groups, tverts, ta


class Pins(unittest.TestCase):
    def test_pins_hash_match(self):
        pins = impl.load_pins()
        self.assertTrue(all(p["raw_match"] for p in pins.values()))
        self.assertEqual(pins["local_contact_py"]["sha256"],
                         "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc")


class FrozenForms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.pins, cls.tb, cls.tq, cls.lc, cls.bundle, cls.surface,
         cls.trunk, cls.groups, cls.tverts, cls.ta) = _assets()

    def test_trunk_partition_is_center_vertex_rule(self):
        self.assertEqual([len(self.groups[k]) for k in
                          ("trunk_01.lateral", "trunk_01.base_cap",
                           "trunk_01.top_cap")], [64, 32, 32])

    def test_frame_map_round_trip(self):
        for p in ((0.0, 0.0, 0.0), (11.976783, 1.158, 2.471766),
                  (-19.3, 0.44, 17.2)):
            self.assertEqual(impl.to_clearing(impl.to_contact(p)), p)

    def test_combined_instantiation_refused_nonfinite_state(self):
        outcome = impl.combined_refusal_probe(
            self.lc, {"bundle": self.bundle}, self.ta)
        self.assertEqual(outcome["outcome"], "refused")
        self.assertIn("nonfinite_state", outcome["code"])

    def test_ground_crossing_ccd_on_is_pre_overlap_and_rests(self):
        sc = impl.scenario_g_high(self.lc, {"bundle": self.bundle},
                                  self.surface)
        firsts = impl.episode_firsts(sc["states"])
        self.assertTrue(firsts)
        self.assertEqual(firsts[0]["kind"], "ccd")
        self.assertGreater(firsts[0]["gap_m"], 0.0)
        worst = impl.metric_worst(sc["states"], "min_clearance_above_query_m")
        self.assertGreaterEqual(worst, -impl.PEN_BAR_M)
        probe = sc["probe"]
        seps = [v[2] - self.surface.height_at(v[0], -v[1])
                for v in probe.vertices]
        self.assertGreaterEqual(min(seps), impl.REST_LO_M)
        self.assertLessEqual(min(seps), impl.REST_HI_M)
        self.assertLessEqual(impl.lc_vlen(probe.velocity), impl.SPEED_BAR_M_S)

    def test_ground_crossing_ccd_off_control_tunnels(self):
        sc = impl.scenario_g_high(self.lc, {"bundle": self.bundle},
                                  self.surface, ccd=False)
        firsts = impl.episode_firsts(sc["states"])
        self.assertTrue(firsts)
        self.assertLess(firsts[0]["gap_m"], 0.0)
        self.assertGreater(-firsts[0]["gap_m"], impl.PEN_BAR_M)

    def test_trunk_crossing_ccd_on_never_enters_solid(self):
        sc = impl.scenario_t_cross(self.lc, self.ta)
        firsts = impl.episode_firsts(sc["states"])
        self.assertTrue(firsts)
        self.assertEqual(firsts[0]["kind"], "ccd")
        self.assertGreater(firsts[0]["gap_m"], 0.0)
        worst = impl.metric_worst(sc["states"], "min_radial_clearance_m")
        self.assertGreaterEqual(worst, -impl.PEN_BAR_M)

    def test_seam_high_phased_first_trunk_contact_is_pre_overlap_in_band(self):
        sc = impl.scenario_seam_high(self.lc, self.ta, self.surface)
        firsts = impl.episode_firsts(sc["states"])
        self.assertTrue(firsts)
        self.assertEqual(firsts[0]["kind"], "ccd")
        self.assertGreater(firsts[0]["gap_m"], 0.0)
        altitude = firsts[0]["point_clearing_a"][1]
        self.assertGreaterEqual(altitude, impl.SEAM_BAND_M[0])
        self.assertLessEqual(altitude, impl.SEAM_BAND_M[1])
        self.assertIsNotNone(sc["handover_tick"])

    def test_cap_rest_displaces_within_frozen_bar(self):
        sc = impl.scenario_trunk_top_rest(self.lc, self.ta)
        disp = max(st.get("max_displacement_m", 0.0)
                   for st in sc["states"])
        self.assertLessEqual(disp, impl.TRUNK_REST_DISP_BAR_M)
        cap_contact = any(
            "trunk_01.top_cap" in (c["surface_a"], c["surface_b"])
            for st in sc["states"] for c in st["contacts"])
        self.assertTrue(cap_contact)

    def test_all_falsifier_arms_bite(self):
        bites = impl.run_bites(self.lc, self.bundle, self.surface, self.ta)
        self.assertEqual(len(bites), 7)
        for row in bites:
            self.assertTrue(row["bites"], row["bite"])
            # house standard: every arm records its own clean control and
            # the bite is credited only when that control passes
            self.assertTrue(row["observed"].get("clean_control"),
                            row["bite"])
        fb4 = next(b for b in bites if b["bite"] == "FB4_ghost_support_trunk")
        # P1-scoped metric: the clean control (cap-centre vertices excluded)
        # is within the declared tolerance; the ghost's own gap violates it
        self.assertLess(
            fb4["observed"]["clean_control"]["worst_vertex_radial_gap_m"],
            impl.TRUNK_RADIAL_TOL_M)
        self.assertGreater(fb4["observed"]["worst_vertex_radial_gap_m"],
                           impl.TRUNK_RADIAL_TOL_M)

    def test_seam_high_records_per_phase_metrics(self):
        """Review law: a phase metric is never derived by scanning
        heterogeneous states; phase-B states carry BOTH metrics."""
        sc = impl.scenario_seam_high(self.lc, self.ta, self.surface)
        a = [st for st in sc["states"] if st.get("phase") == "A"]
        b = [st for st in sc["states"] if st.get("phase") == "B"]
        self.assertTrue(a)
        self.assertTrue(b)
        for st in a:
            self.assertIn("min_clearance_above_query_m", st)
            self.assertNotIn("min_radial_clearance_m", st)
        for st in b:
            self.assertIn("min_radial_clearance_m", st)
            self.assertIn("min_clearance_above_query_m", st)
        worst_b = impl.phase_metric(sc["states"], "B",
                                    "min_clearance_above_query_m")
        self.assertEqual(worst_b,
                         min(st["min_clearance_above_query_m"] for st in b))
        self.assertGreater(worst_b, 0.0)
        self.assertLess(worst_b, impl.SEAM_BAND_M[1])
        # heterogeneous scans refuse: phase A carries no radial metric and
        # no phase "C" exists
        with self.assertRaises(impl.Refusal):
            impl.phase_metric(sc["states"], "A", "min_radial_clearance_m")
        with self.assertRaises(impl.Refusal):
            impl.phase_metric(sc["states"], "C",
                              "min_clearance_above_query_m")

    def test_asset_identity_exact(self):
        trunk_raw = (impl.CONTRIB
                     / impl.PINS["trunk_declaration_json"]["rel"]).read_bytes()
        trunk = json.loads(trunk_raw)
        groups, _ = impl.trunk_partition(trunk)
        tverts = [impl.to_contact(v[0:3])
                  for v in trunk["render_mesh"]["vertices"]]
        p1 = impl.identity_checks(b"b", self.bundle, b"t", trunk, groups,
                                  tverts,
                                  impl.ground_contact_body(self.bundle,
                                                           self.lc),
                                  self.lc)
        self.assertTrue(p1["ground"]["arrays_exact_equal"])
        self.assertTrue(p1["trunk"]["arrays_exact_equal"])
        self.assertLessEqual(p1["trunk"]["worst_radial_gap_to_analytic_m"],
                             impl.TRUNK_RADIAL_TOL_M)
        self.assertTrue(p1["ok"])

    def test_subject_probe_lands_on_camera_facing_facet(self):
        import math
        cam = impl.Camera(impl.VIEW_SPECS["V2_seam_closeup"])
        sp = impl.trunk_subject_probe(cam, self.ta, 0.3)
        base = self.ta["base_clearing"]
        az = math.degrees(math.atan2(sp["point"][2] - base[2],
                                     sp["point"][0] - base[0])) % 360.0
        cam_az = math.degrees(math.atan2(cam.position[2] - base[2],
                                         cam.position[0] - base[0])) % 360.0
        # the probe's facet midpoint must face the camera hemisphere
        self.assertLess(min(abs(az - cam_az), 360.0 - abs(az - cam_az)),
                        90.0 + 11.25)
        mesh = impl.SceneMesh(self.bundle, self.trunk,
                              impl.TRUNK_VERTS_CACHE, self.groups)
        rec = impl.classify_marker(mesh, cam, sp)
        self.assertEqual(rec["outcome"], "VISIBLE_EXACT")


class CaptureRowOrder(unittest.TestCase):
    """Review F3 class kill: frame_bytes must feed the rawvideo pipe
    TOP-DOWN rows so a decoded video frame equals write_bmp's decoded
    orientation (the BMP container flips rows itself; the raw pipe does
    not). Pure stdlib -- runs without ffmpeg or a built capture."""

    def test_bmp_decode_equals_rawvideo_rows_identity(self):
        # asymmetric pattern so a flipped reading can never coincide
        colour = [[((37 * x + 101 * y) % 256, (91 * x + 5 * y) % 256,
                    (7 * x + 211 * y) % 256)
                   for x in range(impl.W)] for y in range(impl.H)]
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "probe.bmp"
            impl.write_bmp(path, colour)
            bmp = path.read_bytes()
        raw = impl.frame_bytes(colour)
        off = struct.unpack_from("<I", bmp, 10)[0]
        pad = (impl.W * 3 + 3) & ~3
        row_bytes = impl.W * 3
        # identity: BMP row H-1-y stores display row y; the raw pipe row y
        # must be the SAME display row, byte for byte
        for y in range(impl.H):
            from_bmp = bmp[off + (impl.H - 1 - y) * pad:
                           off + (impl.H - 1 - y) * pad + row_bytes]
            from_raw = raw[y * pad: y * pad + row_bytes]
            self.assertEqual(from_bmp, from_raw, "display row %d" % y)
        # sensitivity guard: reading the BMP top-down (the old bottom-up
        # bug) must NOT match, so this test still dies if the class returns
        from_bmp_flipped = bmp[off: off + row_bytes]
        from_raw_top = raw[0:row_bytes]
        self.assertNotEqual(from_bmp_flipped, from_raw_top)


class CaptureGate(unittest.TestCase):
    """The reviewer's capture gate, adopted permanently: decode the
    gate-bound video frames at the committed stills' indices and require
    pixel identity under the IDENTITY transform only, across the explicit
    transform list identity/vflip/hflip."""

    TRANSFORMS = ("identity", "vflip", "hflip")

    @classmethod
    def _read_bmp_rows(cls, path):
        raw = path.read_bytes()
        off = struct.unpack_from("<I", raw, 10)[0]
        w = struct.unpack_from("<i", raw, 18)[0]
        h = struct.unpack_from("<i", raw, 22)[0]
        pad = (w * 3 + 3) & ~3
        rows = []  # display row y (top-down) as bytes
        for y in range(h):  # BMP rows are stored bottom-up
            rows.append(raw[off + (h - 1 - y) * pad:
                            off + (h - 1 - y) * pad + w * 3])
        return rows

    @classmethod
    def _decode_frame_rows(cls, video, idx):
        cmd = ["ffmpeg", "-v", "error", "-i", str(video), "-vf",
               "select=eq(n\\,%d)" % idx, "-frames:v", "1",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        out = subprocess.run(cmd, capture_output=True, timeout=600)
        if out.returncode != 0:
            raise AssertionError("ffmpeg decode failed: %r"
                                 % out.stderr[-300:])
        pad = (impl.W * 3 + 3) & ~3
        need = pad * (impl.H - 1) + impl.W * 3
        if len(out.stdout) < need:
            raise AssertionError("short rawvideo frame: %d < %d"
                                 % (len(out.stdout), need))
        return [out.stdout[y * pad: y * pad + impl.W * 3]
                for y in range(impl.H)]

    @staticmethod
    def _hflip_row(row):
        rev = row[::-1]  # reversed pixels, channels per pixel reversed too
        out = bytearray(rev)
        for i in range(0, len(out), 3):
            out[i], out[i + 2] = out[i + 2], out[i]
        return bytes(out)

    @classmethod
    def _transform(cls, rows, kind):
        if kind == "identity":
            return rows
        if kind == "vflip":
            return rows[::-1]
        if kind == "hflip":
            return [cls._hflip_row(r) for r in rows]
        raise ValueError(kind)

    @classmethod
    def _diff_pixels(cls, a_rows, b_rows):
        diff = 0
        for ra, rb in zip(a_rows, b_rows):
            if ra != rb:
                diff += sum(1 for i in range(0, len(ra), 3)
                            if ra[i:i + 3] != rb[i:i + 3])
        return diff

    def test_stills_match_decoded_frames_identity_only(self):
        checks_path = HERE / "evidence" / "checks.json"
        video = (impl.ATTEMPT_WORKSPACE / impl.CAPTURE_DIR_NAME /
                 "mat2_f04_contact_motion.avi")
        if not (checks_path.is_file() and video.is_file()):
            self.skipTest("built capture not present; run "
                          "`python -B implementation.py build` first")
        checks = json.loads(checks_path.read_bytes())
        ticks = {k: v["ticks"]
                 for k, v in checks["scenario_summary"].items()}
        firsts = {k: v["first_contact_tick"]
                  for k, v in checks["scenario_summary"].items()}
        # row windows from the SAME frozen plan the build encodes
        windows = {}
        offset = 0
        for plan_row in impl.ROW_PLAN:
            n = sum(len(rng) if rng is not None else ticks[sname]
                    for sname, rng in plan_row[2])
            windows["%s_%s" % (plan_row[0], plan_row[1])] = (offset,
                                                             offset + n)
            offset += n
        self.assertEqual(offset, checks["capture"]["frames"])
        for vname, mode in [(v, m) for v in impl.VIEW_ORDER
                            for m in ("diagnostic", "clean")]:
            sname, _ = impl.STILL_OF[vname]
            seg = next(p for p in impl.ROW_PLAN
                       if p[0] == vname and p[1] == mode)
            before = 0
            for sname2, rng in seg[2]:
                if sname2 == sname:
                    break
                before += len(rng) if rng is not None else ticks[sname2]
            idx = windows["%s_%s" % (vname, mode)][0] + before + firsts[sname]
            still = self._read_bmp_rows(
                HERE / "evidence" / ("frame_%s_%s.bmp" % (vname, mode)))
            frame = self._decode_frame_rows(video, idx)
            diffs = {kind: self._diff_pixels(still,
                                             self._transform(frame, kind))
                     for kind in self.TRANSFORMS}
            self.assertEqual(
                diffs["identity"], 0,
                "%s still vs decoded frame %d matches only under %s "
                "(diffs %s) -- capture row order is broken"
                % (vname, idx, min(diffs, key=diffs.get), diffs))


if __name__ == "__main__":
    unittest.main()
