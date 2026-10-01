#!/usr/bin/env python3
"""MAT2-W07: the frozen input-pin verifier (prereg section 1).

Verifies every pinned upstream artifact byte-exact BEFORE anything is
loaded or executed; any drift is the named refusal `input_pin_mismatch`.
The W04 freeze records are pinned in the evidence store; the W05/W06
published bytes are pinned AT THEIR MERGED IN-TREE PATHS (base fa02f075);
the sealed lane machinery is pinned at the pass3-integ lane repo and is
consumed ONLY through a byte-verified extraction (import identity); the
ingestion-spike evidence is pinned in the coordination store. Also re-reads
the card identity READ-ONLY from the registry (`file:...?mode=ro`) and
refuses on any criteria mismatch (`criteria_pin_mismatch`). Importable: the
load, the checks and the capture call verify() first.

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
WS = HERE.parents[4]                      # .../kanban-attempts/MAT2-W07/<attempt>
SCRATCH = WS / "scratch"
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
UPSTREAM_W06 = HERE.parent / "MAT2-W06"   # merged MAT2-W06 contribution tree
UPSTREAM_W05 = HERE.parent / "MAT2-W05"   # merged MAT2-W05 contribution tree
SPIKE = Path("E:/ChimeraWork/monkey-coordination/ingestion-spike")
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

CARD_ID = "MAT2-W07"
TASK_SHORT = "W07"
CRITERIA_SHA256 = "2c942079f1c8bb88a7ac41908c9b46d659e05ff0f2b6d79fb14eb8a6e1e98fd0"
ATTEMPT_ID = "bf3fd3e8c78145f6964a661e78d56ea9"
AGENT_ID = "wk-w07-native"
CANDIDATE_BASE = "fa02f075"
PREREG = HERE / "PREREGISTRATION.md"

# (group, pinned path parts, sha256) — prereg section 1, verbatim.
PINS = [
    ("store", ("MAT2-W04", "numerical", "w04_certificate.json"),
     "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598"),
    ("store", ("MAT2-W04", "numerical", "w04_freeze_manifest.json"),
     "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29"),
    ("store", ("MAT2-W04", "numerical", "c09_anchor_reseal.json"),
     "2311c10c05f0846989909090966285f59b84dd4d6b4d6b46c464a6efa7e647f4"),
    ("store", ("MAT2-W04", "numerical", "checks_receipt.json"),
     "05e28bbaffcf9d65db174ec9b83708d33705922ac506b1cee852a2f9790744c9"),
    ("store", ("MAT2-W04", "numerical", "w04_gate_receipt.json"),
     "d8cd056ffb245a910f08bdf15ab1dd068291110badcbf8a3946795b5ebd5d78b"),
    ("store", ("MAT2-W04", "logs", "gates12_w04.json"),
     "1c5d74d9d44c18142f9016bfbc5cd7a9ca85a7673688437955a98c2eef21ef6b"),
    ("w06", ("PREREGISTRATION.md",),
     "31d43b67132b2a4fe0167be0297193734e0a8d2bca929ac8607157b72d53a87e"),
    ("w06", ("PREREGISTRATION-ADDENDUM-1.md",),
     "dea6b825774b0770100a81c482fb08082397ae740f23034954454c2a6df9caba"),
    ("w06", ("REPORT.md",),
     "978aff5eb57416a4ff984c989865381e7bc3c3d54753c6929df4abbd700be61b"),
    ("w06", ("verify_inputs.py",),
     "f02085eae26cd5d3cff1f90c05409a2c797b56c07b552294731465fa2d33a067"),
    ("w06", ("run_replay_capture.py",),
     "fececfbe25dcda4b6ffb37613f51306a8b531603fb38a56bb69ece2e846d75af"),
    ("w06", ("run_checks.py",),
     "f4926e3e89f44af661b5e41a9538aa1151eb082d47bd0174ad92adc22add2235"),
    ("w06", ("checks_receipt.json",),
     "7e4891be165ce9113c3bf7b319e2ab5bb0ac34ec76994264e5339c172c1439b2"),
    ("w06", ("receipts", "evaluation_summary.json"),
     "a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a"),
    ("w06", ("receipts", "input_pins.json"),
     "6740532e6159ebe6493527ed8908f5041841510e29fb344c14a05467382902c1"),
    ("w06", ("capture", "replay_receipt.json"),
     "c8ba8705560a148c82922efd2f194d29378c672a065eea97692900c42d32cd8d"),
    ("w06", ("capture", "trace.json"),
     "15bf0b4c47ba208366b4bf7cd77775d434c836b70c992e198c51aa9012e1d535"),
    ("w06", ("capture", "capture_manifest.json"),
     "6b696efa76b1e9e0a8d3a5ff4f7cbd0a248e65f843d1f8f1ded4d7d29516f181"),
    ("w06", ("capture", "capture_context.json"),
     "7cbc302efe15fad78e1fae557fbfd610c1a77756b697437bcc75567cc4afe390"),
    ("w06", ("capture", "capture_validation_receipt.json"),
     "335a9091071eea6e4881b797094890d792192edc4f0febd6ba6ea0b9d41c003e"),
    ("w06", ("capture", "frame_hashes.json"),
     "be88b5381ab0c814845fcbc7ea99219f704db9695b3ad937856cd965f017f443"),
    ("w05", ("receipts", "deploy_check_receipt.json"),
     "766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635"),
    ("w05", ("PREREGISTRATION.md",),
     "260c6d53e66c79689e95b5f880c1f6828f5316d4d7d6e172132296137d3f1c2a"),
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
    ("lane", ("tools", "science_funnel", "typeb_export", "observation_schema.py"),
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
    ("spike", ("INGESTION_SPIKE.md",),
     "218b34614d8917eceb3f4ea2a6404c5715f8e25f71e57989c53213d7498e512b"),
    ("spike", ("tile_ingest_receipt.json",),
     "bc252e448805bf082198ec5802ff82662fa52a39673236eb001929d86494e97f"),
    ("spike", ("w2-engine-up", "ENGINE_UP_RECEIPT.md"),
     "364ae9453bdba88f636980a971263847823a14d8f7c2e957719a87421b7bb73c"),
    ("spike", ("w2-engine-up", "w2_post.py"),
     "dd1fa9118f73a505bf1c8153f5de2853cf307ba86754e150c562904bc39cf325"),
]

LANE_REPO = Path("E:/ChimeraWork/pass3-integ/repo")
PINNED_ROOT = SCRATCH / "pinned_root"

_GROUP_BASE = {"store": STORE, "w06": UPSTREAM_W06, "w05": UPSTREAM_W05,
               "lane": LANE_REPO, "spike": SPIKE}


def pin_path(group: str, parts: tuple[str, ...]) -> Path:
    return _GROUP_BASE[group].joinpath(*parts)


class Refusal(Exception):
    """A named refusal (the falsifier must be able to FAIL)."""


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


def require(condition, code: str) -> None:
    if not condition:
        raise Refusal(code)


def verify(expect: list | None = None) -> list[dict]:
    """Verify all pins (or an override table for the FB1 bite arm).

    `expect` rows are (group, parts, expected) triples."""
    rows = []
    table = expect if expect is not None else PINS
    for group, parts, expected in table:
        path = pin_path(group, tuple(parts))
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
    import shutil
    if PINNED_ROOT.exists():
        shutil.rmtree(PINNED_ROOT)
    for group, parts, expected in PINS:
        if group != "lane":
            continue
        data = LANE_REPO.joinpath(*parts).read_bytes()
        require(sha_bytes(data) == expected,
                "input_pin_mismatch:extract:" + parts[-1])
        target = PINNED_ROOT.joinpath(*parts)
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


def c09_anchor_reseal() -> dict:
    return json.loads((STORE / "MAT2-W04" / "numerical" / "c09_anchor_reseal.json")
                      .read_bytes().decode("utf-8"))


def main() -> int:
    rows = verify()
    reg = verify_registry()
    record = {
        "schema": "chimera.w07_input_pins.v1",
        "task_id": TASK_SHORT,
        "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "preregistration_sha256": prereg_sha256(),
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
