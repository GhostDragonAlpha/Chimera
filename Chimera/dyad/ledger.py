"""Shared turn ledger for the two CLI agent windows.

Dead simple: one append-only JSON file both agents read and append to.
Each window polls this file, sees the other agent's output, and writes its
own turn whenever it wants. No server, no pipes — just a file both can see.

Entry shape:
  {"n": int, "who": "A"|"B"|"ORCH", "kind": "task"|"reply"|"critique"|"note",
   "text": str, "ts": float}
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

LEDGER_PATH = Path(__file__).resolve().parent / "ledger.json"


def reset() -> None:
    LEDGER_PATH.write_text("[]", encoding="utf-8")


def _load() -> list[dict]:
    if not LEDGER_PATH.exists():
        return []
    try:
        return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict]) -> None:
    LEDGER_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def append(who: str, kind: str, text: str) -> dict:
    entries = _load()
    entry = {
        "n": len(entries) + 1,
        "who": who,
        "kind": kind,
        "text": text,
        "ts": time.time(),
    }
    entries.append(entry)
    _save(entries)
    return entry


def entries() -> list[dict]:
    return _load()


def last_n(n: int) -> list[dict]:
    return _load()[-n:]


def since(index: int) -> list[dict]:
    """All entries with n > index. Used by an agent to see what's new."""
    return [e for e in _load() if e["n"] > index]


def orchestrator_task() -> Optional[dict]:
    """The most recent ORCH task entry, if any."""
    for e in reversed(_load()):
        if e["who"] == "ORCH" and e["kind"] == "task":
            return e
    return None
