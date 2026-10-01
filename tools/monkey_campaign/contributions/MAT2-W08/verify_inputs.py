#!/usr/bin/env python3
"""MAT2-W08: the frozen input-pin verifier (prereg section 1).

Verifies every pinned upstream artifact byte-exact BEFORE anything is
loaded or executed; any drift is the named refusal `input_pin_mismatch`.
Pins: the W04/P06/U01/W07 records in the evidence store, the sealed lane
machinery at the pass3-integ lane repo, the base-blob seam bytes read
READ-ONLY from the shared repository's object database at the package base
(through the DECLARED source_access.py — NO_WORKTREES law), and the card
identity READ-ONLY from the registry (`file:...?mode=ro`; criteria mismatch
= `criteria_pin_mismatch`). Importable: the run, the checks and the capture
all call verify() first.

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

CARD_ID = "MAT2-W08"
TASK_SHORT = "W08"
CRITERIA_SHA256 = "f38c2c96ef22cca080accba4b71b3370ca5b0272b824975c650cd543db9821ea"
ATTEMPT_ID = "c38b22e505874601aa3f3a3ba9035e4d"
AGENT_ID = "wk-w08b-arrival-1"
BASE_SHA = "8b285ee4301a8ed42be54a1924af5db019f9fb20"
PREREG = HERE / "PREREGISTRATION.md"

# Slot-scratch (runner TMP; never inside the contribution directory).
SCRATCH = Path(os.environ.get("TMP", ".")) / ("w08b_pins_" + ATTEMPT_ID[:8])
PINNED_ROOT = SCRATCH / "pinned_root"

# (group, pinned path parts, sha256) — prereg section 1, verbatim.
PINS = [
    # evidence store (durable vault)
    ("store", ("MAT2-W04", "numerical", "w04_certificate.json"),
     "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598"),
    ("store", ("MAT2-W04", "numerical", "w04_freeze_manifest.json"),
     "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29"),
    ("store", ("MAT2-P06", "numerical", "numerical"),
     "a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8"),
    ("store", ("MAT2-U01", "numerical", "qualification_receipt.json"),
     "94887cc14ba6d2fc7a76c04949d5015cbfada899a817c3acb497e5d53a7a0c61"),
    ("store", ("MAT2-W07", "numerical", "native_load_receipt.json"),
     "4f5aac081a3a07fd56733d84ac3069950b00309e54f6402e78ebd22c55e490e9"),
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
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-W07",
              "receipts", "native_load_receipt.json"),
     "4f5aac081a3a07fd56733d84ac3069950b00309e54f6402e78ebd22c55e490e9"),
    ("blob", ("tools", "monkey_campaign", "visual_capture.py"),
     "5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05"),
    # sealed lane machinery (identical to W07's pin table)
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
]

_GROUP_BASE = {"store": STORE, "lane": LANE_REPO}


class Refusal(Exception):
    """A named refusal (the falsifier must be able to FAIL)."""


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


def require(condition, code: str) -> None:
    if not condition:
        raise Refusal(code)


def pin_path(group: str, parts: tuple) -> Path:
    if group == "blob":
        return PINNED_ROOT.joinpath(*parts)
    return _GROUP_BASE[group].joinpath(*parts)


def verify(expect=None) -> list:
    """Verify all pins (or an override table for the FB1 bite arm)."""
    rows = []
    table = PINS if expect is None else expect
    for group, parts, expected in table:
        if group == "blob":
            data = sa.read_blob(BASE_SHA, "/".join(parts))
        else:
            data = pin_path(group, parts).read_bytes()
        got = sha_bytes(data)
        rows.append({"path": "/".join((group,) + parts),
                     "sha256": got, "expected": expected,
                     "ok": got == expected})
        require(got == expected,
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
    same `tools` package as the machinery — no second namespace exists."""
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


def w04_certificate() -> dict:
    return json.loads((STORE / "MAT2-W04" / "numerical" / "w04_certificate.json")
                      .read_bytes().decode("utf-8"))


def p06_limits() -> dict:
    return json.loads((STORE / "MAT2-P06" / "numerical" / "numerical")
                      .read_bytes().decode("utf-8"))


def u01_receipt() -> dict:
    return json.loads((STORE / "MAT2-U01" / "numerical" / "qualification_receipt.json")
                      .read_bytes().decode("utf-8"))


def w07_receipt() -> dict:
    return json.loads((STORE / "MAT2-W07" / "numerical" / "native_load_receipt.json")
                      .read_bytes().decode("utf-8"))


def main() -> int:
    rows = verify()
    reg = verify_registry()
    record = {
        "schema": "chimera.w08_input_pins.v1",
        "task_id": TASK_SHORT,
        "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "agent_id": AGENT_ID,
        "base_sha256": BASE_SHA,
        "preregistration_sha256": prereg_sha256(),
        "criteria_sha256": CRITERIA_SHA256,
        "pins": rows,
        "registry": reg,
        "source_repo": sa.source_repo(),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B verify_inputs.py"},
    }
    sys.stdout.write(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    print("pins verified:", len(rows), "| criteria:", got_short(reg))
    return 0


def got_short(reg):
    return reg.get("criteria_sha256", "")[:12]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        sys.exit(2)
