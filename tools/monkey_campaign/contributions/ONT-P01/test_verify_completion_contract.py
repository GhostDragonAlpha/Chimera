#!/usr/bin/env python3
"""Bounded tests for verify_completion_contract.py.

Two layers:
1. Self-contained synthetic fixtures exercising every named refusal and the
   passing path (no dependency on the campaign records).
2. An integration test against the live campaign records when they exist on
   this host (skipped otherwise).

Bounded: no network, no GPU, no writes outside a tempfile directory.
"""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from verify_completion_contract import Refusal, content_digest, verify  # noqa: E402

LIVE_MAP = Path("E:/PythonChimera/tools/monkey_campaign/monkey_completion_map.json")
LIVE_LOCK = Path("E:/PythonChimera/tools/monkey_campaign/APPROVED_SCOPE.json")
LIVE_ONTOLOGY = Path("E:/PythonChimera/tools/membrane_ontology/ontology.json")
LIVE_CONTRACT = HERE / "completion_contract.json"

CONDITIONAL_IDS = ["B01", "B02"]
FAMILY = "Multiple climbable tree forms and branch traversal"
K08_DONE = "Player approaches, attaches, ascends, holds, descends, releases and resumes all-fours walking in one session"
S05_DONE = "All selected core/product behaviors pass; remaining issues are triaged explicitly; operator accepts actual play"


def make_map():
    return {
        "schema": "chimera.monkey_completion_map.v1",
        "finish_line": "Playable monkey game first; broader Chimera vision later",
        "ontology_contract": {"definition_raw_sha256": "0" * 64},
        "tasks": [
            {"id": "P01", "title": "t", "scope": "core", "depends_on": [],
             "done_when": "d", "calculation_ids": []},
            {"id": "K08", "title": "t", "scope": "core", "depends_on": ["P01"],
             "done_when": K08_DONE, "calculation_ids": []},
            {"id": "S05", "title": "t", "scope": "recommended_product",
             "depends_on": ["K08"], "done_when": S05_DONE, "calculation_ids": []},
            {"id": "B01", "title": "t", "scope": "conditional", "depends_on": [],
             "done_when": "d", "calculation_ids": []},
            {"id": "B02", "title": "t", "scope": "conditional", "depends_on": [],
             "done_when": "d", "calculation_ids": []},
        ],
        "calculations": [{"id": "C1"}],
        "later_backlog": [{"title": FAMILY}],
    }


def make_lock(map_obj, map_raw_sha):
    return {"algorithm": "sha256-chimera-json-v1",
            "scope_sha256": content_digest(map_obj),
            "raw_file_sha256": map_raw_sha,
            "task_count": len(map_obj["tasks"])}


def make_contract(scope_sha, map_raw_sha, lock_raw_sha, onto_raw_sha):
    return {
        "schema": "chimera.completion_contract.v1",
        "status": "FROZEN",
        "identities": {
            "algorithm": "sha256-chimera-json-v1",
            "scope_sha256": scope_sha,
            "map_raw_sha256": map_raw_sha,
            "lock_raw_sha256": lock_raw_sha,
            "ontology_definition_raw_sha256": onto_raw_sha,
            "task_count": 5,
            "selected_count": 3,
            "conditional_ids": list(CONDITIONAL_IDS),
            "selected_rule": "scope != 'conditional'",
            "calculation_contract_count": 1,
            "amendment_chain": [scope_sha],
            "amendments": [],
        },
        "success_conditions": [
            {"id": "SC-LOOP", "clause": "loop",
             "evidence_bound_tasks": ["K08"],
             "terminal_done_when_verbatim": {"K08": K08_DONE}},
            {"id": "SC-ACCEPTANCE", "clause": "accept",
             "evidence_bound_tasks": ["S05"],
             "terminal_done_when_verbatim": {"S05": S05_DONE}},
        ],
        "exclusions": {"deferred_families": [FAMILY],
                       "forbidden_substitutes": ["Kinematic locomotion"]},
    }


