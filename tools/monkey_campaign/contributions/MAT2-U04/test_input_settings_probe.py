"""test_input_settings_probe.py -- MAT2-U04 candidate unit tests.

Pure-function checks of the probe/builder helpers plus the committed-evidence
binding. CPU-only, headless, deterministic; run:

    python -B -m unittest test_input_settings_probe -v
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import input_settings_probe as P          # noqa: E402  (asserts pins at import)
import capture_build_settings as B        # noqa: E402
from tools.monkey_campaign.product import input_settings as IS   # noqa: E402
from tools.monkey_campaign.product import input_mapper as IM     # noqa: E402


def quat_rotate(q, v):
    """Rotate vector v by unit quaternion q=(w,x,y,z)."""
    w, x, y, z = q
    u = (x, y, z)
    uv = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
          u[0] * v[1] - u[1] * v[0])
    uuv = (u[1] * uv[2] - u[2] * uv[1], u[2] * uv[0] - u[0] * uv[2],
           u[0] * uv[1] - u[1] * uv[0])
    return tuple(v[i] + 2.0 * (w * uv[i] + uuv[i]) for i in range(3))


class QuatTests(unittest.TestCase):
    EYE, TARGET = (0.0, 1.4, -3.0), (0.0, 0.5, 0.0)

    def test_forward_axis(self):
        q = B.quat_wxyz_camera_to_frame(self.EYE, self.TARGET)
        f = quat_rotate(q, (0.0, 0.0, 1.0))
        raw = tuple(self.TARGET[i] - self.EYE[i] for i in range(3))
        n = math.sqrt(sum(c * c for c in raw))
        want = tuple(c / n for c in raw)
        for a, b in zip(f, want):
            self.assertAlmostEqual(a, b, places=12)

    def test_up_axis(self):
        q = B.quat_wxyz_camera_to_frame(self.EYE, self.TARGET)
        up = quat_rotate(q, (0.0, 1.0, 0.0))
        self.assertGreater(up[1], 0.9)          # world up dominates
        self.assertAlmostEqual(abs(math.hypot(*q)), 1.0, places=12)

    def test_right_axis_right_handed(self):
        q = B.quat_wxyz_camera_to_frame(self.EYE, self.TARGET)
        right = quat_rotate(q, (1.0, 0.0, 0.0))
        f = quat_rotate(q, (0.0, 0.0, 1.0))
        up = quat_rotate(q, (0.0, 1.0, 0.0))
        cross = (up[1] * f[2] - up[2] * f[1], up[2] * f[0] - up[0] * f[2],
                 up[0] * f[1] - up[1] * f[0])
        for a, b in zip(right, cross):          # right == up x forward
            self.assertAlmostEqual(a, b, places=9)


class ProjectionTests(unittest.TestCase):
    def test_forward_point_projects_to_center(self):
        eye, target = (0.0, 1.4, -3.0), (0.0, 0.5, 0.0)
        axes = B.basis(eye, target)
        n = math.dist(eye, target)
        z = tuple((target[i] - eye[i]) / n for i in range(3))
        p = [eye[i] + z[i] * n for i in range(3)]
        pt = B.project(p, eye, axes)
        self.assertAlmostEqual(pt[0], B.W / 2.0, places=9)
        self.assertAlmostEqual(pt[1], B.H / 2.0, places=9)

    def test_behind_near_returns_none(self):
        eye = (0.0, 1.4, -3.0)
        axes = B.basis(eye, (0.0, 0.5, 0.0))
        behind = tuple(eye[i] - axes[2][i] * 1.0 for i in range(3))
        self.assertIsNone(B.project(behind, eye, axes))


class MapperLawTests(unittest.TestCase):
    def test_clamp_matches_real_mapper(self):
        for s, invert, counts in ((IS.default_settings().sensitivity, False, 5),
                                  (0.008, False, 5),
                                  (IS.SENS_YAW_MAX_RAD_PER_COUNT, False, 5),
                                  (IS.SENS_YAW_MAX_RAD_PER_COUNT, True, 5),
                                  (IS.SENS_YAW_MAX_RAD_PER_COUNT, True, 2)):
            vec = IS.InputSettings(dict(IM.DEFAULT_BINDINGS), s, invert)
            mapper = IS.configured_mapper(IM.MockSink(), vec)
            mapper.press("W", 0)
            mapper.mouse(counts)
            recs = mapper.tick(50)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0].yaw_rate, P.clamp(counts, vec.signed_sensitivity()))

    def test_replay_law_matches_real_mapper(self):
        events = []
        real = P.run_replay(P.s4_vector(), events)
        want = P.replay_law_records(P.s4_vector())
        self.assertEqual(len(real), len(want))
        self.assertEqual(len(real), 10)
        for got, w in zip(real, want):
            self.assertEqual(got["yaw_rate"], w["yaw_rate"])
            self.assertEqual(got["v_forward"], w["v_forward"])
            self.assertEqual(got["issued_tick"], w["issued_tick"])

    def test_settings_vector_laws(self):
        s4 = P.s4_vector()
        self.assertEqual(s4.signed_sensitivity(),
                         -IS.SENS_YAW_MAX_RAD_PER_COUNT)
        self.assertTrue(s4.bindings["A"], "turn_right")
        self.assertEqual(IS.SENS_YAW_MAX_RAD_PER_COUNT,
                         IM.OMEGA_MAX_RAD_S * IM.INTERVAL_MS / 1000.0)


class HelperTests(unittest.TestCase):
    def test_bindings_digest_stable(self):
        b = {"W": "forward", "A": "turn_left"}
        self.assertEqual(P.bindings_digest(b), P.bindings_digest(dict(reversed(list(b.items())))))

    def test_records_equal(self):
        a = {"v_forward": 1.0, "yaw_rate": 0.0, "issued_tick": 3,
             "source": "s", "record_version": 1}
        b = dict(a)
        self.assertTrue(P.records_equal(a, b))
        b["yaw_rate"] = -0.0
        self.assertTrue(P.records_equal(a, b))   # -0.0 == 0.0 numerically
        b["issued_tick"] = 4
        self.assertFalse(P.records_equal(a, b))

    def test_mouse_window_phases(self):
        self.assertEqual(P.mouse_window(250), 5)
        self.assertEqual(P.mouse_window(8450), 5)
        self.assertEqual(P.mouse_window(8460), 0)
        self.assertEqual(P.mouse_window(9000), 5)      # cancel window
        self.assertEqual(P.mouse_window(13500), 0)     # save tick: no mouse
        self.assertTrue(P.in_cancel_window(9000))
        self.assertFalse(P.in_cancel_window(9500))


class EvidenceBindingTests(unittest.TestCase):
    """The committed evidence must agree with the frozen contracts."""

    def test_numerical_receipt_green_and_bound(self):
        d = json.loads((HERE / "evidence/numerical_receipt.json")
                       .read_text(encoding="utf-8"))
        self.assertTrue(d["all_green"])
        self.assertEqual(d["task_id"], "U04")
        self.assertEqual(d["criteria_sha256"],
                         "192ca43f061c4b6b2763d11213e0246ea075c3f62e6948948ba8c64213bf5180")
        self.assertEqual(d["subject_sha256"], P.SUBJECT_SHA256)

    def test_trace_rows_and_hash_bound(self):
        raw = (HERE / "evidence/trace.jsonl").read_bytes()
        rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l]
        self.assertEqual(len(rows), 391)
        d = json.loads((HERE / "evidence/numerical_receipt.json")
                       .read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), d["trace"]["sha256"])

    def test_manifest_identity_envelope(self):
        m = json.loads((HERE / "evidence/capture_manifest.json")
                       .read_text(encoding="utf-8"))
        self.assertEqual(m["schema"], "chimera.visual_capture_manifest.v1")
        self.assertEqual(m["task_id"], "U04")          # the CONTRACT task id
        self.assertNotEqual(m["task_id"], "MAT2-U04")  # never the card id
        self.assertEqual(m["profile_id"], "controls")
        self.assertEqual(m["tick_interval"], [0, 390])
        self.assertEqual(len(m["views"]), 6)
        trace_sha = hashlib.sha256(
            (HERE / "evidence/trace.jsonl").read_bytes()).hexdigest()
        for row in m["views"]:
            self.assertEqual(row["state_binding"]["sha256"], trace_sha)
            self.assertEqual(row["state_binding"]["kind"], "trace")

    def test_capture_receipt_bitexact_and_gate(self):
        c = json.loads((HERE / "evidence/capture_receipt.json")
                       .read_text(encoding="utf-8"))
        self.assertTrue(c["bitexact_proof"]["equal"])
        self.assertEqual(c["bitexact_proof"]["capture_a_sha256"],
                         c["bitexact_proof"]["capture_b_sha256"])
        self.assertTrue(c["validation"]["visual_gate.verify"]["structurally_valid"])
        m = json.loads((HERE / "evidence/capture_manifest.json")
                       .read_text(encoding="utf-8"))
        self.assertEqual(m["capture_sha256"], c["video"]["sha256"])

    def test_card_task_contract(self):
        c = json.loads((HERE / "card_task.json").read_text(encoding="utf-8"))
        self.assertEqual(c["task_id"], "U04")
        self.assertEqual(c["task"]["verification_profile"]["kind"], "motion")
        self.assertEqual(c["definition_raw_sha256"],
                         "57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1")

    def test_records_leg_snapshot_hashes(self):
        rl = HERE / "records_leg/ONT-U04"
        runner = rl / "run_falsifiers.py"
        self.assertEqual(
            hashlib.sha256(runner.read_bytes()).hexdigest(),
            "3a6784952b92455857eea6b50e8e293182e95f954e9964380aecd7b487eef996")
        ref = (rl / "reference/tools/monkey_campaign/product/input_settings.py"
               ).read_bytes()
        self.assertEqual(hashlib.sha256(ref).hexdigest(), P.SUBJECT_SHA256)
        out = json.loads((HERE / "evidence/records_leg_rerun.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual(out["outcome"], "GREEN")
        self.assertEqual(out["pass_fail_counts"], {"pass": 33, "fail": 0})


if __name__ == "__main__":
    unittest.main()
