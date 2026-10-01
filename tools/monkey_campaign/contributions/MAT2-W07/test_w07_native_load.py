#!/usr/bin/env python3
"""MAT2-W07 named-check suite (prereg section 8).

Every FB arm carries a clean control AND a bite: the detector must stay
green on the clean run and must FIRE on the tampered input (a falsifier
that cannot fail is refused by the house standard). The heavy shared
fixture (pin-verify -> gate -> load -> execute) runs ONCE per suite and is
cached; everything else is pure arithmetic on the cached objects and the
emitted receipt.
"""
from __future__ import annotations

import ast
import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi            # noqa: E402
import run_native_load as rnl         # noqa: E402

RELATION_KEYS = rnl.RELATION_KEYS

_FIXTURE = {}


def fixture():
    """The clean pipeline, run once: pins -> validator -> gate -> load ->
    execute. The load ORDER itself is under test (test_02 ordering)."""
    if _FIXTURE:
        return _FIXTURE
    pins, reg = rnl.stage_pins()
    cert = vi.w04_certificate()
    rnl.validate_certificate(cert)
    req, allow, bundle, build_id, params = rnl.gate_and_load(cert)
    res, anchors = rnl.execute(bundle, build_id, params)
    _FIXTURE.update(pins=pins, reg=reg, cert=cert, req=req, allow=allow,
                    bundle=bundle, build_id=build_id, params=params,
                    res=res, anchors=anchors)
    return _FIXTURE


def verdict_for(key, reproduced, frozen):
    """The anchor comparator, isolated so the bite can prove it fails."""
    return {"frozen": frozen, "reproduced": reproduced,
            "verdict": "EXACT" if reproduced == frozen else "DRIFT"}


def bounds_ok(applied_rows, lo, hi):
    eps = 1e-6
    return all(all(l - eps <= c <= h + eps
                   for c, l, h in zip(applied, lo, hi))
               for applied in applied_rows)


def named_missing_present(block):
    """The FB6 presence detector: all four N-records with the verbatim
    certificate prerequisite strings carried in N1/N2."""
    keys = ("N1_adopted_assembly_scene_module", "N2_tc3_drive_table",
            "N3_product_engine_live_control_path", "N4_c09_anchors")
    if not all(k in block for k in keys):
        return False
    return ("runtime scene module executing the adopted assembly"
            in block["N1_adopted_assembly_scene_module"]
            ["certificate_declaration"]
            and "TC-3" in block["N2_tc3_drive_table"]["certificate_declaration"])