class Fixture:
    """Writes a consistent record set to a temp directory; supports mutation."""

    def __init__(self, root: Path):
        self.root = root
        self.map_path = root / "map.json"
        self.lock_path = root / "lock.json"
        self.ontology_path = root / "ontology.json"
        self.contract_path = root / "contract.json"
        self.map_obj = make_map()
        self._write_all()

    def _map_bytes(self):
        return json.dumps(self.map_obj, indent=1).encode("utf-8")

    def _write_all(self):
        onto = b"ontology-bytes"
        self.ontology_path.write_bytes(onto)
        self.map_obj["ontology_contract"]["definition_raw_sha256"] = \
            hashlib.sha256(onto).hexdigest()
        raw = self._map_bytes()
        self.map_path.write_bytes(raw)
        map_sha = hashlib.sha256(raw).hexdigest()
        lock_obj = make_lock(self.map_obj, map_sha)
        lock_raw = json.dumps(lock_obj, indent=1).encode("utf-8")
        self.lock_path.write_bytes(lock_raw)
        contract = make_contract(content_digest(self.map_obj), map_sha,
                                 hashlib.sha256(lock_raw).hexdigest(),
                                 hashlib.sha256(onto).hexdigest())
        self.contract_path.write_bytes(json.dumps(contract, indent=1).encode("utf-8"))

    def rewrite_map(self, obj=None, raw=None):
        if obj is not None:
            self.map_obj = obj
            data = json.dumps(obj, indent=1).encode("utf-8")
        else:
            data = raw
        self.map_path.write_bytes(data)

    def rebind_digests(self, map_obj):
        """Rewrite map with map_obj and make lock/contract digests consistent,
        keeping the contract's count/set expectations at their baseline values
        so a single structural check is isolated."""
        raw = json.dumps(map_obj, indent=1).encode("utf-8")
        self.map_path.write_bytes(raw)
        lock_obj = make_lock(map_obj, hashlib.sha256(raw).hexdigest())
        lock_raw = json.dumps(lock_obj, indent=1).encode("utf-8")
        self.lock_path.write_bytes(lock_raw)
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        ids = contract["identities"]
        ids["scope_sha256"] = content_digest(map_obj)
        ids["map_raw_sha256"] = hashlib.sha256(raw).hexdigest()
        ids["lock_raw_sha256"] = hashlib.sha256(lock_raw).hexdigest()
        self.contract_path.write_bytes(
            json.dumps(contract, indent=1).encode("utf-8"))

    def rewrite_contract(self, mutate):
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        mutate(contract)
        self.contract_path.write_bytes(json.dumps(contract, indent=1).encode("utf-8"))

    def run_verify(self, **kwargs):
        return verify(self.contract_path, self.map_path, self.lock_path,
                      self.ontology_path, verify_amendments=False, **kwargs)


class PositivePath(unittest.TestCase):
    def test_consistent_fixture_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            result = fixture.run_verify()
            self.assertEqual(result["outcome"], "PASS")
            self.assertEqual(result["task_count"], 5)
            self.assertEqual(result["selected_count"], 3)
            self.assertEqual(result["conditional_ids"], CONDITIONAL_IDS)

    def test_idempotent_second_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            first = fixture.run_verify()
            second = fixture.run_verify()
            self.assertEqual(first, second)


class ContentLayerRefusals(unittest.TestCase):
    def test_changed_task_content_refused_p1a(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            mutated = copy.deepcopy(fixture.map_obj)
            mutated["tasks"][0]["done_when"] = "silently weakened"
            fixture.rewrite_map(obj=mutated)
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("P1a_"), ctx.exception)

    def test_whitespace_only_tamper_refused_p2a(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            raw = fixture._map_bytes().replace(b"\n", b"\r\n")
            fixture.rewrite_map(raw=raw)
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("P2"), ctx.exception)

    def test_wrong_trust_anchor_refused_p1c(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify(expected_scope_sha="f" * 64)
            self.assertTrue(str(ctx.exception).startswith("P1c_"), ctx.exception)

    def test_nonfinite_number_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            raw = fixture._map_bytes() + b"\n"
            raw = raw.replace(b'"id": "C1"', b'"id": "C1", "value": NaN')
            fixture.rewrite_map(raw=raw)
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("nonfinite_json_number"),
                            ctx.exception)

    def test_duplicate_json_key_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            raw = b'{"schema": "x", "schema": "x", "tasks": []}'
            fixture.rewrite_map(raw=raw)
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("duplicate_json_key"),
                            ctx.exception)


class InventoryRefusals(unittest.TestCase):
    def _with_fixture(self, mutate_map, assert_refusal):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            mutated = copy.deepcopy(fixture.map_obj)
            mutate_map(mutated)
            fixture.rebind_digests(mutated)
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            assert_refusal(str(ctx.exception))

    def test_conditional_drift_refused_p4b(self):
        self._with_fixture(
            lambda m: m["tasks"][3].__setitem__("scope", "core"),
            lambda msg: self.assertTrue(msg.startswith("P4b_"), msg))

    def test_removed_task_refused_p4a(self):
        self._with_fixture(
            lambda m: m["tasks"].pop(),
            lambda msg: self.assertTrue(msg.startswith("P4a_"), msg))

    def test_duplicate_task_id_refused(self):
        def dup(m):
            m["tasks"].append(copy.deepcopy(m["tasks"][0]))
        self._with_fixture(
            dup,
            lambda msg: self.assertTrue(
                msg.startswith("P4_duplicate_or_missing_task_id"), msg))

    def test_empty_done_when_refused_p4d(self):
        self._with_fixture(
            lambda m: m["tasks"][1].__setitem__("done_when", "  "),
            lambda msg: self.assertTrue(msg.startswith("P4d_"), msg))

    def test_calculation_count_drift_refused_p4e(self):
        self._with_fixture(
            lambda m: m["calculations"].append({"id": "C2"}),
            lambda msg: self.assertTrue(msg.startswith("P4e_"), msg))


