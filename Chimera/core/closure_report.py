"""
Typed closure report — the exit interview a session cannot talk its way past.

WHY (2026-07-17, the human's design: "reports as behavioral guardrails; the
report is the primary actor — agents fill forms, the forms dictate the work").
Three external-agent failures in ONE day all lived in free prose: a skipped
build claimed politely ("UBT verification was skipped due to Live Coding"), a
two-builds-stale LNK2019 quoted as the current blocker, and a witness that
never ran on a task closed `done`. Prose lets a session talk its way past its
own evidence. A typed report with resolving references does not.

THREE LAYERS (each catches what the previous cannot):

  1. MECHANICAL — blocks. Every evidence field is a GRAPH REFERENCE that must
     RESOLVE, and build evidence must be NEWER than the session's Source
     changes (subsumes the tb-0128 build-currency gate). A field can lie; a
     resolving id compared by timestamp cannot — the same doctrine as the
     why-edges, applied to closure.
  2. AUTO ACTION LOG — attached, not described. `git diff --stat` since the
     tunnel's enter snapshot IS the record of what changed; nobody summarizes
     their own diff again.
  3. THE BRAIN — advisory by default (the human: "have the brain be the judge
     of the report"). The Coin judges the TYPED faces: does the claim cohere
     with the auto action log; does could_not_verify contradict the headline;
     is the evidence the target or a proxy. An LLM is never a terminal — its
     verdict is another claim, recorded. CHIMERA_REPORT_JUDGE=block hardens,
     =off disables; LM down -> no judgment, never a block.

CHIMERA_REPORT_GATE=warn softens mechanical blocks to warnings; =off disables.
Waiver idiom preserved: --report-waiver records an honest exception (CAPCOM'd).
"""
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent            # E:\PythonChimera\Chimera
REPO = ROOT.parent            # E:\PythonChimera

_SOURCE_PREFIX = "Chimera/Source/"


def gate_mode() -> str:
    v = os.environ.get("CHIMERA_REPORT_GATE", "").strip().lower()
    return v if v in ("warn", "off") else "block"


def judge_mode() -> str:
    v = os.environ.get("CHIMERA_REPORT_JUDGE", "").strip().lower()
    return v if v in ("block", "off") else "advisory"


def _git(*args, timeout=15) -> str:
    try:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                              text=True, timeout=timeout).stdout
    except Exception:
        return ""


def head_sha() -> str:
    return _git("rev-parse", "HEAD").strip()


def _epoch(ts) -> float:
    """ISO string (naive = UTC, matching graphify's node timestamps) -> epoch."""
    if not ts:
        return 0.0
    try:
        s = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        return 0.0


def source_changes(session: dict) -> dict:
    """C++ (Chimera/Source/**) changed during THIS session: committed since the
    enter snapshot's HEAD plus currently-dirty files. Returns {files, newest_ts}
    (newest_ts = epoch of the latest change; 0 when nothing changed)."""
    sha = (session or {}).get("head_sha") or ""
    entered = _epoch((session or {}).get("entered_at"))
    files, stamps = set(), []
    if sha:
        names = _git("diff", "--name-only", f"{sha}..HEAD", "--", _SOURCE_PREFIX)
        files |= {l.strip() for l in names.splitlines() if l.strip()}
        for t in _git("log", f"{sha}..HEAD", "--format=%at", "--",
                      _SOURCE_PREFIX).split():
            try:
                stamps.append(float(t))
            except ValueError:
                pass
    elif entered:
        # raw claims have no snapshot — fall back to commits since claim time
        since = datetime.fromtimestamp(entered, tz=timezone.utc).isoformat()
        names = _git("log", f"--since={since}", "--name-only", "--format=%at",
                     "--", _SOURCE_PREFIX)
        for l in names.splitlines():
            l = l.strip()
            if not l:
                continue
            if re.fullmatch(r"\d{9,11}", l):
                stamps.append(float(l))
            elif l.startswith(_SOURCE_PREFIX):
                files.add(l)
    # Pre-existing dirt (another lane's staged work, uncommitted session debris)
    # is NOT this session's change — same alarm-fatigue rationale as the tunnel's
    # footprint warnings. A baseline file counts only if touched AGAIN during
    # this session (mtime after enter disambiguates).
    baseline = set((session or {}).get("baseline_dirty") or [])
    porcelain = _git("status", "--porcelain", "--", _SOURCE_PREFIX)
    for line in porcelain.splitlines():
        p = line[3:].strip().strip('"')
        if not p:
            continue
        try:
            mtime = (REPO / p).stat().st_mtime
        except OSError:
            mtime = 0.0
        if p in baseline and (not entered or mtime <= entered):
            continue
        files.add(p)
        if mtime:
            stamps.append(mtime)
    return {"files": sorted(files)[:40], "newest_ts": max(stamps) if stamps else 0.0}


def action_log(session: dict, cap: int = 2400) -> str:
    """The record IS the summary: committed + working-tree diff --stat since
    the enter snapshot."""
    sha = (session or {}).get("head_sha") or ""
    parts = []
    if sha:
        committed = _git("diff", "--stat", f"{sha}..HEAD").strip()
        if committed:
            parts.append(f"committed since enter ({sha[:9]}..HEAD):\n{committed}")
    working = _git("diff", "--stat").strip()
    if working:
        parts.append(f"working tree (uncommitted):\n{working}")
    return ("\n".join(parts) or "(no tracked changes since enter)")[:cap]


