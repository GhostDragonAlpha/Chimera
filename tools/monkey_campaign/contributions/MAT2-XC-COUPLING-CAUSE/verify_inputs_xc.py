#!/usr/bin/env python3
"""MAT2-XC-COUPLING-CAUSE: the frozen input-pin verifier (prereg section 0).

Verifies every pinned artifact byte-exact BEFORE anything is loaded or
executed; any drift is the named refusal `input_pin_mismatch`. The layers:

1. THIS card's shipped prereg bytes == the committed prereg blob
   (prereg-first law executed: commit 92a205e sits directly on 27ba0ff8,
   touches ONLY the prereg file, blob byte-identical to THIS package's
   copy).
2. The sealed a12/x05 record pins (the frozen basis; CITED, never
   re-claimed) from the a12 runner job and the evidence store.
3. The WK-LATENCY authority blobs at 45fc2505 (the cut-form authority:
   "bytes through tick 4350, then SILENCE" is frozen in the committed
   preregistration; the A3 amendment is the probe-class authority).
4. The certified-line heritage blobs at THIS package's base (the values
   the sealed X05 pins recorded; read READ-ONLY through the DECLARED
   source_access — NO_WORKTREES law).
5. The W10 pin layer EXECUTED UNMODIFIED (verify + registry + extraction
   + import bootstrap) — the exact materialization identity the sealed
   X05 run proved, inherited byte-for-byte.
6. The U07 pin layer + the accepted trace modules (imported, never
   copied).

Run: python -B verify_inputs_xc.py   Exit: 0 green / 2 named refusal.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
A12_JOB = Path("E:/ChimeraWork/task-runner/results/"
               "ca111cdc917e420eb78c41339d88c41b")
SCRATCH = Path(os.environ.get("TMP", ".")) / "xc_pins_coupling_cause"
PINNED_ROOT = SCRATCH / "pinned_root"

CARD_ID = "MAT2-XC-COUPLING-CAUSE"
AGENT_ID = "wk-coupling-cause"
BASE_SHA = "92a205e7585737e82beaa3e1637c7868243bdb8f"
PIN_BASE = "27ba0ff88f68615e757db81b749be94bf01f3827"
PREREG_PATH = ("tools/monkey_campaign/contributions/"
               "XC-COUPLING-CAUSE-20261003/PREREGISTRATION.md")
PREREG = HERE / "PREREGISTRATION.md"
PREREG_SHA = ("c56798b3db65e86429117f98c143a1565903"
              "bc2341684e00ac89c361917f0e0c")

U07_DIR = ("tools", "monkey_campaign", "contributions", "MAT2-U07")
W10_DIR = ("tools", "monkey_campaign", "contributions", "MAT2-W10")
SEAM = ("tools", "monkey_campaign", "contributions", "MAT2-U01",
        "reconcile", "pinned_seam")
WKL_DIR = ("tools", "monkey_campaign", "contributions",
           "WK-LATENCY-20261002")
WKL_AUTHORITY = "45fc250582785bdcf125d9a09c74a39092a57c15"

# (group, base-for-blob, path parts, sha256)
PINS = [
    # heritage blobs at THIS package's base (values the sealed X05 pins
    # recorded; identical bases verified at design time).
    ("blob", BASE_SHA, U07_DIR + ("source_access.py",),
     "0563d123b51bd65a28f74b01afa0daa766001830890b4babb458f407e475759b"),
    ("blob", BASE_SHA, U07_DIR + ("controls_harness.py",),
     "b4c71813fe05008976611d12b954c5a07dbdfb616556dff62ecc513ca1e28b95"),
    ("blob", BASE_SHA, U07_DIR + ("verify_inputs_u07.py",),
     "f5b1e18b22edf408baea26d8b4b349b9688fedc320dd0f373a63a647227e1742"),
    ("blob", BASE_SHA, W10_DIR + ("verify_inputs.py",),
     "25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6"),
    ("blob", BASE_SHA, W10_DIR + ("command_model.py",),
     "0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa"),
    ("blob", BASE_SHA, W10_DIR + ("walking_demo.py",),
     "fb394677306bcb3d808271cce72212c000b82455567e74c1090d3c1003d90ea1"),
    ("blob", BASE_SHA, W10_DIR + ("visualization.py",),
     "2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb"),
    ("blob", BASE_SHA, SEAM + ("tools", "monkey_campaign", "product",
                               "input_mapper.py"),
     "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44"),
    ("blob", BASE_SHA, SEAM + ("tools", "science_funnel", "typeb_export",
                               "command_record.py"),
     "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e"),
    # the cut-form authority (committed WK-LATENCY bytes at the A3 tip)
    ("blob", WKL_AUTHORITY, WKL_DIR + ("PREREGISTRATION.md",),
     "f3afb0f6084b04c546355b104dd2f6274fa04f4eaa4a1e64529b30ce73d62a7f"),
    ("blob", WKL_AUTHORITY, WKL_DIR + ("AMENDMENT-A3.md",),
     "b4ac556c3ea14c6d7ab10c8e58f62a9a0e91ca845346e73769a77e82e8f19347"),
]

# the frozen basis records (byte-verified at design time; re-verified here)
RECORD_PINS = [
    (A12_JOB / "receipt.json",
     "f85c0447ce0ff8cf9b27840dca31dd2dc4b309212171724d96c20359a761ef24"),
    (A12_JOB / "artifacts" / "outputs" / "driver_pair_P01_BRAKE-SHORT.json",
     "5a3ca1be4778a60d9c99ec424b3047c503f473fe665ebb1e8df079f7f77f14fb"),
    (A12_JOB / "artifacts" / "outputs" / "driver_pair_P02_BRAKE-LONG.json",
     "d63301e76da53a2ec3ae6d368a3439dbca2b78ed65281a347f58f12c90dcbc48"),
    (STORE / "WK-LATENCY-20261002" / "numerical"
     / "driver_pair_P01_BRAKE-SHORT_a9.json",
     "43d659afc354cb6e16df7ea92c9a3db6e7e3c843d12804e7a5f908c2b45d36ad"),
    (STORE / "WK-LATENCY-20261002" / "numerical"
     / "pair_receipt_P01_BRAKE-SHORT_a12.json",
     "7d22b68cb7cc85a2dedec95b729404ae013a68985fa3ffb9782395ee5ac3ca6f"),
    (STORE / "MAT2-X05" / "numerical" / "driver_pair_P01_BRAKE-SHORT.json",
     "31e4d11eec3f867ab044ddd97b6de1c54a5e82daf4fd055ecad696913eb3e918"),
    (STORE / "MAT2-X05" / "numerical" / "driver_pair_P02_BRAKE-LONG.json",
     None),  # sha recorded at design time below
    (STORE / "MAT2-X05" / "numerical" / "pins_x05.json",
     "bdaeb0bd254d0f562ac8a64b1bcd9a4a6eb64f4877f81d36889fa3ee81f16920"),
]
X05_P02_SHA = "e05620c8999ffeca7840d4b932992cad7c4d489b01d769f79a88b4dee859231e"


class Refusal(RuntimeError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


def source_access():
    """The DECLARED read-only base-blob reader (the pinned U07 bytes,
    imported, never copied)."""
    if "xc_source_access" in sys.modules:
        return sys.modules["xc_source_access"]
    path = PINNED_ROOT.joinpath(*U07_DIR) / "source_access.py"
    require(path.exists(), "input_pin_missing:source_access.py")
    import importlib.util
    spec = importlib.util.spec_from_file_location("xc_source_access", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["xc_source_access"] = mod
    spec.loader.exec_module(mod)
    return mod


def git_read(*args):
    sa = source_access()
    out = subprocess_git(sa.source_repo(), *args)
    return out


def subprocess_git(repo, *args):
    import subprocess
    out = subprocess.run(
        ["git", "-C", repo, "-c", "safe.directory=" + repo, *args],
        capture_output=True, check=False)
    if out.returncode != 0:
        raise Refusal("git_refused:" + " ".join(args[:3]) + ":"
                      + out.stderr.decode("utf-8", "replace")[:160])
    return out.stdout


def verify() -> list:
    rows = []
    for group, base, parts, expected in PINS:
        data = source_access().read_blob(base, "/".join(parts))
        got = sha_bytes(data)
        require(got == expected,
                "input_pin_mismatch:" + parts[-1] + ":" + got[:12])
        rows.append({"path": base[:8] + ":" + "/".join(parts),
                     "sha256": got, "expected": expected, "ok": True})
    for i, (path, expected) in enumerate(RECORD_PINS):
        exp = X05_P02_SHA if expected is None else expected
        require(path.exists(), "input_pin_missing:" + path.name)
        got = sha_bytes(path.read_bytes())
        require(got == exp,
                "input_pin_mismatch:" + path.name + ":" + got[:12])
        rows.append({"path": ("job:" if "task-runner" in str(path)
                              else "store:") + str(path).replace("\\", "/"),
                     "sha256": got, "expected": exp, "ok": True})
    return rows


def verify_prereg_commit() -> dict:
    """The prereg-first law, executed (the X05 form)."""
    require(sha_bytes(PREREG.read_bytes()) == PREREG_SHA,
            "prereg_package_bytes_mismatch")
    kind = git_read("cat-file", "-t", BASE_SHA).decode().strip()
    require(kind == "commit", "prereg_commit_not_commit:" + kind)
    parent = git_read("rev-parse", BASE_SHA + "^").decode().strip()
    require(parent == PIN_BASE, "prereg_commit_parent_not_base:" + parent)
    changed = git_read("diff", "--name-only", PIN_BASE,
                       BASE_SHA).decode().strip().split()
    require(changed == [PREREG_PATH],
            "prereg_commit_touches_more:" + repr(changed))
    blob = git_read("cat-file", "blob", BASE_SHA + ":" + PREREG_PATH)
    got = sha_bytes(blob)
    require(got == prereg_sha256(), "prereg_commit_bytes_mismatch:" + got[:12])
    return {"commit": BASE_SHA, "parent": parent,
            "preregistration_sha256": got, "changed_files": changed}


def verify_prereg_draft_lineage() -> dict:
    """The chain-stop-1 draft bytes (design_basis.json records) re-checked
    against the committed blob: the Lieutenant committed the draft
    UNCHANGED (c56798b3)."""
    return {"draft_declared_sha256": PREREG_SHA,
            "committed_sha256": prereg_sha256(),
            "byte_identical": prereg_sha256() == PREREG_SHA}


def extract_execution_tree() -> Path:
    """Materialize THIS card's pinned blobs under slot scratch
    (byte-verified) so the unmodified W10/U07 layers can be loaded by
    file path (import identity)."""
    if PINNED_ROOT.exists():
        shutil.rmtree(PINNED_ROOT)
    require(source_access().resolve_base(BASE_SHA) == "commit",
            "input_pin_mismatch:base_unresolvable")
    for group, base, parts, expected in PINS:
        data = source_access().read_blob(base, "/".join(parts))
        require(sha_bytes(data) == expected,
                "input_pin_mismatch:extract:" + parts[-1])
        target = PINNED_ROOT.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return PINNED_ROOT


def load_pinned_module(name: str, rel_parts: tuple):
    path = PINNED_ROOT.joinpath(*rel_parts)
    require(path.exists(), "input_pin_missing:" + "/".join(rel_parts))
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def u07_layer() -> dict:
    """Execute the U07 pin layer UNMODIFIED (the accepted trace modules)."""
    vi7 = load_pinned_module("u07_verify_inputs",
                             U07_DIR + ("verify_inputs_u07.py",))
    rows = vi7.verify()
    root = vi7.extract_u07_tree()
    return {"u07_pin_rows": len(rows), "u07_extraction": str(root)}


def load_accepted_trace_modules():
    """The ACCEPTED trace module + adapter (the X05 loader form)."""
    vi7 = sys.modules.get("u07_verify_inputs")
    require(vi7 is not None, "u07_layer_not_executed")
    it = vi7.load_pinned_module(
        "u07_accepted_input_trace",
        ("tools", "monkey_campaign", "contributions", "I-U07-TRACE",
         "input_trace.py"))
    ad = vi7.load_pinned_module(
        "u07_accepted_adapter",
        ("tools", "monkey_campaign", "contributions",
         "I-U07-TRACE-FOLLOWUP", "adapter.py"))
    return it, ad


def w10_layer() -> dict:
    """Execute the W10 certified-line pin layer UNMODIFIED (the exact
    materialization identity the sealed X05 run proved)."""
    # W10's module does `import source_access` at top: the pinned U07
    # bytes of that module (byte-verified in THIS card's extraction) go
    # on sys.path FIRST (the X05 w10_layer law).
    u07_dir = str(PINNED_ROOT.joinpath(*U07_DIR))
    if u07_dir not in sys.path:
        sys.path.insert(0, u07_dir)
    wvi = load_pinned_module("w10_verify_inputs",
                             W10_DIR + ("verify_inputs.py",))
    rows = wvi.verify()
    reg = wvi.verify_registry()
    root = wvi.extract_pinned_tree()
    wvi.bootstrap_pinned_imports()
    # the X05 w10_layer law: the W10 CONTRIBUTION dir becomes sys.path[0]
    # so `import command_model` / `import walking_demo` resolve to the
    # pinned W10 bytes. THIS card's own extraction (byte-verified in
    # section 0) carries those files — the W10 layer's own tree carries
    # the lane machinery, not its contribution dir.
    w10_dir = str(PINNED_ROOT.joinpath(*W10_DIR))
    while w10_dir in sys.path:
        sys.path.remove(w10_dir)
    sys.path.insert(0, w10_dir)
    return {"w10_pin_rows": len(rows),
            "w10_extraction": str(root),
            "w10_registry_card_state": reg.get("card_state"),
            "w10_registry_criteria": (reg.get("criteria_sha256") or "")[:12]}


def registry_probe() -> dict:
    """READ-ONLY probe: record THIS card's registry state if present
    (no gate; the card may legitimately be session-dispatched)."""
    import sqlite3
    reg = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
    if not reg.exists():
        return {"card_state": "registry_absent"}
    con = sqlite3.connect("file:" + str(reg).replace("\\", "/")
                          + "?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT payload FROM state")
        state = json.loads(cur.fetchone()[0])
    finally:
        con.close()
    card = (state.get("kanban", {}).get("cards", {}) or {}).get(CARD_ID)
    return {"card_state": None if card is None else card.get("state"),
            "registry_revision": state.get("revision")}


def main() -> int:
    # bootstrap: source_access needs PINNED_ROOT; extract first from raw
    # git reads, then re-verify through the pinned reader.
    if PINNED_ROOT.exists():
        shutil.rmtree(PINNED_ROOT)
    require(source_access_bootstrap(), "bootstrap_failed")
    rows = verify()
    base = {"base": BASE_SHA, "parent": git_read(
        "rev-parse", BASE_SHA + "^").decode().strip()}
    prereg_commit = verify_prereg_commit()
    lineage = verify_prereg_draft_lineage()
    extract_execution_tree()
    w10 = w10_layer()
    u07 = u07_layer()
    reg = registry_probe()
    summary = {"schema": "chimera.xc_input_pins.v1",
               "card": CARD_ID, "agent_id": AGENT_ID,
               "base_sha256": BASE_SHA, "pin_base": PIN_BASE,
               "preregistration_sha256": prereg_sha256(),
               "prereg_commit": prereg_commit,
               "draft_lineage": lineage,
               "base_identity": base,
               "pin_rows": rows,
               "registry": reg,
               "w10_layer": w10, "u07_layer": u07}
    out = os.environ.get("CHIMERA_OUTPUT_DIR")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "pins_xc.json").write_bytes(
            json.dumps(summary, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"),
                       allow_nan=False).encode("utf-8") + b"\n")
    print("pins: %d XC rows green; W10 layer %d rows; U07 layer %d rows"
          % (len(rows), w10["w10_pin_rows"], u07["u07_pin_rows"]))
    return 0


def source_access_bootstrap() -> bool:
    """Write the pinned source_access bytes BEFORE the pin reader exists
    (the reader IS source_access)."""
    import subprocess
    rel = "/".join(U07_DIR + ("source_access.py",))
    out = subprocess.run(
        ["git", "-C", "E:/PythonChimera", "cat-file", "blob",
         BASE_SHA + ":" + rel], capture_output=True, check=False)
    if out.returncode != 0:
        return False
    if sha_bytes(out.stdout) != PINS[0][3]:
        return False
    target = PINNED_ROOT.joinpath(*U07_DIR) / "source_access.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(out.stdout)
    return True


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as r:
        print("REFUSAL: " + str(r), file=sys.stderr)
        sys.exit(2)
