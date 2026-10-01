#!/usr/bin/env python3
"""MAT2-U07: the frozen input-pin verifier (prereg section 1).

The U07 ADD-ON pin layer. The certified-line pin table (W04 certificate
machinery, lane repo machinery, scene, F04 rasterizer, terrain, visual
validator, W09 supervisor, the W10/W08/W09/G07 records) is verified by W10's
OWN verify_inputs.py, extracted UNMODIFIED at the package base and executed
first (prereg: "verified work is reused, not repeated"). This module adds and
verifies exactly the U07 pins: the accepted trace/adapter/camera-law/focus
modules, the W10 harness files, the P06/W08/W10 records, the in-tree seam
equality to the U01 pinned lineage, the card identity and the `controls`
profile READ-ONLY from the registry (profile check BEFORE capture; G7).

Run:  python -B verify_inputs_u07.py
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
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

import source_access as sa  # noqa: E402  (the DECLARED git blob reader)

CARD_ID = "MAT2-U07"
CRITERIA_SHA256 = "029dc39358471b06fed736c4712d6b1d92d4b1c22178e20027dfff53cbdc1532"
ATTEMPT_ID = "5e2bc3cb1fec4305911a1048b600723d"
AGENT_ID = "wk-u07-arrival-1"
BASE_SHA = "a07ac859d4ef16bb34d4006a75c4de8dbee462b4"
PREREG = HERE / "PREREGISTRATION.md"

SCRATCH = Path(os.environ.get("TMP", ".")) / ("u07_pins_" + ATTEMPT_ID[:8])
PINNED_ROOT = SCRATCH / "pinned_root"

W10_DIR = ("tools", "monkey_campaign", "contributions", "MAT2-W10")

# (group, pinned path parts, sha256) — prereg section 1 (U07 add-on pins).
PINS = [
    # evidence store (durable vault)
    ("store", ("MAT2-P06", "numerical", "numerical"),
     "a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8"),
    ("store", ("MAT2-U01", "numerical", "qualification_receipt.json"),
     "94887cc14ba6d2fc7a76c04949d5015cbfada899a817c3acb497e5d53a7a0c61"),
    ("store", ("MAT2-W08", "numerical", "checks_receipt.json"),
     "cd9998ab612b0e320b657a196d672e668199bb92188527d887aafeb321014c37"),
    ("store", ("MAT2-W10", "numerical", "walking_demo_receipt.json"),
     "2fa7dbf180db6090611fdc0d074ebe80d79b43eb25a4a7162e218cbacd22aa02"),
    ("store", ("MAT2-W10", "numerical", "checks_receipt.json"),
     "999fc693dab04199fe3459ff332577d1d73a7e9506a335e2db5f0a3f7ec142b2"),
    # base blobs (the shared object database at the package base)
    ("blob", ("tools", "monkey_campaign", "contributions", "I-U07-TRACE",
              "input_trace.py"),
     "c8f4e4442a3ceedecd9c636857eda92642d26ec535d45f2c91a3ce9fd4550a57"),
    ("blob", ("tools", "monkey_campaign", "contributions",
              "I-U07-TRACE-FOLLOWUP", "adapter.py"),
     "8522cbefb176fbd512f7191dfc79e8ff6dd45d9ed51fe4d34b23c307829df723"),
    ("blob", ("tools", "monkey_campaign", "contributions",
              "I-U07-TRACE-FOLLOWUP", "reference", "tools",
              "monkey_campaign", "product", "follow_camera.py"),
     "d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-U02",
              "reference", "tools", "monkey_campaign", "product",
              "focus_policy.py"),
     "e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0"),
    ("blob", W10_DIR + ("command_model.py",),
     "0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa"),
    ("blob", W10_DIR + ("visualization.py",),
     "2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb"),
    ("blob", W10_DIR + ("verify_inputs.py",),
     "25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6"),
    ("blob", W10_DIR + ("walking_demo.py",),
     "fb394677306bcb3d808271cce72212c000b82455567e74c1090d3c1003d90ea1"),
    ("blob", W10_DIR + ("run_capture.py",),
     "a078928fcdbe78b7982d20fc362f7f9e021c3360c47523fb2af6cc564af9bf2a"),
    ("blob", W10_DIR + ("lint_report_numbers.py",),
     "c2f046439ad330a1d748468b20fefdfc452f67deaa64272b931f0eb8ccfd1405"),
    ("blob", ("tools", "monkey_campaign", "visual_capture.py"),
     "5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05"),
    # the seam bytes equal to the U01 pinned lineage, at their REAL base
    # paths (the FOLLOWUP reference copies; the seam is NOT in-tree — the
    # runtime resolves it through the W10 extraction's stripped namespace)
    ("blob", ("tools", "monkey_campaign", "contributions",
              "I-U07-TRACE-FOLLOWUP", "reference", "tools",
              "monkey_campaign", "product", "input_mapper.py"),
     "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44"),
    ("blob", ("tools", "monkey_campaign", "contributions",
              "I-U07-TRACE-FOLLOWUP", "reference", "tools",
              "monkey_campaign", "product", "input_mapper_tests.py"),
     "95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e"),
    ("blob", ("tools", "monkey_campaign", "contributions",
              "I-U07-TRACE-FOLLOWUP", "reference", "tools",
              "monkey_campaign", "product", "follow_camera_tests.py"),
     "4d75164ff6a16bf0d817332b7c5229513750782727ad1a23911025dc93d31b27"),
    ("blob", ("tools", "monkey_campaign", "contributions",
              "I-U07-TRACE-FOLLOWUP", "reference", "tools",
              "science_funnel", "typeb_export", "command_record.py"),
     "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e"),
]

# The U10 extractor strips this prefix (the W08 import-namespace law: two
# `tools` roots collide).
SEAM_PREFIX = ("tools", "monkey_campaign", "product")


class Refusal(RuntimeError):
    pass


def require(condition, code: str) -> None:
    if not condition:
        raise Refusal(code)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


def amendment_a1_sha256() -> str:
    return sha_bytes((HERE / "AMENDMENT-A1.md").read_bytes())


def amendment_a2_sha256() -> str:
    return sha_bytes((HERE / "AMENDMENT-A2.md").read_bytes())


def amendment_a3_sha256() -> str:
    return sha_bytes((HERE / "AMENDMENT-A3.md").read_bytes())


def pin_path(group: str, parts: tuple) -> Path:
    if group == "blob":
        return PINNED_ROOT.joinpath(*parts)
    return STORE.joinpath(*parts)


def verify() -> list:
    rows = []
    for group, parts, expected in PINS:
        if group == "blob":
            data = sa.read_blob(BASE_SHA, "/".join(parts))
        else:
            path = pin_path(group, parts)
            require(path.exists(), "input_pin_missing:" + "/".join(parts))
            data = path.read_bytes()
        got = sha_bytes(data)
        ok = got == expected
        require(ok, "input_pin_mismatch:" + parts[-1] + ":" + got[:12])
        rows.append({"path": "/".join((group,) + parts), "sha256": got,
                     "expected": expected, "ok": True})
    return rows


def verify_registry() -> dict:
    """READ-ONLY registry identity + profile check (BEFORE any capture; G7)."""
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
    task = card["spec"]["ontology_qualification"]["task"]
    profile = task["verification_profile"]
    require(profile.get("id") == "controls" and profile.get("kind") == "motion",
            "criteria_pin_mismatch:profile_identity")
    return {"card_state": card.get("state"), "criteria_sha256": got,
            "registry_revision": state.get("revision"),
            "attempt_agent": attempt_agent,
            "attempt_state": attempt.get("state") if isinstance(attempt, dict) else None,
            "done_when": task.get("done_when"),
            "observation": task.get("observation"),
            "falsifier": task.get("falsifier"),
            "calculation_ids": task.get("calculation_ids"),
            "profile": {"id": profile.get("id"), "kind": profile.get("kind"),
                        "subject": profile.get("subject"),
                        "scenario": profile.get("scenario"),
                        "views": profile.get("views"),
                        "clean_view_required": profile.get("clean_view_required"),
                        "diagnostic_layers": profile.get("diagnostic_layers"),
                        "camera_required_fields": profile.get("camera_required_fields"),
                        "numerical_evidence_required":
                            profile.get("numerical_evidence_required"),
                        "falsifier": profile.get("falsifier")}}


def extract_u07_tree() -> Path:
    """Materialize the U07 pinned blobs under slot scratch (byte-verified).

    Layout law: product seam modules (input_mapper, focus_policy,
    follow_camera) extract at their REPO-RELATIVE paths so the pinned imports
    resolve inside ONE `tools` namespace beside the W10 machinery extraction;
    the follow_camera/focus_policy reference copies keep their provenance
    path under contributions/ as well.
    """
    if PINNED_ROOT.exists():
        shutil.rmtree(PINNED_ROOT)
    require(sa.resolve_base(BASE_SHA) == "commit",
            "input_pin_mismatch:base_unresolvable")
    for group, parts, expected in PINS:
        if group != "blob":
            continue
        data = sa.read_blob(BASE_SHA, "/".join(parts))
        require(sha_bytes(data) == expected,
                "input_pin_mismatch:extract:" + parts[-1])
        target = PINNED_ROOT.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return PINNED_ROOT


def load_pinned_module(name: str, rel_parts: tuple):
    """Import a pinned NON-package module by file path (import identity)."""
    path = PINNED_ROOT.joinpath(*rel_parts)
    require(path.exists(), "input_pin_missing:" + "/".join(rel_parts))
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def w10_layer() -> dict:
    """Execute the W10 certified-line pin/extract layer, UNMODIFIED.

    W10's verify_inputs.py is loaded from THIS card's byte-verified
    extraction (its own pins include its own prereg and its own base blobs,
    all contained in this package base). Its scratch/extraction identity is
    its own; nothing it writes leaves slot scratch.
    """
    wvi = load_pinned_module("w10_verify_inputs",
                             W10_DIR + ("verify_inputs.py",))
    rows = wvi.verify()
    reg = wvi.verify_registry()
    root = wvi.extract_pinned_tree()
    wvi.bootstrap_pinned_imports()
    # walking_demo/command_model/visualization resolve through THIS card's
    # byte-verified extraction of the W10 files (W10's own extraction holds
    # the certified-line machinery but not W10's own contribution files);
    # their sibling imports (verify_inputs, command_model) then resolve to
    # the SAME pinned bytes, never to this card's files.
    w10_dir = str(PINNED_ROOT.joinpath(*W10_DIR))
    while w10_dir in sys.path:
        sys.path.remove(w10_dir)
    sys.path.insert(0, w10_dir)
    return {"w10_pin_rows": len(rows), "w10_extraction": str(root),
            "w10_registry": {
                k: reg[k] for k in ("card_state", "criteria_sha256")}}


def p06_limits() -> dict:
    """The frozen P06 caller-data limits this card consumes (prereg section 6)."""
    doc = json.loads((STORE / "MAT2-P06" / "numerical" / "numerical")
                     .read_bytes().decode("utf-8"))
    carried = {lim.get("id"): lim for lim in doc.get("carried_limits", [])}
    require("ui-poll-cadence-ms" in carried,
            "p06_limits_missing:ui-poll-cadence-ms")
    requests = {r.get("id"): r for r in doc.get("operator_decision_requests", [])}
    require("network-latency-sla-ms" in requests,
            "p06_limits_missing:network-latency-sla-ms-decision-request")
    sla = requests["network-latency-sla-ms"]
    # Honest negative A2 (prereg section 8): the wall-clock SLA must STILL be
    # an open operator decision. If P06 ever records a resolved numeric, the
    # prereg's limits law must be re-frozen BEFORE any run claims it.
    require(sla.get("class") == "OPERATOR_DECISION_REQUESTED"
            and sla.get("source") is None,
            "p06_sla_state_changed:recheck_prereg_honest_negative_a2")
    return {"ui_poll_cadence_ms": carried["ui-poll-cadence-ms"].get("value"),
            "ui_poll_cadence_source": carried["ui-poll-cadence-ms"].get("source"),
            "camera_visible_player_outcomes":
                doc.get("camera_visible_player_outcomes"),
            "latency_sla_decision": sla}


def main() -> int:
    rows = verify()
    reg = verify_registry()
    extract_u07_tree()
    w10 = w10_layer()
    limits = p06_limits()
    summary = {"schema": "chimera.u07_input_pins.v1",
               "card": CARD_ID, "attempt_id": ATTEMPT_ID,
               "agent_id": AGENT_ID, "base_sha256": BASE_SHA,
               "preregistration_sha256": prereg_sha256(),
               "pin_rows": rows, "registry": reg, "w10_layer": w10,
               "p06_caller_limits": {"ui_poll_cadence_ms":
                                     limits["ui_poll_cadence_ms"]}}
    out = os.environ.get("CHIMERA_OUTPUT_DIR")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "pins_u07.json").write_bytes(
            json.dumps(summary, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False).encode("utf-8")
            + b"\n")
    print("pins: %d U07 rows green; W10 layer %d rows green; profile %s/%s"
          % (len(rows), w10["w10_pin_rows"], reg["profile"]["id"],
             reg["profile"]["kind"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as r:
        print("REFUSAL: " + str(r), file=sys.stderr)
        sys.exit(2)
