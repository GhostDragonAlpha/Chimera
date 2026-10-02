#!/usr/bin/env python3
"""MAT2-X04: the frozen input-pin verifier (prereg section 1).

The X04 ADD-ON pin layer. The certified-line pin table (W04 certificate
machinery, lane repo machinery, scene, F04 rasterizer, terrain, visual
validator, W09 supervisor) is verified by W10's OWN verify_inputs.py,
extracted UNMODIFIED at the package base and executed first (prereg:
"reuse verified work; do not repeat completed implementation"). This module
adds and verifies exactly the X04 pins: the W10 harness files, the seam
lineage references, the M12 render-binding law module + capture precedent,
the F08/A09 dependency receipts, the P06/W10 store records, the card
identity and the `presentation` profile READ-ONLY from the registry
(profile check BEFORE capture; G7).

Run:  python -B verify_inputs_x04.py
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

CARD_ID = "MAT2-X04"
CRITERIA_SHA256 = ("e5c1d5517a78d74f22eb4692236dcd716d0f82c9e49c9586"
                   "023b913a56a0e72a")
ATTEMPT_ID = "50ff462483fd487db3ec9d38fa656f92"
AGENT_ID = "wk-x04-arrival-1"
BASE_SHA = "a07ac859d4ef16bb34d4006a75c4de8dbee462b4"
# The separate-first prereg commit (the Lieutenant's publication; the ONLY
# commit between the base and the implementation). Verified at run: its
# parent IS the package base and its PREREGISTRATION.md blob IS these bytes.
PREREG_COMMIT = "06f76dd1d55c42628d72aa473526f6f8ec3f0a3e"
PREREG = HERE / "PREREGISTRATION.md"

SCRATCH = Path(os.environ.get("TMP", ".")) / ("x04_pins_" + ATTEMPT_ID[:8])
PINNED_ROOT = SCRATCH / "pinned_root"

W10_DIR = ("tools", "monkey_campaign", "contributions", "MAT2-W10")

# (group, pinned path parts, sha256) — prereg section 1 (X04 add-on pins).
PINS = [
    # evidence store (durable vault)
    ("store", ("MAT2-P06", "numerical", "numerical"),
     "a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8"),
    ("store", ("MAT2-W10", "numerical", "walking_demo_receipt.json"),
     "2fa7dbf180db6090611fdc0d074ebe80d79b43eb25a4a7162e218cbacd22aa02"),
    ("store", ("MAT2-W10", "numerical", "checks_receipt.json"),
     "999fc693dab04199fe3459ff332577d1d73a7e9506a335e2db5f0a3f7ec142b2"),
    ("store", ("MAT2-F08", "numerical", "checks.json"),
     "837644333f9412f9074cc47d26dbf06f38b202613fac1e6f49097e4ad20a0da5"),
    ("store", ("MAT2-M12", "numerical", "experiment_receipt.json"),
     "db516434a1034d0703a362aaecfd7b983b9a38d36dbcd390b31d2e15f1b4c589"),
    ("store", ("MAT2-M12", "numerical", "falsifier_receipt.json"),
     "f42004d6320cb54ffa167a95ab555d78af8bdf6f88e55b481467e8cc5632766c"),
    # base blobs (the shared object database at the package base)
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
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-U01",
              "reconcile", "pinned_seam", "tools", "monkey_campaign",
              "product", "input_mapper.py"),
     "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-U01",
              "reconcile", "pinned_seam", "tools", "science_funnel",
              "typeb_export", "command_record.py"),
     "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M12",
              "m12_lod.py"),
     "f08fd1d2e24f8b72b9833936d49db23cae9d5ef8c3bbedd1bdc2b9ec792849cc"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M12",
              "capture_manifest.json"),
     "0ea48c70af67b9336a3b95ca03a5a6ad0ccdad7a0d80db1e77c6dffff8139d40"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F08",
              "report.md"),
     "fcd973c335a1163694bc4a57a87550890e94f214e0c92d06dbec18756b2033c1"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-A09",
              "report.md"),
     "feb132dca3b2da0df58bc7fea9bd27581613fb48999beb9c4be8be3eacd7daf2"),
    ("blob", ("tools", "monkey_campaign", "visual_capture.py"),
     "5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05"),
]


class Refusal(RuntimeError):
    pass


def require(condition, code: str) -> None:
    if not condition:
        raise Refusal(code)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


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
    require(profile.get("id") == "presentation"
            and profile.get("kind") == "motion",
            "criteria_pin_mismatch:profile_identity")
    return {"card_state": card.get("state"), "criteria_sha256": got,
            "registry_revision": state.get("revision"),
            "attempt_agent": attempt_agent,
            "attempt_state": (attempt.get("state")
                              if isinstance(attempt, dict) else None),
            "done_when": task.get("done_when"),
            "observation": task.get("observation"),
            "falsifier": task.get("falsifier"),
            "calculation_ids": task.get("calculation_ids"),
            "profile": {"id": profile.get("id"), "kind": profile.get("kind"),
                        "subject": profile.get("subject"),
                        "scenario": profile.get("scenario"),
                        "views": profile.get("views"),
                        "clean_view_required":
                            profile.get("clean_view_required"),
                        "diagnostic_layers":
                            profile.get("diagnostic_layers"),
                        "camera_required_fields":
                            profile.get("camera_required_fields"),
                        "numerical_evidence_required":
                            profile.get("numerical_evidence_required"),
                        "nonvisual_reason": profile.get("nonvisual_reason"),
                        "falsifier": profile.get("falsifier")}}


def verify_prereg_commit() -> dict:
    """The prereg-first law, executed: the separate-first commit exists,
    sits DIRECTLY on the package base, touches ONLY PREREGISTRATION.md, and
    its blob is byte-identical to THIS card's frozen file."""
    import subprocess
    def git(*args):
        out = subprocess.run(["git", "-C", sa.source_repo(), *args],
                             capture_output=True, check=False)
        require(out.returncode == 0,
                "prereg_commit_unreadable:" + args[0] + ":"
                + out.stderr.decode("utf-8", "replace")[:120])
        return out.stdout
    kind = git("cat-file", "-t", PREREG_COMMIT).decode().strip()
    require(kind == "commit", "prereg_commit_not_commit:" + kind)
    parent = git("rev-parse", PREREG_COMMIT + "^").decode().strip()
    require(parent == BASE_SHA,
            "prereg_commit_parent_not_base:" + parent)
    changed = git("diff", "--name-only", BASE_SHA, PREREG_COMMIT
                  ).decode().strip().splitlines()
    require(changed == ["tools/monkey_campaign/contributions/MAT2-X04/"
                        "PREREGISTRATION.md"],
            "prereg_commit_touches_more:" + repr(changed))
    blob = git("cat-file", "blob", PREREG_COMMIT
               + ":tools/monkey_campaign/contributions/MAT2-X04/"
                 "PREREGISTRATION.md")
    got = sha_bytes(blob)
    require(got == prereg_sha256(),
            "prereg_commit_bytes_mismatch:" + got[:12])
    return {"commit": PREREG_COMMIT, "parent": parent,
            "preregistration_sha256": got,
            "changed_files": changed}


