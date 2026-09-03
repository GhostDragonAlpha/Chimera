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


def _plain_text(s: str) -> str:
    """Markdown-normalize a report for the HUMAN log: the eye answers in
    markdown (**bold**, `code`, ### headings), which reads as raw markup
    artifacts in a one-line log view (the dyad's own round-4 finding). The
    .jsonl keeps the raw text; this is the readable twin's rendering."""
    import re
    s = re.sub(r"^#{1,6}\s+", "", s, flags=re.M)     # heading markers
    s = s.replace("**", "").replace("__", "")          # bold
    s = re.sub(r"(?<!\w)\*(?!\s)\s*|\s*\*(?!\w)", "", s)  # italic stars (keep stray math asterisks rare)
    s = s.replace("`", "")                            # code spans
    s = s.replace('\\"', '"').replace("\\n", " ")     # JSON escapes that leak
    return s

# Anchored to THIS file's location (ChimeraEngine/) so the log is found no
# matter the caller's CWD — the engine reads it at <repo>/Saved/dyad/.
def dyad_log_path() -> Path:
    return Path(__file__).resolve().parent.parent / "Saved" / "dyad" / "dyad_log.jsonl"


def dyad_log_txt_path() -> Path:
    """The HUMAN-READABLE companion the Studio serves on its DYAD LOG page.
    The .jsonl stays the machine record (tools parse it); this file is what
    the operator's eyes get — one clean line per call, no JSON noise. The
    WRITER owns the formatting; the engine stays a verbatim file browser."""
    return Path(__file__).resolve().parent.parent / "Saved" / "dyad" / "dyad_log.txt"


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
        # The human-readable twin — the line the operator reads in the editor.
        human = f"{rec['ts']} | {kind} | {model or '?'}"
        if served and served != model:
            human += f" (served {served})"
        if n_images:
            human += f" | {n_images} img"
        if tag:
            human += f" | {tag}"
        if elapsed_s is not None:
            human += f" | {elapsed_s:.1f}s"
        if error:
            human += f" | ERROR: {error}"
        elif rep:
            flat = " ".join(_plain_text(rep).split())   # markdown-normalized, flattened: one line per call
            human += " | " + (flat[:220] + "..." if len(flat) > 220 else flat)
        if finish_reason:
            human += f" [{finish_reason}]"
        with dyad_log_txt_path().open("a", encoding="utf-8") as f:
            f.write(human + "\n")
    except Exception as e:                                   # never break perception
        try:
            print(f"[dyad_log] append FAILED: {e}", flush=True)
        except Exception:
            pass
