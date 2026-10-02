#!/usr/bin/env python3
"""MAT2-F06: the frozen input-pin verifier (prereg section 1).

Verifies every pinned upstream artifact byte-exact BEFORE anything is
loaded or executed; any drift is the named refusal `input_pin_mismatch`.
Pins: the sealed W04/W09/F05/F07 records in the evidence store, the F-tier
clearing/obstacle pins, the sealed W08/W09/W10 preregistration and script
authorities and the seam/asset bytes as base blobs read READ-ONLY from the
shared repository's object database at the package base (through the
DECLARED source_access.py -- NO_WORKTREES law), the sealed lane machinery at
the pass3-integ lane repo, and the card identity READ-ONLY from the registry
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

CARD_ID = "MAT2-F06"
TASK_SHORT = "F06"
CRITERIA_SHA256 = "a1d7040a03bd15fc12797edbb11cf44e081712539de84e900e99b95478772779"
ATTEMPT_ID = "36d640396a624ee79056fef8c8a74cd9"
AGENT_ID = "wk-f06-arrival-1"
BASE_SHA = "22757b7222b463ce660059d254ab1d7fe9007a05"
PREREG = HERE / "PREREGISTRATION.md"
AMENDMENT_A1 = HERE / "AMENDMENT-A1.md"
PREREG_COMMIT = "22757b7222b463ce660059d254ab1d7fe9007a05"

# Slot-scratch (runner TMP; never inside the contribution directory).
SCRATCH = Path(os.environ.get("TMP", ".")) / ("f06_pins_" + ATTEMPT_ID[:8])
PINNED_ROOT = SCRATCH / "pinned_root"

C = "tools/monkey_campaign/contributions"

# (group, pinned path parts, sha256) -- prereg section 1.
PINS = [
    # evidence store (durable vault)
    ("store", ("MAT2-W04", "numerical", "w04_certificate.json"),
     "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598"),
    ("store", ("MAT2-W04", "numerical", "checks_receipt.json"),
     "05e28bbaffcf9d65db174ec9b83708d33705922ac506b1cee852a2f9790744c9"),
    ("store", ("MAT2-W09", "numerical", "out_of_envelope_receipt.json"),
     "0880a18a46b99e9463cde8f64fafc6daff82a9b78f04ea5e2960abef963cb4c7"),
    ("store", ("MAT2-W09", "numerical", "checks_receipt.json"),
     "e4cd94ae5c77a7dc9a5ecfba0e02ad4ae100ebabf1995132bbe9f41a3c2b4430"),
    ("store", ("MAT2-W09", "numerical", "falsifier_receipt.json"),
     "3a61cdbf43f7b11b4b284c7be969c5f0a36208556942f0832f1022fe87b1204c"),
    ("store", ("MAT2-F07", "numerical", "checks.json"),
     "0a7e94b545e4add955eb3f0315f8a783f00e2ebbcf4a2a44f43398b72916fb70"),
    ("store", ("MAT2-F05", "source", "TERRAIN_REPORT.md"),
     "2b4d9905be1f9f888a3ff33cb4c22a23f009053471c4fd609280bc7b2cba4672"),
    # base blobs (the shared object database at the package base)
    ("blob", (C, "MAT2-F02", "pins", "terrain_bundle.json"),
     "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52"),
    ("blob", (C, "MAT2-F02", "pins", "terrain_query.py"),
     "b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1"),
    ("blob", (C, "MAT2-F02", "pins", "terrain_bundle.py"),
     "c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e"),
    ("blob", (C, "MAT2-F02", "pins", "clearing_recipe.py"),
     "ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc"),
    ("blob", (C, "MAT2-F02", "pins", "clearing_declaration.json"),
     "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1"),
    ("blob", (C, "MAT2-F02", "pins", "trunk_declaration.json"),
     "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1"),
    ("blob", (C, "MAT2-F02", "pins", "f01_implementation.py"),
     "50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af"),
    ("blob", (C, "MAT2-F03", "assets", "trunk_01_mesh.json"),
     "3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7"),
    ("blob", (C, "MAT2-M06", "local_contact.py"),
     "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc"),
    ("blob", (C, "MAT2-M06", "contact_law.json"),
     "583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b"),
    ("blob", (C, "MAT2-F04", "implementation.py"),
     "5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083"),
    ("blob", (C, "MAT2-F07", "implementation.py"),
     "49a975c7a1a14238eb79bd5edcb0e96bbd5231a2cdf329dccacd282f65b36a94"),
    ("blob", (C, "MAT2-F07", "assets", "obstacle_declaration.json"),
     "73525a3de022d5b8d9901ca90fde77124904471f33a67f2f79a94f7ad1636769"),
    ("blob", (C, "MAT2-F07", "evidence", "route_trace.json"),
     "f159edd59fa2047326c130945a74d4451c164e38d7a8b371a5e6330c69d0b729"),
    ("blob", (C, "MAT2-F05", "evidence", "terrain_envelope_declaration.json"),
     "3fa7e5f4d91936012716f44212cb05f853e8335a9e561c5a53fb7902a5624208"),
    ("blob", (C, "MAT2-F05", "checks_receipt.json"),
     "cdc00269b928fcdd858a618acc8a824e6ea0f7a332e8673a3d0492d65b87b1e5"),
    ("blob", (C, "MAT2-W08", "PREREGISTRATION.md"),
     "00a04e08411ed079aee9e0ef43f9221c69abc84612f66311e4db4822f6c8412a"),
    ("blob", (C, "MAT2-W08", "receipts", "command_verification_receipt.json"),
     "bb9e014b160062d486002745571fd4485a50431cfdbc25038ebb9bed1171f787"),
    ("blob", (C, "MAT2-W09", "PREREGISTRATION.md"),
     "6a3e0f6f5e0a0d7cbad595e0d16285556608b93fa77ef77dc59c30ae962f9d7b"),
    ("blob", (C, "MAT2-W09", "out_of_envelope.py"),
     "7245739a746aaeb259a2720c97dbdfec4a88b77aed997cd0c9f961f5ca89d782"),
    ("blob", (C, "MAT2-W10", "PREREGISTRATION.md"),
     "394463ab4172590af881194980460913dac751cde77ba32aab6111c497eda655"),
    ("blob", (C, "MAT2-W10", "AMENDMENT-A1.md"),
     "9c32048ce80a33f9b40d5f41ee9bd4111deb307ccb65f6d2bf2c5776b3aa42de"),
    ("blob", (C, "MAT2-W10", "AMENDMENT-A2.md"),
     "f47b30f0244954ee18a0cddd37af2e633fcbe791e940a3a858c8cb3ccd04e837"),
    ("blob", (C, "MAT2-W10", "AMENDMENT-A3.md"),
     "caca29ac7df93fa2e569349a1b28e05b64039401dc59f314bfd897917a0c4b10"),
    ("blob", (C, "MAT2-W10", "command_model.py"),
     "0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa"),
    ("blob", (C, "MAT2-W10", "source_access.py"),
     "4eea1c5c9e10263b02f3a607a280d52f2a8f5862d651834e1794e22c80963ccc"),
    ("blob", (C, "MAT2-W10", "run_capture.py"),
     "a078928fcdbe78b7982d20fc362f7f9e021c3360c47523fb2af6cc564af9bf2a"),
    ("blob", (C, "MAT2-W10", "visualization.py"),
     "2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb"),
    ("blob", (C, "MAT2-W10", "make_report.py"),
     "b40b1f9ee349ee095e0b20a155d504f236f87e6177e96fdb15d17603eeb8a31d"),
    ("blob", (C, "MAT2-W10", "lint_report_numbers.py"),
     "c2f046439ad330a1d748468b20fefdfc452f67deaa64272b931f0eb8ccfd1405"),
    ("blob", (C, "MAT2-W10", "DEV_RUN_REFUSALS.md"),
     "5c88d0d1061dcee8466b5683dbaa771d8dbd6b357aa6297ae8957f85c3b0e6f2"),
    ("blob", (C, "MAT2-W10", "verify_inputs.py"),
     "25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6"),
    ("blob", (C, "MAT2-U01", "reconcile", "pinned_seam", "tools",
              "monkey_campaign", "product", "input_mapper.py"),
     "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44"),
    ("blob", (C, "MAT2-U01", "reconcile", "pinned_seam", "tools",
              "monkey_campaign", "product", "input_mapper_tests.py"),
     "95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e"),
    ("blob", (C, "MAT2-U01", "reconcile", "pinned_seam", "tools",
              "science_funnel", "typeb_export", "command_record.py"),
     "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e"),
    ("blob", ("tools", "monkey_campaign", "visual_capture.py"),
     "5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05"),
    # sealed lane machinery (identical to the W07-W10 pin table)
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
    ("lane", ("tools", "science_funnel", "validation",
              "upgrade_gate_20260920", "receipt.json"),
     "2c7794e6ff0c5c2d81c39536076ce1d6a0900333f4738549079afbe21012685a"),
    ("lane", ("tools", "creature_graph", "data", "authored",
              "project_program.json"),
     "3e5182f5a8bd85995f3dd0dac1ae24a27cdc0a9539e4da9ec0aef17018b1555c"),
    ("lane", ("tools", "science_funnel", "validation",
              "gait_controller_20260918", "derived_numbers.json"),
     "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"),
]


class Refusal(Exception):
    """A named refusal (the falsifier must be able to FAIL)."""


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


def amendment_a1_sha256() -> str:
    return sha_bytes(AMENDMENT_A1.read_bytes())


def require(condition, code: str = "", detail="") -> None:
    if not condition:
        raise Refusal(code + (": " + str(detail) if detail else ""))


def pin_path(group: str, parts: tuple) -> Path:
    if group == "blob":
        return PINNED_ROOT.joinpath(*parts)
    return (_GROUP_BASE[group]).joinpath(*parts)


_GROUP_BASE = {"store": STORE, "lane": LANE_REPO}


def verify(expect=None) -> list:
    """Verify all pins (or an override table for the FB bite arms)."""
    rows = []
    table = PINS if expect is None else expect
    for group, parts, expected in table:
        if group == "blob":
            data = sa.read_blob(BASE_SHA, "/".join(parts))
        else:
            path = pin_path(group, parts)
            if not path.is_file():
                raise Refusal("input_pin_missing:" + "/".join(parts))
            data = path.read_bytes()
        got = sha_bytes(data)
        ok = got == expected
        rows.append({"path": "/".join((group,) + parts),
                     "sha256": got, "expected": expected, "ok": ok})
        require(ok, "input_pin_mismatch:" + parts[-1] + ":" + got[:12])
    return rows


def verify_registry() -> dict:
    """READ-ONLY registry identity check (the criteria + the profile)."""
    con = sqlite3.connect("file:" + str(REGISTRY).replace("\\\\", "/")
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
    (byte-verified): the lane machinery PLUS the base-blob trees, ONE import
    namespace. The U01 pinned_seam blobs extract at their seam-relative
    paths; the F02/F07/F05/W08/W09/W10 authority files extract at their
    contribution-relative paths (the pinned F07 module resolves its own
    pin tree from there)."""
    seam_head = (C, "MAT2-U01", "reconcile", "pinned_seam")
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
            target_parts = (parts[4:] if (len(parts) > 4
                and parts[:4] == seam_head) else parts)
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
    bytes are pin-verified BEFORE this loader runs)."""
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


def w08_command_receipt() -> dict:
    return json.loads((PINNED_ROOT / C / "MAT2-W08" / "receipts" /
                       "command_verification_receipt.json").read_bytes()
                      .decode("utf-8"))


def w09_out_of_envelope_receipt() -> dict:
    return json.loads((STORE / "MAT2-W09" / "numerical" /
                       "out_of_envelope_receipt.json").read_bytes()
                      .decode("utf-8"))


def f07_route_trace() -> dict:
    return json.loads((PINNED_ROOT / C / "MAT2-F07" / "evidence" /
                       "route_trace.json").read_bytes().decode("utf-8"))


def f05_terrain_envelope() -> dict:
    return json.loads((PINNED_ROOT / C / "MAT2-F05" / "evidence" /
                       "terrain_envelope_declaration.json").read_bytes()
                      .decode("utf-8"))


def main() -> int:
    rows = verify()
    reg = verify_registry()
    record = {
        "schema": "chimera.f06_input_pins.v1",
        "task_id": TASK_SHORT,
        "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "agent_id": AGENT_ID,
        "base_sha256": BASE_SHA,
        "prereg_commit": PREREG_COMMIT,
        "preregistration_sha256": prereg_sha256(),
        "criteria_sha256": CRITERIA_SHA256,
        "pins": rows,
        "registry": reg,
        "source_repo": sa.source_repo(),
        "determinism": {"canonical_json": True, "newline": "\\n",
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
