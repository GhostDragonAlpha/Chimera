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

FOOTPRINT SCOPING (2026-07-18, tb-0182): layers 1+2 used to diff the WHOLE
repo. Three concurrent subagents false-convicted each other in one night —
each got handed a build-evidence demand (or a Coin tails) naming a SIBLING's
Source/ file, because `source_changes`/`action_log` never looked at the
claiming task's own footprint (`resources.files`, already sitting on the
`task` dict `validate()` receives). Fix: every changed-file list is split by
`_in_scope()` (an fnmatch against the footprint globs, mirroring
`agent_tunnel._offenders_from_porcelain`'s Chimera/-stripped matching) BEFORE
it drives a demand. In-footprint files behave exactly as before; out-of-
footprint files are never hidden — they still appear, under a labeled
"outside footprint (concurrent sessions)" section — but they cannot trigger
the build-evidence demand and the Coin's tails no longer sees them as if
they were this task's own diff. No declared footprint (`resources.files`
empty) -> everything counts as in-footprint, unchanged from before: absence
of a footprint is not evidence a file is a sibling's, so nothing is exempted.

CHIMERA_REPORT_GATE=warn softens mechanical blocks to warnings; =off disables.
Waiver idiom preserved: --report-waiver records an honest exception (CAPCOM'd).
"""
import fnmatch
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


_REPO_PREFIX = "Chimera/"


def _footprint_scopes(task: dict) -> list:
    """The claiming task's declared file footprint (resources.files globs,
    Chimera-root-relative — see task_board.py's docstring). Empty when the
    task declared none."""
    return list(((task or {}).get("resources") or {}).get("files") or [])


def _in_scope(path: str, scopes: list) -> bool:
    """True if repo-relative `path` (e.g. 'Chimera/core/x.py') falls inside
    one of the task's footprint globs. Mirrors agent_tunnel's
    `_offenders_from_porcelain` matching exactly (fnmatch against both the
    raw and the Chimera/-stripped path, plus a literal-prefix fallback for
    globs without a trailing wildcard) — one matching rule, not two
    almost-the-same ones. No scopes declared -> everything is in-footprint:
    absence of a declared footprint is not evidence a file is a SIBLING's, so
    nothing gets exempted from the demand by default."""
    if not scopes:
        return True
    p = (path or "").replace("\\", "/")
    rel = p[len(_REPO_PREFIX):] if p.startswith(_REPO_PREFIX) else p
    return any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(p, g)
               or rel.startswith(g.split("*")[0]) for g in scopes)


def _split_paths(paths, scopes: list) -> tuple:
    """(in_footprint, out_of_footprint), order-preserving."""
    inn, out = [], []
    for p in paths:
        (inn if _in_scope(p, scopes) else out).append(p)
    return inn, out


def _log_blocks(rev_args: list, pathspec: str) -> list:
    """[(commit_epoch, [files]), ...], newest first, ONE git call. A footprint
    split needs to know WHICH commit touched WHICH file — the old code read
    timestamps and filenames as two unrelated streams (fine when nothing
    needed to attribute a stamp to a file; not fine once a foreign commit
    landed on HEAD mid-session from a concurrent agent's Lead-integration and
    its timestamp got attributed to THIS task's footprint by proximity
    alone)."""
    out = _git("log", *rev_args, "--name-only", "--format=@@%at", "--", pathspec)
    blocks, ts, cur = [], None, []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("@@"):
            if ts is not None:
                blocks.append((ts, cur))
            try:
                ts = float(line[2:])
            except ValueError:
                ts = 0.0
            cur = []
        else:
            cur.append(line)
    if ts is not None:
        blocks.append((ts, cur))
    return blocks


def source_changes(session: dict, task: dict = None) -> dict:
    """C++ (Chimera/Source/**) changed during THIS session: committed since the
    enter snapshot's HEAD plus currently-dirty files, SCOPED to the claiming
    task's declared footprint (resources.files) so a CONCURRENT session's
    sibling Source/ edits never feed THIS task's build-evidence demand (three
    same-night false-convictions, tb-0182). Returns {files, newest_ts,
    outside_footprint} — outside_footprint is never hidden, just excluded
    from the demand (newest_ts is computed from in-footprint stamps only)."""
    scopes = _footprint_scopes(task)
    sha = (session or {}).get("head_sha") or ""
    entered = _epoch((session or {}).get("entered_at"))
    files_in, files_out, stamps = set(), set(), []

    if sha:
        blocks = _log_blocks([f"{sha}..HEAD"], _SOURCE_PREFIX)
    elif entered:
        # raw claims have no snapshot — fall back to commits since claim time
        since = datetime.fromtimestamp(entered, tz=timezone.utc).isoformat()
        blocks = _log_blocks([f"--since={since}"], _SOURCE_PREFIX)
    else:
        blocks = []
    for ts, fs in blocks:
        inn, out = _split_paths(fs, scopes)
        files_in.update(inn)
        files_out.update(out)
        if inn:
            stamps.append(ts)

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
        if _in_scope(p, scopes):
            files_in.add(p)
            if mtime:
                stamps.append(mtime)
        else:
            files_out.add(p)
    return {"files": sorted(files_in)[:40],
            "newest_ts": max(stamps) if stamps else 0.0,
            "outside_footprint": sorted(files_out)[:40]}


def _git_stat_for(extra_args: list, paths: list) -> str:
    """`git diff --stat` restricted to an explicit pathspec list. Empty
    `paths` returns '' rather than falling through to a bare `--` (which git
    reads as NO restriction at all — exactly the silent-widen this scoping
    exists to stop)."""
    if not paths:
        return ""
    return _git("diff", *extra_args, "--stat", "--", *paths).strip()


def action_log(session: dict, task: dict = None, cap: int = 2400) -> str:
    """The record IS the summary: everything that changed since the enter
    snapshot — committed, staged, unstaged, AND untracked-new.

    Naive `git diff --stat` sees only UNSTAGED tracked changes, so it is blind to
    exactly the work a build/train task exists to do: a brand-new trainables/*.py
    or objectives/*.json is untracked, and running it through `core.membrane`
    (whose `git stash create` only captures the index) forces it STAGED first —
    either way `git diff --stat` shows nothing, the log reads empty, and the Coin
    correctly convicts a claim whose files 'aren't in the record'. That was a
    false negative on new-file work (found by sub-22 on tb-0166, 2026-07-18).

    SCOPED to the claiming task's footprint (2026-07-18, tb-0182): each
    changed-file list is split against resources.files globs before the stat
    is computed, so a CONCURRENT session's edits elsewhere in the repo land
    in a separate 'outside footprint (concurrent sessions)' section instead
    of reading as THIS task's own diff — the Coin's tails face now judges
    only what this task actually touched. Nothing is hidden: outside-
    footprint files are still listed, just segregated."""
    scopes = _footprint_scopes(task)
    sha = (session or {}).get("head_sha") or ""
    parts, outside = [], set()

    if sha:
        names = [n.strip() for n in
                 _git("diff", "--name-only", f"{sha}..HEAD").splitlines() if n.strip()]
        inn, out = _split_paths(names, scopes)
        outside |= set(out)
        committed = _git_stat_for([f"{sha}..HEAD"], inn)
        if committed:
            parts.append(f"committed since enter ({sha[:9]}..HEAD):\n{committed}")

    staged_names = [n.strip() for n in
                    _git("diff", "--cached", "--name-only").splitlines() if n.strip()]
    inn, out = _split_paths(staged_names, scopes)
    outside |= set(out)
    staged = _git_stat_for(["--cached"], inn)
    if staged:
        parts.append(f"staged (index):\n{staged}")

    working_names = [n.strip() for n in
                     _git("diff", "--name-only").splitlines() if n.strip()]
    inn, out = _split_paths(working_names, scopes)
    outside |= set(out)
    working = _git_stat_for([], inn)
    if working:
        parts.append(f"working tree (unstaged):\n{working}")

    # Untracked NEW files appear in NO `git diff` — only in status --porcelain.
    untracked = [ln[3:].strip() for ln in _git("status", "--porcelain").splitlines()
                 if ln.startswith("??")]
    inn, out = _split_paths(untracked, scopes)
    outside |= set(out)
    if inn:
        shown = "\n".join(f" {u}" for u in inn[:40])
        more = f"\n …(+{len(inn) - 40} more)" if len(inn) > 40 else ""
        parts.append(f"untracked (new files):\n{shown}{more}")

    if outside:
        shown = "\n".join(f" {u}" for u in sorted(outside)[:40])
        more = f"\n …(+{len(outside) - 40} more)" if len(outside) > 40 else ""
        parts.append(f"outside footprint (concurrent sessions):\n{shown}{more}")

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
    # Match the witness ARTIFACT, never the English verb. Bare singular "beat"
    # caught "cannot beat the mesh render" in tb-0168's own recipe and forced a
    # bogus witness demand (found by sub-20, 2026-07-18). The real signals are
    # the plural "beats" (the file convention, "run the beats"), "beat script",
    # a ".beats"/"beats.json" path, or the tool names — not "beat" alone.
    text = f"{(task or {}).get('title', '')} {(task or {}).get('recipe', '')}"
    pat = r"\b(witness|sleepwalker|simtest|beats|beat[\s_-]scripts?)\b|\.beats\b|beats\.json"
    return re.search(pat, text, re.I) is not None


_WITNESS_TYPES = {"SimPlaytest", "Observation"}


def validate(task: dict, session: dict, result: str, build_evidence: str = "",
             witness_evidence: str = "", could_not_verify: str = None,
             waiver: str = "", build_waiver: str = "") -> tuple:
    """(status, detail, report). status: 'pass' | 'waived' | 'missing'.
    The caller refuses closure on 'missing' when gate_mode() == 'block'."""
    changes = source_changes(session, task)
    report = {
        "claim": (result or "")[:800],
        "build_evidence": (build_evidence or "").strip(),
        "witness_evidence": (witness_evidence or "").strip(),
        "could_not_verify": (could_not_verify or "").strip(),
        "source_changes": changes["files"],
        "source_changes_outside_footprint": changes.get("outside_footprint", []),
        "action_log": action_log(session, task),
        "validated": {},
        "waiver": (waiver or "").strip(),
        "build_waiver": (build_waiver or "").strip(),
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
                f'{", ".join(changes["files"][:4])}…\n'
                f'To build: E:\\PythonChimera\\Chimera> run_build.bat build\n'
                f'Or via UBT directly: dotnet "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll" '
                f'Chimera Win64 Development -project="E:\\PythonChimera\\Chimera\\Chimera.uproject" -progress')
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
                    f'change — a historical green is not a current green; rebuild.\n'
                    f'To build: E:\\PythonChimera\\Chimera> run_build.bat build\n'
                    f'Or via UBT directly: dotnet "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll" '
                    f'Chimera Win64 Development -project="E:\\PythonChimera\\Chimera\\Chimera.uproject" -progress')
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
    # Check for build-waiver (honest exceptions like header-only doc comment)
    if report["build_waiver"] and any("build_evidence" in m or "historical green" in m or "names no graph node" in m for m in misses):
        _capcom(f"report WAIVED on {task.get('id')}: build-waiver — {report['build_waiver'][:70]}", "note")
        return "waived", report["build_waiver"], report
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
