"""test_implementation.py -- R5-forest-review-FOLLOWUP targeted tests.

FakeTransport CPU regressions for the four card scenarios + the endpoint and
labeling laws. Fixtures are labeled fixtures; no native acceptance is claimed
anywhere (asserted).
"""
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402

PINNED = {
    "clearing_self_pin": "aa2607df97e0d6ec",
    "terrain_self_pin": "8c7d60c88a75234a",
    "trunk_self_pin": "b7089e7826a221a5",
    "routes_self_pin": "7c3ad6e86039b633",
    "seed": 4598321,
    "extent_half_width_m": 20.0,
    "trunk_site_m": [11.976783, 2.471766],
}


class FakeTransport:
    def __init__(self, responses=None, fail=False):
        self.responses = responses or {}
        self.fail = fail
        self.calls = []

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if self.fail:
            raise ConnectionRefusedError("fixture: engine down")
        if path in self.responses:
            status, payload = self.responses[path]
            return status, payload
        raise FileNotFoundError("fixture: no response for " + path)


def base_config(**over):
    cfg = {
        "timeout_s": 1.0,
        "expected_health": {"ok": True, "world_booted": True},
        "scene_identity": {"field": "scene", "expected": "forest-one-clearing"},
        "collision_routes": [],              # today's documented truth
        "walking_prerequisites_open": True,
        "pinned_scene_identities": PINNED,
    }
    cfg.update(over)
    return cfg


class ReadinessRunnerTests(unittest.TestCase):
    def test_unavailable_engine(self):
        runner = impl.ReadinessRunner(base_config(), FakeTransport(fail=True))
        v = runner.run()
        self.assertEqual(v["verdict"], "NOT_READY")
        codes = [f["code"] for f in v["findings"]]
        self.assertIn("engine_unavailable", codes)
        self.assertLess(v["elapsed_seconds"], 5.0)

    def test_mismatched_scene_identity(self):
        transport = FakeTransport(responses={
            "/api/health": (200, {"ok": True, "world_booted": True}),
            "/api/status": (200, {"scene": "SOME-OTHER-SCENE"}),
        })
        v = impl.ReadinessRunner(base_config(), transport).run()
        mismatch = next(f for f in v["findings"]
                        if f["code"] == "scene_identity_mismatch")
        self.assertEqual(mismatch["expected"], "forest-one-clearing")
        self.assertEqual(mismatch["served"], "SOME-OTHER-SCENE")

    def test_missing_native_collision_named(self):
        transport = FakeTransport(responses={
            "/api/health": (200, {"ok": True, "world_booted": True}),
            "/api/status": (200, {"scene": "forest-one-clearing"}),
        })
        v = impl.ReadinessRunner(base_config(), transport).run()
        codes = [f["code"] for f in v["findings"]]
        self.assertIn("native_collision_route_missing", codes)
        self.assertIn("walking_open", codes)
        self.assertEqual(v["verdict"], "NOT_READY")

    def test_supported_responses_ready_but_labeled_fixture(self):
        transport = FakeTransport(responses={
            "/api/health": (200, {"ok": True, "world_booted": True}),
            "/api/status": (200, {"scene": "forest-one-clearing"}),
            "/api/collision_query": (200, {"h_m": 0.0, "inside": True}),
        })
        v = impl.ReadinessRunner(
            base_config(collision_routes=["/api/collision_query"],
                        extra_documented_endpoints=["/api/collision_query"],
                        walking_prerequisites_open=False),
            transport).run()
        self.assertEqual(v["verdict"], "READY")
        self.assertEqual(v["transport"], "injected-fixture")
        self.assertFalse(v["native_acceptance"])
        self.assertIn("NOT native acceptance", v["note"])

    def test_only_documented_or_configured_routes_probed(self):
        transport = FakeTransport(responses={
            "/api/health": (200, {"ok": True, "world_booted": True}),
            "/api/status": (200, {"scene": "forest-one-clearing"}),
        })
        runner = impl.ReadinessRunner(base_config(), FakeTransport(responses={
            "/api/health": (200, {"ok": True, "world_booted": True}),
            "/api/status": (200, {"scene": "forest-one-clearing"}),
        }))
        runner.run()
        for method, path in runner.requests:
            self.assertIn(path, runner.documented)
            self.assertIn(path, impl.DOCUMENTED_ENDPOINTS)

    def test_invented_endpoint_refused(self):
        class Sneaky(impl.ReadinessRunner):
            def run(self):                     # try to probe an invented route
                self._request("GET", "/totally/new/route")
                return {}
        with self.assertRaises(ValueError) as ctx:
            Sneaky(base_config(), FakeTransport()).run()
        self.assertIn("endpoint_not_documented", str(ctx.exception))

    def test_verdict_schema_and_pins_carried(self):
        transport = FakeTransport(responses={
            "/api/health": (200, {"ok": True, "world_booted": True}),
            "/api/status": (200, {"scene": "forest-one-clearing"}),
        })
        v = impl.ReadinessRunner(base_config(), transport).run()
        self.assertEqual(v["schema"], impl.SCHEMA)
        self.assertEqual(v["pinned_scene_identities"]["seed"], 4598321)
        self.assertEqual(v["pinned_scene_identities"]["extent_half_width_m"],
                         20.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