class ContractRefusals(unittest.TestCase):
    def test_ontology_drift_refused_p3a(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.ontology_path.write_bytes(b"other-bytes")
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("P3a_"), ctx.exception)

    def test_terminal_quote_drift_refused_p4f(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rewrite_contract(
                lambda c: c["success_conditions"][0]["terminal_done_when_verbatim"]
                .__setitem__("K08", K08_DONE + " (edited)"))
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("P4f_"), ctx.exception)

    def test_unknown_evidence_task_refused_p4g(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rewrite_contract(
                lambda c: c["success_conditions"][0]
                .__setitem__("evidence_bound_tasks", ["Z99"]))
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("P4g_"), ctx.exception)

    def test_conditional_evidence_task_refused_p4g(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rewrite_contract(
                lambda c: c["success_conditions"][0]
                .__setitem__("evidence_bound_tasks", ["B01"]))
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(
                str(ctx.exception).startswith("P4g_evidence_task_is_conditional"),
                ctx.exception)

    def test_deferred_family_drift_refused_p4h(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rewrite_contract(
                lambda c: c["exclusions"]
                .__setitem__("deferred_families", ["Invented family"]))
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("P4h_"), ctx.exception)

    def test_broken_amendment_chain_refused_p4i(self):
        origin = "a" * 64

        def mutate(c):
            c["identities"]["amendment_chain"] = [
                origin, c["identities"]["scope_sha256"]]
            c["identities"]["amendments"] = [
                {"path": "tools/monkey_campaign/A.json",
                 "raw_sha256": "0" * 64,
                 "previous_scope_sha256": "1" * 64,  # not the declared origin
                 "resulting_scope_sha256": c["identities"]["scope_sha256"]}]
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rewrite_contract(mutate)
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("P4i_"), ctx.exception)

    def test_unfrozen_contract_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rewrite_contract(
                lambda c: c.__setitem__("status", "DRAFT"))
            with self.assertRaises(Refusal) as ctx:
                fixture.run_verify()
            self.assertTrue(str(ctx.exception).startswith("contract_not_frozen"),
                            ctx.exception)

    def test_amendment_raw_hash_mismatch_refused(self):
        origin = "b" * 64

        def mutate(c):
            scope = c["identities"]["scope_sha256"]
            c["identities"]["amendment_chain"] = [origin, scope]
            c["identities"]["amendments"] = [
                {"path": "tools/monkey_campaign/A.json",
                 "raw_sha256": "0" * 64,
                 "previous_scope_sha256": origin,
                 "resulting_scope_sha256": scope}]
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rewrite_contract(mutate)
            (Path(tmp) / "A.json").write_bytes(b"amendment bytes")
            with self.assertRaises(Refusal) as ctx:
                verify(fixture.contract_path, fixture.map_path, fixture.lock_path,
                       fixture.ontology_path, verify_amendments=True)
            self.assertTrue(
                str(ctx.exception).startswith("P4i_amendment_raw_sha"),
                ctx.exception)


@unittest.skipUnless(LIVE_MAP.exists() and LIVE_LOCK.exists()
                     and LIVE_ONTOLOGY.exists() and LIVE_CONTRACT.exists(),
                     "live campaign records not present on this host")
class LiveRecordsIntegration(unittest.TestCase):
    """Numerical evidence for the records profile: run against the real records."""

    def test_live_records_pass_and_are_idempotent(self):
        first = verify(LIVE_CONTRACT, LIVE_MAP, LIVE_LOCK, LIVE_ONTOLOGY,
                       verify_amendments=True)
        second = verify(LIVE_CONTRACT, LIVE_MAP, LIVE_LOCK, LIVE_ONTOLOGY,
                        verify_amendments=True)
        self.assertEqual(first["outcome"], "PASS")
        self.assertEqual(first, second)
        self.assertEqual(first["task_count"], 83)
        self.assertEqual(first["selected_count"], 76)


if __name__ == "__main__":
    unittest.main(verbosity=2)
