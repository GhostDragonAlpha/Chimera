#!/usr/bin/env python3
"""MAT2-W06: the frozen input-pin verifier (prereg section 1).

Verifies every pinned upstream artifact byte-exact BEFORE anything is
evaluated; any drift is the named refusal `input_pin_mismatch`. All W05
outcome artifacts are pinned AT THEIR MERGED IN-TREE PATHS (the sealed
published bytes at base af751aa5), not workspace copies. Also re-reads the
card identity READ-ONLY from the registry (`file:...?mode=ro`) and refuses
on any criteria mismatch (`criteria_pin_mismatch`). Importable: the
evaluator and the named checks call verify() first.

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
WS = HERE.parents[4]                      # .../kanban-attempts/MAT2-W06/<attempt>
SCRATCH = WS / "scratch"
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
UPSTREAM = HERE.parent / "MAT2-W05"       # merged MAT2-W05 contribution tree
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

CARD_ID = "MAT2-W06"
TASK_SHORT = "W06"
CRITERIA_SHA256 = "2b9478cb28462c029f9d51267f933474878ba78438e4be88a5a3707808850d26"
ATTEMPT_ID = "a5ccec3526f344438a1cc484cae1bd58"
AGENT_ID = "wk-w06-eval"
CANDIDATE_BASE = "af751aa5"
PREREG = HERE / "PREREGISTRATION.md"

# (pinned path relative to the merged MAT2-W05 contribution tree, sha256)
# prereg section 1, verbatim.
PINS_UPSTREAM = [
    (("runbook.json",),
     "f173a1c5993929e10bac3365a46739aad0f9856b640b5de66ae06eaac2e1d6b0"),
    (("w05_freeze_fill.json",),
     "258749b826bc1dcd86d2b3a127606e11792c3b014d904f0e105cea124a48bf63"),
    (("PREREGISTRATION.md",),
     "260c6d53e66c79689e95b5f880c1f6828f5316d4d7d6e172132296137d3f1c2a"),
    (("PREREGISTRATION-ADDENDUM-1.md",),
     "a257826f26936f4bf388d140ff7158eac851a0c9dae4ca01a9db3a6abdd886d7"),
    (("checks_receipt.json",),
     "69e315a1e1aa54eb0221127acd7e4a93ff9036eaedade1f21d6170ae68683677"),
    (("receipts", "baseline_receipt.json"),
     "6ede18c05e9cd31b9c6cf493bfe471a1711439980dbe55723dfe4fc6f4bc3bb2"),
    (("receipts", "recipe_equivalence_receipt.json"),
     "bbb6dbd34dff0d9f8a3f4940e947eba428b330f25bff3c15b7fcbdb7bbf22bdd"),
    (("receipts", "heldout_receipt.json"),
     "4deff1a2efec7112b975230fba24fa8818715fc378f453654e57a5cb05fce4f1"),
    (("receipts", "deploy_check_receipt.json"),
     "766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635"),
    (("trained", "trained_policy_manifest.json"),
     "02538194cad7f200985e628c55c86fb3fb6d2b76bfb6b44220fab7d32343571e"),
    (("receipts", "seed_20260919_receipt.json"),
     "b866e9b1e2a3d516a960a88362c95d2f8211d28b894cc4d8c16dcebc4dc8b896"),
    (("receipts", "seed_20260919_curve.json"),
     "56e645a2a6ba7b594e0d98ab682c169e5132bca70abc233aa67eae19548fb450"),
    (("trained", "theta_20260919.npz"),
     "eacdafdb1de9034a39084f4fd81eaad8c4d3d9a09496c9d6b6758e2391388589"),
    (("receipts", "seed_20260920_receipt.json"),
     "3d795b5ca523289c1ceac7dac72070875d8cc4b8e24e4ac2a5a64a9733e766ff"),
    (("receipts", "seed_20260920_curve.json"),
     "185ac6e3afa5b891d4032256f59c1340421ae7c649ed5cac173adc18c2e4835c"),
    (("trained", "theta_20260920.npz"),
     "89df7ac6ca3c94c547be5692da55c98e0e510050ff0b1e8df6912f2bb4d949aa"),
    (("receipts", "seed_20260921_receipt.json"),
     "10c4090473c75ec99559dd9f1f13729d96c3c7d5cf037569c63253e308f472af"),
    (("receipts", "seed_20260921_curve.json"),
     "145b2eb6069913719f7a1f575fad76a32764127ae62b736ad5209c2ce0c09972"),
    (("trained", "theta_20260921.npz"),
     "7b11dd01f8495068f46def84a072d211fe47b778bfc0fbc3f53fe3e82a7fe1a7"),
]

# (store-relative parts, sha256)
PINS_STORE = [
    (("MAT2-W04", "numerical", "w04_freeze_manifest.json"),
     "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29"),
    (("MAT2-W04", "numerical", "w04_certificate.json"),
     "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598"),
]


def pin_path(parts: tuple[str, ...]) -> Path:
    if parts[0] == "MAT2-W04":
        return STORE.joinpath(*parts)
    return UPSTREAM.joinpath(*parts)


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
    """Verify all pins (or an override table for the FB1 bite arm)."""
    rows = []
    table = expect if expect is not None else (PINS_UPSTREAM + PINS_STORE)
    for parts, expected in table:
        path = parts[0] if isinstance(parts, Path) else pin_path(tuple(parts))
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


def main() -> int:
    rows = verify()
    reg = verify_registry()
    record = {
        "schema": "chimera.w06_input_pins.v1",
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