def extract_x04_tree() -> Path:
    """Materialize the X04 pinned blobs under slot scratch (byte-verified).

    The W10 machinery extracts under its own contribution path so its
    sibling imports (verify_inputs, command_model, visualization) resolve to
    the SAME pinned bytes; walking_demo's pinned imports resolve through the
    W10 extraction's stripped namespace (bootstrap_pinned_imports).
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
    extraction; its scratch/extraction identity is its own; nothing it
    writes leaves slot scratch.
    """
    wvi = load_pinned_module("w10_verify_inputs",
                             W10_DIR + ("verify_inputs.py",))
    rows = wvi.verify()
    reg = wvi.verify_registry()
    root = wvi.extract_pinned_tree()
    wvi.bootstrap_pinned_imports()
    # walking_demo/command_model/visualization resolve through THIS card's
    # byte-verified extraction of the W10 files; their sibling imports then
    # resolve to the SAME pinned bytes, never to this card's files.
    w10_dir = str(PINNED_ROOT.joinpath(*W10_DIR))
    while w10_dir in sys.path:
        sys.path.remove(w10_dir)
    sys.path.insert(0, w10_dir)
    return {"w10_pin_rows": len(rows), "w10_extraction": str(root),
            "w10_registry": {
                k: reg[k] for k in ("card_state", "criteria_sha256")}}


def p06_limits() -> dict:
    """The frozen P06 caller-data this card consumes (prereg section 6)."""
    doc = json.loads((STORE / "MAT2-P06" / "numerical" / "numerical")
                     .read_bytes().decode("utf-8"))
    carried = {lim.get("id"): lim for lim in doc.get("carried_limits", [])}
    require("ui-poll-cadence-ms" in carried,
            "p06_limits_missing:ui-poll-cadence-ms")
    requests = {r.get("id"): r
                for r in doc.get("operator_decision_requests", [])}
    require("network-latency-sla-ms" in requests,
            "p06_limits_missing:network-latency-sla-ms-decision-request")
    return {"ui_poll_cadence_ms":
            carried["ui-poll-cadence-ms"].get("value"),
            "camera_visible_player_outcomes":
                doc.get("camera_visible_player_outcomes"),
            "latency_sla_decision": requests["network-latency-sla-ms"]}


def main() -> int:
    rows = verify()
    reg = verify_registry()
    prereg_commit = verify_prereg_commit()
    extract_x04_tree()
    w10 = w10_layer()
    limits = p06_limits()
    summary = {"schema": "chimera.x04_input_pins.v1",
               "card": CARD_ID, "attempt_id": ATTEMPT_ID,
               "agent_id": AGENT_ID, "base_sha256": BASE_SHA,
               "preregistration_sha256": prereg_sha256(),
               "prereg_commit": prereg_commit,
               "pin_rows": rows, "registry": reg, "w10_layer": w10,
               "p06_caller_limits": {"ui_poll_cadence_ms":
                                     limits["ui_poll_cadence_ms"]}}
    out = os.environ.get("CHIMERA_OUTPUT_DIR")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "pins_x04.json").write_bytes(
            json.dumps(summary, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"),
                       allow_nan=False).encode("utf-8") + b"\n")
    print("pins: %d X04 rows green; W10 layer %d rows green; profile %s/%s"
          % (len(rows), w10["w10_pin_rows"], reg["profile"]["id"],
             reg["profile"]["kind"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as r:
        print("REFUSAL: " + str(r), file=sys.stderr)
        sys.exit(2)
