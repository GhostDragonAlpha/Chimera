"""collectors.py -- retroactive collectors over EXISTING evidence, READ-ONLY.

Four independent record families (the F-EVENT-GAP reconciliation surface):
  1. wave receipts   tools/science_funnel/validation/gait_zero_20260919/receipt_waveNN.json
                     (read from the most complete w3*-agent worktree; sha256'd)
  2. git history     prereg / amendment / ship commits per wave, from the canonical
                     clone AND from a chained lane worktree (waves 33-38 chain)
  3. janitor ledger  E:/ChimeraWork/lane-archive/_janitor/janitor.jsonl (worktree
                     lifecycle: spared / deleted / archived, with ts + tip shas)
  4. lane artifacts  .tmp/wNN_receipt/* file mtimes in the wave worktrees -- the
                     only sub-commit-granularity clock that survives

No lane is modified. Nothing is written outside this repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime
from typing import Optional

# ---- fixed source locations (existing evidence; none of this is written) ----

CHIMERA_WORK = r"E:\ChimeraWork"
# most-complete-first: the later lanes carry every earlier receipt
RECEIPT_WORKTREES = ["w39-agent", "w38-agent", "w37-agent", "w36-agent", "w35-agent"]
RECEIPT_REL = os.path.join("tools", "science_funnel", "validation",
                           "gait_zero_20260919")
WAVES = [28, "28b", 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]
# lanes whose .tmp artifacts survive with mtimes (the timed half of the pilot)
TIMED_WAVES = [35, 36, 37, 38]
JANITOR_JSONL = os.path.join(CHIMERA_WORK, "lane-archive", "_janitor",
                             "janitor.jsonl")
# chained lane repo: its history contains the full wave-33..38 commit chain
LANE_REPO = os.path.join(CHIMERA_WORK, "w38-agent")
CANON_REPO = os.path.join(CHIMERA_WORK, "telem-agent")

WAVE_PAT = re.compile(r"wave[- ]?(\d+[b]?)", re.IGNORECASE)
# the janitor names worktrees 'w34-agent' (no 'ave') -- match that shape too
WORKTREE_PAT = re.compile(r"^w(\d+[b]?)-agent$", re.IGNORECASE)


def _norm_wave(tok: str):
    tok = tok.lower().rstrip(".:")
    if tok.endswith("b"):
        return tok
    return int(tok)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime(path: str) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).astimezone()
    except OSError:
        return None


def iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def to_epoch(dt: Optional[datetime]) -> Optional[float]:
    return dt.timestamp() if dt else None


# ---------------------------------------------------------------- receipts --

def collect_receipts() -> dict:
    """wave -> {path, sha256, doc}; first worktree that carries the receipt."""
    out = {}
    for w in WAVES:
        name = f"receipt_wave{w}.json"
        for wt in RECEIPT_WORKTREES:
            p = os.path.join(CHIMERA_WORK, wt, RECEIPT_REL, name)
            if os.path.isfile(p):
                with open(p, encoding="utf-8") as fh:
                    doc = json.load(fh)
                out[str(w)] = {"wave": str(w), "path": p, "source_worktree": wt,
                               "sha256": sha256_file(p), "doc": doc,
                               "file_mtime": iso(mtime(p))}
                break
    return out


# --------------------------------------------------------------------- git --

def git_log(repo: str, *args: str) -> list:
    cmd = ["git", "-C", repo, "log", "--format=%h|%cI|%s", *args]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    if res.returncode != 0:
        return []
    rows = []
    for line in res.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append({"sha": parts[0], "ts": parts[1],
                         "subject": parts[2], "repo": os.path.basename(repo)})
    return rows


def _role(subject: str) -> str:
    """Classify a wave commit by its LEAD-IN, not its full subject.

    The ship commits' subjects run hundreds of chars and routinely mention
    'amendment' or 'frozen' in the body of the sentence; the prereg/amendment
    commits name it in the LEAD. So: markers are only trusted in the lead.
      'Wave NN RULE-0 PRE-REGISTRATION (...)' / 'WAVE NN AMENDMENT...' -> prereg
      'Wave NN: THE ... LAW ...' / 'WAVE NN SHIP (...)'                -> ship
      'Merge wave-NN ...'                                             -> merge
    """
    s = subject.strip().lower()
    if s.startswith("merge wave"):
        return "merge"
    if not s.startswith("wave"):
        return "other"
    lead = subject.split(":", 1)[0][:48].lower()
    if any(m in lead for m in ("pre-registration", "prereg", "amendment",
                               "freeze")):
        return "prereg"
    return "ship"


def collect_wave_commits() -> dict:
    """wave -> [commit rows] from BOTH git sources (canonical + chained lane)."""
    out = {str(w): [] for w in WAVES}
    seen = set()
    for repo, rng in ((CANON_REPO, ["master", "--since=2026-09-19"]),
                      (LANE_REPO, ["--since=2026-09-20"])):
        for row in git_log(repo, *rng):
            key = row["sha"]
            if key in seen:
                continue
            seen.add(key)
            m = WAVE_PAT.search(row["subject"])
            if not m:
                continue
            w = _norm_wave(m.group(1))
            if str(w) in out:
                row["wave"] = str(w)
                row["role"] = _role(row["subject"])
                out[str(w)].append(row)
    return out


# --------------------------------------------------------- lane artifacts --

def collect_lane_artifacts() -> dict:
    """wave -> {filename: iso_mtime} for .tmp/wNN_receipt (waves 35-38)."""
    out = {}
    for w in TIMED_WAVES:
        wt = f"w{w}-agent"
        d = os.path.join(CHIMERA_WORK, wt, ".tmp", f"w{w}_receipt")
        files = {}
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                p = os.path.join(d, fn)
                if os.path.isfile(p):
                    files[fn] = iso(mtime(p))
        out[str(w)] = {"worktree": wt, "dir": d, "files": files}
    return out


# ----------------------------------------------------------------- janitor --

def collect_janitor() -> list:
    rows = []
    if not os.path.isfile(JANITOR_JSONL):
        return rows
    with open(JANITOR_JSONL, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = WAVE_PAT.search(str(doc.get("dir", ""))) or \
                WORKTREE_PAT.match(str(doc.get("dir", "")).strip())
            if m:
                w = _norm_wave(m.group(1))
                doc["wave"] = str(w)
                rows.append(doc)
    return rows
