#!/usr/bin/env python3
"""MAT2-W10: the frozen input-pin verifier (prereg section 1 + amendment A1).

Verifies every pinned upstream artifact byte-exact BEFORE anything is
loaded or executed; any drift is the named refusal `input_pin_mismatch`.
Pins: the sealed W-tier/W04/U01/G07 records in the evidence store, the F-tier
clearing pins and the seam/asset bytes as base blobs read READ-ONLY from the
shared repository's object database at the package base (through the
DECLARED source_access.py — NO_WORKTREES law), the sealed lane machinery at
the pass3-integ lane repo (including this card's added
creature_graph/data/authored/project_program.json — the existing monkey
asset bytes), and the card identity READ-ONLY from the registry
(`file:...?mode=ro`; criteria mismatch = `criteria_pin_mismatch`).
Importable: the run, the checks and the capture all call verify() first.

Run:  python -B verify_inputs.py
Exit: 0 green / 2 named refusal.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
LANE_REPO = Path("E:/ChimeraWork/pass3-integ/repo")
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

import source_access as sa  # noqa: E402  (the DECLARED git blob reader)

CARD_ID = "MAT2-W10"
TASK_SHORT = "W10"
CRITERIA_SHA256 = "044fd755f9bcf10895e50ef1c569dc584415ab5cce67497848197621cbc1b23d"
ATTEMPT_ID = "e0dd5f03572f4b95b7f5a6013327d906"
AGENT_ID = "wk-w10-arrival-1"
BASE_SHA = "273d7e592ceec83b272416cf4ce9f4e16a9e3720"
PREREG = HERE / "PREREGISTRATION.md"
AMENDMENT_A1 = HERE / "AMENDMENT-A1.md"
AMENDMENT_A2 = HERE / "AMENDMENT-A2.md"
AMENDMENT_A3 = HERE / "AMENDMENT-A3.md"
PREREG_COMMIT = "2bbc6f3317310738667b99fb1f096dadfc39acd7"
AMENDMENT_A1_COMMIT = "efe5b749870fdbd31895e14a409615a2a460bec1"
AMENDMENT_A2_COMMIT = "3d0da80b378949b33e953a68ae37c5535c45f179"
AMENDMENT_A3_COMMIT = "90a9367a4809d2b5e76f182ac8b6287be5646fa5"

# Slot-scratch (runner TMP; never inside the contribution directory).
SCRATCH = Path(os.environ.get("TMP", ".")) / ("w10_pins_" + ATTEMPT_ID[:8])
PINNED_ROOT = SCRATCH / "pinned_root"

# (group, pinned path parts, sha256) — prereg section 1 + amendment A1.
PINS = [
    # evidence store (durable vault)
    ("store", ("MAT2-W04", "numerical", "w04_certificate.json"),
     "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598"),
    ("store", ("MAT2-W04", "numerical", "w04_freeze_manifest.json"),
     "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29"),
    ("store", ("MAT2-U01", "numerical", "qualification_receipt.json"),
     "94887cc14ba6d2fc7a76c04949d5015cbfada899a817c3acb497e5d53a7a0c61"),
    ("store", ("MAT2-W07", "numerical", "native_load_receipt.json"),
     "4f5aac081a3a07fd56733d84ac3069950b00309e54f6402e78ebd22c55e490e9"),
    ("store", ("MAT2-W07", "numerical", "checks_receipt.json"),
     "f599720bbcd06e4888d933d11a7e48f29430635189acf79bd79ad7305559d342"),
    ("store", ("MAT2-W08", "numerical", "checks_receipt.json"),
     "cd9998ab612b0e320b657a196d672e668199bb92188527d887aafeb321014c37"),
    ("store", ("MAT2-W09", "numerical", "out_of_envelope_receipt.json"),
     "0880a18a46b99e9463cde8f64fafc6daff82a9b78f04ea5e2960abef963cb4c7"),
    ("store", ("MAT2-W09", "numerical", "checks_receipt.json"),
     "e4cd94ae5c77a7dc9a5ecfba0e02ad4ae100ebabf1995132bbe9f41a3c2b4430"),
    ("store", ("MAT2-W09", "numerical", "falsifier_receipt.json"),
     "3a61cdbf43f7b11b4b284c7be969c5f0a36208556942f0832f1022fe87b1204c"),
    ("store", ("MAT2-W09", "numerical", "input_pins.final.json"),
     "RECORDED_AT_RUN_TIME"),
    ("store", ("MAT2-G07", "verdict_ref", "PREREGISTRATION.md"),
     "1e55df6da88dbb9fdc3c296b2965042b0a6828b0d6387a2c9eb8bb53f7bb87df"),
    ("store", ("MAT2-G07", "numerical", "experiment_receipt.json"),
     "c539617b098190918187d9a7dcbb0a5e33a85998adaa58f6b781703bbdeb88f8"),
    ("coord", ("ingestion-spike", "INGESTION_SPIKE.md"),
     "218b34614d8917eceb3f4ea2a6404c5715f8e25f71e57989c53213d7498e512b"),
    ("coord", ("ingestion-spike", "w2-engine-up", "ENGINE_UP_RECEIPT.md"),
     "364ae9453bdba88f636980a971263847823a14d8f7c2e957719a87421b7bb73c"),
    # base blobs (the shared object database at the package base)
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-U01",
              "reconcile", "pinned_seam", "tools", "monkey_campaign",
              "product", "input_mapper.py"),
     "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-U01",
              "reconcile", "pinned_seam", "tools", "monkey_campaign",
              "product", "input_mapper_tests.py"),
     "95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-U01",
              "reconcile", "pinned_seam", "tools", "science_funnel",
              "typeb_export", "command_record.py"),
     "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e"),
    ("blob", ("tools", "monkey_campaign", "visual_capture.py"),
     "5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-W05",
              "receipts", "deploy_check_receipt.json"),
     "766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-W06",
              "receipts", "evaluation_summary.json"),
     "a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-W07",
              "run_native_load.py"),
     "780dde4e0ea9fa0d6ecab41a42cbac85f73192d552aceef7fd2cb8ff4d75f766"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-W08",
              "PREREGISTRATION.md"),
     "00a04e08411ed079aee9e0ef43f9221c69abc84612f66311e4db4822f6c8412a"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-W08",
              "receipts", "command_verification_receipt.json"),
     "bb9e014b160062d486002745571fd4485a50431cfdbc25038ebb9bed1171f787"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-W09",
              "PREREGISTRATION.md"),
     "6a3e0f6f5e0a0d7cbad595e0d16285556608b93fa77ef77dc59c30ae962f9d7b"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-W09",
              "out_of_envelope.py"),
     "7245739a746aaeb259a2720c97dbdfec4a88b77aed997cd0c9f961f5ca89d782"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F02",
              "pins", "terrain_bundle.json"),
     "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F02",
              "pins", "terrain_query.py"),
     "b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F02",
              "pins", "terrain_bundle.py"),
     "c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F02",
              "pins", "clearing_recipe.py"),
     "ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F02",
              "pins", "clearing_declaration.json"),
     "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F02",
              "pins", "trunk_declaration.json"),
     "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F02",
              "pins", "f01_implementation.py"),
     "50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F03",
              "assets", "trunk_01_mesh.json"),
     "3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M06",
              "local_contact.py"),
     "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M06",
              "contact_law.json"),
     "583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F04",
              "implementation.py"),
     "5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F04",
              "evidence", "camera_manifest.json"),
     "79cf207b8b53f07ef2f5ff8fa42133144feeccf75f7b2b0fd4cfe5fb0ce09b3a"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F01",
              "evidence", "pins_materialized", "gait_controller.hpp"),
     "f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-B07",
              "adoption_record.json"),
     "638884569ac106cb7ed738381e804e4f936877f05fd572a5763064cdcb711a0a"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M02",
              "data", "macaque_arm", "monkeyArm_current.osim"),
     "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M02",
              "data", "macaque_arm", "Geometry", "humerus.vtp"),
     "87f6034aa082c49b6448259ae7ec4452c6b0d3314442d5be3e8e1a5e4ec8118b"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M02",
              "data", "macaque_arm", "Geometry", "radius.vtp"),
     "8a2d3f2fe5f8b27014c0f024994ff76659bac73a52844494926dd29b9f3bb10e"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M02",
              "data", "macaque_arm", "Geometry", "ulna.vtp"),
     "8f80ac47453fa175118fa385a5fbcb9cf770a21cf10c1757dccc5df2cceb1409"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M02",
              "data", "macaque_arm", "Geometry", "hand.vtp"),
     "a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M02",
              "data", "macaque_arm", "Geometry", "scapula.vtp"),
     "e9ffe8ef9ad2dc577fb8c50afd87f694d0ddb6e243d230ba91e2aa7137480fe7"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M02",
              "data", "macaque_arm", "Geometry", "clavicle.vtp"),
     "84caf2d4724aef05b7f8e904474deda7342db1b6c0329cfa5b399802bfebc905"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M02",
              "data", "macaque_arm", "Geometry", "sternum.vtp"),
     "fc688ea2643c356f28a6eb3c825e056941d307d407414f77f0c5d655c91a227d"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M12",
              "capture_manifest.json"),
     "0ea48c70af67b9336a3b95ca03a5a6ad0ccdad7a0d80db1e77c6dffff8139d40"),
    # sealed lane machinery (identical to W07/W08/W09's pin table)
    ("lane", ("tools", "policy_compat", "__init__.py"),
     "11d523c8c0ee363e09c4e57afa564f3e38b178e274d7ee3ef335f5a0c44e9f4e"),
    ("lane", ("tools", "policy_compat", "__main__.py"),
     "74d592d0551e226289f944e8182a19a3b574d7d2ee331e157e17ac55ea969528"),
    ("lane", ("tools", "policy_compat", "certificate.py"),
     "2b6a75ba79c367a646d89fdc8cbe2243239dbc5e336f1eba1deb33aa30e295ac"),
    ("lane", ("tools", "policy_compat", "engine_cert.py"),
     "c1aa05362e20a3e0c8967634af2d97fadd11d62daf412e07917824f16c1e5152"),
    ("lane", ("tools", "policy_compat", "injections.py"),
     "1b5b978bf5feafb93801066486a5656caaba7cf3a618949036c13d0ceae28f1e"),
    ("lane", ("tools", "policy_compat", "runner.py"),
     "1fa8d8b70836d6e3355e3e2630f83e0a6a31a9658104e9f928d7ef52cfef5160"),
    ("lane", ("tools", "policy_compat", "scene_cpu.py"),
     "ab4257024df63d9755e9c1ae524ee631339ce24a2fd36615d40575335f835af2"),
    ("lane", ("tools", "policy_compat", "snapshot_api.py"),
     "c47a09596dd36692aa28f8f10b2967d9276b78082a96d0bba27bf632b8f0e493"),
    ("lane", ("tools", "science_funnel", "typeb_export", "infer_numpy.py"),
     "8030b609c7ecbfcc368addee2c140b830450fff48ecb62e02683d62062bfbfc4"),
    ("lane", ("tools", "science_funnel", "typeb_export",
              "observation_schema.py"),
     "8876e1a64d68e93b003c6daba8cacb34bff02c11133eb098bf1ef85bf8a39894"),
    ("lane", ("tools", "science_funnel", "typeb_export", "policy_manifest.py"),
     "a65cf8757c9d4d4d6a8d5fce30be6aaebb016c98d7dc69f972b0b7781e2961d7"),
    ("lane", ("tools", "science_funnel", "validation", "typeb_p3_20260921",
              "policy_manifest.json"),
     "aa5334f797b50c2ac3950cec5b82b439f982c1090dd66827754a1acbb8a26b6f"),
    ("lane", ("tools", "science_funnel", "validation", "typeb_p3_20260921",
              "dummy_actor.npz"),
     "5fb2b7857d872fccc0bb89d6733582647da04d11d636e84c266912ce9c027f0f"),
    ("lane", ("tools", "science_funnel", "validation", "typeb_p3_20260921",
              "trace_slice_wave38.json"),
     "69babe846e2447333b527c7fd8c190499e5ac1d55733dbd043edd0422245daa2"),
    ("lane", ("tools", "science_funnel", "validation", "upgrade_gate_20260920",
              "receipt.json"),
     "2c7794e6ff0c5c2d81c39536076ce1d6a0900333f4738549079afbe21012685a"),
    # THE EXISTING MONKEY ASSET BYTES (this card's added lane pin)
    ("lane", ("tools", "creature_graph", "data", "authored",
              "project_program.json"),
     "3e5182f5a8bd85995f3dd0dac1ae24a27cdc0a9539e4da9ec0aef17018b1555c"),
    # THE DECLARED SKELETON GEOMETRY (amendment A2's lane pin)
    ("lane", ("tools", "science_funnel", "validation",
              "gait_controller_20260918", "derived_numbers.json"),
     "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"),
]

_GROUP_BASE = {"store": STORE, "lane": LANE_REPO,
               "coord": Path("E:/ChimeraWork/monkey-coordination")}

# Pins whose sha is RECORDED at run time (declared context pins; the frozen
# refusal law still applies to every sha-pinned row above).
RUNTIME_RECORDED = ("RECORDED_AT_RUN_TIME")


class Refusal(Exception):
    """A named refusal (the falsifier must be able to FAIL)."""


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


def amendment_a1_sha256() -> str:
    return sha_bytes(AMENDMENT_A1.read_bytes())


def amendment_a2_sha256() -> str:
    return sha_bytes(AMENDMENT_A2.read_bytes())


def amendment_a3_sha256() -> str:
    return sha_bytes(AMENDMENT_A3.read_bytes())


def require(condition, code: str) -> None:
    if not condition:
        raise Refusal(code)


def pin_path(group: str, parts: tuple) -> Path:
    if group == "blob":
        return PINNED_ROOT.joinpath(*parts)
    return _GROUP_BASE[group].joinpath(*parts)


def verify(expect=None) -> list:
    """Verify all pins (or an override table for the FB bite arms)."""
    rows = []
    table = PINS if expect is None else expect
    for group, parts, expected in table:
        if group == "blob":
            data = sa.read_blob(BASE_SHA, "/".join(parts))
        else:
            data = pin_path(group, parts).read_bytes()
        got = sha_bytes(data)
        recorded = expected == RUNTIME_RECORDED
        rows.append({"path": "/".join((group,) + parts),
                     "sha256": got, "expected": expected,
                     "recorded_at_run_time": recorded,
                     "ok": True if recorded else got == expected})
        require(recorded or got == expected,
                "input_pin_mismatch:" + parts[-1] + ":" + got[:12])
    return rows


def verify_registry() -> dict:
    """READ-ONLY registry identity check (the criteria + the profile)."""
    con = sqlite3.connect("file:" + str(REGISTRY).replace("\\", "/")
                          + "?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT payload FROM state")
        state = json.loads(cur.fetchone()[0])
    finally:
        con.close()
    card = (state.get("kanban", {}).get("cards", {}) or {}).get(CARD_ID)
    require(card is not None, "criteria_pin_mismatch:card_missing")
    got = card.get("criteria_sha256")
    require(got == CRITERIA_SHA256, "criteria_pin_mismatch:" + repr(got))
    attempt = (card.get("attempts") or {}).get(ATTEMPT_ID)
    attempt_agent = attempt.get("agent_id") if isinstance(attempt, dict) else attempt
    require(attempt_agent == AGENT_ID,
            "criteria_pin_mismatch:attempt_owner:" + repr(attempt_agent))
    profile = (card["spec"]["ontology_qualification"]["task"]
               ["verification_profile"])
    require(profile.get("id") == "walking" and profile.get("kind") == "motion",
            "criteria_pin_mismatch:profile_identity")
    return {"card_state": card.get("state"), "criteria_sha256": got,
            "registry_revision": state.get("revision"),
            "attempt_agent": attempt_agent,
            "attempt_state": attempt.get("state") if isinstance(attempt, dict) else None,
            "profile": {"id": profile.get("id"), "kind": profile.get("kind"),
                        "views": profile.get("views"),
                        "clean_view_required": profile.get("clean_view_required"),
                        "diagnostic_layers": profile.get("diagnostic_layers"),
                        "camera_required_fields": profile.get("camera_required_fields")}}


def extract_pinned_tree() -> Path:
    """Materialize the pinned execution tree under slot scratch
    (byte-verified): the lane machinery PLUS the base-blob seam bytes, ONE
    import namespace. Seam blobs (the U01 pinned_seam subtree) extract at
    their seam-relative paths so `tools.monkey_campaign.product.input_mapper`
    and `tools.science_funnel.typeb_export.command_record` resolve inside the
    same `tools` package as the machinery. The sealed W09 supervisor module
    (amendment A1) extracts at its contribution-relative path and is imported
    by file path (import identity; zero modification)."""
    seam_prefix = ("tools", "monkey_campaign", "contributions", "MAT2-U01",
                   "reconcile", "pinned_seam")
    if PINNED_ROOT.exists():
        shutil.rmtree(PINNED_ROOT)
    require(sa.resolve_base(BASE_SHA) == "commit",
            "input_pin_mismatch:base_unresolvable")
    for group, parts, expected in PINS:
        if group == "lane":
            data = LANE_REPO.joinpath(*parts).read_bytes()
            require(sha_bytes(data) == expected,
                    "input_pin_mismatch:extract:" + parts[-1])
            target_parts = parts
        elif group == "blob":
            data = sa.read_blob(BASE_SHA, "/".join(parts))
            require(sha_bytes(data) == expected,
                    "input_pin_mismatch:extract:" + parts[-1])
            target_parts = parts[len(seam_prefix):] if tuple(parts[:6]) == seam_prefix else parts
        else:
            continue
        target = PINNED_ROOT.joinpath(*target_parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return PINNED_ROOT


def bootstrap_pinned_imports() -> None:
    """Point sys.path at the pinned extraction (identity checked by callers)."""
    require(PINNED_ROOT.exists(), "input_pin_mismatch:extraction_missing")
    root = str(PINNED_ROOT)
    while root in sys.path:
        sys.path.remove(root)
    sys.path.insert(0, root)


def load_pinned_module(name: str, rel_parts: tuple):
    """Import a pinned NON-package module by file path (import identity; the
    W09 supervisor: its bytes are pin-verified BEFORE this loader runs)."""
    path = PINNED_ROOT.joinpath(*rel_parts)
    require(path.exists(), "input_pin_missing:" + "/".join(rel_parts))
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def w04_certificate() -> dict:
    return json.loads((STORE / "MAT2-W04" / "numerical" / "w04_certificate.json")
                      .read_bytes().decode("utf-8"))


def w09_out_of_envelope_receipt() -> dict:
    return json.loads((STORE / "MAT2-W09" / "numerical" /
                       "out_of_envelope_receipt.json").read_bytes().decode("utf-8"))


def gait_walker_record() -> dict:
    """The existing monkey asset: model.dynamics.gait_walker from the pinned
    authored program bytes."""
    prog = PINNED_ROOT.joinpath("tools", "creature_graph", "data",
                                "authored", "project_program.json")
    require(prog.exists(), "input_pin_missing:project_program.json")
    doc = json.loads(prog.read_bytes().decode("utf-8"))
    for obj in doc.get("objects", []):
        if isinstance(obj, dict) and obj.get("id") == "model.dynamics.gait_walker":
            return obj
    raise Refusal("asset_geometry_absent:gait_walker_record_missing")


def main() -> int:
    rows = verify()
    reg = verify_registry()
    record = {
        "schema": "chimera.w10_input_pins.v1",
        "task_id": TASK_SHORT,
        "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "agent_id": AGENT_ID,
        "base_sha256": BASE_SHA,
        "prereg_commit": PREREG_COMMIT,
        "amendment_a1_commit": AMENDMENT_A1_COMMIT,
        "amendment_a2_commit": AMENDMENT_A2_COMMIT,
        "amendment_a3_commit": AMENDMENT_A3_COMMIT,
        "preregistration_sha256": prereg_sha256(),
        "amendment_a1_sha256": amendment_a1_sha256(),
        "amendment_a2_sha256": amendment_a2_sha256(),
        "amendment_a3_sha256": amendment_a3_sha256(),
        "criteria_sha256": CRITERIA_SHA256,
        "pins": rows,
        "registry": reg,
        "source_repo": sa.source_repo(),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B verify_inputs.py"},
    }
    sys.stdout.write(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    print("pins verified:", len(rows), "| criteria:",
          reg.get("criteria_sha256", "")[:12])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        sys.exit(2)
