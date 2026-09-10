"""orient.py -- the ONE live read: engine tree + verdict ledger + git, together.

The session used to start with `python Chimera/core/grow.py --read --depth 2` -- a command
that does not exist. The engine's ORIENT (mcp `orient`) reads the engine store but
not the verdict lane, and the verdict lane (LightEngine/JOINT_ATLAS) has no single
read at all. This is the replacement: both halves of the dyad, one command, machine-
readable with --json.

    python tools/orient.py            # the day starts here (fail-closed)
    python tools/orient.py --json     # for a second system to consume
    python tools/orient.py --allow-synthetic   # explicit demo mode, empty store

FAIL-CLOSED (GLM-WF-01 F1, R1/R3 recorded in docs/evidence/glm_wf01/SLOT_REGISTRY.md):
`ChimeraEngine/engine_state.json` is the per-checkout term store. When it is ABSENT
or UNREADABLE this tool refuses to print a plausible term tree: an agent that
orients in a store-less checkout gets an explicit UNORIENTED verdict and a nonzero
exit, never a synthetic leaderboard presented as recovered state. The synthetic
default engine remains available ONLY under `--allow-synthetic`, which labels its
output `synthetic:true`, `oriented:false`, and exits 0 without claiming authority.

Reads, all live:
  - ChimeraEngine/engine_state.json   (the term hierarchy, gate progress, current)
  - tools/verdict_registry.json       (the Rule-0 verdict ledger)
  - git HEAD                           (the last membrane that landed)

Every recorded orientation carries R3 provenance: store path, store presence,
store byte size, store sha256, checkout HEAD, and the verdict-lane commit
identity. An orientation record without these is NOT_TESTED, not oriented.

PREREGISTRATION (STATE / PREDICTION / FALSIFIER):
- STATEMENT: fail-closing orient.py removes the silent-default hazard GLM measured.
- PREDICTION: in a checkout without engine_state.json, default orient exits != 0
  and marks the output UNORIENTED; `--allow-synthetic` exits 0 with the tree
  labeled synthetic.
- FALSIFIER: any invocation without `--allow-synthetic` in a store-less checkout
  that exits 0 while printing a plausible tree, or any store-present invocation
  that refuses to record store size + sha256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
sys.path.insert(0, str(ROOT / "tools"))

from engine_state import Engine   # noqa: E402
from verdict import VerdictLedger  # noqa: E402

STORE = ROOT / "ChimeraEngine" / "engine_state.json"


def _store_record() -> dict:
    """R3 provenance for the per-checkout term store, read without side effects."""
    if not STORE.exists():
        return {"path": str(STORE), "exists": False, "size_bytes": None, "sha256": None}
    try:
        raw = STORE.read_bytes()
    except OSError as e:
        return {"path": str(STORE), "exists": True, "size_bytes": None,
                "sha256": None, "unreadable": str(e)}
    rec = {"path": str(STORE), "exists": True, "size_bytes": len(raw),
           "sha256": hashlib.sha256(raw).hexdigest()}
    try:
        json.loads(raw.decode("utf-8", errors="replace"))
    except (ValueError, UnicodeDecodeError) as e:
        rec["unreadable"] = "json decode failed: %s" % e
    return rec


def _git(log: bool = False) -> str:
    try:
        r = subprocess.run(["git", "log", "--oneline", "-5" if log else "-1"],
                           capture_output=True, text=True, cwd=ROOT)
        return r.stdout.strip()
    except Exception:
        return "(no git)"


def main() -> int:
    ap = argparse.ArgumentParser(description="the one live read -- engine + verdicts + git")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--allow-synthetic", action="store_true",
                    help="explicit demo mode: when the term store is absent, print the "
                         "synthetic starter tree LABELED as synthetic (never recovered state)")
    ap.add_argument("--strict", action="store_true",
                    help="alias of the fail-closed default; kept for callers of record "
                         "(GLM-WF-01 R5 named this flag; defaults now fail closed)")
    a = ap.parse_args()

    store = _store_record()
    store_ok = (store["exists"] and store.get("sha256") is not None
                and "unreadable" not in store)
    verdict_commit = "(not recorded)"
    vcommit = subprocess.run(["git", "rev-parse", "HEAD:tools/verdict_registry.json"],
                             capture_output=True, text=True, cwd=ROOT)
    if vcommit.returncode == 0:
        verdict_commit = vcommit.stdout.strip()[:12]
    head = _git()

    if not store_ok:
        reason = ("no term store" if not store["exists"]
                  else "term store unreadable: %s" % store.get("unreadable"))
        if a.json:
            print(json.dumps({
                "oriented": False, "synthetic": store["exists"] is False,
                "reason": reason, "store": store, "head": head,
                "verdicts": {"neutral_note": "verdict lane tracked separately"},
                "current": None, "next_term": None}, indent=2, sort_keys=True))
        else:
            print(f"UNORIENTED -- {head}")
            print("=" * 100)
            print(f"  No authoritative term store in this checkout: {store['path']}")
            print(f"  {reason}. A synthetic starter is available ONLY with --allow-synthetic.")
            print("  Nothing here is recovered state. Record store size+sha256 before admission.")
            print("=" * 100)
            ledger = VerdictLedger()
            ledger.print_status()
            print()
            print(f"  verdict lane tracked at this HEAD: {verdict_commit} "
                  f"(commit-identity recorded; reads commit-safe per R4)")
        if a.allow_synthetic:
            synthetic = Engine()
            if a.json:
                # emitted above with oriented:false; append nothing further
                return 0
            print()
            print(f"  SYNTHETIC/uninitialized engine (--allow-synthetic): "
                  f"{len(synthetic.state.get('hierarchy', {}))} starter terms.")
            print()
            print(synthetic.orient())
            return 0
        return 3 if not store["exists"] else 4

    eng = Engine()
    if a.json:
        out = {
            "oriented": True, "synthetic": False, "store": store,
            "current": eng.state.get("current"),
            "next_term": eng.next_term(),
            "head": head,
            "verdicts_commit": verdict_commit,
            "open_terms": len([1 for v in eng.state["hierarchy"].values()
                               if v.get("status") not in ("proven", "decided")]),
            "proven_terms": len([1 for v in eng.state["hierarchy"].values()
                                 if v.get("status") in ("proven", "decided")]),
            "verdicts": {"open": None, "closed": None, "next_number": None},
        }
        ledger = VerdictLedger()
        st = ledger.status()
        out["verdicts"] = {"open": len(st["open"]), "closed": len(st["closed"]),
                           "next_number": st["next_number"]}
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0

    print(f"ORIENT -- {head}")
    print("=" * 100)
    print(eng.orient())
    print("=" * 100)
    ledger = VerdictLedger()
    ledger.print_status()

    print()
    print(f"  store: {store['path']}  {store['size_bytes']} B  sha256 "
          f"{store['sha256'][:12]}…  verdict-lane commit {verdict_commit}")

    orphans = [v for v in ledger.status()["closed"] if not v.get("term")]
    if orphans:
        print()
        print(f"  {len(orphans)} CLOSED verdict(s) not linked to any engine term "
              f"(`python tools/verdict.py link <n> <term>`).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
