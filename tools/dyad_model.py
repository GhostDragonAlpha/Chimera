"""dyad_model.py — switch the dyad's eye at runtime (operator decree 2026-09-03).

The dyad's model is whatever LM Studio has loaded — but "loaded" is the
OPERATOR's choice, not the code's. This tool writes the override file that
`senses.dyad_model()` reads fresh on every call, so the next ask uses the
named model. No restart, no code edit.

Usage:
  python tools/dyad_model.py                # list what LM Studio serves now
  python tools/dyad_model.py <model-id>     # switch (verified against the list)
  python tools/dyad_model.py auto           # clear the override (fall to env/default)

Rule-0 membrane:
  STATEMENT:  the eye's identity is an operator-owned runtime value, and a
              switch takes effect on the NEXT call without process restart.
  PREDICTION: after `set`, the next senses.watch report logs
              "dyad model switch: A -> B" and answers come from B (echoed in
              the response payload's `model` field).
  FALSIFIER:  a call after `set` still served by the old model, or LM Studio
              returns NoModelLoaded / a model-miss for the written id.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

LMSTUDIO_URL = "http://localhost:1234"
OVERRIDE = Path(__file__).resolve().parent.parent / "Saved" / "dyad_model.txt"


def served() -> list[str]:
    try:
        with urllib.request.urlopen(LMSTUDIO_URL + "/v1/models", timeout=4) as r:
            return [m.get("id", "") for m in json.load(r).get("data", [])]
    except Exception as e:
        print(f"(cannot reach LM Studio: {e})")
        return []


def main() -> int:
    ids = served()
    print("LM Studio serves:")
    for i in ids:
        cur = ""
        if OVERRIDE.exists():
            cur = "   <-- dyad override" if i == OVERRIDE.read_text(encoding="utf-8").strip() else ""
        print(f"  {i}{cur}")
    if len(sys.argv) < 2:
        print("\nusage: python tools/dyad_model.py <model-id | auto>")
        return 0
    want = sys.argv[1].strip()
    if want not in ("auto",) and ids and want not in ids:
        print(f"\nREFUSED: '{want}' is not in the served list — a typo'd id is a silently dark eye.")
        print("Copy an id exactly from the list above.")
        return 1
    OVERRIDE.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDE.write_text(want + "\n", encoding="utf-8")
    print(f"\ndyad override written: {want}" + ("" if want != "auto" else " (fall through to env/default)"))
    print("Takes effect on the next senses call; every switch is logged by senses.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
