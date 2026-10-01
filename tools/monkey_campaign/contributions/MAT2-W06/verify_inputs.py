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

# (pinned path parts relative to the pinned lane repo, sha256)
# prereg addendum 1 section A1, verbatim (the replay-capture machinery).
PINS_LANE = [
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
]

# (store-relative parts, sha256)
PINS_STORE = [
    (("MAT2-W04", "numerical", "w04_freeze_manifest.json"),
     "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29"),
    (("MAT2-W04", "numerical", "w04_certificate.json"),
     "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598"),
]

LANE_REPO = Path("E:/ChimeraWork/pass3-integ/repo")
PINNED_ROOT = SCRATCH / "pinned_root"


def pin_path(parts: tuple[str, ...]) -> Path:
    if parts[0] == "MAT2-W04":
        return STORE.joinpath(*parts)
    if parts[0] == "tools":
        return LANE_REPO.joinpath(*parts)
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


def addendum_sha256() -> str:
    return sha_bytes((HERE / "PREREGISTRATION-ADDENDUM-1.md").read_bytes())


def extract_pinned_tree() -> Path:
    """Materialize the pinned execution tree under scratch (byte-verified);
    the extracted bytes import exactly like the lane repo layout."""
    import shutil
    if PINNED_ROOT.exists():
        shutil.rmtree(PINNED_ROOT)
    for parts, expected in PINS_LANE:
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


def require(condition, code: str) -> None:
    if not condition:
        raise Refusal(code)


def verify(expect: list | None = None) -> list[dict]:
    """Verify all pins (or an override table for the FB1 bite arm)."""
    rows = []
    table = expect if expect is not None else (PINS_UPSTREAM + PINS_LANE
                                               + PINS_STORE)
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
