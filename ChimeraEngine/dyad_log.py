"""dyad_log.py — THE DYAD'S WRITTEN RECORD (operator decree 2026-09-03).

"I want two logs: the engine log and the dyad log, both available in the editor,
especially the dyad log so I can watch the reports it gives."

The engine already records its own session (F4: session_*.jsonl, drawn in the
LOG dock). This module is the dyad's half: every report the eye produces —
see / watch_one / watch / hear — lands as ONE JSON line in
Saved/dyad/dyad_log.jsonl the moment it completes. The Studio DOCS browser
serves both files as live pages, so the operator reads the eye's verdicts in
the editor instead of a terminal scroll.

LAWS
- Append-only. One record per call. The record lands whether the call
  SUCCEEDED, FAILED, or never spoke (dark eye) — a log of only successes
  is a lie.
- Model identity is recorded twice: what was REQUESTED and what actually
  SERVED (the identity law — readings are comparable only when the eye's
  identity is known).
- The report text is stored capped at DYAD_LOG_REPORT_CAP chars with an
  explicit truncation marker; `report_chars` always carries the TRUE length.
  (The full report lives with the caller; the log is the readable record,
  and a 60k-token dump would make the docs page unusable.)
- Never raises. A logging failure must not take down perception.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

REPORT_CAP = 16384   # chars of the report kept per line; the marker records the rest

# Anchored to THIS file's location (ChimeraEngine/) so the log is found no
# matter the caller's CWD — the engine reads it at <repo>/Saved/dyad/.
def dyad_log_path() -> Path:
    return Path(__file__).resolve().parent.parent / "Saved" / "dyad" / "dyad_log.jsonl"


def append(kind: str, *, model=None, served=None, tag: str = "",
           prompt_chars: int = 0, n_images: int = 0, image: str = "",
           report=None, error: str = "", elapsed_s: float | None = None,
           finish_reason=None) -> None:
    """One dyad call = one line. Never raises."""
    try:
        rep = "" if report is None else str(report)
        true_len = len(rep)
        trunc = False
        if true_len > REPORT_CAP:
            rep = rep[:REPORT_CAP] + f" ...[+{true_len - REPORT_CAP} chars truncated in log]"
            trunc = True
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "kind": kind,                                   # see|watch_one|watch|hear
            "model": model,                                 # requested
            "served": served,                               # what actually answered
            "tag": tag,
            "prompt_chars": prompt_chars,
            "n_images": n_images,
            "image": os.path.basename(image) if image else "",
            "report_chars": true_len,
            "truncated_in_log": trunc,
            "report": rep,
            "error": error,
            "elapsed_s": round(elapsed_s, 1) if elapsed_s is not None else None,
            "finish_reason": finish_reason,
        }
        p = dyad_log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:                                   # never break perception
        try:
            print(f"[dyad_log] append FAILED: {e}", flush=True)
        except Exception:
            pass
