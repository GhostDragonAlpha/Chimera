"""Focused unit tests for MAT2-F08's repeatable-loading vocabulary.

Fast: no capture frames, no full build, no fresh subprocesses. The scene is
loaded once per test class; every refusal is exercised through the public
strict loader (F01 prereg vocabulary).
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(CONTRIB.parent))

spec = importlib.util.spec_from_file_location("f08_impl", HERE / "implementation.py")
impl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(impl)

SCENE = None


def load_once():
    global SCENE
    if SCENE is None:
        SCENE = impl.load_scene()
    return SCENE


class ConfigurationIntake(unittest.TestCase):
    """The scene seed/configuration is strict: no defaults, named refusals."""

    def test_config_roundtrip_and_self_sha(self):
        cfg, raw = impl.load_config()
        self.assertEqual(cfg["schema"], impl.CONFIG_SCHEMA)
        self.assertEqual(cfg["self_sha256"], impl.config_self_sha(cfg))
        self.assertEqual(len(cfg["assets"]), len(impl.PINS))

    def test_missing_config_refuses(self):
        with self.assertRaises(impl.Refusal) as cm:
            impl.load_config(HERE / "no_such_configuration.json")
        self.assertEqual(cm.exception.code, "f08_config_missing")

    def test_tampered_self_sha_refuses(self):
        cfg, _ = impl.load_config()
        cfg["self_sha256"] = "0" * 64
        path = impl.SCRATCH / "t_test_tampered.json"
        impl.SCRATCH.mkdir(parents=True, exist_ok=True)
        path.write_bytes(impl.canonical(cfg))
        with self.assertRaises(impl.Refusal) as cm:
            impl.load_config(path)
        self.assertEqual(cm.exception.code, "f08_config_hash_mismatch")

    def test_missing_section_refuses(self):
        cfg, _ = impl.load_config()
        del cfg["collision_state"]
        cfg["self_sha256"] = impl.config_self_sha(cfg)
        path = impl.SCRATCH / "t_test_nosection.json"
        impl.SCRATCH.mkdir(parents=True, exist_ok=True)
        path.write_bytes(impl.canonical(cfg))
        with self.assertRaises(impl.Refusal) as cm:
            impl.load_config(path)
        self.assertEqual(cm.exception.code, "f08_config_missing_section")
        self.assertEqual(cm.exception.detail, "collision_state")

    def test_asset_dropped_from_config_refuses(self):
        cfg, _ = impl.load_config()
        cfg["assets"] = [a for a in cfg["assets"]
                         if a["id"] != "terrain_bundle_json"]
        cfg["self_sha256"] = impl.config_self_sha(cfg)
        path = impl.SCRATCH / "t_test_dropasset.json"
        impl.SCRATCH.mkdir(parents=True, exist_ok=True)
        path.write_bytes(impl.canonical(cfg))
        with self.assertRaises(impl.Refusal) as cm:
            impl.load_config(path)
        self.assertEqual(cm.exception.code, "f08_config_asset_set_mismatch")


class PinRefusals(unittest.TestCase):
    """Missing assets fail CLEARLY: the refusal names the asset (FB1/FB2)."""

    def test_missing_asset_named(self):
        sandbox = impl.build_sandbox("t_missing", drop="terrain_bundle_json")
        with self.assertRaises(impl.Refusal) as cm:
            impl.load_scene(sandbox_root=sandbox)
        self.assertEqual(cm.exception.code, "f08_pin_missing")
        self.assertIn("terrain_bundle_json", str(cm.exception.detail))

    def test_corrupt_bytes_named(self):
        sandbox = impl.build_sandbox("t_corrupt", corrupt="f03_trunk_mesh_json")
        with self.assertRaises(impl.Refusal) as cm:
            impl.load_scene(sandbox_root=sandbox)
        self.assertEqual(cm.exception.code, "f08_pin_hash_mismatch")
        self.assertIn("f03_trunk_mesh_json", str(cm.exception.detail))

    def test_complete_sandbox_materializes_production_state(self):
        scene = load_once()
        sandbox = impl.build_sandbox("t_full")
        clean = impl.load_scene(sandbox_root=sandbox)
        self.assertEqual(clean["scene_sha256"], scene["scene_sha256"])


class SeedReproduction(unittest.TestCase):
    """The seed drives the assets; the byte-equality check has teeth."""

    def test_regeneration_byte_exact(self):
        scene = load_once()
        regen = scene["scene_state"]["regeneration"]
        self.assertEqual(len(regen), 3)
        self.assertTrue(all(r["byte_equal"] for r in regen))

    def test_seed_plus_one_refuses(self):
        cfg, _ = impl.load_config()
        cfg["seeds"]["obstacle_placement"] = impl.SEED_OBSTACLES + 1
        cfg["self_sha256"] = impl.config_self_sha(cfg)
        path = impl.SCRATCH / "t_seedplus1.json"
        impl.SCRATCH.mkdir(parents=True, exist_ok=True)
        path.write_bytes(impl.canonical(cfg))
        with self.assertRaises(impl.Refusal) as cm:
            impl.load_scene(config_path=path)
        self.assertEqual(cm.exception.code, "f08_seed_reproduction_mismatch")


class ByteGate(unittest.TestCase):
    """The cross-instantiation gate detects a 1e-9 perturbation (FB5 teeth)."""

    def test_identical_states_pass(self):
        scene = load_once()
        self.assertIsNone(
            impl.compare_states(scene["scene_state_raw"],
                                scene["scene_state_raw"]))

    def test_1e9_spawn_perturbation_fires(self):
        scene = load_once()
        doc = json.loads(scene["scene_state_raw"])
        doc["initial_state"]["spawn_clearing_m"][2] += 1e-9
        diff = impl.compare_states(scene["scene_state_raw"],
                                   impl.canonical(doc))
        self.assertIsNotNone(diff)
        self.assertIn("initial_state", diff["differing_sections"])

    def test_substituted_pin_fires_fingerprint_gate(self):
        scene = load_once()
        doc = json.loads(scene["scene_state_raw"])
        doc["pins"]["terrain_bundle_json"] = {
            "published": "contributions/" + impl.PINS["terrain_bundle_json"]["rel"],
            "sha256": impl.sha_bytes(impl.canonical(impl.FB3_DEFAULT_TERRAIN_DOC)),
            "raw_match": False, "lenient_default": True}
        diff = impl.compare_states(scene["scene_state_raw"],
                                   impl.canonical(doc))
        self.assertIsNotNone(diff)
        self.assertIn("pins", diff["differing_sections"])

    def test_default_bytes_differ_from_real_pin(self):
        self.assertNotEqual(
            impl.sha_bytes(impl.canonical(impl.FB3_DEFAULT_TERRAIN_DOC)),
            impl.PINS["terrain_bundle_json"]["sha256"])


class Determinism(unittest.TestCase):
    """Canonical JSON and the materialized fingerprint are stable."""

    def test_canonical_idempotent(self):
        doc = {"b": [1.5, 2], "a": {"z": None, "y": True}, "c": "x"}
        once = impl.canonical(doc)
        self.assertEqual(once, impl.canonical(json.loads(once)))

    def test_scene_fingerprint_stable(self):
        first = load_once()
        second = impl.load_scene()
        self.assertEqual(first["scene_sha256"], second["scene_sha256"])

    def test_body_doc_deterministic(self):
        scene = load_once()
        body = scene["ground_body"]
        self.assertEqual(impl.canonical(impl.body_doc(body)),
                         impl.canonical(impl.body_doc(body)))


class DynamicsReproduction(unittest.TestCase):
    """The frozen schedule re-derives the published merged trace."""

    def test_trace_matches_published_bytes(self):
        scene = load_once()
        pub = (impl.CONTRIB /
               impl.REPRO_TARGETS["f07_contact_trace"]["rel"]).read_bytes()
        self.assertEqual(impl.sha_bytes(scene["trace_raw"]),
                         impl.sha_bytes(pub))

    def test_ledger_bar_on_every_run(self):
        scene = load_once()
        for run in scene["scene_state"]["dynamics"]["ledgers"]:
            self.assertTrue(run["within_bar"], run)
            self.assertLessEqual(run["worst_ledger_residual"], impl.LEDGER_BAR)


class RefusalVocabulary(unittest.TestCase):
    """Every refusal code is namespaced f08_ (no anonymous failures)."""

    def test_all_codes_prefixed(self):
        codes = set()

        def walk(v):
            if isinstance(v, dict):
                for k, vv in v.items():
                    if k == "code" and isinstance(vv, str):
                        codes.add(vv)
                    walk(vv)
            elif isinstance(v, (list, tuple)):
                for vv in v:
                    walk(vv)

        checks = json.loads((HERE / "evidence" / "checks.json").read_bytes())
        walk(checks["p0_intake_strict"]["refusal_codes"])
        for code in codes:
            self.assertTrue(code.startswith("f08_"), code)

    def test_declared_refusal_codes_are_f08_namespaced(self):
        for code in json.loads(
                (HERE / "evidence" / "checks.json").read_bytes()
        )["p0_intake_strict"]["refusal_codes"]:
            self.assertTrue(code.startswith("f08_"), code)


if __name__ == "__main__":
    unittest.main()
