"""test_implementation.py -- MAT2-P06 contract tests (CPU-only, deterministic).

Runs under `python -B test_implementation.py` and under pytest.  Every test
uses plain asserts.  Negative tests exercise the card falsifier: pin drift,
missing identities, disagreeing cross-checks and crosswalk diffs must refuse
loudly.  No network, no GPU, no live-worktree writes; the only subprocesses
are read-only `git cat-file -e` identity checks inside implementation.py.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import implementation as impl  # noqa: E402

REFERENCE = HERE / "reference"
NUMERIC_ALLOWLIST_PREFIXES = (
    ("carried_limits", "*", "value"),
    ("material_first_limits", "*", "value"),
    ("carried_count",),
    ("material_first_derived_count",),
    ("decision_requested_count",),
    ("measurement_modes", "*"),
    ("crosswalk", "values_checked"),
    ("crosswalk", "requests_checked"),
)


def _build(tmp_ref=None):
    return impl.build_contract(tmp_ref or REFERENCE)


def _match_prefix(path, prefix):
    if len(path) < len(prefix):
        return False
    for got, want in zip(path, prefix):
        if want == "*" or got == want:
            continue
        return False
    return True


def _numeric_leaves(node, path=()):
    if isinstance(node, bool):
        return
    if isinstance(node, (int, float)):
        yield path
    elif isinstance(node, dict):
        for key, val in node.items():
            yield from _numeric_leaves(val, path + (key,))
    elif isinstance(node, list):
        for i, val in enumerate(node):
            yield from _numeric_leaves(val, path + (i,))


def _dump(contract):
    return json.dumps(contract, indent=1, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------- law shape

def test_contract_law_every_numeric_sourced():
    contract = _build()
    for path in _numeric_leaves(contract):
        assert any(_match_prefix(path, p)
                   for p in NUMERIC_ALLOWLIST_PREFIXES), (
        f"un-sourced numeric leaf at {path}")
    for limit in contract["carried_limits"] + contract["material_first_limits"]:
        assert limit["class"] == "DERIVED"
        assert limit["measured_now"] is True
        assert limit["provenance"], limit["id"]
        for p in limit["provenance"]:
            assert set(p) >= {"path", "commit", "blob_sha256", "method",
                              "locator"}, (limit["id"], p)
            assert len(p["commit"]) == 40 and len(p["blob_sha256"]) == 64
    for request in contract["operator_decision_requests"]:
        assert request["class"] == "OPERATOR_DECISION_REQUESTED"
        assert request["source"] is None
        assert request["options"] and request["recommendation"]


def test_counts_and_measurement_modes_consistent():
    contract = _build()
    assert contract["carried_count"] == 15
    assert contract["material_first_derived_count"] == 8
    assert contract["decision_requested_count"] == 7
    assert contract["crosswalk"]["values_checked"] == 15
    assert contract["crosswalk"]["requests_checked"] == 4
    assert sum(contract["measurement_modes"].values()) == 23


def test_crosswalk_zero_diff_empty():
    contract = _build()
    assert contract["crosswalk"]["value_diffs"] == []
    assert contract["crosswalk"]["decision_request_diffs"] == []
    target = json.loads((REFERENCE / impl.CROSSWALK_TARGET[0])
                        .read_text(encoding="utf-8"))
    new_values = {l["id"]: l["value"] for l in contract["carried_limits"]}
    old_values = {l["id"]: l["value"] for l in target["derived_limits"]}
    assert new_values == old_values
    new_req = {r["id"]: r for r in contract["operator_decision_requests"][:4]}
    old_req = {r["id"]: r for r in target["operator_decision_requests"]}
    assert new_req == old_req


def test_camera_outcomes_match_pinned_catalog():
    contract = _build()
    catalog = json.loads((REFERENCE / impl.CATALOG).read_text(encoding="utf-8"))
    profiles = {p["id"]: p
                for p in catalog["ontology_contract"]["visual_profiles"]}
    checkpoints = {c["id"]: c
                   for c in catalog["ontology_contract"]["checkpoints"]}
    outcomes = contract["camera_visible_player_outcomes"]
    assert outcomes["walking_replay_scenario"]["value"] == \
        profiles["walking"]["scenario"]
    assert outcomes["walking_falsifier_outcomes"]["value"] == \
        profiles["walking"]["falsifier"]
    assert outcomes["material_falsifier_outcomes"]["value"] == \
        profiles["material"]["falsifier"]
    assert outcomes["walking_through_woods_acceptance"]["value"] == \
        checkpoints["MAT-WOODS"]["acceptance"]
    assert outcomes["climb_loop_acceptance"]["value"] == \
        checkpoints["V07"]["acceptance"]
    assert outcomes["camera_required_fields"]["value"] == \
        profiles["walking"]["camera_required_fields"]
    assert outcomes["clean_view_required"]["value"] == {
        "walking": True, "material": True}


def test_separate_reports_structure():
    contract = _build()
    reports = contract["separate_acceptance_reports"]
    a = reports["report_A_walking_through_woods"]
    b = reports["report_B_full_climbing_completion"]
    assert a["reported"] == "FIRST (the first product milestone)"
    assert b["reported"].startswith("SEPARATELY")
    assert "MAT-WOODS" in a["checkpoints"] and "V07" in b["checkpoints"]
    assert set(b["contributor_tasks"]) == {"K04", "K05", "K06", "K07", "K08"}
    assert b["feature_acceptance_task"] == "S05"
    assert a["gate_limits"] == [l["id"] for l in contract["carried_limits"]]
    sequence = contract["camera_visible_player_outcomes"][
        "demonstration_order_first_visible_sequence"]["value"]
    assert sequence.index("W10") < sequence.index("K08") < sequence.index("S05")
    assert sequence.index("F06") < sequence.index("K08")


def test_identity_pinings_recorded():
    contract = _build()
    ident = contract["identities"]
    assert ident["criteria_sha256"] == impl.CRITERIA
    assert ident["dependency_P01"]["state"] == "DONE"
    assert ident["dependency_P01"]["merge_commit_sha"] == \
        "97993cbefaf00380803d8e67652ac51d50c37d06"
    assert ident["archived_lineage_ONT-P06"]["lead_verdict"] == "ACCEPTED"
    assert ident["catalog_live_matches_pin"] is True


def test_deterministic_regeneration():
    assert _dump(_build()) == _dump(_build())


# ------------------------------------------------------- negative falsifiers

def test_negative_pin_drift_refuses():
    with tempfile.TemporaryDirectory() as tmp:
        ref = pathlib.Path(tmp) / "reference"
        shutil.copytree(REFERENCE, ref)
        victim = ref / impl.CLEARING
        data = bytearray(victim.read_bytes())
        data[0] ^= 0x20
        victim.write_bytes(bytes(data))
        try:
            impl.build_contract(ref)
        except impl.SourceFailure as exc:
            assert "PIN DRIFT" in str(exc), str(exc)
        else:
            raise AssertionError("tampered pin did not refuse")


def test_negative_crosswalk_target_tamper_refuses():
    with tempfile.TemporaryDirectory() as tmp:
        ref = pathlib.Path(tmp) / "reference"
        shutil.copytree(REFERENCE, ref)
        victim = ref / impl.CROSSWALK_TARGET[0]
        proposal = json.loads(victim.read_text(encoding="utf-8"))
        proposal["derived_limits"][0]["value"] = 999.0
        victim.write_text(json.dumps(proposal, indent=1), encoding="utf-8")
        try:
            impl.build_contract(ref)
        except impl.SourceFailure as exc:
            assert "PIN DRIFT" in str(exc), str(exc)
        else:
            raise AssertionError("tampered crosswalk target did not refuse")


def test_negative_missing_source_refuses():
    with tempfile.TemporaryDirectory() as tmp:
        ref = pathlib.Path(tmp) / "reference"
        shutil.copytree(REFERENCE, ref)
        (ref / impl.ACC).unlink()
        try:
            impl.build_contract(ref)
        except impl.SourceFailure as exc:
            assert "pinned_source_missing" in str(exc), str(exc)
        else:
            raise AssertionError("missing pin did not refuse")


def test_negative_missing_git_identity_refuses():
    saved = dict(impl.PINNED["play"])
    try:
        rel = impl.CLEARING
        commit, sha = saved[rel]
        impl.PINNED["play"][rel] = ("0" * 40, sha)
        try:
            impl.carried_limits(REFERENCE)
        except impl.SourceFailure as exc:
            assert "git_identity_missing" in str(exc), str(exc)
        else:
            raise AssertionError("nulled commit did not refuse")
    finally:
        impl.PINNED["play"] = saved


def test_negative_tick_pins_disagree_refuses():
    gait = (REFERENCE / impl.GAIT).read_text(encoding="utf-8")
    earth = (REFERENCE / impl.EARTH).read_text(encoding="utf-8")
    # sanity: the true pins agree
    assert impl._tick_crosscheck(gait, earth) == (300, 4, 300)
    earth_bad = earth.replace('tick_hz"))==300', 'tick_hz"))==500')
    assert earth_bad != earth
    try:
        impl._tick_crosscheck(gait, earth_bad)
    except impl.SourceFailure as exc:
        assert "tick_pins_disagree" in str(exc), str(exc)
    else:
        raise AssertionError("disagreeing tick pins did not refuse")


def test_negative_crosswalk_value_diff_refuses():
    saved_target = impl.CROSSWALK_TARGET
    try:
        # point the crosswalk target at a proposal whose values were edited,
        # with the tampered bytes' real hash so the tamper reaches the diff.
        with tempfile.TemporaryDirectory() as tmp:
            ref = pathlib.Path(tmp) / "reference"
            shutil.copytree(REFERENCE, ref)
            victim = ref / impl.CROSSWALK_TARGET[0]
            proposal = json.loads(victim.read_text(encoding="utf-8"))
            for limit in proposal["derived_limits"]:
                if limit["id"] == "scene-seed":
                    limit["value"] = 1
            raw = json.dumps(proposal, indent=1,
                             ensure_ascii=False) + "\n"
            victim.write_bytes(raw.encode("utf-8"))
            impl.CROSSWALK_TARGET = (
                impl.CROSSWALK_TARGET[0],
                hashlib.sha256(raw.encode("utf-8")).hexdigest())
            try:
                impl.build_contract(ref)
            except impl.SourceFailure as exc:
                assert "CROSSWALK DIFF" in str(exc), str(exc)
            else:
                raise AssertionError("crosswalk diff did not refuse")
    finally:
        impl.CROSSWALK_TARGET = saved_target


def _main() -> int:
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print(f"OK {name}")
    print(f"Ran {len(tests)} tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