def _resolve(node_id: str):
    """A citation must NAME A NODE (the why-doctrine: a non-empty string is not
    a citation). Live graph only."""
    if not (node_id or "").strip():
        return None
    try:
        from core.graphify_interface import load_dna_graph
        for n in load_dna_graph().get("nodes", []):
            if n.get("id") == node_id.strip():
                return n
    except Exception:
        return None
    return None


def demands_witness(task: dict) -> bool:
    text = f"{(task or {}).get('title', '')} {(task or {}).get('recipe', '')}"
    return re.search(r"\b(witness|sleepwalker|simtest|beats?)\b", text, re.I) is not None


_WITNESS_TYPES = {"SimPlaytest", "Observation"}


def validate(task: dict, session: dict, result: str, build_evidence: str = "",
             witness_evidence: str = "", could_not_verify: str = None,
             waiver: str = "") -> tuple:
    """(status, detail, report). status: 'pass' | 'waived' | 'missing'.
    The caller refuses closure on 'missing' when gate_mode() == 'block'."""
    changes = source_changes(session)
    report = {
        "claim": (result or "")[:800],
        "build_evidence": (build_evidence or "").strip(),
        "witness_evidence": (witness_evidence or "").strip(),
        "could_not_verify": (could_not_verify or "").strip(),
        "source_changes": changes["files"],
        "action_log": action_log(session),
        "validated": {},
        "waiver": (waiver or "").strip(),
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    misses = []

    # A) could_not_verify is MANDATORY — explicit "none" allowed, silence is not.
    if not report["could_not_verify"]:
        misses.append('could_not_verify is required — state what you could NOT '
                      'verify, or explicitly "none"')
    report["validated"]["could_not_verify"] = bool(report["could_not_verify"])

    # B) Source changed -> build evidence must resolve, pass, and be NEWER.
    if changes["files"]:
        node = _resolve(report["build_evidence"])
        if node is None:
            misses.append(
                f'{len(changes["files"])} Source file(s) changed this session but '
                f'build_evidence names no graph node — run the real UBT, record it '
                f'(record_build), cite the mutation id. Files: '
                f'{", ".join(changes["files"][:4])}…')
            report["validated"]["build"] = "missing"
        else:
            ok_pass = (node.get("error_signature") == "success_no_error"
                       or "Succeeded" in str(node.get("ubt_output_excerpt", "")))
            ok_fresh = _epoch(node.get("timestamp")) >= changes["newest_ts"]
            if not ok_pass:
                misses.append(f'build_evidence {node["id"]} is not a PASSING build')
            if not ok_fresh:
                misses.append(
                    f'build_evidence {node["id"]} is OLDER than the newest Source '
                    f'change — a historical green is not a current green; rebuild')
            report["validated"]["build"] = ("ok" if (ok_pass and ok_fresh)
                                            else "stale-or-failing")
    else:
        report["validated"]["build"] = "n/a (no Source changes)"

    # C) Recipe demands a witness -> the id must resolve to a witness-type node
    #    created during this session.
    if demands_witness(task):
        node = _resolve(report["witness_evidence"])
        entered = _epoch((session or {}).get("entered_at"))
        if node is None:
            misses.append(
                "this task's recipe demands a witness (witness/sleepwalker/beats) "
                "but witness_evidence names no graph node — run the beats, cite "
                "the simtest id")
            report["validated"]["witness"] = "missing"
        elif node.get("type") not in _WITNESS_TYPES:
            misses.append(f'witness_evidence {node["id"]} is a {node.get("type")}, '
                          f'not a SimPlaytest/Observation')
            report["validated"]["witness"] = "wrong-type"
        elif entered and _epoch(node.get("timestamp")) < entered:
            misses.append(f'witness_evidence {node["id"]} predates this session — '
                          f'H-19: an old simtest can describe a feature already '
                          f'changed since')
            report["validated"]["witness"] = "stale"
        else:
            report["validated"]["witness"] = "ok"
    else:
        report["validated"]["witness"] = "n/a (recipe demands none)"

    if not misses:
        return "pass", "closure report validated", report
    if report["waiver"]:
        _capcom(f"report WAIVED on {task.get('id')}: {report['waiver'][:70]}", "note")
        return "waived", report["waiver"], report
    return "missing", "; ".join(misses), report


def brain_judgment(report: dict, task: dict):
    """Layer 3 — the Coin flips over the TYPED faces (the human: 'have the
    brain be the judge of the report'). Returns the judgment dict, or None
    (LM down / disabled) — advisory unless CHIMERA_REPORT_JUDGE=block."""
    if judge_mode() == "off":
        return None
    try:
        from core.coin_verifier import judge
    except Exception:
        return None
    heads = (f"Task '{(task or {}).get('id')}: {(task or {}).get('title', '')}' is "
             f"being closed DONE.\nAgent's claim: {report.get('claim')}\n"
             f"Agent's could_not_verify: {report.get('could_not_verify')}")
    tails = (f"AUTO-COLLECTED ACTION LOG (git, not the agent):\n"
             f"{report.get('action_log')}\n\n"
             f"MECHANICAL VALIDATION: {json.dumps(report.get('validated'))}\n"
             f"build_evidence: {report.get('build_evidence') or '(none cited)'}\n"
             f"witness_evidence: {report.get('witness_evidence') or '(none cited)'}"
             + (f"\nRECORDED WAIVER (explains any misses above): "
                f"{report['waiver']}" if report.get("waiver") else ""))
    return judge(heads, tails)


def _capcom(msg: str, level: str = "warn"):
    try:
        from core.capcom import post_safe
        post_safe("report", msg, level=level, source="closure-report")
    except Exception:
        pass
