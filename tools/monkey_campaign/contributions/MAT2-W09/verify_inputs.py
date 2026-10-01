#!/usr/bin/env python3
"""MAT2-W09: the frozen input-pin verifier (prereg section 1).

Verifies every pinned upstream artifact byte-exact BEFORE anything is
loaded or executed; any drift is the named refusal `input_pin_mismatch`.
The W04 freeze records, the W07 published receipts and the G07 falsifier
lineage are pinned in the evidence store; the W05/W06 published bytes and
W07's driver are pinned AT THEIR MERGED IN-TREE PATHS and extracted from
the shared repository's Git object database at THIS CARD'S PINNED BASE
commit (immutable; `git cat-file blob <base>:<path>`); the sealed lane
machinery is pinned at the pass3-integ lane repo (the identical 15-file
table W07 verified) and consumed ONLY through a byte-verified extraction;
the ingestion-spike honesty records are pinned in the coordination store.
Also re-reads the card identity READ-ONLY from the registry
(`file:...?mode=ro`) and refuses on any criteria mismatch
(`criteria_pin_mismatch`). Importable: the load, the checks and the capture
call verify() first.

Run:  python -B verify_inputs.py
Exit: 0 green / 2 named refusal. CPU only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# package layout: files/tools/monkey_campaign/contributions/MAT2-W09
# HERE.parents: [contributions, monkey_campaign, tools, files, package, attempt]
WS = HERE.parents[5]
SCRATCH = WS / "scratch"
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
SPIKE = Path("E:/ChimeraWork/monkey-coordination/ingestion-spike")
LANE_REPO = Path("E:/ChimeraWork/pass3-integ/repo")
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
PINNED_ROOT = Path(os.environ.get("TMP") or (SCRATCH / "pinned_root")) \
    / "w09_pinned_root"

CARD_ID = "MAT2-W09"
TASK_SHORT = "W09"
CRITERIA_SHA256 = "b9470c8cac79c4a9374cac7b9a31dccfbb496e4d755ee4dc57bff98de0cd6d0a"
ATTEMPT_ID = "2090c714d92a451bbc84ba1d599a8222"
# the registry's attempt owner is the ARRIVAL identity (the card worker name
# `wk-w09-envelope` is the dispatch address, not the registered owner)
AGENT_ID = "wk-w09-arrival-1"
BASE_COMMIT = "8b285ee4301a8ed42be54a1924af5db019f9fb20"
SOURCE_REPO = Path(os.environ.get("CHIMERA_SOURCE_REPO")
                   or "E:/PythonChimera")
PREREG = HERE / "PREREGISTRATION.md"

GIT_TREE_PREFIX = "tools/monkey_campaign/"

# (group, pinned path parts, sha256) — prereg section 1, verbatim.
# group "tree" rows are extracted from the pinned base commit via git.
PINS = [
    ("store", ("MAT2-W04", "numerical", "w04_certificate.json"),
     "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598"),
    ("store", ("MAT2-W04", "numerical", "w04_freeze_manifest.json"),
     "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29"),
    ("store", ("MAT2-W07", "source", "PREREGISTRATION.md"),
     "09e8ce87f56d88326df936e6ef51560349d086376e0f3116ed3927a643b429c7"),
    ("store", ("MAT2-W07", "numerical", "native_load_receipt.json"),
     "4f5aac081a3a07fd56733d84ac3069950b00309e54f6402e78ebd22c55e490e9"),
    ("store", ("MAT2-W07", "numerical", "checks_receipt.json"),
     "f599720bbcd06e4888d933d11a7e48f29430635189acf79bd79ad7305559d342"),
    ("store", ("MAT2-G07", "verdict_ref", "PREREGISTRATION.md"),
     "1e55df6da88dbb9fdc3c296b2965042b0a6828b0d6387a2c9eb8bb53f7bb87df"),
    ("store", ("MAT2-G07", "numerical", "experiment_receipt.json"),
     "c539617b098190918187d9a7dcbb0a5e33a85998adaa58f6b781703bbdeb88f8"),
    ("tree", ("contributions", "MAT2-W06", "receipts", "evaluation_summary.json"),
     "a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a"),
    ("tree", ("contributions", "MAT2-W05", "receipts", "deploy_check_receipt.json"),
     "766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635"),
    ("tree", ("contributions", "MAT2-W07", "run_native_load.py"),
     "780dde4e0ea9fa0d6ecab41a42cbac85f73192d552aceef7fd2cb8ff4d75f766"),
    ("tree", ("visual_capture.py",),
     "5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05"),
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
    ("spike", ("w2-engine-up", "ENGINE_UP_RECEIPT.md"),
     "364ae9453bdba88f636980a971263847823a14d8f7c2e957719a87421b7bb73c"),
]

_GROUP_BASE = {"store": STORE, "lane": LANE_REPO, "spike": SPIKE}


def pin_path(group: str, parts: tuple[str, ...]) -> Path:
    if group == "tree":
        return PINNED_ROOT / GIT_TREE_PREFIX / Path(*parts)
    return _GROUP_BASE[group].joinpath(*parts)


def tree_relpath(parts: tuple[str, ...]) -> str:
    return GIT_TREE_PREFIX + "/".join(parts)


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


def git_blob(relpath: str) -> bytes:
    """A pinned blob from the shared repository at the pinned base commit."""
    p = subprocess.run(
        ["git", "-C", str(SOURCE_REPO), "cat-file", "blob",
         BASE_COMMIT + ":" + relpath],
        capture_output=True, check=True)
    return p.stdout


def verify(expect: list | None = None) -> list[dict]:
    """Verify all pins (or an override table for a bite arm)."""
    rows = []
    table = expect if expect is not None else PINS
    for group, parts, expected in table:
        if group == "tree":
            data = git_blob(tree_relpath(parts))
        else:
            data = pin_path(group, tuple(parts)).read_bytes()
        got = sha_bytes(data)
        rows.append({"path": str(pin_path(group, tuple(parts)))
                     .replace("\\", "/"),
                     "sha256": got, "expected": expected,
                     "ok": got == expected})
        require(got == expected,
                "input_pin_mismatch:" + parts[-1] + ":" + got[:12])
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
                "criteria_pin_mismatch:attempt_criteria:"
                + repr(attempt.get("criteria_sha256")))
    return {"card_state": card.get("state"), "criteria_sha256": got,
            "registry_revision": state.get("revision"),
            "attempt_agent": attempt_agent,
            "attempt_state": attempt.get("state")
            if isinstance(attempt, dict) else None}


def extract_pinned_tree() -> Path:
    """Materialize the pinned execution tree (lane machinery + in-tree
    upstream bytes) byte-verified; the extracted layout imports exactly like
    the lane repo. Sources are read-only; bytes land ONLY under the
    pinned root."""
    import shutil
    if PINNED_ROOT.exists():
        shutil.rmtree(PINNED_ROOT)
    for group, parts, expected in PINS:
        if group == "lane":
            data = LANE_REPO.joinpath(*parts).read_bytes()
            target = PINNED_ROOT.joinpath(*parts)
        elif group == "tree":
            data = git_blob(tree_relpath(parts))
            target = pin_path(group, parts)
        else:
            continue
        require(sha_bytes(data) == expected,
                "input_pin_mismatch:extract:" + parts[-1])
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


def w07_load_receipt() -> dict:
    return json.loads((STORE / "MAT2-W07" / "numerical"
                       / "native_load_receipt.json").read_bytes().decode("utf-8"))


def w06_evaluation_summary() -> dict:
    """The merged in-tree bytes at the pinned base (W07's own consumed copy)."""
    return json.loads(git_blob(
        tree_relpath(("contributions", "MAT2-W06", "receipts",
                      "evaluation_summary.json"))).decode("utf-8"))


def w05_deploy_receipt() -> dict:
    return json.loads(git_blob(
        tree_relpath(("contributions", "MAT2-W05", "receipts",
                      "deploy_check_receipt.json"))).decode("utf-8"))


def outputs_dir() -> Path:
    """Declared-outputs directory (runner keeps these via --keep)."""
    env = os.environ.get("CHIMERA_OUTPUT_DIR")
    return Path(env) if env else (HERE / "receipts")


def main() -> int:
    rows = verify()
    reg = verify_registry()
    record = {
        "schema": "chimera.w09_input_pins.v1",
        "task_id": TASK_SHORT,
        "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "preregistration_sha256": prereg_sha256(),
        "criteria_sha256": CRITERIA_SHA256,
        "base_commit": BASE_COMMIT,
        "source_repo": str(SOURCE_REPO).replace("\\", "/"),
        "registry": reg,
        "pins": rows,
        "pins_ok": sum(1 for r in rows if r["ok"]),
        "pins_total": len(rows),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B verify_inputs.py"},
    }
    out = outputs_dir() / "input_pins.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(canonical(record) + b"\n")
    print("pins OK:", record["pins_ok"], "/", record["pins_total"])
    print("registry:", reg)
    print("preregistration_sha256:", record["preregistration_sha256"])
    print("wrote", out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