def structural_scan(paths):
    """FB7: the contribution launches no engine/simulation/training process;
    the only subprocess module in the whole contribution is run_capture.py
    (the declared ffmpeg capture-tool calls)."""
    violations = []
    for path in paths:
        tree = ast.parse(path.read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    if name == "subprocess" and path.name != "run_capture.py":
                        violations.append("subprocess:" + path.name)
                    if name == "socket":
                        violations.append("socket:" + path.name)
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                if root == "socket":
                    violations.append("socket:" + path.name)
        source = path.read_bytes()
        engine_needle = b"chimera" b"_engine"   # not matched in this file
        if engine_needle in source:
            violations.append("engine-ref:" + path.name)
    return violations


class Test01CleanPipeline(unittest.TestCase):
    """The clean control: the emitted receipt is green end to end."""

    def test_receipt_green(self):
        fx = fixture()
        raw = (HERE / "receipts" / "native_load_receipt.json").read_bytes()
        receipt = json.loads(raw.decode("utf-8"))
        self.assertEqual(receipt["load"]["deploy_decision"], "ALLOW")
        self.assertEqual(receipt["load"]["trained_bundles_loaded"], 0)
        for key, row in receipt["execution"]["anchor_comparisons"].items():
            self.assertEqual(row["verdict"], "EXACT", key)
        cons = receipt["contract_consumption"]
        self.assertEqual(cons["recipe_mismatch_ticks"], [])
        self.assertEqual(cons["decision_ticks"], 60)
        self.assertEqual(cons["masked_channels_mean_filled_violations"], 0)
        self.assertEqual(cons["limiter_saturation_report_mismatches"], 0)
        self.assertTrue(all(cons["bars"].values()))
        dep = receipt["deploy_discrimination"]
        self.assertEqual(dep["matching_tuple"]["decision"], "ALLOW")
        for k in ("foreign_build", "missing_certificate",
                  "trained_bundle_tuple"):
            self.assertEqual(dep[k]["decision"], "BLOCK", k)
        self.assertTrue(named_missing_present(receipt["named_missing"]))
        # the receipt's own identity binds this suite's inputs
        self.assertEqual(receipt["preregistration_sha256"],
                         vi.prereg_sha256())
        self.assertEqual(receipt["criteria_sha256"], vi.CRITERIA_SHA256)


class Test02LoadOrdering(unittest.TestCase):
    """The load order is law: validator -> gate ALLOW -> loader."""

    def test_gate_precedes_loader_and_identity_binds(self):
        fx = fixture()
        # the ALLOW verdict was produced against the certificate BEFORE the
        # bundle identity was checked (rnl.gate_and_load executes in that
        # order and any non-ALLOW raises SystemExit 2)
        self.assertEqual(fx["allow"]["decision"], "ALLOW")
        pb = fx["cert"]["relation"]["policy_bundle"]
        self.assertEqual(fx["bundle"]["manifest"]["manifest_hash"],
                         pb["manifest_hash"])
        self.assertEqual(fx["bundle"]["manifest"]["policy"]["weights_sha256"],
                         pb["weights_sha256"])
        self.assertEqual(fx["bundle"]["weights_file_sha256"],
                         pb["weights_file_sha256"])


class Test03Fb1PinBite(unittest.TestCase):
    def test_clean_green_tamper_fires(self):
        fixture()
        clean = vi.verify()
        self.assertTrue(all(r["ok"] for r in clean))
        tampered = [list(row) for row in vi.PINS]
        tampered[0] = ["store", ("MAT2-W04", "numerical", "w04_certificate.json"),
                       "0" * 64]
        with self.assertRaises(vi.Refusal) as ctx:
            vi.verify([tuple(r) for r in tampered])
        self.assertIn("input_pin_mismatch", str(ctx.exception))


class Test04Fb2GateBites(unittest.TestCase):
    def test_validator_bite(self):
        fx = fixture()
        from tools.policy_compat.certificate import (validate_certificate,)
        broken = copy.deepcopy(fx["cert"])
        broken["relation"]["policy_bundle"]["normalization_clip"] = 9.0
        errs = validate_certificate(broken)
        self.assertTrue(errs, "tampered certificate must violate")

    def test_trained_foreign_missing_block(self):
        fx = fixture()
        from tools.policy_compat.certificate import check_deploy
        req = fx["req"]
        foreign = copy.deepcopy(req)
        foreign["policy_bundle"] = dict(req["policy_bundle"])
        foreign["policy_bundle"]["manifest_hash"] = "0" * 64
        self.assertEqual(check_deploy(foreign, fx["cert"])["decision"],
                         "BLOCK")
        foreign_build = copy.deepcopy(req)
        foreign_build["physics_build"] = dict(req["physics_build"])
        foreign_build["physics_build"]["build_id"] = "cpu-walk-scene-build-N+1"
        self.assertEqual(check_deploy(foreign_build, fx["cert"])["decision"],
                         "BLOCK")
        self.assertEqual(check_deploy(req, None)["decision"], "BLOCK")


class Test05Fb3AnchorDriftBite(unittest.TestCase):
    def test_comparator_clean_exact_tamper_drift(self):
        fx = fixture()
        got = {
            "trajectory_sha256": vi.sha_bytes(fx["res"]["traj_bytes"]),
            "initial_snapshot_sha256": fx["res"]["initial_snapshot_sha256"],
            "final_state_sha256": fx["res"]["final_state_sha256"],
        }
        for key, row in rnl_and_receipt_anchors().items():
            self.assertEqual(verdict_for(key, got[key],
                                         row["frozen"])["verdict"], "EXACT")
            tampered = row["frozen"][:-1] + \
                ("0" if row["frozen"][-1] != "0" else "1")
            self.assertEqual(verdict_for(key, got[key],
                                         tampered)["verdict"], "DRIFT")


def rnl_and_receipt_anchors():
    receipt = json.loads((HERE / "receipts" / "native_load_receipt.json")
                         .read_bytes().decode("utf-8"))
    return receipt["execution"]["anchor_comparisons"]


class Test06Fb4BoundsBite(unittest.TestCase):
    def test_clean_within_caps_tamper_fires(self):
        fx = fixture()
        manifest = fx["bundle"]["manifest"]
        lo = np.asarray(manifest["action"]["bounds_lo"], dtype=np.float32)
        hi = np.asarray(manifest["action"]["bounds_hi"], dtype=np.float32)
        applied = fx["res"]["applied_per_tick"]
        self.assertTrue(bounds_ok(applied, lo, hi))
        breach = [list(applied[0])]
        breach[0][1] = float(hi[1]) + 1.0
        self.assertFalse(bounds_ok(breach, lo, hi))


class Test07Fb5RecipeBite(unittest.TestCase):
    def test_recipe_bit_exact_clean_swapped_detected(self):
        fx = fixture()
        manifest = fx["bundle"]["manifest"]
        obs_path = (vi.PINNED_ROOT / "tools" / "science_funnel"
                    / "typeb_export" / "observation_schema.py")
        obs, _ = rnl.load_pinned_module("t_obs_schema", obs_path)
        mean = np.asarray(manifest["normalization"]["mean"], dtype=np.float32)
        std = np.asarray(manifest["normalization"]["std"], dtype=np.float32)
        W = [np.ascontiguousarray(fx["bundle"]["params"][f"W{i}"],
                                  dtype=np.float32)
             for i in range(len(manifest["policy"]["architecture"]) - 1)]
        b = [np.ascontiguousarray(fx["bundle"]["params"][f"b{i}"],
                                  dtype=np.float32)
             for i in range(len(manifest["policy"]["architecture"]) - 1)]
        lo = np.asarray(manifest["action"]["bounds_lo"], dtype=np.float32)
        hi = np.asarray(manifest["action"]["bounds_hi"], dtype=np.float32)
        scale = np.asarray(manifest["action"]["scale"], dtype=np.float32)
        center = np.asarray(manifest["action"]["center"], dtype=np.float32)
        records = fx["res"]["records"]
        applied_rt = fx["res"]["applied_per_tick"]

        def recompute(t, mean_v, std_v):
            rec = dict(records[t])
            rec["is_decision_tick"] = True
            rec["hold_tick"] = t % 15
            rec["ticks_since_reset"] = t
            rec["ticks_since_intervention"] = 3000
            prev_yaw = 0.0 if t == 0 else float(records[t - 1]["yaw_rate"])
            x, _ = obs.project_trace(rec, mean_v, std_v,
                                     {"yaw_rate": prev_yaw})
            h = x
            for Wi, bi in zip(W, b):
                h = h @ Wi + bi
                h = np.tanh(h, out=h) if h.dtype == np.float32 \
                    else np.tanh(h)
                h = h.astype(np.float32, copy=False)
            return np.clip(center + scale * h, lo, hi).astype(np.float32)

        t = 0
        clean = recompute(t, mean, std)
        self.assertTrue(np.array_equal(
            clean, np.asarray(applied_rt[t], dtype=np.float32)))
        swapped = recompute(t, std, mean)   # the I2 injection class
        self.assertFalse(np.array_equal(
            swapped, np.asarray(applied_rt[t], dtype=np.float32)))


class Test08Fb6NamedMissingPresenceBite(unittest.TestCase):
    def test_presence_clean_ok_stripped_fires(self):
        receipt = json.loads((HERE / "receipts" / "native_load_receipt.json")
                             .read_bytes().decode("utf-8"))
        self.assertTrue(named_missing_present(receipt["named_missing"]))
        stripped = {k: v for k, v in receipt["named_missing"].items()
                    if k != "N1_adopted_assembly_scene_module"}
        self.assertFalse(named_missing_present(stripped))


class Test09Fb7StructuralScan(unittest.TestCase):
    def test_contribution_clean_scan_and_bite(self):
        paths = sorted(HERE.glob("*.py"))
        self.assertEqual(structural_scan(paths), [])
        # bite: a fake module importing subprocess outside the capture tool
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "rogue.py"
            fake.write_bytes(b"import subprocess\n")
            self.assertEqual(structural_scan([fake]),
                             ["subprocess:rogue.py"])


class Test10ContractInterfaceIdentity(unittest.TestCase):
    def test_80_field_v2_interface_declared(self):
        fixture()
        receipt = json.loads((HERE / "receipts" / "native_load_receipt.json")
                             .read_bytes().decode("utf-8"))
        si = receipt["contract_consumption"]["schema_identity"]
        self.assertEqual(si["obs_schema_version"], 2)
        self.assertEqual(si["obs_dim"], 80)
        self.assertEqual(si["legacy_obs_dim"], 64)
        self.assertEqual(si["declared_field_count"], 80)
        self.assertTrue(si["declared_field_names_unique"])
        self.assertTrue(si["no_privileged_field"])
        self.assertTrue(si["no_privileged_source"])
        self.assertEqual(receipt["contract_consumption"]["consumer_width"], 64)
        clock = receipt["contract_consumption"]["clock"]
        self.assertEqual(clock["physics_hz"], 300)
        self.assertEqual(clock["policy_hz"], 20)
        self.assertEqual(clock["hold_ticks"], 15)


if __name__ == "__main__":
    unittest.main()
