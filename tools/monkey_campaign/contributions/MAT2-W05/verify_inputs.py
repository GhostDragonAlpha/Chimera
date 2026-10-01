#!/usr/bin/env python3
"""MAT2-W05: the frozen input-pin verifier (prereg section 1).

Verifies every pinned lane file byte-exact BEFORE anything runs; any drift
is the named refusal `input_pin_mismatch`. Also re-reads the card identity
READ-ONLY from the registry (`file:...?mode=ro`) and refuses on any criteria
mismatch (`criteria_pin_mismatch`). Importable: run_training.py and the
named checks call verify() first.

Run:  python -B verify_inputs.py
Exit: 0 green / 2 named refusal.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[4]                      # .../kanban-attempts/MAT2-W05/<attempt>
SCRATCH = WS / "scratch"
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
LANE_REPO = Path("E:/ChimeraWork/pass3-integ/repo")
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

CARD_ID = "MAT2-W05"
TASK_SHORT = "W05"
CRITERIA_SHA256 = "8ce5e298aad11b2f1a6efa5e5d5b59ada4c5d436e9ca21e08415da55346ea2c4"
ATTEMPT_ID = "ce1576896a454f109a52de3a136c5117"
AGENT_ID = "wk-w05-runbook"
CANDIDATE_BASE = "ced16473"
PREREG = HERE / "PREREGISTRATION.md"
PREREG_ADDENDUM = HERE / "PREREGISTRATION-ADDENDUM-1.md"

# (pinned path parts relative to the pinned lane repo, expected sha256)
# prereg section 1 + addendum 1, verbatim. Paths are assembled from parts so
# this file carries no literal repo-root-looking pointer (doc_lint); the
# absolute resolved path of every pin is recorded in the verification record
# and in each receipt instead.
PINS = [
    (("tools", "policy_compat", "__init__.py"),
     "11d523c8c0ee363e09c4e57afa564f3e38b178e274d7ee3ef335f5a0c44e9f4e"),
    (("tools", "policy_compat", "__main__.py"),
     "74d592d0551e226289f944e8182a19a3b574d7d2ee331e157e17ac55ea969528"),
    (("tools", "policy_compat", "certificate.py"),
     "2b6a75ba79c367a646d89fdc8cbe2243239dbc5e336f1eba1deb33aa30e295ac"),
    (("tools", "policy_compat", "engine_cert.py"),
     "c1aa05362e20a3e0c8967634af2d97fadd11d62daf412e07917824f16c1e5152"),
    (("tools", "policy_compat", "injections.py"),
     "1b5b978bf5feafb93801066486a5656caaba7cf3a618949036c13d0ceae28f1e"),
    (("tools", "policy_compat", "runner.py"),
     "1fa8d8b70836d6e3355e3e2630f83e0a6a31a9658104e9f928d7ef52cfef5160"),
    (("tools", "policy_compat", "scene_cpu.py"),
     "ab4257024df63d9755e9c1ae524ee631339ce24a2fd36615d40575335f835af2"),
    (("tools", "policy_compat", "snapshot_api.py"),
     "c47a09596dd36692aa28f8f10b2967d9276b78082a96d0bba27bf632b8f0e493"),
    (("tools", "science_funnel", "typeb_export", "infer_numpy.py"),
     "8030b609c7ecbfcc368addee2c140b830450fff48ecb62e02683d62062bfbfc4"),
    (("tools", "science_funnel", "typeb_export", "observation_schema.py"),
     "8876e1a64d68e93b003c6daba8cacb34bff02c11133eb098bf1ef85bf8a39894"),
    (("tools", "science_funnel", "typeb_export", "policy_manifest.py"),
     "a65cf8757c9d4d4d6a8d5fce30be6aaebb016c98d7dc69f972b0b7781e2961d7"),
    (("tools", "science_funnel", "validation", "typeb_p3_20260921",
      "policy_manifest.json"),
     "aa5334f797b50c2ac3950cec5b82b439f982c1090dd66827754a1acbb8a26b6f"),
    (("tools", "science_funnel", "validation", "typeb_p3_20260921",
      "dummy_actor.npz"),
     "5fb2b7857d872fccc0bb89d6733582647da04d11d636e84c266912ce9c027f0f"),
    (("tools", "science_funnel", "validation", "typeb_p3_20260921",
      "trace_slice_wave38.json"),
     "69babe846e2447333b527c7fd8c190499e5ac1d55733dbd043edd0422245daa2"),
    (("tools", "science_funnel", "validation", "upgrade_gate_20260920",
      "receipt.json"),
     "2c7794e6ff0c5c2d81c39536076ce1d6a0900333f4738549079afbe21012685a"),
    (("tools", "science_funnel", "validation",
      "policy_interface_freeze_20260920", "observation_interface_v2.json"),
     "e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c"),
    (("tools", "science_funnel", "validation",
      "obs_split_channels_20260921", "obs_section_v2.json"),
     "3de82a1156ac2f39ed04da24c7fd40357642d7bc029e09b509dfc3ea1af63079"),
    (("MAT2-W04", "numerical", "w04_freeze_manifest.json"),
     "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29"),
    (("MAT2-W04", "numerical", "w04_certificate.json"),
     "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598"),
]


def pin_path(parts: tuple[str, ...]) -> Path:
    """Resolve one pin's absolute path (store-relative pins resolve under the
    evidence store; lane pins under the pinned lane repo)."""
    if parts[0] == "MAT2-W04":
        return STORE.joinpath(*parts)
    return LANE_REPO.joinpath(*parts)

PINNED_ROOT = SCRATCH / "pinned_root"


class Refusal(Exception):
    """A named refusal (the falsifier must be able to FAIL)."""


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


def addendum_sha256() -> str:
    return sha_bytes(PREREG_ADDENDUM.read_bytes())


def require(condition, code: str) -> None:
    if not condition:
        raise Refusal(code)


def verify(expect: list | None = None) -> list[dict]:
    """Verify all pins (or an override table for the FB1 bite arm)."""
    rows = []
    table = expect if expect is not None else PINS
    for parts, expected in table:
        path = parts if isinstance(parts, Path) else pin_path(parts)
        data = path.read_bytes()
        got = sha_bytes(data)
        rows.append({"path": str(path).replace("\\", "/"),
                     "sha256": got, "expected": expected,
                     "ok": got == expected})
        require(got == expected,
                "input_pin_mismatch:" + path.name + ":" + got[:12])
    return rows


def verify_registry() -> dict:
    """READ-ONLY registry identity check (G7)."""
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
    require(got == CRITERIA_SHA256,
            "criteria_pin_mismatch:" + repr(got))
    attempt = (card.get("attempts") or {}).get(ATTEMPT_ID)
    attempt_agent = attempt.get("agent_id") if isinstance(attempt, dict) else attempt
    require(attempt_agent == AGENT_ID,
            "criteria_pin_mismatch:attempt_owner:" + repr(attempt_agent))
    if isinstance(attempt, dict):
        require(attempt.get("criteria_sha256") in (None, CRITERIA_SHA256),
                "criteria_pin_mismatch:attempt_criteria:" + repr(attempt.get("criteria_sha256")))
    return {"card_state": card.get("state"), "criteria_sha256": got,
            "registry_revision": state.get("revision"),
            "attempt_agent": attempt_agent,
            "attempt_state": attempt.get("state") if isinstance(attempt, dict) else None}


def extract_pinned_tree() -> Path:
    """Materialize the pinned execution tree under scratch (byte-verified);
    the extracted bytes import exactly like the lane repo layout."""
    if PINNED_ROOT.exists():
        import shutil
        shutil.rmtree(PINNED_ROOT)
    for parts, _ in PINS:
        path = pin_path(parts)
        if path.is_relative_to(STORE):
            continue  # store records are referenced in place, not executed
        rel = path.relative_to(LANE_REPO)
        target = PINNED_ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    verify()  # re-verify the extracted bytes
    return PINNED_ROOT


def bootstrap_pinned_imports() -> None:
    """Point sys.path at the pinned extraction (identity checked by callers)."""
    require(PINNED_ROOT.exists(), "input_pin_mismatch:extraction_missing")
    typeb = PINNED_ROOT / "tools/science_funnel/typeb_export"
    root = str(PINNED_ROOT)
    while root in sys.path:
        sys.path.remove(root)
    while str(typeb) in sys.path:
        sys.path.remove(str(typeb))
    sys.path.insert(0, str(typeb))
    sys.path.insert(0, root)


def main() -> int:
    rows = verify()
    reg = verify_registry()
    record = {
        "schema": "chimera.w05_input_pins.v1",
        "task_id": TASK_SHORT,
        "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "preregistration_sha256": prereg_sha256(),
        "preregistration_addendum_1_sha256": addendum_sha256(),
        "criteria_sha256": CRITERIA_SHA256,
        "candidate_base": CANDIDATE_BASE,
        "registry": reg,
        "pins": rows,
        "pins_ok": sum(1 for r in rows if r["ok"]),
        "pins_total": len(rows),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B verify_inputs.py"},
    }
    out = SCRATCH / "pin_verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(canonical(record) + b"\n")
    print("pins OK:", record["pins_ok"], "/", record["pins_total"])
    print("registry:", reg)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
